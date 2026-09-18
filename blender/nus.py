"""nus — the 3D shots, built from nothing and rendered headless.

  blender -b --factory-startup -P blender/nus.py -- --shot open [--frames 0:189] [--engine eevee|cycles] [--samples 64] [--scale 100]

Shots (film frames, 60 fps, 152 bpm — every key comes from src/score.json's grid):
  open       beats 0–8    white   the lid lifts, the screen comes on, the camera flies into it
  macro      beats 24–25  white   Ctrl+Shift, then K, at f/1.8
  internals  beats 28–44  black   the software's parts as machined slabs, parting in haze
  outro      beats 52–64  black   rim light, a theme a beat, the lid shuts

Output: public/renders/<shot>/f####.png, numbered by film frame, so the
film maps a frame straight to a file. White shots render with a transparent
ground and a shadow-only floor, to sit on pure #fff; black shots on pure #000.

The laptop is ours: an ink-anodised unibody with a polished chamfer on every
edge (the line the light rides), a red hinge, a square lid with no notch and
no logo, keycaps with Plex Mono legends. Units are metres.
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE = json.load(open(os.path.join(ROOT, "src", "score.json")))
FPS = 60
FPB = FPS * 60 / SCORE["bpm"]  # 23.684 frames a beat
SHOTS = os.path.join(ROOT, "public", "shots")
FOOTAGE = os.path.join(ROOT, "public", "footage")
FONT = os.path.join(ROOT, "public", "fonts", "IBMPlexMono-Regular.ttf")
FONT_BOLD = os.path.join(ROOT, "public", "fonts", "IBMPlexMono-SemiBold.ttf")

RANGES = {"open": (0, 8), "macro": (24, 25), "internals": (28, 44), "outro": (52, 64)}


def B(beat):
    """A beat on the film's frame axis."""
    return beat * FPB


def frames(shot):
    a, b = RANGES[shot]
    return math.ceil(B(a)), math.ceil(B(b)) - 1


# ── Keys, with the app's one curve ─────────────────────────────────────────────
_EASE = []


def key(obj, path, beat, value, ease="out", index=-1):
    """Keyframe `path` at `beat`; `ease` shapes the move that leaves this key:
    'out' (cubic ease-out — nus's curve), 'linear', or 'hold'."""
    target = obj
    attr = path
    if "." in path:
        head, attr = path.rsplit(".", 1)
        target = obj.path_resolve(head)
    if index >= 0:
        getattr(target, attr)[index] = value
    else:
        setattr(target, attr, value)
    obj.keyframe_insert(data_path=path, frame=B(beat), index=index)
    _EASE.append((obj, path, B(beat), ease))


def finish_keys():
    for obj, path, frame, ease in _EASE:
        ad = obj.animation_data
        if not ad or not ad.action:
            continue
        for fc in ad.action.fcurves:
            if fc.data_path != path:
                continue
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 1e-3:
                    if ease == "out":
                        kp.interpolation = "CUBIC"
                        kp.easing = "EASE_OUT"
                    elif ease == "linear":
                        kp.interpolation = "LINEAR"
                    else:
                        kp.interpolation = "CONSTANT"


# ── Materials ──────────────────────────────────────────────────────────────────
def principled(name, color, metallic=0.0, roughness=0.5, **extra):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    for k, v in extra.items():
        p.inputs[k].default_value = v
    return m


