"""3D look-dev mocks for the new cut (PLAN.md): stills, not shots. Each one
tries an idea the film's 3D will use, on the real sets, with the real rig.

  blender -b -P blender/mocks.py -- --mock memphis|cards|first-light|dolly-35|dolly-85|glint|all
                                    [--samples 64] [--scale 100] [--laptop apple]

Renders to out/mocks/<mock>.png. Not factory startup: the user's add-ons
load, and Photographer drives the camera where it's installed (a plain
Blender camera otherwise — the mock says which in its log line).
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nus  # noqa: E402
from nus import LOOK, MAT, OPEN_DEG, aim, area, camera, cyclorama, haze, hdri_world, image_material, panel, principled, screen_source, screen_world, srgb, studio  # noqa: E402

OUT = os.path.join(nus.ROOT, "out", "mocks")
BASE_LOOK = dict(LOOK)
SIGNAL = {"red": "#c8102e", "blue": "#1f5fbf", "gold": "#d9a400", "green": "#2e7d32", "violet": "#6b3fa0", "teal": "#1a7f8a"}
INK = "#141414"
PAPER = "#f4f1ea"


# ── Photographer, where it's installed ────────────────────────────────────────
def photographer(cam, focal=None, aperture=None, ev=None):
    """Drive the camera through Photographer's physical controls (focal,
    aperture, exposure value) so a mock's numbers are the ones the user will
    turn in the add-on's panel. Falls back to Blender's own camera."""
    pg = getattr(cam.data, "photographer", None)
    if pg is None:
        if focal:
            cam.data.lens = focal
        if aperture:
            cam.data.dof.aperture_fstop = aperture
        return "blender camera"
    try:
        if focal:
            pg.focal = focal
        if aperture:
            pg.aperture_slider_enable = True
            pg.aperture = aperture
        if ev is not None:
            pg.exposure_enabled = True
            pg.exposure_mode = "EV"
            pg.ev = ev
        # Its update callbacks write through to the camera; make sure they did.
        if focal and abs(cam.data.lens - focal) > 0.01:
            cam.data.lens = focal
        if aperture and abs(cam.data.dof.aperture_fstop - aperture) > 0.01:
            cam.data.dof.aperture_fstop = aperture
        return f"photographer: {cam.data.lens:.0f} mm f/{cam.data.dof.aperture_fstop:g}" + (f" EV {ev:g}" if ev is not None else "")
    except Exception as e:  # an add-on version with other names: say so, carry on
        if focal:
            cam.data.lens = focal
        if aperture:
            cam.data.dof.aperture_fstop = aperture
        return f"photographer failed ({e!r}); blender camera"


# ── The Memphis kit, in 3D ────────────────────────────────────────────────────
def plastic(name, hex_, rough=0.42):
    """Painted MDF, the Memphis objects' own material: flat colour, a soft sheen."""
    return principled(name, srgb(hex_), roughness=rough, **{"Specular IOR Level": 0.35, "Coat Weight": 0.15, "Coat Roughness": 0.2})


