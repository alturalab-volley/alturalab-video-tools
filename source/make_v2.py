# Altura LAB · MY VOLLEYBALL WEEK · reel v2 (EN) · 1080x1920 · 30 fps · 120 BPM
# Visuals use real captures of the product (p1.png, p2.png) and cell positions (boxes.json).
# The soundtrack is synthesized here from scratch (no samples, no third-party audio).
import json, math, os, subprocess, sys, wave, datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR, BEAT = 1080, 1920, 30, 18.0, 0.5
INK, LIME, WHITE, GREY = (17, 17, 17), (200, 226, 58), (255, 255, 255), (205, 205, 200)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # repository root
FD = os.path.join(ROOT, "tools", "fonts") + os.sep   # Inter 4.0 (OFL), bundled in the project
FFMPEG = os.path.join(ROOT, "tools", "ffmpeg")
OUTDIR = os.path.join(ROOT, "renders")             # never overwrites the approved MP4 in ROOT
os.makedirs(OUTDIR, exist_ok=True)
BLACK = lambda s: ImageFont.truetype(FD + "InterDisplay-BlackItalic.otf", s)
XB = lambda s: ImageFont.truetype(FD + "InterDisplay-ExtraBoldItalic.otf", s)
BOLD = lambda s: ImageFont.truetype(FD + "Inter-Bold.otf", s)
SEMI = lambda s: ImageFont.truetype(FD + "Inter-SemiBold.otf", s)
ITAL = lambda s: ImageFont.truetype(FD + "Inter-Italic.otf", s)

info = json.load(open(os.path.join(HERE, "boxes.json")))
P1, P2 = Image.open(os.path.join(HERE, "p1.png")).convert("RGB"), Image.open(os.path.join(HERE, "p2.png")).convert("RGB")
PX = P1.width / info["sec"][0]                       # image px per CSS px
CARD = (40, 330, 1000, 1100)                         # x, y, w, h on screen
BASE = 1000 / 714                                    # screen px per CSS px at zoom 1

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEK = [(1, "Court", ""), (3, "Gym", ""), (1, "Court", "Most of my movement was backward"), (4, "Rest", ""),
        (1, "Court", ""), (2, "Match", "Noted 2 passes to review on video"), (4, "Rest", "")]
T_D0, T_D = 4.5, 1.0                                  # day i starts at T_D0 + i (on the beat)
HOOK = [("PRACTICE.", 0.0), ("GYM.", 0.5), ("MATCH.", 1.0), ("REST.", 1.5)]

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def inout(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, x): return a + (b - a) * x
def mix(c, p): return tuple(int(INK[j] + (c[j] - INK[j]) * p) for j in range(3))
def text_c(d, y, s, f, fill): d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)

def row_cy(i): r = info["rows"][i][0]; return r[1] + r[3] / 2