def srgb(hex_):
    c = [int(hex_[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def image_material(name, path, strength=1.0, gloss=0.05, start_beat=0):
    """A screen: the picture as emission, under a thin glossy coat that
    catches the rim lights. A movie's first frame lands on `start_beat`."""
    m = principled(name, (0, 0, 0), roughness=gloss)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    if path.endswith(".mp4"):
        img = bpy.data.images.load(path)
        img.source = "MOVIE"
        tex.image_user.frame_duration = 100000
        tex.image_user.frame_start = round(B(start_beat))
        tex.image_user.use_auto_refresh = True
    else:
        img = bpy.data.images.load(path, check_existing=True)
    tex.image = img
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Specular IOR Level"].default_value = 0.35
    return m


def screen_source(name):
    """Reshoot footage wins over the still, when it has arrived."""
    mp4 = os.path.join(FOOTAGE, f"{name}.mp4")
    return mp4 if os.path.exists(mp4) else os.path.join(SHOTS, f"{name}.png")


INTERNALS = os.path.join(ROOT, "public", "internals")


def layer_source(layer):
    """The compositor's own layer dump (RESHOOT.md), else the window capture."""
    png = os.path.join(INTERNALS, f"{layer}.png")
    return png if os.path.exists(png) else screen_source("window-ink")


MAT = {}


def materials():
    MAT["body"] = principled("Anodised ink", srgb("#141517"), metallic=0.9, roughness=0.26)
    MAT["chamfer"] = principled("Polished chamfer", srgb("#d9dadc"), metallic=1.0, roughness=0.06)
    MAT["bezel"] = principled("Bezel glass", (0.002, 0.002, 0.002), roughness=0.05, **{"Specular IOR Level": 0.5})
    MAT["well"] = principled("Key well", (0.003, 0.003, 0.003), roughness=0.8)
    MAT["cap"] = principled("Keycap", srgb("#0d0d0f"), roughness=0.68, **{"Specular IOR Level": 0.08})
    MAT["legend"] = principled("Legend", srgb("#bdb8ab"), roughness=0.6)
    MAT["pad"] = principled("Trackpad", srgb("#141518"), metallic=0.3, roughness=0.34, **{"Specular IOR Level": 0.2})
    MAT["hinge"] = principled("Signal hinge", srgb("#c8102e"), metallic=0.9, roughness=0.3)
    MAT["black"] = principled("Off", (0, 0, 0), roughness=0.05, **{"Specular IOR Level": 0.35})
    # White-ground floor: invisible where lit, ink where shadowed (EEVEE's
    # stand-in for a shadow catcher).
    m = bpy.data.materials.new("Shadow only")
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    nt = m.node_tree
    nt.nodes.clear()
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.25
    ramp.inputs["From Max"].default_value = 0.9
    ramp.inputs["To Min"].default_value = 0.42
    ramp.inputs["To Max"].default_value = 0.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0, 0, 0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    L = nt.links.new
    L(diff.outputs[0], s2r.inputs[0])
    L(s2r.outputs["Color"], bw.inputs[0])
    L(bw.outputs[0], ramp.inputs["Value"])
    L(ramp.outputs[0], mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs[0])
    MAT["floor"] = m


# ── Geometry ───────────────────────────────────────────────────────────────────
def rounded_prism(name, w, d, h, r, seg=10, chamfer=0.0006, mats=("body", "chamfer")):
    bm = bmesh.new()
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), 0)))
    face = bm.faces.new(pts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    top = [v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, 0, h))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        me.materials.append(MAT[m])
    if chamfer:
        bev = ob.modifiers.new("Chamfer", "BEVEL")
        bev.width = chamfer
        bev.segments = 1
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(35)
        bev.material = 1
    smooth(ob)
    return ob