def striped(name, a, b, bands=10):
    """Hazard tape as a material: hard diagonal bands."""
    m = principled(name, srgb(a), roughness=0.45)
    nt = m.node_tree
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = bands
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*srgb(a), 1)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (*srgb(b), 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def memphis(ob):
    """Into the Memphis collection: Freestyle draws the ink outline on these only."""
    col = bpy.data.collections.get("Memphis") or bpy.data.collections.new("Memphis")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob


def squiggle(name, hex_, loc, length=0.5, amp=0.035, waves=1.5, radius=0.011, rot=0.0):
    """The icon's orbit band, as a tube lying on the floor."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    n = 40
    sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1)
        sp.points[i].co = (t * length - length / 2, amp * math.sin(2 * math.pi * waves * t), 0, 1)
        sp.points[i].radius = 0.35 + 0.65 * math.sin(math.pi * t)  # it swells, like the band
    sp.use_endpoint_u = True
    sp.order_u = 4
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.location = (loc[0], loc[1], radius)
    ob.rotation_euler.z = rot
    cu.materials.append(plastic(name, hex_))
    return memphis(ob)


def solid(name, kind, hex_, loc, size, rot=0.0, mat=None):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size / 2, location=(loc[0], loc[1], size / 2), segments=64, ring_count=32)
    elif kind == "arch":  # a half-cylinder, flat side down
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=size / 2, depth=size * 0.55, location=(loc[0], loc[1], 0), rotation=(0, math.pi / 2, 0))
        ob = bpy.context.object
        import bmesh

        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
        edges = [e for e in bm.edges if e.is_boundary]
        bmesh.ops.holes_fill(bm, edges=edges)
        bm.to_mesh(ob.data)
        bm.free()
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=size / 2, depth=size, location=(loc[0], loc[1], size / 2))
    elif kind == "block":
        bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], size * 0.18))
        bpy.context.object.scale = (size, size * 0.36, size * 0.36)
    elif kind == "ring":
        bpy.ops.mesh.primitive_torus_add(major_radius=size / 2, minor_radius=size * 0.09, location=(loc[0], loc[1], size * 0.09), major_segments=96, minor_segments=24)
    elif kind == "hoop":  # a ring stood on its edge
        bpy.ops.mesh.primitive_torus_add(major_radius=size / 2, minor_radius=size * 0.07, location=(loc[0], loc[1], size / 2 + size * 0.07), rotation=(math.pi / 2, 0, 0), major_segments=128, minor_segments=24)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler.z += rot
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat or plastic(name, hex_))
    return memphis(ob)


def outlines(px=2.2):
    """The kit's 2 px ink outline, drawn by Freestyle on the Memphis collection
    only — the machine keeps its own edges."""
    sc = bpy.context.scene
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "RELATIVE"  # scales with the render size
    sc.render.line_thickness = px
    vl = bpy.context.view_layer
    fs = vl.freestyle_settings
    for ls in list(fs.linesets):
        fs.linesets.remove(ls)
    ls = fs.linesets.new("Ink")
    ls.select_by_collection = True
    ls.collection = bpy.data.collections["Memphis"]
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = False
    ls.linestyle.color = srgb(INK)
    ls.linestyle.thickness = 1.0


def card(name, image, loc, size=0.26, look=(0, 0, 0.1), shadow=0.008):
    """A UI card in the air: the capture, and behind it, offset down-right, an
    ink slab — the app's hard 8×8 shadow, built as an object."""
    w, h = size, size / 1.6
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    face = bpy.context.object
    face.name = f"Card {name}"
    face.scale = (w, h, 1)
    face.data.materials.append(image_material(f"Card {name}", screen_source(image), strength=1.0, gloss=0.08))
    bpy.ops.mesh.primitive_cube_add(size=1)
    back = bpy.context.object
    back.name = f"Card {name} shadow"
    back.parent = face
    back.matrix_parent_inverse.identity()
    back.location = (shadow / w, -shadow / h, -0.004)  # parent-local: in card widths
    back.scale = (1 + 0.004 / w, 1 + 0.004 / h, 0.003)
    back.data.materials.append(principled("Ink", srgb(INK), roughness=0.6))
    # Face the viewer with the picture's side (+Z), not the back: the image reads right way round.
    face.rotation_euler = (Vector(look) - face.location).to_track_quat("Z", "Y").to_euler()
    return face


def blind(loc, look, slats=9, w=0.9, h=0.7, gap=0.5):
    """A venetian blind in front of a spot: the gobo, as geometry. Real
    occlusion in real haze makes real shafts."""
    parent = bpy.data.objects.new("Blind", None)
    bpy.context.collection.objects.link(parent)
    parent.location = loc
    aim(parent, look)
    pitch = h / slats
    ink = principled("Blind", (0.02, 0.02, 0.02), roughness=0.9)
    for i in range(slats):
        bpy.ops.mesh.primitive_cube_add(size=1)
        s = bpy.context.object
        s.name = f"Slat {i}"
        s.parent = parent
        s.location = (0, -h / 2 + (i + 0.5) * pitch, 0)
        s.scale = (w, pitch * (1 - gap), 0.004)
        s.data.materials.append(ink)
        s.visible_camera = False  # the gobo casts, the camera never sees it
        s.visible_glossy = False
    return parent


def spot(name, loc, look, energy, size_deg=30, blend=0.15, radius=0.02):
    d = bpy.data.lights.new(name, "SPOT")
    d.energy = energy
    d.spot_size = math.radians(size_deg)
    d.spot_blend = blend
    d.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, look)
    return ob


def sun(name, look_from, energy, angle=0.6):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(ob)
    ob.location = look_from
    aim(ob, (0, 0, 0))
    return ob


def open_screen(rig, image="window-ink"):
    return panel(rig, image, image_material(image, screen_source(image)))


