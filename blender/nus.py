"""nus — the 3D shots, built from nothing and rendered headless.

  blender -b --factory-startup -P blender/nus.py -- --shot open [--frames 0:189] [--engine cycles|eevee] [--samples 64] [--scale 200]

Defaults render the master: 3840×2160 (scale 200 of the 1920×1080 film
frame) in Cycles on the M4 Pro's GPU — Metal, MetalRT hardware ray tracing,
persistent data (the scene stays resident in unified memory between
frames), adaptive sampling, OIDN on the GPU. `--scale 50` for quick looks.

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


def image_material(name, path, strength=1.0, gloss=0.18, start_beat=0, glass=True):
    """A screen: the picture as emission, under a thin glossy coat that
    catches the rim lights. A movie's first frame lands on `start_beat`."""
    m = principled(name, (0, 0, 0), roughness=gloss)
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Specular IOR Level"].default_value = 0.06  # a matte panel: rims glint, the studio doesn't
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
    picture = tex.outputs["Color"]
    if VIEW == "Khronos PBR Neutral":
        picture = display_inverse(nt, picture)
    nt.links.new(picture, p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = strength
    if STAGE >= 2 and glass:
        # A display is light under glass: no sheen of its own, a clear coat
        # at glass's IOR on top, so it reflects the studio the way a real
        # screen does (4 % head-on, a mirror at grazing angles).
        p.inputs["Specular IOR Level"].default_value = 0.0
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = LOOK["screen_coat"]
        p.inputs["Coat IOR"].default_value = 1.5
        p.inputs["Emission Strength"].default_value = strength * LOOK["screen_nits"]
    return m


def display_inverse(nt, color_socket):
    """Undo Khronos PBR Neutral for a picture that must come out as its own
    sRGB pixels: a screen is display-referred, the scene around it isn't.
    The view transform's forward path is offset (x < 0.08: x → 6.25x², else
    x − 0.04), then a shoulder on the peak channel above 0.76; this runs it
    backwards — shoulder first, then the toe. (Its small highlight
    desaturation isn't inverted; UI whites sit barely into the shoulder.)"""
    def math(op, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(color_socket, sep.inputs[0])
    r, g, b = sep.outputs[0], sep.outputs[1], sep.outputs[2]
    # Shoulder: m' = 1 − d²/(m + d − s) forward, so m = d²/(1 − m') − d + s.
    s0, d = 0.76, 0.24
    m = math("MAXIMUM", math("MAXIMUM", r, g), b)
    mc = math("MINIMUM", m, 0.995)
    peak = math("ADD", math("SUBTRACT", math("DIVIDE", d * d, math("SUBTRACT", 1.0, mc)), d), s0)
    over = math("GREATER_THAN", m, s0)
    ratio = math("DIVIDE", peak, math("MAXIMUM", m, 1e-6))
    scale = math("ADD", 1.0, math("MULTIPLY", over, math("SUBTRACT", ratio, 1.0)))
    out = []
    for c in (r, g, b):
        y = math("MULTIPLY", c, scale)
        # Toe: y = 6.25x² below 0.04 (x < 0.08), else y = x − 0.04.
        low = math("LESS_THAN", y, 0.04)
        a_ = math("SQRT", math("MULTIPLY", y, 0.16, clamp=False))
        b_ = math("ADD", y, 0.04)
        out.append(math("ADD", math("MULTIPLY", low, a_), math("MULTIPLY", math("SUBTRACT", 1.0, low), b_)))
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for i, o in enumerate(out):
        nt.links.new(o, comb.inputs[i])
    return comb.outputs[0]


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


# ── Apple's MacBook Pro 14" (the AR asset from apple.com) — a stand-in for
# blocking until the licensed model arrives; never published. Names are the
# USDZ's own (obfuscated); the logo and the underside engravings are removed.
APPLE = os.path.join(ROOT, "assets", "models", "macbook-pro-14-space-black.usdz")
APPLE_LID = "RcexTyyhpuJYATQ"
APPLE_SCREEN = "tfTbkkzhxqpKRgC"
APPLE_GLASS = "nAIWMiVEtSYdjdZ"
APPLE_KEYBOARD = "dAVNlHAHYLbkxrB"
# Marks → the metal around them: the logo insert takes the lid shell's
# aluminium (deleting it would leave its cut-out), the engravings the base's.
APPLE_MARKS = {"xiLiwJHfkqIwaTs": "KjpcUkkMjGYeXkV", "IJeReHnhQHJFtgB": "WZqbfOdYdlPMpRs", "lzNeOaWQWAReGok": "WZqbfOdYdlPMpRs"}


def apple_laptop():
    before = set(bpy.data.objects)
    bpy.ops.wm.usd_import(filepath=APPLE)
    new = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in new if o.parent is None)
    for mark, surround in APPLE_MARKS.items():
        # Hide the insert and close the cut-out it sat in, so the surround
        # reads as one unbroken surface.
        ob = bpy.data.objects[mark]
        ob.hide_render = True
        shell = bpy.data.objects[surround]
        corners = [shell.matrix_world.inverted() @ (ob.matrix_world @ Vector(c)) for c in ob.bound_box]
        lo = Vector([min(c[i] for c in corners) for i in range(3)]) - Vector((0.002,) * 3)
        hi = Vector([max(c[i] for c in corners) for i in range(3)]) + Vector((0.002,) * 3)
        bm = bmesh.new()
        bm.from_mesh(shell.data)
        inside = lambda v: all(lo[i] <= v.co[i] <= hi[i] for i in range(3))
        edges = [e for e in bm.edges if e.is_boundary and all(inside(v) for v in e.verts)]
        if edges:
            bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            bm.to_mesh(shell.data)
        bm.free()
    bpy.context.view_layer.update()
    # Sit it on the floor (z = 0), like ours.
    low = min((o.matrix_world @ Vector(c)).z for o in new if o.type == "MESH" for c in o.bound_box)
    root.location.z -= low
    bpy.context.view_layer.update()
    lid_grp = bpy.data.objects[APPLE_LID]
    lid_meshes = [o for o in lid_grp.children_recursive if o.type == "MESH"]
    base_meshes = [o for o in new if o.type == "MESH" and o not in lid_meshes]
    lid_pts = [o.matrix_world @ v.co for o in lid_meshes if not o.hide_render for v in o.data.vertices]
    base_pts = [o.matrix_world @ v.co for o in base_meshes for v in o.data.vertices]
    # The screen's facing (front and up, since the lid leans back) and the
    # lid's own up (along the lid, away from the hinge).
    import numpy as np
    scr = np.array([tuple(bpy.data.objects[APPLE_SCREEN].matrix_world @ v.co) for v in bpy.data.objects[APPLE_SCREEN].data.vertices])
    n = Vector(np.linalg.svd(scr - scr.mean(axis=0))[2][2]).normalized()
    if n.y > 0:
        n = -n
    u = Vector((0, n.z, -n.y))
    # Shut: rotate about x until the screen faces straight down.
    theta = math.atan2(-n.y, -n.z)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    # The lid's far edge must land on the base's front edge; its innermost
    # face (the glass) must rest on the deck. p' = R p + (I − R) c, linear in
    # the axis c = (cy, cz): two conditions, two unknowns.
    top = max(p.dot(u) for p in lid_pts)
    A = sum((p for p in lid_pts if p.dot(u) > top - 0.0005), Vector()) / sum(1 for p in lid_pts if p.dot(u) > top - 0.0005)
    inner = max(p.dot(n) for p in lid_pts)
    B = next(p for p in lid_pts if p.dot(n) > inner - 1e-6)
    front = min(p.y for p in base_pts)
    deck = max(p.z for p in base_pts) + 0.0004
    a_, b_ = 1 - cos_t, sin_t
    r1 = front - (cos_t * A.y - sin_t * A.z)
    r2 = deck - (sin_t * B.y + cos_t * B.z)
    det = a_ * a_ + b_ * b_
    cy = (a_ * r1 - b_ * r2) / det
    cz = (b_ * r1 + a_ * r2) / det
    pivot = bpy.data.objects.new("Lid pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (0, cy, cz)
    shut_deg = math.degrees(theta)
    bpy.context.view_layer.update()
    mw = lid_grp.matrix_world.copy()
    lid_grp.parent = pivot
    lid_grp.matrix_world = mw
    screen = bpy.data.objects[APPLE_SCREEN]
    screen.hide_render = True  # our panels replace Apple's wallpaper
    # The cover glass: keep a thin, honest reflection, not a mirror of the studio.
    glass = bpy.data.objects[APPLE_GLASS].data.materials[0]
    g = next(n for n in glass.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    g.inputs["Metallic"].default_value = 0.0
    g.inputs["Roughness"].default_value = 0.06
    g.inputs["Specular IOR Level"].default_value = 0.05
    g.inputs["Roughness"].default_value = 0.12
    if STAGE >= 2:
        g.inputs["Roughness"].default_value = LOOK["screen_coat"]
        g.inputs["Specular IOR Level"].default_value = 0.5  # IOR 1.5: the same sheet as the screen's coat
        aluminium([o for o in new if o.type == "MESH"])
    rig = {"kind": "apple", "base": root, "pivot": pivot, "lid": lid_grp, "screen": screen, "open_deg": shut_deg}
    return rig


def aluminium(meshes):
    """Apple's AR model bakes the aluminium's roughness into a 512 px JPEG at
    ~0.55, tuned for Quick Look on a phone; under a softbox that smears every
    reflection flat. Keep its variation, scale it to bead-blasted anodised
    aluminium (~0.3), and add the blast itself — a fine bump a 512 px normal
    map can't carry at 4K."""
    seen = set()
    for ob in meshes:
        for slot in ob.material_slots:
            m = slot.material
            if not m or m.name in seen or not m.use_nodes:
                continue
            seen.add(m.name)
            nt = m.node_tree
            p = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not p or p.inputs["Metallic"].is_linked or p.inputs["Metallic"].default_value < 0.99:
                continue
            r = p.inputs["Roughness"]
            if r.is_linked:
                src = r.links[0].from_socket
                mul = nt.nodes.new("ShaderNodeMath")
                mul.operation = "MULTIPLY"
                mul.inputs[1].default_value = LOOK["metal_rough"]
                nt.links.new(src, mul.inputs[0])
                nt.links.new(mul.outputs[0], r)
            else:
                r.default_value = min(r.default_value, 0.3) if r.default_value > 0.05 else r.default_value
            if LOOK["bead"] > 0:
                coord = nt.nodes.new("ShaderNodeTexCoord")
                noise = nt.nodes.new("ShaderNodeTexNoise")
                noise.inputs["Scale"].default_value = 9000.0  # object space, metres: grains of ~0.1 mm
                noise.inputs["Detail"].default_value = 2.0
                nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
                bump = nt.nodes.new("ShaderNodeBump")
                bump.inputs["Strength"].default_value = 0.035 * LOOK["bead"]
                bump.inputs["Distance"].default_value = 0.00002
                nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
                n = p.inputs["Normal"]
                if n.is_linked:
                    nt.links.new(n.links[0].from_socket, bump.inputs["Normal"])
                nt.links.new(bump.outputs["Normal"], n)


def panel(rig, name, mat):
    if rig.get("kind") == "apple":
        # A copy of Apple's screen surface, carrying our picture.
        src = rig["screen"]
        ob = src.copy()
        ob.name = f"Panel {name}"
        ob.hide_render = False
        bpy.context.collection.objects.link(ob)
        ob.parent = src.parent
        ob.matrix_world = src.matrix_world.copy()
        slot = ob.material_slots[0]
        slot.link = "OBJECT"
        slot.material = mat
        return ob
    corners, uvs = rig["panel"]
    return plane(f"Panel {name}", corners, uvs, mat, rig["lid"])


# ── World, lights, camera ──────────────────────────────────────────────────────
HDRI = os.path.join(ROOT, "assets", "hdri")


def hdri_world(name, strength, rotation=0.0, camera=(1, 1, 1)):
    """A Poly Haven studio for light and reflections only: camera rays see a
    flat colour (the film's #fff or #000), everything else sees the studio."""
    path = next(os.path.join(HDRI, f) for f in os.listdir(HDRI) if f.startswith(name + "."))
    w = bpy.data.worlds.new(name)
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    mapping = nt.nodes.new("ShaderNodeMapping")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    if STAGE >= 2:
        # In stage 2 the studio is fill, not key (the softboxes and the set
        # light do the lighting), so its lamps are clamped for every ray: its
        # hot spot can't burn a disc into the glass. (By ray type isn't
        # enough: Cycles samples the world as a light, and those samples
        # don't carry "glossy".)
        clamp = nt.nodes.new("ShaderNodeVectorMath")
        clamp.operation = "MINIMUM"
        clamp.inputs[1].default_value = (LOOK["hdri_clamp"],) * 3
        nt.links.new(env.outputs["Color"], clamp.inputs[0])
        nt.links.new(clamp.outputs[0], bg.inputs["Color"])
    flat = nt.nodes.new("ShaderNodeBackground")
    flat.inputs["Color"].default_value = (*camera, 1)
    path_ = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(path_.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(flat.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs["Surface"])


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


TONE = "white"


def studio(key, rims):
    if STAGE >= 2:
        return stage(TONE)
    """Product lighting that keeps the flats dark: a high key behind and
    above (outside the deck's mirror path from a front camera), strip rims
    at the sides at edge height to ride the chamfers, black everywhere else."""
    if key:
        area("Key", (0.0, 0.55, 1.5), (1.0, 0.6), key, look=(0, 0, 0.05))
    area("Rim left", (-0.95, -0.05, 0.22), (0.05, 1.3), rims, look=(0, 0, 0.04))
    area("Rim right", (0.95, 0.05, 0.26), (0.05, 1.3), rims * 0.8, look=(0, 0, 0.04))


def sweep(beat, y, z, length=0.9, energy=140):
    """A strip light crossing above the machine on a downbeat: the glint."""
    s = area(f"Sweep {beat}", (-1.2, y, z), (0.04, length), 0, look=(0, 0, 0))
    key(s.data, "energy", beat - 0.01, 0, "hold")
    key(s.data, "energy", beat, energy, "hold")
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


def cyclorama(tone):
    """A real set: floor, a curved cove, a wall. White is a matte cove the
    studio HDRI and a soft top light roll across; black is a glossy floor
    that holds a faint reflection of the machine, falling off to nothing."""
    R, y_cove, reach, height, width = 0.9, 0.42, 4.0, 3.2, 8.0
    prof = [(-reach, 0.0), (y_cove, 0.0)]
    for i in range(1, 25):
        a = math.radians(90 * i / 24)
        prof.append((y_cove + R * math.sin(a), R * (1 - math.cos(a))))
    prof.append((y_cove + R, height))
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-width / 2, width / 2)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Cyclorama")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("Cyclorama", me)
    bpy.context.collection.objects.link(ob)
    global TONE
    TONE = tone
    if STAGE >= 2 and tone == "white":
        # Satin: a soft sheen that carries a faint reflection of the machine.
        mat = principled("Cyc white", (0.9, 0.9, 0.9), roughness=0.42, **{"Specular IOR Level": 0.35})
    elif STAGE >= 2:
        # Black acrylic: a clear reflection that falls off with the light.
        mat = principled("Cyc black", (0.007, 0.007, 0.0075), roughness=0.14, **{"Specular IOR Level": 0.5})
    elif tone == "white":
        w = LOOK["white_cyc"]
        mat = principled("Cyc white", (w, w, w), roughness=0.85, **{"Specular IOR Level": 0.2})
    else:
        mat = principled("Cyc black", (0.012, 0.012, 0.013), roughness=LOOK["black_rough"], **{"Specular IOR Level": LOOK["black_spec"]})
    me.materials.append(mat)
    return ob


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
    if rig.get("kind") == "apple":
        # It ships open; shutting swings the top forward about +x, down onto the deck.
        key(rig["pivot"], "rotation_euler", beat, math.radians(rig["open_deg"] * (1 - degrees / OPEN_DEG)), ease, index=0)
        return
    key(rig["pivot"], "rotation_euler", beat, -math.radians(degrees), ease, index=0)


OPEN_DEG = 112

# The set's look, in one place; NUS_<KEY> overrides for look development.
# Tuned against the frame: the white cove ~241 near, ~210 far; black ~15–35.
LOOK = {"white_hdri": 0.15, "white_key": 20, "white_rims": 160, "white_cyc": 0.86, "black_hdri": 0.12, "black_rough": 0.3, "black_spec": 0.3,
        # Stage 2 (NUS_STAGE=2, the default): the product-photography stage.
        "exposure": 0.0, "screen_nits": 1.5, "screen_coat": 0.03, "set_light": 1.0, "softbox": 1.0, "bloom": 1.0, "dispersion": 0.004,
        "metal_rough": 0.55, "bead": 1.0, "hdri_clamp": 2.0}
LOOK = {k: float(os.environ.get("NUS_" + k.upper(), v)) for k, v in LOOK.items()}
# Stage 1 is the first look (Standard view, area rims, the HDRI in every
# reflection); stage 2 lights like a product shoot: Khronos PBR Neutral
# (product colour stays true, highlights roll off, the ground still reaches
# #fff), a glass-coated screen, feathered softboxes and black flags that
# only the machine sees, a set light only the set sees, and a lens pass.
STAGE = int(os.environ.get("NUS_STAGE", 2))
VIEW = os.environ.get("NUS_VIEW", "Khronos PBR Neutral" if STAGE >= 2 else "Standard")
GROUND = {"white": 1.0, "black": 0.0}  # the film's flat grounds, display-referred
OPEN_HDRI_ROT = float(os.environ.get("NUS_HDRI_ROT", 40))


def screen_world(rig, deg=OPEN_DEG):
    """Where the panel's centre is, and which way it faces, when the lid is open."""
    if rig.get("kind") == "apple":
        # The screen's plane from its shape: the axis it's thinnest along.
        import numpy as np
        scr = rig["screen"]
        bpy.context.view_layer.update()
        vs = np.array([tuple(scr.matrix_world @ v.co) for v in scr.data.vertices])
        _, _, vt = np.linalg.svd(vs - vs.mean(axis=0))
        n = Vector(vt[2]).normalized()
        if n.y > 0:  # face the front (−y)
            n = -n
        # The centre of its extent, not of its vertices — the notch crowds the top.
        return Vector((vs.min(axis=0) + vs.max(axis=0)) / 2), n
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
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=OPEN_HDRI_ROT)
    cyclorama("white")
    studio(key=LOOK["white_key"], rims=LOOK["white_rims"])
    sweep(4, 0.1, 0.9, energy=18)  # a faint pass over the lid as the screen wakes
    lid(rig, 0, 0)
    lid(rig, 3, OPEN_DEG, "hold")
    off = panel(rig, "off", MAT["black"])
    on_mat = image_material("Screen window", screen_source("window-ink"), start_beat=4)
    on = panel(rig, "on", on_mat)
    if STAGE >= 2:
        # The glass fades as the camera squares up, so the last 3D frame is the
        # flat capture the film cuts to at 8 — no reflection to jump.
        coat = 'nodes["Principled BSDF"].inputs["Coat Weight"].default_value'
        key(on_mat.node_tree, coat, 5, 1.0)
        key(on_mat.node_tree, coat, 7.6, 0.0, "hold")
        nits = 'nodes["Principled BSDF"].inputs["Emission Strength"].default_value'
        key(on_mat.node_tree, nits, 5, LOOK["screen_nits"])
        key(on_mat.node_tree, nits, 7.6, 1.0, "hold")  # 1.0 through Khronos PBR Neutral = the capture's own sRGB
    for ob, vis in ((off, (False, True)), (on, (True, False))):
        key(ob, "hide_render", 0, vis[0], "hold")
        key(ob, "hide_render", 4, vis[1], "hold")
    cam, look = camera(50, 4.0)
    centre, n = screen_world(rig)
    # Establishing three-quarter, drifting; then square up and fly in until
    # the panel fills the frame's width — the frame the film cuts to at 8.
    width = rig["screen"].dimensions.x if rig.get("kind") == "apple" else PANEL_W
    d_fill = (width / 2) / math.tan(math.atan(18 / 50))
    key(cam, "location", 0, (-0.58, -0.62, 0.34))
    key(look, "location", 0, (0, 0.0, 0.05))
    key(cam, "location", 4, (-0.46, -0.58, 0.28))
    key(look, "location", 4, (0, 0.02, 0.07))
    key(cam, "location", 8, tuple(centre + n * d_fill), "hold")
    key(look, "location", 8, tuple(centre), "hold")
    key(cam.data, "dof.aperture_fstop", 0, 4.0)
    key(cam.data, "dof.aperture_fstop", 8, 16.0, "hold")


def shot_macro(rig):
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=40)
    cyclorama("white")
    studio(key=12, rims=45)
    sweep(24, 0.0, 0.35, 0.5)
    lid(rig, 0, OPEN_DEG, "hold")
    panel(rig, "on", image_material("Screen palette", screen_source("palette-ink"), start_beat=24))
    if rig.get("kind") == "apple":
        # One mesh for the whole keyboard: aim where K sits — the home row,
        # 9.3 key-widths in from the left (caps is 1.8 wide) — no press.
        kb = bpy.data.objects[APPLE_KEYBOARD]
        vs = [kb.matrix_world @ v.co for v in kb.data.vertices]
        x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
        y1 = max(v.y for v in vs)
        unit = (x1 - x0) / 15
        kw = (x0 + 9.3 * unit, y1 - 3.5 * (max(v.y for v in vs) - min(v.y for v in vs)) / 6)
        kz = max(v.z for v in vs)
    else:
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
    hdri_world("monochrome_studio_02", 0.12, rotation=60, camera=(0, 0, 0))
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
        mat = image_material(f"Face {name}", layer_source(layers[name]), strength=1.0, glass=False)  # layers are diagrams, not glass
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
    plane("Face atlas", [(-0.0346, 0.0346, 0.00302), (-0.0346, -0.0346, 0.00302), (0.0346, -0.0346, 0.00302), (0.0346, 0.0346, 0.00302)], [(0, 1), (0, 0), (1, 0), (1, 1)], image_material("Atlas", os.path.join(ROOT, "public", "internals", "atlas.png"), 1.3, glass=False), atlas)
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
    hdri_world("monochrome_studio_02", LOOK["black_hdri"], rotation=-30, camera=(0, 0, 0))
    cyclorama("black")
    studio(key=25, rims=420)
    for b in (52, 56, 60):
        sweep(b, 0.35, 0.8, energy=60)  # high and behind: it rides the edges, not the glass
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


def light_product_only():
    """Rims and sweeps light the machine, never the set: Cycles light linking,
    the product shoot's flags and cutters. The set takes the HDRI and the key."""
    set_names = ("Cyclorama", "Haze", "Floor")
    rig_names = RIG_NAMES
    rig_col = bpy.data.collections.get("Rig")
    rig_objs = set(rig_col.all_objects) if rig_col else set()
    product = bpy.data.collections.new("Product")
    bpy.context.scene.collection.children.link(product)
    stage_set = bpy.data.collections.new("Set")
    bpy.context.scene.collection.children.link(stage_set)
    # Set dressing (the Memphis objects) takes neither the product's boxes nor
    # the set light that drives the cyc to white — only the sun and the fill,
    # at an exposure where the signals keep their colour.
    dressing = bpy.data.collections.get("Memphis")
    for ob in bpy.context.scene.objects:
        if (dressing and ob.name in dressing.objects) or ob in rig_objs:
            continue
        elif ob.type in ("MESH", "FONT", "CURVE") and not ob.name.startswith(set_names + rig_names):
            product.objects.link(ob)
        elif ob.name.startswith(set_names):
            stage_set.objects.link(ob)
    # The metal alone: the product less its glass and screens. Highlights and
    # sweeps light this, so their reflections sit on edges, never on the display.
    metal = bpy.data.collections.new("Product metal")
    for ob in product.objects:
        if not ob.name.startswith(GLASS_NAMES):
            metal.objects.link(ob)
    for ob in bpy.context.scene.objects:
        if ob.get("nus_metal") or ob.name.startswith("Sweep"):
            ob.light_linking.receiver_collection = metal
        elif ob in rig_objs:
            link = ob.get("nus_link") or ("set" if ob.name.startswith("Set light") else "product")
            ob.light_linking.receiver_collection = {"set": stage_set, "product": product, "metal": metal}.get(link)
        elif ob.name.startswith(("Rim", "Sweep", "Softbox")):
            ob.light_linking.receiver_collection = product
        elif ob.name.startswith("Set light"):
            ob.light_linking.receiver_collection = stage_set


# ── Stage 2: the product shoot ─────────────────────────────────────────────────
def _plane(name, loc, size, look):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (size[0], size[1], 1)
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("Z", "Y").to_euler()  # +Z faces the subject
    return ob


def softbox(name, loc, size, strength, look=(0, 0, 0.08), feather=0.3, color=(1, 1, 1)):
    """A softbox the machine sees and the camera doesn't: an emissive panel
    whose edges feather to nothing, so a reflection in the metal is a soft
    gradient with no hard rectangle. Light-linked to the product."""
    ob = _plane(name, loc, size, look)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    uv = nt.nodes.new("ShaderNodeTexCoord")
    xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], xyz.inputs[0])

    def edge(axis):  # distance to the nearer edge, 0 at the edge, 0.5 in the middle
        a = nt.nodes.new("ShaderNodeMath")
        a.operation = "SUBTRACT"
        a.inputs[0].default_value = 1.0
        nt.links.new(xyz.outputs[axis], a.inputs[1])
        mn = nt.nodes.new("ShaderNodeMath")
        mn.operation = "MINIMUM"
        nt.links.new(xyz.outputs[axis], mn.inputs[0])
        nt.links.new(a.outputs[0], mn.inputs[1])
        return mn

    both = nt.nodes.new("ShaderNodeMath")
    both.operation = "MINIMUM"
    nt.links.new(edge("X").outputs[0], both.inputs[0])
    nt.links.new(edge("Y").outputs[0], both.inputs[1])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHSTEP"
    ramp.inputs["From Min"].default_value = 0.0
    ramp.inputs["From Max"].default_value = feather
    nt.links.new(both.outputs[0], ramp.inputs["Value"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength * LOOK["softbox"]
    nt.links.new(ramp.outputs["Result"], mul.inputs[0])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(m)
    ob.visible_camera = False
    ob.visible_shadow = False
    return ob


def flag(name, loc, size, look=(0, 0, 0.08)):
    """Black card: seen only in reflections, where it draws the dark lines
    that give metal and glass their shape. Blocks no light."""
    ob = _plane(name, loc, size, look)
    ob.data.materials.append(principled(name, (0.0, 0.0, 0.0), roughness=1.0, **{"Specular IOR Level": 0.0}))
    ob.visible_camera = False
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_volume_scatter = False
    return ob


RIGS = os.environ.get("NUS_RIGS", os.path.join(ROOT, "blender", "rigs"))
SHOT = None  # set by main(): which shot's rig file to look for
RIG_NAMES = ("Softbox", "Flag", "Set light")


def rig_path(shot=None):
    return os.path.join(RIGS, f"{shot or SHOT}.blend")


def append_rig(path):
    """The user's light, blocked by hand (Light Wrangler, Photographer) in a
    rig workfile, replaces the scripted stage: every object in its `Rig`
    collection comes in as it was left. Lights, emitters and flags light the
    product only, unless an object carries a custom property
    `nus_link` = "set" (the cyc only) or "all" (everything), or its name
    starts with "Set light". Light Wrangler's node groups and textures come
    with it, so the add-on needn't be loaded to render."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Rig"]
    if not dst.collections:
        raise SystemExit(f"{path}: no collection named Rig")
    rig = dst.collections[0]
    bpy.context.scene.collection.children.link(rig)
    # Anything that rode in with the rig but isn't in it (collections its
    # light linking pointed at, and their objects) goes: the scene is ours.
    keep = set(rig.all_objects)
    for ob in list(bpy.data.objects):
        if ob.library is None and ob not in keep and not ob.users_scene:
            bpy.data.objects.remove(ob)
    for ob in keep:
        ob.light_linking.receiver_collection = None
        ob.light_linking.blocker_collection = None
    print(f"RIG {os.path.relpath(path, ROOT)}: {len(rig.all_objects)} objects", flush=True)
    return rig


def stage(tone):
    if SHOT and os.path.exists(rig_path()):
        return append_rig(rig_path())
    return scripted_stage(tone)


def scripted_stage(tone):
    """Light for a product, not a scene. The machine sees a top softbox and
    two feathered strips (edge light on the chamfers), a long gradient bar
    above the camera (the diagonal sheen on the glass), and black flags
    around the lens (so the screen reflects darkness, not the room). The
    set sees one broad light of its own; neither touches the other."""
    s = 6.0 if tone == "white" else 10.0  # dark metal reflects ~9 %: the boxes are hot so their reflections read
    softbox("Softbox top", (0.0, 0.25, 1.15), (1.3, 0.9), 2.2 * s, look=(0, 0.02, 0.05), feather=0.4)
    softbox("Softbox left", (-0.95, -0.1, 0.32), (0.22, 1.1), 7.0 * s, look=(0, 0, 0.06), feather=0.45)
    softbox("Softbox right", (0.95, 0.18, 0.36), (0.22, 1.1), 5.0 * s, look=(0, 0, 0.06), feather=0.45)
    softbox("Softbox bar", (0.1, -1.45, 0.62), (2.6, 0.1), 1.1 * s, look=(0, 0, 0.12), feather=0.5)
    softbox("Softbox back", (0.0, 0.95, 0.62), (1.4, 0.16), 9.0 * s, look=(0, 0, 0.16), feather=0.45)  # the lid's edge against the ground
    flag("Flag front", (0.0, -1.7, 0.7), (3.2, 1.8), look=(0, 0, 0.12))
    flag("Flag low left", (-1.3, -0.9, 0.25), (1.2, 0.8), look=(0, 0, 0.1))
    if tone == "white":
        # The cyc goes to white: one broad light over the set, the floor just
        # under #fff so the machine's shadow reads, the far wall past it.
        d = bpy.data.lights.new("Set light", "AREA")
        d.shape = "RECTANGLE"
        d.size, d.size_y = 2.2, 1.6
        d.energy = 240 * LOOK["set_light"]
        ob = bpy.data.objects.new("Set light", d)
        bpy.context.collection.objects.link(ob)
        ob.location = (0.25, -0.45, 2.3)  # high and a little forward: a contact shadow that reads, under and behind
        aim(ob, (0, 0.35, 0))
        fill = bpy.data.lights.new("Set light fill", "AREA")
        fill.size = 5.0
        fill.energy = 210 * LOOK["set_light"]
        fo = bpy.data.objects.new("Set light fill", fill)
        bpy.context.collection.objects.link(fo)
        fo.location = (0.0, 0.2, 3.2)  # carries the cove and wall on past white
        aim(fo, (0, 1.2, 0.8))


# ── Stage 2: highlights placed by reflection ───────────────────────────────────
# Light Wrangler's interactive mode, as geometry: name a point on the machine,
# cast the camera's ray at it, mirror the ray about the surface normal, and put
# a feathered softbox along the mirrored ray, facing the point. Its reflection
# then sits exactly there. Re-aimed on every frame given, so a highlight stays
# on its edge while the camera moves.
GLASS_NAMES = ("Panel", APPLE_GLASS, APPLE_SCREEN)


def _cast(sc, origin, target, metal=True):
    """First product surface on the ray from `origin` through `target`
    (softboxes, flags and the set don't count; with `metal`, nor the glass)."""
    dg = bpy.context.evaluated_depsgraph_get()
    d = (Vector(target) - origin).normalized()
    o = origin.copy()
    for _ in range(12):
        hit, loc, normal, _i, ob, _m = sc.ray_cast(dg, o, d)
        if not hit:
            return None
        if ob.name.startswith(RIG_NAMES + ("Cyclorama", "Haze", "Floor")) or not ob.visible_camera or (metal and ob.name.startswith(GLASS_NAMES)):
            o = loc + d * 1e-4
            continue
        n = normal if normal.dot(d) < 0 else -normal
        return loc, n.normalized(), d
    return None


def highlight(name, targets, size=(0.6, 0.1), strength=40.0, distance=1.1, along=(1, 0, 0), feather=0.45, metal=True):
    """A softbox whose reflection lands on `targets`: {frame: world point on
    the machine}. One entry places it once; several animate it (linear), so the
    highlight holds its place — or travels, for a glint — as camera and lid
    move. `along`: the direction the softbox's long side runs, usually the edge
    it lights."""
    sc = bpy.context.scene
    cam = sc.camera
    ob = softbox(f"Softbox {name}", (0, 0, 0), size, strength, look=(0, 0, 1), feather=feather)
    if metal:
        ob["nus_metal"] = 1  # lights the aluminium, never the glass: no stray bar across the screen
    placed = 0
    for frame, target in sorted(targets.items()):
        sc.frame_set(frame)
        if callable(target):  # a target that depends on where things are at this frame
            target = target()
        hit = _cast(sc, cam.matrix_world.translation, target, metal)
        if not hit:
            print(f"HIGHLIGHT {name}: frame {frame}: nothing at {tuple(round(x, 3) for x in target)}", flush=True)
            continue
        p, n, v = hit
        r = v - 2 * v.dot(n) * n
        ob.location = p + r * distance
        z = (p - ob.location).normalized()  # the panel's emitting face (+Z) looks at the point
        x = Vector(along) - z * Vector(along).dot(z)
        if x.length < 1e-4:
            x = z.orthogonal()
        x.normalize()
        from mathutils import Matrix
        ob.rotation_euler = Matrix((x, z.cross(x), z)).transposed().to_euler()
        if len(targets) > 1:
            ob.keyframe_insert("location", frame=frame)
            ob.keyframe_insert("rotation_euler", frame=frame)
        placed += 1
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    print(f"HIGHLIGHT {name}: placed on {placed}/{len(targets)} frames", flush=True)
    return ob


def lid_points(rig):
    """The lid's vertices in world space, as they are at the current frame."""
    import numpy as np
    bpy.context.view_layer.update()
    meshes = [o for o in rig["lid"].children_recursive if o.type == "MESH" and not o.hide_render and not o.name.startswith(GLASS_NAMES)]
    pts = []
    for o in meshes:
        m = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        pts.append(co @ m[:3, :3].T + m[:3, 3])
    return np.concatenate(pts)


def lid_edge(rig):
    """The middle of the lid's far edge (the one away from the hinge), now."""
    import numpy as np
    _, n, up = lid_frame(rig)
    p = lid_points(rig)
    d = p @ np.array(up)
    near = p[d > d.max() - 0.0015]
    c = near.mean(axis=0)
    return Vector((0.0, c[1], c[2]))


def lid_back(rig, t, across=0.0):
    """A point on the lid's outside (the aluminium face), `t` 0→1 from its
    left to its right edge, `across` −0.5…0.5 from hinge to far edge."""
    import numpy as np
    _, n, up = lid_frame(rig)
    p = lid_points(rig)
    back = p[p @ np.array(n) < (p @ np.array(n)).min() + 0.002]  # the face that looks away from the glass
    lo, hi = back.min(axis=0), back.max(axis=0)
    c = back.mean(axis=0)
    ext = back @ np.array(up)
    return Vector((lo[0] + (hi[0] - lo[0]) * (0.1 + 0.8 * t), c[1], c[2])) + up * (across * (ext.max() - ext.min()) * 0.8)


def lid_frame(rig):
    """The open lid's centre, its facing and its up (along the lid, away from
    the hinge), for aiming at its edges."""
    centre, n = screen_world(rig)
    up = Vector((0, n.z, -n.y)) if n.z <= 0 else Vector((0, -n.z, n.y))
    if up.z < 0:
        up = -up
    return centre, n, up


def design_open(rig):
    """The open, white: the machine's shape drawn in three highlights that hold
    their place as the camera drifts in — a line along the lid's top edge, the
    long chamfer of the base's front, and a soft sheen down the left side of
    the deck. The scripted edge strips go; the top box, flags and set stay."""
    for n_ in ("Softbox left", "Softbox right", "Softbox back"):
        ob = bpy.data.objects.get(n_)
        if ob:
            bpy.data.objects.remove(ob)
    frames = {round(b * FPB): None for b in (3, 4.5, 6, 7.5)}
    highlight("lid edge", {f: (lambda: lid_edge(rig)) for f in frames}, size=(0.9, 0.05), strength=70, distance=1.2, along=(1, 0, 0), feather=0.4)
    front = Vector((0.0, -0.112, 0.012))  # the base's front edge, the chamfer the thumb rests on
    highlight("front chamfer", {f: front for f in frames}, size=(1.0, 0.06), strength=45, distance=1.2, along=(1, 0, 0), feather=0.45)
    deck = Vector((-0.09, -0.06, 0.0158))  # the palm rest, left of the trackpad
    highlight("deck sheen", {f: deck for f in frames}, size=(0.55, 0.9), strength=9, distance=1.4, along=(0, 1, 0), feather=0.5)


def design_outro(rig):
    """The outro, black: a rim that traces the lid's top edge while it's open
    (56–60), then, the lid shut, one glint that travels across it (60.5–63.5),
    front-left to back-right, and is gone. It replaces the scripted sweeps."""
    for ob in [o for o in bpy.data.objects if o.name.startswith("Sweep")]:
        bpy.data.objects.remove(ob)
    highlight("rim", {round(b * FPB): (lambda: lid_edge(rig)) for b in (56, 57.5, 59)}, size=(1.0, 0.05), strength=60, distance=1.2, along=(1, 0, 0), feather=0.4)
    rim = bpy.data.objects["Softbox rim"]
    mat = rim.data.materials[0].node_tree.nodes
    level = next(nd for nd in mat if nd.type == "MATH" and nd.operation == "MULTIPLY" and not nd.inputs[1].is_linked)
    for beat, v in ((55.9, 0.0), (56.4, level.inputs[1].default_value), (59.6, level.inputs[1].default_value), (60.2, 0.0)):
        level.inputs[1].default_value = v
        level.inputs[1].keyframe_insert("default_value", frame=round(beat * FPB))
    # The glint rides the lid's outside as it closes: left to right, a narrow
    # line, catching the shut lid's last moment.
    path = {round((60.5 + 3.0 * t) * FPB): (lambda t=t: lid_back(rig, t, 0.1 - 0.2 * t)) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)}
    glint = highlight("glint", path, size=(0.035, 1.2), strength=34, distance=1.3, along=(0.3, 1, 0), feather=0.3)
    gm = glint.data.materials[0].node_tree.nodes
    glevel = next(nd for nd in gm if nd.type == "MATH" and nd.operation == "MULTIPLY" and not nd.inputs[1].is_linked)
    peak = glevel.inputs[1].default_value
    for beat, v in ((60.4, 0.0), (61.0, peak), (63.0, peak), (63.6, 0.0)):
        glevel.inputs[1].default_value = v
        glevel.inputs[1].keyframe_insert("default_value", frame=round(beat * FPB))


DESIGNS = {"open": design_open, "outro": design_outro}


def lens():
    """The lens pass, in the compositor: a faint bloom on what's hot (the
    screen's whites, the glints), a touch of lateral dispersion at the
    frame's edges, then the film's flat ground under everything the set
    doesn't cover — laid after the bloom, so the ground never blooms."""
    sc = bpy.context.scene
    sc.render.film_transparent = True
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    try:
        glare.glare_type = "BLOOM"
    except TypeError:
        glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    for attr, val in (("threshold", 1.2), ("mix", -1 + 0.08 * LOOK["bloom"]), ("size", 7)):
        if hasattr(glare, attr):
            setattr(glare, attr, val)
        elif attr.capitalize() in glare.inputs:
            glare.inputs[attr.capitalize()].default_value = val
    lensd = nt.nodes.new("CompositorNodeLensdist")
    if hasattr(lensd, "use_fit"):
        lensd.use_fit = True
    for key, val in (("Distortion", 0.0), ("Dispersion", LOOK["dispersion"])):
        if key in lensd.inputs:
            lensd.inputs[key].default_value = val
    ground = nt.nodes.new("CompositorNodeRGB")
    g = 20.0 * GROUND[TONE] if VIEW != "Standard" else GROUND[TONE]  # 20 → #fff through Khronos PBR Neutral
    ground.outputs[0].default_value = (g, g, g, 1)
    over = nt.nodes.new("CompositorNodeAlphaOver")
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], lensd.inputs["Image"])
    nt.links.new(ground.outputs[0], over.inputs[1])
    nt.links.new(lensd.outputs["Image"], over.inputs[2])
    nt.links.new(over.outputs["Image"], comp.inputs["Image"])