def smooth(ob):
    """Smooth the rounded corners, keep the chamfers crisp."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))


def plane(name, corners, uvs, mat, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(c) for c in corners], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, l in enumerate(me.loops):
        uv.data[i].uv = uvs[l.vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def text(name, body, size, mat, parent, loc, rot=(0, 0, 0), bold=False, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT_BOLD if bold else FONT, check_existing=True)
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# The laptop. Base: x across, y front (−) to back (+), z up.
W, D, T = 0.312, 0.221, 0.0142
LID_D, LID_T = 0.214, 0.0052
PANEL_W = 0.296
PANEL_H = PANEL_W / 1.6
KEY_PITCH, KEY_CAP = 0.0182, 0.0162
ROWS = [
    (0.55, [("esc", 1.5)] + [(f"F{i}", 1) for i in range(1, 13)] + [("del", 1.5)]),
    (1, [("`", 1)] + [(c, 1) for c in "1234567890-="] + [("bksp", 2)]),
    (1, [("tab", 1.5)] + [(c, 1) for c in "QWERTYUIOP[]"] + [("\\", 1.5)]),
    (1, [("caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL;'"] + [("enter", 2.25)]),
    (1, [("shift", 2.25)] + [(c, 1) for c in "ZXCVBNM,./"] + [("shift", 2.75)]),
    (1, [("ctrl", 1.5), ("fn", 1), ("alt", 1.25), ("", 5.75), ("alt", 1.25), ("ctrl", 1.25), ("←", 1), ("↑↓", 1), ("→", 1)]),
]
KEYS = {}


def laptop():
    base = rounded_prism("Base", W, D, T, 0.006)
    # Keyboard: a dark well, then caps with Plex Mono legends.
    kb_w = 15 * KEY_PITCH
    top = D / 2 - 0.022
    heights = [h * KEY_PITCH for h, _ in ROWS]
    kb_d = sum(heights)
    well = plane("Key well", [(-kb_w / 2 - 0.002, top + 0.002, T + 0.00004), (kb_w / 2 + 0.002, top + 0.002, T + 0.00004), (kb_w / 2 + 0.002, top - kb_d - 0.002, T + 0.00004), (-kb_w / 2 - 0.002, top - kb_d - 0.002, T + 0.00004)], [(0, 1), (1, 1), (1, 0), (0, 0)], MAT["well"], base)
    y = top
    for r, (h, row) in enumerate(ROWS):
        x = -kb_w / 2
        pitch_h = h * KEY_PITCH
        for legend, units in row:
            cw = units * KEY_PITCH - (KEY_PITCH - KEY_CAP)
            ch = pitch_h - (KEY_PITCH - KEY_CAP)
            cx, cy = x + units * KEY_PITCH / 2, y - pitch_h / 2
            if legend == "↑↓":
                for i, (lg, dy) in enumerate((("↑", ch / 4 + 0.0003), ("↓", -ch / 4 - 0.0003))):
                    cap = rounded_prism(f"Key {r} {lg}", cw, ch / 2 - 0.0006, 0.0011, 0.0012, seg=3, chamfer=0.00025, mats=("cap", "chamfer"))
                    cap.parent = base
                    cap.location = (cx, cy + dy, T + 0.0002)
                    text(f"Legend {lg}", lg, 0.0026, MAT["legend"], cap, (0, 0, 0.00112))
            else:
                cap = rounded_prism(f"Key {r} {legend or 'space'} {x:.3f}", cw, ch, 0.0011, 0.0012, seg=3, chamfer=0.00025, mats=("cap", "chamfer"))
                cap.parent = base
                cap.location = (cx, cy, T + 0.0002)
                if legend:
                    size = 0.0034 if len(legend) == 1 else 0.0023
                    text(f"Legend {legend}", legend.lower() if len(legend) > 1 else legend, size, MAT["legend"], cap, (0, 0, 0.00112))
                KEYS.setdefault(legend or "space", []).append(cap)
            x += units * KEY_PITCH
        y -= pitch_h
    pad = rounded_prism("Trackpad", 0.126, 0.078, 0.0003, 0.003, seg=4, chamfer=0.0002, mats=("pad", "chamfer"))
    pad.parent = base
    pad.location = (0, -D / 2 + 0.012 + 0.039, T - 0.00012)
    # The hinge, in the signal red: the carapace's band, made of metal.
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0034, depth=W - 0.05, vertices=48, location=(0, D / 2 - 0.0036, T + 0.0006), rotation=(0, math.radians(90), 0))
    hinge = bpy.context.object
    hinge.name = "Hinge"
    hinge.data.materials.append(MAT["hinge"])
    for p in hinge.data.polygons:
        p.use_smooth = True
    # The lid, pivoting on the hinge line; it lies shut over the base, screen
    # down, and opens by rotating about x.
    lid = rounded_prism("Lid", W, LID_D, LID_T, 0.006, mats=("body", "chamfer", "bezel"))
    for v in lid.data.vertices:
        v.co.y -= LID_D / 2
    for p in lid.data.polygons:
        if p.normal.z < -0.9:
            p.material_index = 2
    pivot = bpy.data.objects.new("Lid pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (0, D / 2 - 0.0036, T + 0.0006)
    lid.parent = pivot
    lid.location = (0, 0.0024, 0)
    # The panel: under the bezel glass, facing −z while shut, the viewer when open.
    top_y, bot_y = -LID_D + 0.0095, -LID_D + 0.0095 + PANEL_H
    corners = [(-PANEL_W / 2, top_y, -0.00012), (-PANEL_W / 2, bot_y, -0.00012), (PANEL_W / 2, bot_y, -0.00012), (PANEL_W / 2, top_y, -0.00012)]
    uvs = [(0, 1), (0, 0), (1, 0), (1, 1)]
    return {"base": base, "lid": lid, "pivot": pivot, "panel": (corners, uvs)}


def panel(rig, name, mat):
    corners, uvs = rig["panel"]
    return plane(f"Panel {name}", corners, uvs, mat, rig["lid"])


# ── World, lights, camera ──────────────────────────────────────────────────────
def world(color, strength, volume=0.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    if volume:
        vol = w.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = volume
        w.node_tree.links.new(vol.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])


def area(name, loc, size, power, color=(1, 1, 1), look=(0, 0, 0), shape="RECTANGLE"):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = shape
    if shape == "RECTANGLE":
        d.size, d.size_y = size
    else:
        d.size = size[0]
    d.energy = power
    d.color = color
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, look)
    return ob


def aim(ob, at):
    direction = Vector(at) - ob.location
    ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(lens=50, fstop=5.6):
    cd = bpy.data.cameras.new("Camera")
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("Camera", cd)
    bpy.context.collection.objects.link(cam)
    target = bpy.data.objects.new("Look", None)
    bpy.context.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    cd.dof.focus_object = target
    bpy.context.scene.camera = cam
    return cam, target


def studio(key, rims):
    """Product lighting that keeps the flats dark: a high key behind and
    above (outside the deck's mirror path from a front camera), strip rims
    at the sides at edge height to ride the chamfers, black everywhere else."""
    if key:
        area("Key", (0.0, 0.55, 1.5), (1.0, 0.6), key, look=(0, 0, 0.05))
    area("Rim left", (-0.95, -0.05, 0.22), (0.05, 1.3), rims, look=(0, 0, 0.04))
    area("Rim right", (0.95, 0.05, 0.26), (0.05, 1.3), rims * 0.8, look=(0, 0, 0.04))


def sweep(beat, y, z, length=0.9):
    """A strip light crossing above the machine on a downbeat: the glint."""
    s = area(f"Sweep {beat}", (-1.2, y, z), (0.04, length), 0, look=(0, 0, 0))
    key(s.data, "energy", beat - 0.01, 0, "hold")
    key(s.data, "energy", beat, 400, "hold")
    key(s.data, "energy", beat + 1.2, 0, "hold")
    key(s, "location", beat, -0.9, "linear", index=0)
    key(s, "location", beat + 1.2, 0.9, "linear", index=0)
    s.rotation_euler = (0, 0, 0)
    return s


def haze(density=0.003):
    """Haze in a box around the subject only, so the ground beyond stays #000."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.12))
    box = bpy.context.object
    box.name = "Haze"
    box.scale = (0.55, 0.45, 0.24)
    m = bpy.data.materials.new("Haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = density
    nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    box.data.materials.append(m)
    return box


def floor():
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.00005))
    f = bpy.context.object
    f.name = "Floor"
    if bpy.context.scene.render.engine == "CYCLES":
        f.is_shadow_catcher = True  # shadows only, onto the film's alpha
    else:
        f.data.materials.append(MAT["floor"])
    return f


