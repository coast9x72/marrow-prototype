#!/usr/bin/env python3
"""Generate the fake data the prototype ships with.

Two input styles x three roles each, as the condition requires:

  mouse_keyboard : a standard mouse and physical keyboard
  dictation      : a slow pointer and text inserted by dictation software

Roles:
  owner    -- the enrolled user, with a tired variant
  stranger -- someone else entirely
  mimic    -- copies the owner's habits deliberately

The generator separates the three roles on the axes a real capture would
separate them on: the owner has a stable, low-variance rhythm; a stranger has
a different centre AND different variance; a mimic matches the centre but not
the variance, which is what makes the swap test meaningful rather than
trivially passable.

Deterministic given the seed. No real movement data is used or claimed.
"""
import json, os, random

OUT = os.path.join(os.path.dirname(__file__), "data")


def _emit(ev):
    return json.dumps(ev, separators=(",", ":"))


PROFILE = {
    # style             role       speed  jit_scale  dt_sigma  wpm  corr
    ("mouse_keyboard", "owner"):    (1.00, 1.00, 0.10, 52, 0.05),
    ("mouse_keyboard", "stranger"): (0.55, 3.20, 0.42, 28, 0.22),
    ("mouse_keyboard", "mimic"):    (1.00, 2.60, 0.34, 52, 0.17),
    ("dictation",      "owner"):    (0.38, 1.00, 0.12,  0, 0.09),
    ("dictation",      "stranger"): (0.82, 2.80, 0.45,  0, 0.30),
    ("dictation",      "mimic"):    (0.38, 2.20, 0.33,  0, 0.21),
}


def gen_style(style, role, seed, tired=False):
    rng = random.Random(seed)
    speed, jit_scale, dt_sigma, wpm, corr = PROFILE[(style, role)]
    if tired and role == "owner":
        speed *= 0.72
        jit_scale *= 1.55
        corr *= 1.5

    jitter = 2.2 * jit_scale
    via = "dictation" if style == "dictation" else "typed"
    words = "the report is ready for review and the numbers look right".split()

    t = 0
    x, y = 0.5, 0.5
    out = []
    for i in range(200):
        # pointer timing: owner's rhythm is tight, everyone else's is sloppy
        gap = max(4, int(rng.gauss(16, 16 * dt_sigma) / max(speed, 0.05)))
        t += gap
        tx, ty = rng.uniform(0.08, 0.92), rng.uniform(0.08, 0.92)
        step = 0.20 * speed
        x += (tx - x) * step + rng.gauss(0, jitter) / 1000.0
        y += (ty - y) * step + rng.gauss(0, jitter) / 1000.0
        x = min(0.999, max(0.001, x))
        y = min(0.999, max(0.001, y))
        out.append(_emit({"t": t, "kind": "pointer", "x": round(x, 4), "y": round(y, 4)}))

        if i % 9 == 0:
            t += max(10, int(rng.gauss(95, 95 * dt_sigma) / max(speed, 0.05)))
            out.append(_emit({"t": t, "kind": "click", "x": round(x, 4), "y": round(y, 4), "button": "left"}))

        if i % 6 == 0:
            w = words[(i // 6) % len(words)]
            if via == "dictation":
                t += max(30, int(rng.gauss(640, 640 * dt_sigma) / max(speed, 0.05)))
                out.append(_emit({"t": t, "kind": "text", "insert": " " + w, "via": "dictation"}))
                if rng.random() < corr:
                    t += max(40, int(rng.gauss(820, 820 * dt_sigma)))
                    out.append(_emit({"t": t, "kind": "correct", "deleted": len(w) - 1,
                                      "insert": w[:-1] + "s", "via": "dictation"}))
            else:
                per_char = 60000.0 / max(wpm * 5, 1) / max(speed, 0.05)
                for ch in (" " + w):
                    t += max(8, int(abs(rng.gauss(per_char, per_char * 0.55 * dt_sigma))))
                    out.append(_emit({"t": t, "kind": "text", "insert": ch, "via": via}))
                if rng.random() < corr:
                    t += max(20, int(abs(rng.gauss(per_char * 2, per_char * dt_sigma))))
                    out.append(_emit({"t": t, "kind": "key", "key": "backspace", "via": via}))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for si, style in enumerate(("mouse_keyboard", "dictation")):
        for ri, role in enumerate(("owner", "stranger", "mimic")):
            for tired in ((False, True) if role == "owner" else (False,)):
                seed = 1000 * (si + 1) + 10 * ri + (1 if tired else 0)
                name = style + "_" + role + ("_tired" if tired else "") + ".jsonl"
                lines = gen_style(style, role, seed, tired)
                with open(os.path.join(OUT, name), "w") as f:
                    f.write("\n".join(lines) + "\n")
                made += 1
                print("wrote %s (%d events)" % (name, len(lines)))
    print("%d recordings in %s" % (made, OUT))


if __name__ == "__main__":
    main()