# ── Main ───────────────────────────────────────────────────────────────────────
def args(defaults):
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    opt = dict(defaults)
    for i in range(0, len(argv), 2):
        opt[argv[i].lstrip("-")] = argv[i + 1]
    return opt


def setup(opt, factory=True):
    """An empty scene with the film's render settings. factory=False keeps
    the user's preferences, so their add-ons (Photographer, Light Wrangler)
    stay loaded; the film's own renders start from factory settings."""
    if factory:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    else:
        bpy.ops.wm.read_homefile(use_empty=True, load_ui=False)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = int(opt["scale"])
    sc.view_settings.view_transform = VIEW
    sc.view_settings.look = "None"
    sc.view_settings.exposure = LOOK["exposure"]
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.film_transparent = False  # the set is in the frame now
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    if opt["engine"] == "cycles":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.metalrt = "ON"  # hardware ray tracing on M3/M4
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        sc.render.engine = "CYCLES"
        sc.cycles.device = "GPU"
        sc.cycles.samples = int(opt["samples"])
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.01
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
        sc.cycles.denoising_use_gpu = True
        sc.cycles.denoising_quality = "HIGH"
        sc.render.use_persistent_data = True  # BVH and textures stay resident between frames
        sc.cycles.sample_clamp_indirect = 8.0  # no fireflies off the polished edges
        sc.cycles.glossy_bounces = 6  # glass over panel over metal
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
    return sc