# ── Shots ──────────────────────────────────────────────────────────────────────
def lid(rig, beat, degrees, ease="out"):
    key(rig["pivot"], "rotation_euler", beat, -math.radians(degrees), ease, index=0)


OPEN_DEG = 112


def screen_world(rig, deg=OPEN_DEG):
    """Where the panel's centre is, and which way it faces, when the lid is open."""
    a = math.radians(deg)
    corners, _ = rig["panel"]
    cy = (corners[0][1] + corners[1][1]) / 2
    # Lid-local (0, cy, 0) rotated by −a about x, offset by the pivot and the lid.
    ly = cy + 0.0024
    y = ly * math.cos(-a)
    z = ly * math.sin(-a)
    p = rig["pivot"].location
    centre = Vector((0, p.y + y, p.z + z))
    n = Vector((0, 0, -1))
    n = Vector((0, n.y * math.cos(-a) - n.z * math.sin(-a), n.y * math.sin(-a) + n.z * math.cos(-a)))
    return centre, n.normalized()


def shot_open(rig):
    world((1, 1, 1), 0.06)
    floor()
    studio(key=160, rims=300)
    sweep(4, -0.1, 0.55)
    lid(rig, 0, 0)
    lid(rig, 3, OPEN_DEG, "hold")
    off = panel(rig, "off", MAT["black"])
    on = panel(rig, "on", image_material("Screen window", screen_source("window-ink"), start_beat=4))
    for ob, vis in ((off, (False, True)), (on, (True, False))):
        key(ob, "hide_render", 0, vis[0], "hold")
        key(ob, "hide_render", 4, vis[1], "hold")
    cam, look = camera(50, 4.0)
    centre, n = screen_world(rig)
    # Establishing three-quarter, drifting; then square up and fly in until
    # the panel fills the frame's width — the frame the film cuts to at 8.
    d_fill = (PANEL_W / 2) / math.tan(math.atan(18 / 50))
    key(cam, "location", 0, (-0.58, -0.62, 0.34))
    key(look, "location", 0, (0, 0.0, 0.05))
    key(cam, "location", 4, (-0.46, -0.58, 0.28))
    key(look, "location", 4, (0, 0.02, 0.07))
    key(cam, "location", 8, tuple(centre + n * d_fill), "hold")
    key(look, "location", 8, tuple(centre), "hold")
    key(cam.data, "dof.aperture_fstop", 0, 4.0)
    key(cam.data, "dof.aperture_fstop", 8, 16.0, "hold")