def camera(t):
    """returns zoom, cx, cy in CSS px"""
    if t < 4.0:
        return 1.0, 401, 560
    if t < 11.0:
        if t < 4.5: x = inout((t - 4.0) / 0.5); return lerp(1.0, 1.8, x), lerp(401, 245, x), lerp(560, max(row_cy(0), 497), x)
        i = min(6, int((t - T_D0) // T_D)); ti = t - (T_D0 + i * T_D)
        cy_prev = min(max(row_cy(max(i - 1, 0)), 497), 640); cy_now = min(max(row_cy(i), 497), 640)
        cy = lerp(cy_prev, cy_now, inout(ti / 0.35))
        cx = 245
        if WEEK[i][2]: cx = lerp(245, 520, inout((ti - 0.15) / 0.3))
        if i > 0 and WEEK[i - 1][2] and ti < 0.35: cx = lerp(520, 245, inout(ti / 0.35))
        return 1.8, cx, cy
    if t < 11.6:
        x = inout((t - 11.0) / 0.6); return lerp(1.8, 0.9, x), lerp(245, 397, x), lerp(640, 480, x)
    return 0.9, 397, 480

def view(img, z, cx, cy):
    k = BASE * z; sw, sh = CARD[2] / k, CARD[3] / k
    box = ((cx - sw / 2) * PX, (cy - sh / 2) * PX, (cx + sw / 2) * PX, (cy + sh / 2) * PX)
    v = img.resize((CARD[2], CARD[3]), Image.LANCZOS, box=box)
    to = lambda x, y: ((x - (cx - sw / 2)) * k, (y - (cy - sh / 2)) * k)
    return v, to, k

def check(d, cx, cy, size, p, w):
    a = (cx - size * .45, cy); b = (cx - size * .12, cy + size * .35); c = (cx + size * .5, cy - size * .42)
    l1, l2 = math.dist(a, b), math.dist(b, c); L = (l1 + l2) * max(0, min(1, p))
    if L <= 0: return
    if L <= l1: d.line([a, (lerp(a[0], b[0], L / l1), lerp(a[1], b[1], L / l1))], fill=INK, width=w); return
    d.line([a, b], fill=INK, width=w); x = (L - l1) / l2
    d.line([b, (lerp(b[0], c[0], x), lerp(b[1], c[1], x))], fill=INK, width=w, joint="curve")

def planner(t):
    z, cx, cy = camera(t)
    v, to, k = view(P1, z, cx, cy); d = ImageDraw.Draw(v)
    cur = int((t - T_D0) // T_D) if t >= T_D0 else -1
    for i, (col, label, note) in enumerate(WEEK):
        t0 = T_D0 + i * T_D
        if t < t0: continue
        row = info["rows"][i]; rx, ry, _, rh = row[0]; lx, _, lw, _ = row[5]
        if i == cur and t < 11.0:
            x0, y0 = to(rx, ry); x1, y1 = to(lx + lw, ry + rh)
            bx = (max(0, int(x0)), max(0, int(y0)), min(v.width, int(x1)), min(v.height, int(y1)))
            if bx[2] > bx[0] and bx[3] > bx[1]:
                reg = v.crop(bx); v.paste(Image.blend(reg, Image.new("RGB", reg.size, LIME), 0.38), bx[:2]); d = ImageDraw.Draw(v)
        bxx, byy, bw, bh = row[col]
        ccx, ccy = to(bxx + bw / 2, byy + 21)
        check(d, ccx, ccy, 26 * k, (t - t0) / 0.25, max(4, int(4.2 * k)))
        if note:
            p = ease((t - t0 - 0.3) / 0.4); nx, ny = to(lx + 8, ry + 13)
            d.text((nx, ny), note[:int(len(note) * p)], font=ITAL(int(13.5 * k)), fill=INK)
    return v

def frame(t):
    im = Image.new("RGB", (W, H), INK); d = ImageDraw.Draw(im)
    d.text((60, 120), "ALTURA LAB", font=BOLD(30), fill=LIME)
    # A · hook, one word per beat
    if t < 2.0:
        for i, (w_, t0) in enumerate(HOOK):
            if t0 <= t < t0 + BEAT:
                p = ease((t - t0) / 0.18); f = BLACK(int(lerp(150, 170, p)))
                col = LIME if w_ == "REST." else WHITE
                text_c(d, 820 - (1 - p) * 30, w_, f, mix(col, p))
        return im
    # B · question
    if t < 3.5:
        p1 = ease((t - 2.0) / 0.25); p2 = ease((t - 2.5) / 0.25); out = 1 - ease((t - 3.3) / 0.2)
        text_c(d, 700 + (1 - p1) * 30, "What's your plan", BLACK(112), mix(WHITE, p1 * out))
        text_c(d, 850 + (1 - p2) * 30, "this week?", BLACK(140), mix(LIME, p2 * out))
        return im
    # C/D · planner page 1
    if t < 13.0:
        badge = "EXAMPLE WEEK · FICTIONAL DATA"; f = SEMI(28); bw = d.textlength(badge, font=f)
        d.rounded_rectangle([60, 230, 60 + bw + 36, 282], radius=26, outline=LIME, width=3); d.text((78, 238), badge, font=f, fill=LIME)
        v = planner(t)
        slide = ease((t - 3.5) / 0.5); out = 1 - ease((t - 12.8) / 0.2)
        mask = Image.new("L", v.size, int(255 * slide * out))
        im.paste(v, (CARD[0], int(CARD[1] + (1 - slide) * 120)), mask)
        cur = int((t - T_D0) // T_D) if t >= T_D0 else -1
        if 0 <= cur <= 6 and t < 11.0:
            col, label, _ = WEEK[cur]; p = ease((t - (T_D0 + cur * T_D)) / 0.2)
            day = DAYS[cur]; f1, f2 = BLACK(92), BLACK(92)
            w1 = d.textlength(day + " ", font=f1); w2 = d.textlength(label, font=f2); x = (W - w1 - w2) / 2
            d.text((x, 1480 + (1 - p) * 18), day + " ", font=f1, fill=mix(WHITE, p))
            d.text((x + w1, 1480 + (1 - p) * 18), label, font=f2, fill=mix(LIME, p))
        elif t >= 11.2:
            p = ease((t - 11.2) / 0.3) * out
            text_c(d, 1480, "One week. One page.", BLACK(92), mix(WHITE, p))
        return im
    # E · page 2, weekly review
    if t < 14.5:
        p = ease((t - 13.0) / 0.35); out = 1 - ease((t - 14.3) / 0.2)
        z = lerp(0.9, 0.95, (t - 13.0) / 1.5)
        v, _, _ = view(P2, z, 397, 480)
        im.paste(v, (CARD[0], int(CARD[1] + (1 - p) * 120)), Image.new("L", v.size, int(255 * p * out)))
        text_c(d, 1480, "+ a weekly review.", BLACK(92), mix(WHITE, p * out))
        return im
    # F · call to action
    p1 = ease((t - 14.5) / 0.3); p2 = ease((t - 15.0) / 0.3); p3 = ease((t - 15.5) / 0.3)
    text_c(d, 600 + (1 - p1) * 30, "Free weekly", BLACK(124), mix(WHITE, p1))
    text_c(d, 750 + (1 - p1) * 30, "planner", BLACK(124), mix(LIME, p1))
    if p2 > 0:
        url = "payhip.com/AlturaLAB"; f = XB(76); w = d.textlength(url, font=f); x0 = (W - w) / 2 - 30
        d.rectangle([x0, 950, x0 + (w + 60) * p2, 1060], fill=LIME)
        if p2 > 0.6: d.text((x0 + 30, 958), url, font=f, fill=INK)
    text_c(d, 1120, "Printable PDF · 2 pages", SEMI(38), mix(GREY, p3))
    return im

# ---------------------------------------------------------------- soundtrack (original, synthesized)
SR = 44100; N = int(DUR * SR); tt = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); j = min(N, i + len(sig)); s = sig[: j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))
def env(n, a, r): e = np.ones(n); ai = int(a * SR); e[:ai] = np.linspace(0, 1, ai) if ai else 1; e *= np.exp(-np.arange(n) / (r * SR)); return e
def kick():
    n = int(.35 * SR); x = np.arange(n) / SR; f = 45 + 90 * np.exp(-x * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-x * 9)
def hat():
    n = int(.06 * SR); nz = np.random.default_rng(1).standard_normal(n); nz = np.diff(np.concatenate([[0], nz]))
    return nz * np.exp(-np.arange(n) / (0.012 * SR)) * 0.5
def tick():
    n = int(.05 * SR); x = np.arange(n) / SR; return (np.sin(2 * np.pi * 2200 * x) + .5 * np.sin(2 * np.pi * 3300 * x)) * np.exp(-x * 90)
def pluck(freq, dur, bright=3):
    n = int(dur * SR); x = np.arange(n) / SR; s = sum(np.sin(2 * np.pi * freq * h * x) / h ** 1.3 for h in range(1, bright + 1))
    return s * env(n, 0.005, dur / 3)
def pad(freqs, dur):
    n = int(dur * SR); x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * x) + .3 * np.sin(2 * np.pi * f * 2.003 * x) for f in freqs) / len(freqs)
    e = np.minimum(1, x / 0.4) * np.minimum(1, (dur - x) / 0.3); return s * e
