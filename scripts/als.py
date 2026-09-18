"""Write the Live set: ableton/nus-object Project/nus-object.als.

Built from Live 12.4's own "Quick Start Beat" template so the schema is
Live's, not guessed:

  1  Perc Kitchen Kit   MIDI — the rack from the Core Library .adg, and one
                        arrangement clip holding every hit in src/score.json
  2  cuelume · arrival  audio — the one cuelume cue, at bar 17 (beat 64)
  A  Reverb, B  Delay   the template's returns, untouched

Tempo 152, 4/4, a locator at every section. Open it, play it, change it,
then File → Export Audio/Video to ableton/bounce.wav (0.0.0 to 20.0.0,
48 kHz); `npm run mux` puts that under the picture.
"""

import copy
import gzip
import json
import os
import xml.etree.ElementTree as ET

LIVE = "/Applications/Ableton Live 12 Intro.app/Contents/App-Resources"
TEMPLATE = f"{LIVE}/Core Library/Templates/Quick Start Beat.als"
DEMO = f"{LIVE}/Core Library/Lessons/Demo Songs/Chuck Sutton - Patience (Live 12 Intro Demo).als"
KIT = f"{LIVE}/Core Library/Racks/Drum Racks/Acoustic/Perc Kitchen Kit.adg"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The generated starting point only. The set you edit in Live (under
# "nus-object Project/nus-object Project/") is yours and never written here.
PROJECT = os.path.join(ROOT, "ableton", "nus-object Project")
OUT_NAME = "nus-object (generated).als"
SCORE = json.load(open(os.path.join(ROOT, "src", "score.json")))
BPM = SCORE["bpm"]
BEATS = SCORE["beats"]


def load(path):
    return ET.fromstring(gzip.open(path).read())


def val(e, path, v):
    e.find(path).set("Value", str(v))


class Ids:
    """Pointee-space ids (automation, modulation, pointees) must be unique in a
    set; anything grafted in from elsewhere is renumbered past NextPointeeId."""

    def __init__(self, start):
        self.next = start

    def graft(self, tree):
        remap = {}
        for e in tree.iter():
            if e.tag in ("AutomationTarget", "ModulationTarget", "Pointee") and "Id" in e.attrib:
                remap[e.get("Id")] = str(self.next)
                e.set("Id", str(self.next))
                self.next += 1
        for e in tree.iter("PointeeId"):
            if e.get("Value") in remap:
                e.set("Value", remap[e.get("Value")])


def clear(e):
    for c in list(e):
        e.remove(c)


def fit_slots(track, n):
    for seq in ("DeviceChain/MainSequencer/ClipSlotList", "DeviceChain/FreezeSequencer/ClipSlotList"):
        lst = track.find(seq)
        slots = list(lst)
        for s in slots[n:]:
            lst.remove(s)
        while len(lst) < n:
            s = copy.deepcopy(slots[0])
            s.set("Id", str(len(lst)))
            lst.append(s)
        for s in lst:
            v = s.find("ClipSlot/Value")
            if v is not None:
                clear(v)


# ── Presets → set ─────────────────────────────────────────────────────────────
# An .adg keeps a rack's chains beside the device, as BranchPresets; a set
# keeps them inside it, as Branches. Convert, using the template's own
# set-format branches as the shape of each kind.
def templates(doc):
    return {
        "drum": copy.deepcopy(next(doc.iter("DrumBranch"))),
        "instrument": copy.deepcopy(next(doc.iter("InstrumentBranch"))),
        "return": copy.deepcopy(next(doc.iter("ReturnBranch"))),
    }


def device_from(preset):
    if preset.tag == "GroupDevicePreset":
        return convert_group(preset)
    return copy.deepcopy(preset.find("Device")[0])


def branch_from(kind, bp, chain, name):
    b = copy.deepcopy(SHAPES[kind])
    val(b, "Name/UserName", bp.find("Name").get("Value"))
    val(b, "Name/EffectiveName", bp.find("Name").get("Value") or name)
    devs = b.find(f"DeviceChain/{chain}/Devices")
    clear(devs)
    for i, dp in enumerate(bp.find("DevicePresets")):
        d = device_from(dp)
        d.set("Id", str(i))
        devs.append(d)
    # The branch mixer is the preset's AudioBranchMixerDevice, renamed.
    pm = bp.find("MixerPreset/AbletonDevicePreset/Device")[0]
    mx = b.find("MixerDevice")
    for c in pm:
        old = mx.find(c.tag)
        if old is not None:
            mx.insert(list(mx).index(old), copy.deepcopy(c))
            mx.remove(old)
    for tag in ("IsSoloed", "SessionViewBranchWidth", "AutoColored", "AutoColorScheme"):
        if bp.find(tag) is not None and b.find(tag) is not None:
            val(b, tag, bp.find(tag).get("Value"))
    val(b, "Color", bp.find("DocumentColorIndex").get("Value"))
    b.remove(b.find("BranchSelectorRange"))
    b.insert(4, copy.deepcopy(bp.find("BranchSelectorRange")))
    sc = b.find("SourceContext")
    clear(sc)
    v = ET.SubElement(sc, "Value")
    for c in bp.find("SourceContext"):
        v.append(copy.deepcopy(c))
    return b


def convert_group(gdp):
    dev = copy.deepcopy(gdp.find("Device")[0])
    drum = dev.tag == "DrumGroupDevice"
    branches = dev.find("Branches")
    clear(branches)
    for i, bp in enumerate(gdp.find("BranchPresets")):
        if drum:
            sample = next((p.get("Value") for p in bp.iter("RelativePath") if p.get("Value")), "Pad")
            b = branch_from("drum", bp, "MidiToAudioDeviceChain", os.path.splitext(os.path.basename(sample))[0])
            for z in bp.find("ZoneSettings"):
                val(b, f"BranchInfo/{z.tag}", z.get("Value"))
        else:
            b = branch_from("instrument", bp, "MidiToAudioDeviceChain", "Perc Kitchen Kit")
            b.remove(b.find("ZoneSettings"))
            b.append(copy.deepcopy(bp.find("ZoneSettings")))
        b.set("Id", str(i))
        branches.append(b)
    returns = dev.find("ReturnBranches")
    clear(returns)
    rbp = gdp.find("ReturnBranchPresets")
    for i, bp in enumerate(list(rbp) if rbp is not None else []):
        b = branch_from("return", bp, "AudioToAudioDeviceChain", "Reverb")
        b.set("Id", str(i))
        returns.append(b)
    return dev


doc = load(TEMPLATE)
SHAPES = templates(doc)
live = doc.find("LiveSet")
ids = Ids(int(live.find("NextPointeeId").get("Value")))
scenes = len(live.find("Scenes"))
tracks = live.find("Tracks")

# ── 1 · Perc Kitchen Kit ──────────────────────────────────────────────────────
midi = [t for t in tracks if t.tag == "MidiTrack"]
drums = midi[0]
template_clip = copy.deepcopy(next(drums.iter("MidiClip")))
for t in midi[1:]:
    tracks.remove(t)

val(drums, "Name/EffectiveName", "Perc Kitchen Kit")
val(drums, "Name/UserName", "Perc Kitchen Kit")
fit_slots(drums, scenes)
clear(drums.find("AutomationEnvelopes/Envelopes"))

devices = drums.find("DeviceChain/DeviceChain/Devices")
clear(devices)
rack = convert_group(load(KIT).find("GroupDevicePreset"))
rack.set("Id", "0")
ids.graft(rack)
devices.append(rack)

clip = template_clip
clip.set("Id", "0")
clip.set("Time", "0")
val(clip, "CurrentStart", 0)
val(clip, "CurrentEnd", BEATS)
for k, v in dict(LoopStart=0, LoopEnd=BEATS, StartRelative=0, LoopOn="false", OutMarker=BEATS, HiddenLoopStart=0, HiddenLoopEnd=BEATS).items():
    val(clip, f"Loop/{k}", v)
val(clip, "Name", "nus · 152 bpm")
val(clip, "ScrollerTimePreserver/RightTime", BEATS)
val(clip, "TimeSelection/AnchorTime", 0)
val(clip, "TimeSelection/OtherTime", 0)
clear(clip.find("Envelopes/Envelopes"))
keytracks = clip.find("Notes/KeyTracks")
proto_kt = copy.deepcopy(keytracks[0])
clear(keytracks)
note_id = 1
for i, key in enumerate(sorted({n["note"] for n in SCORE["notes"]})):
    kt = copy.deepcopy(proto_kt)
    kt.set("Id", str(i))
    evs = kt.find("Notes")
    clear(evs)
    for n in (n for n in SCORE["notes"] if n["note"] == key):
        ET.SubElement(evs, "MidiNoteEvent", Time=repr(n["beat"]), Duration=repr(n["dur"]), Velocity=str(n["vel"]), OffVelocity="64", NoteId=str(note_id))
        note_id += 1
    val(kt, "MidiKey", key)
    keytracks.append(kt)
val(clip, "Notes/NoteIdGenerator/NextId", note_id)
arr = drums.find("DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events")
clear(arr)
arr.append(clip)

# ── 2 · cuelume, once ─────────────────────────────────────────────────────────
demo = load(DEMO).find("LiveSet")
audio = copy.deepcopy(next(t for t in demo.find("Tracks") if t.tag == "AudioTrack"))
audio.set("Id", str(max(int(t.get("Id")) for t in tracks) + 1))
val(audio, "Name/EffectiveName", "cuelume · arrival")
val(audio, "Name/UserName", "cuelume · arrival")
val(audio, "TrackGroupId", -1)
fit_slots(audio, scenes)
clear(audio.find("AutomationEnvelopes/Envelopes"))
clear(audio.find("DeviceChain/DeviceChain/Devices"))
for lanes in audio.iter("TakeLanes"):
    inner = lanes.find("TakeLanes")
    if inner is not None:
        clear(inner)
events = audio.find("DeviceChain/MainSequencer/Sample/ArrangerAutomation/Events")
aclip = copy.deepcopy(events[0])
clear(events)

wav = os.path.join(PROJECT, "Samples", "Imported", "cuelume-arrival.wav")
frames = (os.path.getsize(wav) - 44) // 4
seconds = frames / 48000
beat = SCORE["cuelume"][0]["beat"]
length = seconds * BPM / 60
aclip.set("Id", "0")
aclip.set("Time", repr(beat))
val(aclip, "CurrentStart", beat)
val(aclip, "CurrentEnd", beat + length)
for k, v in dict(LoopStart=0, LoopEnd=length, StartRelative=0, LoopOn="false", OutMarker=length, HiddenLoopStart=0, HiddenLoopEnd=length).items():
    val(aclip, f"Loop/{k}", v)
val(aclip, "Name", "cuelume · arrival")
val(aclip, "IsWarped", "false")
val(aclip, "TakeId", 0)
val(aclip, "ScrollerTimePreserver/RightTime", length)
clear(aclip.find("Envelopes/Envelopes"))
fr = aclip.find("SampleRef/FileRef")
for k, v in dict(RelativePathType=3, RelativePath="Samples/Imported/cuelume-arrival.wav", Path=wav, Type=1, LivePackName="", LivePackId="", OriginalFileSize=os.path.getsize(wav), OriginalCrc=0).items():
    val(fr, k, v)
val(aclip, "SampleRef/DefaultDuration", frames)
val(aclip, "SampleRef/DefaultSampleRate", 48000)
wm = aclip.find("WarpMarkers")
m0, m1 = list(wm)[:2]
clear(wm)
m0.attrib.update(Id="0", SecTime="0", BeatTime="0")
m1.attrib.update(Id="1", SecTime=repr(seconds), BeatTime=repr(length))
wm.extend([m0, m1])
events.append(aclip)
val(audio, "DeviceChain/Mixer/Volume/Manual", 0.5)
ids.graft(audio)
tracks.insert(1, audio)

# ── Tempo, locators, transport ────────────────────────────────────────────────
main = live.find("MainTrack")
tempo = main.find(".//Tempo")
val(tempo, "Manual", BPM)
tempo_target = tempo.find("AutomationTarget").get("Id")
for env in main.iter("AutomationEnvelope"):
    if env.find("EnvelopeTarget/PointeeId").get("Value") == tempo_target:
        for ev in env.iter("FloatEvent"):
            ev.set("Value", str(BPM))

locators = live.find("Locators/Locators")
clear(locators)
for i, s in enumerate(SCORE["sections"]):
    loc = ET.SubElement(locators, "Locator", Id=str(i))
    for tag, v in (("LomId", 0), ("Time", s["beat"]), ("Name", s["name"]), ("Annotation", ""), ("IsSongStart", "false")):
        ET.SubElement(loc, tag, Value=str(v))

val(live, "Transport/LoopStart", 0)
val(live, "Transport/LoopLength", BEATS)
val(live, "Transport/LoopOn", "false")
val(live, "Transport/CurrentTime", 0)
val(live, "NextPointeeId", ids.next)

# ── Sanity: every pointee id unique, every reference resolves ─────────────────
seen = {}
for e in doc.iter():
    if e.tag in ("AutomationTarget", "ModulationTarget", "Pointee") and "Id" in e.attrib:
        assert e.get("Id") not in seen, f"duplicate pointee id {e.get('Id')}"
        seen[e.get("Id")] = e.tag
dangling = [e.get("Value") for e in doc.iter("PointeeId") if e.get("Value") not in seen and e.get("Value") != "0"]
assert not dangling, f"dangling PointeeIds: {dangling[:5]}"
track_ids = [t.get("Id") for t in tracks]
assert len(set(track_ids)) == len(track_ids), track_ids

os.makedirs(PROJECT, exist_ok=True)
out = os.path.join(PROJECT, OUT_NAME)
xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(doc, encoding="utf-8")
with gzip.open(out, "wb") as f:
    f.write(xml)
print(f"{os.path.relpath(out, ROOT)} · {BPM} bpm · {len(SCORE['notes'])} notes on {len(keytracks)} pads · {len(locators)} locators · tracks {[t.find('Name/EffectiveName').get('Value') for t in tracks]}")