def shot_macro(rig):
    world((1, 1, 1), 0.04)
    floor()
    studio(key=35, rims=150)
    sweep(24, 0.0, 0.35, 0.5)
    lid(rig, 0, OPEN_DEG, "hold")
    panel(rig, "on", image_material("Screen palette", screen_source("palette-ink"), start_beat=24))
    k = KEYS["K"][0]
    ctrl = KEYS["ctrl"][0]
    shift = KEYS["shift"][0]
    kz = k.location.z
    for cap, down, up in ((ctrl, 23.8, 24.9), (shift, 23.9, 24.9), (k, 24.25, 24.6)):
        key(cap, "location", 23.5, kz, "hold", index=2)
        key(cap, "location", down, kz, "out", index=2)
        key(cap, "location", down + 0.08, kz - 0.0009, "hold", index=2)
        key(cap, "location", up, kz - 0.0009, "out", index=2)
        key(cap, "location", up + 0.12, kz, "hold", index=2)
    kw = (k.location.x, k.location.y)
    cam, look = camera(85, 2.8)
    key(cam, "location", 24, (kw[0] - 0.09, kw[1] - 0.16, 0.085), "linear")
    key(look, "location", 24, (kw[0], kw[1], T + 0.001), "linear")
    key(cam, "location", 25, (kw[0] - 0.06, kw[1] - 0.15, 0.075), "linear")
    key(look, "location", 25, (kw[0] + 0.004, kw[1], T + 0.001), "linear")


INTERNAL_LAYERS = [
    # name, capture crop (px of 1600×1000), lift (m), rise beat, label
    ("Native UI · header", (0, 0, 1600, 47), 0.030, 30, None),
    ("Native UI", (0, 47, 311, 1000), 0.030, 30, "Native UI"),
    ("Terminal", (311, 47, 949, 1000), 0.060, 31, "Terminal · own VT core"),
    ("Chromium", (949, 47, 1600, 1000), 0.090, 32, "Chromium · shared texture"),  # label sits on its right
]
PX = 0.0002  # metres a capture pixel

# The reshoot's own layout, when it has sent one (logical px, x0 y0 x1 y1).
_marks = os.path.join(ROOT, "public", "internals", "marks.json")
if os.path.exists(_marks):
    _m = json.load(open(_marks))
    _crop = {"Native UI · header": "header", "Native UI": "sidebar", "Terminal": "terminal", "Chromium": "chromium"}
    INTERNAL_LAYERS = [(n, tuple(_m[_crop[n]]) if _crop[n] in _m else c, lift, rise, label) for n, c, lift, rise, label in INTERNAL_LAYERS]


def slab(name, w, d, h, mat_top):
    ob = rounded_prism(name, w, d, h, 0.0015, seg=3, chamfer=0.0004, mats=("body", "chamfer"))
    return ob