def main():
    global SHOT
    opt = args({"shot": "open", "engine": "cycles", "samples": 64, "scale": 200, "frames": None,
                "laptop": "apple" if os.path.exists(APPLE) else "ours"})
    shot = opt["shot"]
    SHOT = None if opt.get("rig-out") or opt.get("no-rig") else shot
    sc = setup(opt)

    materials()
    rig = apple_laptop() if opt["laptop"] == "apple" else laptop()
    {"open": shot_open, "macro": shot_macro, "internals": shot_internals, "outro": shot_outro}[shot](rig)
    finish_keys()
    if STAGE >= 2 and SHOT and os.path.exists(rig_path()):
        for ob in [o for o in bpy.data.objects if o.name.startswith("Sweep")]:
            bpy.data.objects.remove(ob)  # a rig owns all the light, the glints included
    elif STAGE >= 2 and shot in DESIGNS:
        DESIGNS[shot](rig)  # after the camera and lid are keyed: highlights aim through them
    light_product_only()
    if STAGE >= 2:
        lens()

    a, b = frames(shot)
    if opt["frames"]:
        a, b = (int(x) for x in opt["frames"].split(":"))
    sc.frame_start, sc.frame_end = a, b
    if opt.get("exr"):
        # Plates for Resolve: multilayer half-float EXR, scene-linear, with
        # Cryptomatte (object, material) for mattes and power windows. The
        # composite (lens pass, ground) rides along as the Composite layer.
        img = sc.render.image_settings
        img.file_format = "OPEN_EXR_MULTILAYER"
        img.color_depth = "16"
        img.exr_codec = "DWAA"
        vl = bpy.context.view_layer
        vl.use_pass_cryptomatte_object = True
        vl.use_pass_cryptomatte_material = True
        vl.pass_cryptomatte_depth = 4
    out = opt.get("out") or os.path.join(ROOT, "public", "renders", shot)
    os.makedirs(out, exist_ok=True)
    sc.render.filepath = os.path.join(out, "f")
    if opt.get("rig-out"):
        return write_rig(shot, sc, force=opt.get("force") == "1")
    if opt.get("save"):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "blender", f"{shot}.blend"))
    bpy.ops.render.render(animation=True)


def write_rig(shot, sc, force=False):
    """A lighting workfile for a shot: the whole scene, animated, with the
    scripted stage (softboxes, flags, set light) gathered into a `Rig`
    collection. Light it by hand, keep your lights in `Rig`, save in place;
    renders then use it instead of the scripted stage. Never overwritten
    unless --force 1 — it's the user's work. Local only: it holds the
    Apple model."""
    path = rig_path(shot)
    if os.path.exists(path) and not force:
        raise SystemExit(f"{path} exists — it's the user's; --force 1 to replace it")
    rig = bpy.data.collections.new("Rig")
    sc.collection.children.link(rig)
    for ob in list(bpy.data.objects):
        if ob.name.startswith(RIG_NAMES):
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            rig.objects.link(ob)  # its linking stays, so the viewport shows the render's light
    # Open on the shot's key moment, in the rendered viewport, through its camera.
    a, b = frames(shot)
    sc.frame_current = {"open": a + round(3 * FPB), "outro": a + round(4 * FPB)}.get(shot, (a + b) // 2)
    os.makedirs(RIGS, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"RIG written {os.path.relpath(path, ROOT)}: {len(rig.objects)} objects in Rig", flush=True)


if __name__ == "__main__":
    main()