def set_lid(rig, degrees):
    """Stills: the lid at an angle directly (OPEN_DEG is open, 0 shut)."""
    rig["pivot"].rotation_euler.x = math.radians(rig["open_deg"] * (1 - degrees / OPEN_DEG))


def place_cam(cam, look, at, target):
    cam.location = at
    look.location = target


# ── The mocks ─────────────────────────────────────────────────────────────────
def mock_memphis(rig):
    """The cove as a Memphis set: painted objects around the machine, a hard
    sun for the kit's hard shadows, the ink outline on the objects only."""
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"] * 0.45, rotation=40)
    cyclorama("white")
    LOOK["set_light"] = float(os.environ.get("NUS_SET_LIGHT", 0.2))  # a dimmer white-maker: the sun's shadows read
    studio(key=0, rims=LOOK["white_rims"] * 0.25)
    sun("Hard sun", (-1.6, 0.15, 1.25), float(os.environ.get("NUS_SUN", 2.6)), angle=0.4)  # from the side, clear of the cove wall: shadows rake right, the kit's 8×8
    open_screen(rig)
    squiggle("Squiggle", SIGNAL["violet"], (-0.36, 0.02), length=0.3, amp=0.03, radius=0.009, rot=0.9)
    solid("Arch", "arch", SIGNAL["gold"], (0.33, 0.1), 0.16, rot=-0.5)
    solid("Sphere", "sphere", SIGNAL["blue"], (0.3, -0.16), 0.075)
    solid("Cone", "cone", SIGNAL["teal"], (-0.3, 0.16), 0.09)
    solid("Tape", "block", "", (0.1, -0.26), 0.2, rot=0.12, mat=striped("Tape", SIGNAL["gold"], PAPER, bands=3))
    solid("Ring", "ring", SIGNAL["red"], (-0.13, -0.3), 0.08)
    outlines()
    cam, look = camera(40, 5.6)
    place_cam(cam, look, (-0.72, -0.9, 0.52), (0.0, -0.02, 0.06))
    return cam, dict(focal=40, aperture=5.6)


def mock_cards(rig):
    """The UI in the air: three captures as cards, hard-shadowed, staggered
    in depth over the cove, shallow focus on the middle one."""
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=40)
    cyclorama("white")
    studio(key=LOOK["white_key"], rims=LOOK["white_rims"] * 0.5)
    open_screen(rig)
    set_lid(rig, OPEN_DEG)
    cam, look = camera(50, 2.4)
    place_cam(cam, look, (-0.35, -1.55, 0.42), (0.02, 0.0, 0.16))
    card("ports", "ports-ink", (-0.34, -0.38, 0.3), 0.2, look=(-0.6, -1.8, 0.4))
    card("ask", "ask-ink", (0.3, -0.3, 0.26), 0.2, look=(-0.2, -1.8, 0.36))
    card("palette", "palette-ink", (0.2, 0.12, 0.42), 0.18, look=(-0.2, -1.6, 0.42))
    cam.data.dof.focus_object = bpy.data.objects["Card ask"]
    return cam, dict(focal=50, aperture=2.4)


def mock_first_light(rig):
    """First light: the machine shut on black, one spot through a blind, in
    haze — shafts of light, and bars across the lid."""
    hdri_world("monochrome_studio_02", LOOK["black_hdri"] * 0.5, rotation=-30, camera=(0, 0, 0))
    cyclorama("black")
    set_lid(rig, 0.4)
    src = (1.1, 0.9, 1.3)
    spot("Gobo", src, (0.0, 0.0, 0.0), 2400, size_deg=22, blend=0.05, radius=0.004)
    blind((0.62, 0.5, 0.78), (0.0, 0.0, 0.0), slats=8, w=0.6, h=0.45, gap=0.45)
    box = haze(0.05)
    box.scale = (1.6, 1.4, 0.9)
    box.location = (0.3, 0.2, 0.45)
    area("Rim left", (-0.95, -0.05, 0.22), (0.05, 1.3), 120, look=(0, 0, 0.04))
    cam, look = camera(35, 4.0)
    place_cam(cam, look, (-0.62, -0.78, 0.3), (0.05, 0.05, 0.12))
    return cam, dict(focal=35, aperture=4.0)