def shot_internals(rig):
    # The laptop is hidden: this is the software's own hardware.
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "FONT", "EMPTY") and ob.name not in ():
            ob.hide_render = True
    world((0, 0, 0), 0.0)
    haze()
    win = screen_source("window-ink")
    base_w, base_d = 1600 * PX, 1000 * PX
    root = bpy.data.objects.new("Stack", None)
    bpy.context.collection.objects.link(root)
    key(root, "rotation_euler", 28, math.radians(-8), "linear", index=2)
    key(root, "rotation_euler", 44, math.radians(10), "linear", index=2)

    layers = {"Compositor": "compositor", "Native UI · header": "native-ui", "Native UI": "native-ui", "Terminal": "terminal", "Chromium": "chromium"}

    def slab_with(name, crop, z0, parent):
        x0, y0, x1, y1 = crop
        w, d = (x1 - x0) * PX, (y1 - y0) * PX
        cx = (x0 + x1) / 2 * PX - base_w / 2
        cy = base_d / 2 - (y0 + y1) / 2 * PX
        s = slab(name, w, d, 0.003, None)
        s.parent = parent
        s.location = (cx, cy, z0)
        mat = image_material(f"Face {name}", layer_source(layers[name]), strength=1.0)
        # Crop the capture onto this slab's top.
        u0, u1 = x0 / 1600, x1 / 1600
        v0, v1 = 1 - y1 / 1000, 1 - y0 / 1000
        face = plane(f"Face {name}", [(-w / 2 + 0.0004, d / 2 - 0.0004, 0.00302), (-w / 2 + 0.0004, -d / 2 + 0.0004, 0.00302), (w / 2 - 0.0004, -d / 2 + 0.0004, 0.00302), (w / 2 - 0.0004, d / 2 - 0.0004, 0.00302)], [(u0, v1), (u0, v0), (u1, v0), (u1, v1)], mat, s)
        return s, (w, d)

    base, _ = slab_with("Compositor", (0, 0, 1600, 1000), 0, root)
    tabs = [(base, "Compositor · wgpu", (-base_w / 2, -base_d / 2 - 0.012, 0.0015), 34)]
    for i, (name, crop, lift, rise, label) in enumerate(INTERNAL_LAYERS):
        s, (w, d) = slab_with(name, crop, 0.0032, root)
        z0 = 0.0032
        key(s, "location", 28, z0, "hold", index=2)
        key(s, "location", rise, z0, "out", index=2)
        key(s, "location", rise + 1, z0 + lift, "hold", index=2)
        key(s, "location", 42, z0 + lift, "out", index=2)
        key(s, "location", 43, z0, "hold", index=2)
        if label:
            at = (w / 2, -d / 2 - 0.012, 0.0015) if name == "Chromium" else (-w / 2, -d / 2 - 0.012, 0.0015)
            tabs.append((s, label, at, 34 + 0.5 * len(tabs)))
    # The glyph atlas the terminal draws from, above it.
    atlas = slab("Glyph atlas", 0.07, 0.07, 0.003, None)
    atlas.parent = root
    atlas.location = (-0.03, 0.02, 0.0032)
    plane("Face atlas", [(-0.0346, 0.0346, 0.00302), (-0.0346, -0.0346, 0.00302), (0.0346, -0.0346, 0.00302), (0.0346, 0.0346, 0.00302)], [(0, 1), (0, 0), (1, 0), (1, 1)], image_material("Atlas", os.path.join(ROOT, "public", "internals", "atlas.png"), 1.3), atlas)
    key(atlas, "hide_render", 28, True, "hold")
    key(atlas, "hide_render", 33, False, "hold")
    key(atlas, "location", 33, 0.0032 + 0.06, "hold", index=2)
    key(atlas, "location", 33.001, 0.0032 + 0.06, "out", index=2)
    key(atlas, "location", 34, 0.0032 + 0.125, "hold", index=2)
    key(atlas, "location", 42, 0.0032 + 0.125, "out", index=2)
    key(atlas, "location", 43, 0.0032 + 0.06, "hold", index=2)
    key(atlas, "hide_render", 43, True, "hold")
    tabs.append((atlas, "Glyph atlas", (-0.035, -0.035 - 0.012, 0.0015), 36))
    # Labels: a tab off each slab's front edge, set on its beat.
    white = principled("Label", (1, 1, 1), roughness=0.5, **{"Emission Color": (1, 1, 1, 1), "Emission Strength": 1.6})
    for parent, label, loc, beat in tabs:
        right = label.startswith("Chromium")
        t = text(f"Tab {label}", label, 0.014, white, parent, loc, bold=True, align="RIGHT" if right else "LEFT")
        key(t, "hide_render", 28, True, "hold")
        key(t, "hide_render", beat, False, "hold")
        key(t, "hide_render", 42, True, "hold")
    # Light: rims to draw the edges, a key from above through the haze.
    studio(key=0, rims=260)
    sp = bpy.data.lights.new("Shaft", "SPOT")
    sp.energy = 120
    sp.spot_size = math.radians(40)
    sp.spot_blend = 0.3
    so = bpy.data.objects.new("Shaft", sp)
    bpy.context.collection.objects.link(so)
    so.location = (0.05, 0.1, 0.9)
    aim(so, (0, 0, 0))
    cam, look = camera(50, 9.0)
    key(cam, "location", 28, (0.40, -0.56, 0.42), "linear")
    key(cam, "location", 44, (0.34, -0.54, 0.37), "linear")
    key(look, "location", 28, (-0.11, 0.06, 0.03), "out")
    key(look, "location", 34, (-0.11, 0.06, 0.07), "out")
    key(look, "location", 42, (-0.11, 0.06, 0.04), "out")