def whoosh(dur=0.45):
    n = int(dur * SR); nz = np.random.default_rng(2).standard_normal(n); out = np.zeros(n); a = 0
    for i in range(n): a += (0.02 + 0.25 * i / n) * (nz[i] - a); out[i] = a
    return out * np.sin(np.pi * np.arange(n) / n) ** 2
A1, F1, C2, G1 = 55.0, 43.65, 65.41, 49.0
CH = [(A1, [220, 261.6, 329.6]), (F1, [174.6, 220, 261.6]), (C2, [196, 261.6, 329.6]), (G1, [196, 246.9, 293.7])]
for i, (_, t0) in enumerate(HOOK): add(kick(), t0, .95); add(pluck(440 if i < 3 else 659.3, .3, 4), t0, .18)
for b in range(int(2.0 / BEAT), int(14.5 / BEAT)):
    t0 = b * BEAT; add(kick(), t0, .85 if t0 >= 3.5 else .6)
    if t0 >= 3.5: add(hat(), t0 + BEAT / 2, .35, .3)
    bar = int((t0 - 2.0) // 2) % 4; root = CH[bar][0]
    add(pluck(root * 2, .45, 5), t0, .32); add(pluck(root * 2, .2, 5), t0 + .25 + 0.0, .16)
for bar in range(int((14.5 - 3.5) // 2) + 1):
    t0 = 3.5 + bar * 2; dur = min(2.0, 14.5 - t0)
    if dur > 0.3: add(pad(CH[int((t0 - 2.0) // 2) % 4][1], dur), t0, .10)
for i in range(7): add(tick(), T_D0 + i * T_D + .12, .30, -.2)
for t0 in (3.4, 10.95, 12.9, 14.4): add(whoosh(), t0 - .2, .25)
add(kick(), 14.5, 1.0); add(pad([220, 261.6, 329.6, 440], 3.4), 14.5, .16)
for i, f in enumerate([440, 523.3, 659.3]): add(pluck(f, .6, 3), 15.0 + i * .5, .14)
fade = np.minimum(1, (DUR - tt) / 1.0); L *= fade; R *= fade
st = np.stack([L, R], 1); st /= np.max(np.abs(st)) / 0.9
MUSIC = os.path.join(OUTDIR, "music_render.wav")
with wave.open(MUSIC, "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st * 32767).astype("<i2").tobytes())

# ---------------------------------------------------------------- video + mux
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
OUT = os.path.join(OUTDIR, sys.argv[1] if len(sys.argv) > 1 else f"AlturaLAB_MY_VOLLEYBALL_WEEK_reel_v2_EN_render_{STAMP}.mp4")
assert not os.path.exists(OUT), f"refusing to overwrite {OUT}"
cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", MUSIC, "-filter:a", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
       "-map_metadata", "-1", "-metadata", "title=MY VOLLEYBALL WEEK · Example week", "-metadata", "artist=Altura LAB",
       "-metadata", "author=Altura LAB", "-shortest", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(int(DUR * FPS)): pr.stdin.write(frame(n / FPS).tobytes())
pr.stdin.close(); pr.wait(); print("done", pr.returncode)