def dolly(rig, focal):
    """A dolly-zoom pair: the machine the same size, the cove behind it
    stretching (35 mm, close) or compressing (85 mm, far)."""
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=40)
    cyclorama("white")
    studio(key=LOOK["white_key"], rims=LOOK["white_rims"])
    open_screen(rig)
    sun("Hard sun", (-1.6, 0.15, 1.25), 2.0, angle=0.6)
    solid("Sphere", "sphere", SIGNAL["blue"], (0.36, 0.3), 0.12)
    solid("Arch", "arch", SIGNAL["gold"], (-0.42, 0.32), 0.2, rot=0.3)
    solid("Hoop", "hoop", SIGNAL["red"], (0.12, 0.36), 0.42, rot=-0.45)  # right behind the lid: it swells at 85, shrinks at 35
    outlines()
    target = Vector((0, 0.0, 0.1))
    direction = Vector((-0.45, -0.85, 0.22)).normalized()
    d = 0.95 * focal / 35  # same subject size: distance in step with focal length
    cam, look = camera(focal, 8.0)
    place_cam(cam, look, tuple(target + direction * d), tuple(target))
    return cam, dict(focal=focal, aperture=8.0)


def mock_glint(rig):
    """The outro's last light: the lid shut on black, a strip light caught
    mid-pass, one line of light along the edge."""
    hdri_world("monochrome_studio_02", LOOK["black_hdri"], rotation=-30, camera=(0, 0, 0))
    cyclorama("black")
    set_lid(rig, 0.4)
    studio(key=18, rims=260)
    s = area("Sweep glint", (0.05, 0.35, 0.8), (0.04, 0.9), 70, look=(0, 0, 0))
    s.rotation_euler = (0, 0, 0)
    cam, look = camera(50, 4.0)
    place_cam(cam, look, (0.5, -0.6, 0.4), (-0.02, 0.0, 0.02))
    return cam, dict(focal=50, aperture=4.0)


def hero(rig, tone):
    """The machine alone, open, three-quarter: the look-dev reference for
    metal, glass and the set."""
    if tone == "white":
        hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=40)
    else:
        hdri_world("monochrome_studio_02", LOOK["black_hdri"], rotation=-30, camera=(0, 0, 0))
    cyclorama(tone)
    studio(key=LOOK["white_key"], rims=LOOK["white_rims"])
    open_screen(rig)
    cam, look = camera(50, 5.6)
    place_cam(cam, look, (-0.62, -0.72, 0.36), (0.0, 0.0, 0.07))
    return cam, dict(focal=50, aperture=5.6)


def mock_screen(rig):
    """Macro on the display's corner: the glass, the bezel, the aluminium edge."""
    hdri_world("cyclorama_hard_light", LOOK["white_hdri"], rotation=40)
    cyclorama("white")
    studio(key=LOOK["white_key"], rims=LOOK["white_rims"])
    open_screen(rig)
    centre, n = screen_world(rig)
    corner = centre + Vector((-0.12, 0, 0.07))
    cam, look = camera(85, 5.6)
    place_cam(cam, look, tuple(corner + Vector((-0.12, -0.3, 0.04))), tuple(corner))
    return cam, dict(focal=85, aperture=5.6)


MOCKS = {
    "hero-white": lambda rig: hero(rig, "white"),
    "hero-black": lambda rig: hero(rig, "black"),
    "screen": mock_screen,
    "memphis": mock_memphis,
    "cards": mock_cards,
    "first-light": mock_first_light,
    "dolly-35": lambda rig: dolly(rig, 35),
    "dolly-85": lambda rig: dolly(rig, 85),
    "glint": mock_glint,
}


def main():
    opt = nus.args({"mock": "all", "engine": "cycles", "samples": 64, "scale": 100, "laptop": "apple"})
    names = list(MOCKS) if opt["mock"] == "all" else opt["mock"].split(",")
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        sc = nus.setup(opt, factory=False)
        LOOK.update(BASE_LOOK)
        sc.render.use_motion_blur = False
        nus.MAT.clear()
        nus.materials()
        rig = nus.apple_laptop() if opt["laptop"] == "apple" else nus.laptop()
        cam, lens = MOCKS[name](rig)
        how = photographer(cam, **lens)
        nus.light_product_only()
        if nus.STAGE >= 2:
            nus.lens()
        sc.frame_set(1)
        sc.render.filepath = os.path.join(OUT, f"{name}{opt.get('suffix', '')}.png")
        bpy.ops.render.render(write_still=True)
        print(f"MOCK {name}: {how} -> {sc.render.filepath}", flush=True)


if __name__ == "__main__":
    main()