def shot_outro(rig):
    world((0, 0, 0), 0.0)
    studio(key=25, rims=420)
    for b in (52, 56, 60):
        sweep(b, -0.05, 0.5)
    if os.path.exists(os.path.join(FOOTAGE, "outro-screen.mp4")):
        # One clip from the reshoot: a theme a beat, then paper, recorded live.
        panels = [(panel(rig, "outro", image_material("outro", screen_source("outro-screen"), start_beat=52)), 52, 99)]
    else:
        themes = ["theme-catppuccin-ink", "theme-gruvbox-ink", "theme-nord-ink", "theme-rose-pine-ink"]
        panels = [(panel(rig, t, image_material(t, screen_source(t))), 52 + i, 53 + i) for i, t in enumerate(themes)]
        panels.append((panel(rig, "paper", image_material("paper", screen_source("window-paper"))), 56, 99))
    for ob, a, b in panels:
        key(ob, "hide_render", 51, True, "hold")
        key(ob, "hide_render", a, False, "hold")
        key(ob, "hide_render", b, True, "hold")
    lid(rig, 52, OPEN_DEG, "hold")
    lid(rig, 60, OPEN_DEG, "out")
    lid(rig, 63, 0.4, "hold")
    cam, look = camera(50, 4.0)
    key(cam, "location", 52, (0.62, -0.6, 0.36), "linear")
    key(cam, "location", 60, (0.56, -0.64, 0.32), "out")
    key(cam, "location", 64, (0.5, -0.6, 0.4), "hold")
    key(look, "location", 52, (-0.03, 0.02, 0.07), "linear")
    key(look, "location", 60, (-0.03, 0.02, 0.06), "out")
    key(look, "location", 64, (-0.02, 0.0, 0.02), "hold")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    opt = {"shot": "open", "engine": "eevee", "samples": 64, "scale": 100, "frames": None}
    for i in range(0, len(argv), 2):
        opt[argv[i].lstrip("-")] = argv[i + 1]
    shot = opt["shot"]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = int(opt["scale"])
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.film_transparent = shot in ("open", "macro")
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    if opt["engine"] == "cycles":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        sc.render.engine = "CYCLES"
        sc.cycles.device = "GPU"
        sc.cycles.samples = int(opt["samples"])
        sc.cycles.use_denoising = True
    else:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        e = sc.eevee
        e.taa_render_samples = int(opt["samples"])
        e.use_raytracing = True
        e.ray_tracing_options.resolution_scale = "1"
        e.use_shadows = True
        e.volumetric_tile_size = "4"
        e.volumetric_samples = 96
        e.use_volumetric_shadows = True

    materials()
    rig = laptop()
    {"open": shot_open, "macro": shot_macro, "internals": shot_internals, "outro": shot_outro}[shot](rig)
    finish_keys()

    a, b = frames(shot)
    if opt["frames"]:
        a, b = (int(x) for x in opt["frames"].split(":"))
    sc.frame_start, sc.frame_end = a, b
    out = os.path.join(ROOT, "public", "renders", shot)
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "f")
    if opt.get("save"):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", f"{shot}.blend"))
    bpy.ops.render.render(animation=True)


main()
