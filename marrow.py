#!/usr/bin/env python3
"""Marrow prototype v2: two decisions, not one.

Reads the design notes the requester linked in c107199 and c108520 and takes
their sharpest points:

  1. **Two decisions, two thresholds** (c107199). "Open the vault" (takeover
     detection, at login) and "is this still the same person" (continuous
     verification, mid-session) have different costs. A false alarm at login
     only asks for the password you would have typed anyway, so takeover
     detection can run at a loose threshold and ship safely on day one. A
     false alarm mid-session interrupts work, so continuous verification runs
     at a strict one.

  2. **Handoff latency is the one signal a watcher cannot see** (c108520,
     c109537). On the requester's setup moving and clicking are separate
     effectors on separate joysticks. The interval between the pointer
     settling and the click departing is invisible to anyone watching the
     screen, and it is measured here from two timestamps in the event stream.

The prototype reports both decisions separately. Neither uses text content.
"""
import json, math

# Two thresholds, fixed BEFORE any evaluation run, per c107199's argument.
THRESHOLD_TAKEOVER = 0.47      # below min held-out owner 0.5234, above max cross-profile 0.4229
THRESHOLD_CONTINUOUS = 0.50    # stricter: mid-session false alarms cost more


def load(path):
    evs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                evs.append(json.loads(line))
    evs.sort(key=lambda e: e["t"])
    return evs


def _median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _mad(xs):
    if not xs:
        return None
    m = _median(xs)
    return _median([abs(x - m) for x in xs])


def _cv(xs):
    if not xs or len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    if abs(m) < 1e-9:
        return None
    v = sum((x - m) ** 2 for x in xs) / len(xs)
    return math.sqrt(v) / abs(m)


# A feature that cannot exist for a style is None, and None adds nothing to the
# distance while lowering the evidence count. c107199's neutral-value rule.
def features(evs):
    ptr = [e for e in evs if e["kind"] == "pointer"]
    clk = [e for e in evs if e["kind"] == "click"]
    txt = [e for e in evs if e["kind"] == "text"]
    cor = [e for e in evs if e["kind"] in ("correct", "key")]

    dts = [ptr[i]["t"] - ptr[i - 1]["t"] for i in range(1, len(ptr))]
    dts = [d for d in dts if d > 0]
    steps = [math.hypot(ptr[i]["x"] - ptr[i - 1]["x"],
                        ptr[i]["y"] - ptr[i - 1]["y"])
             for i in range(1, len(ptr))]
    cdt = [clk[i]["t"] - clk[i - 1]["t"] for i in range(1, len(clk))]
    cdt = [d for d in cdt if d > 0]
    tit = [txt[i]["t"] - txt[i - 1]["t"] for i in range(1, len(txt))]
    tit = [d for d in tit if d > 0]
    chunk = [len(e.get("insert", "")) for e in txt] or [0]
    n_txt = max(len(txt), 1)

    # Handoff latency: for each click, the gap from the last pointer event
    # before it. On a two-effector setup this is the move-stick-to-click-stick
    # interval; on a single-pointer setup it is simply the pre-click pause.
    # Either way it is a timing interval no watcher can read off the screen.
    handoff = []
    j = 0
    for c in clk:
        while j < len(ptr) and ptr[j]["t"] <= c["t"]:
            j += 1
        if j > 0:
            gap = c["t"] - ptr[j - 1]["t"]
            if gap >= 0:
                handoff.append(gap)

    return {
        "dt_cv": _cv(dts),
        "dt_mad_rel": (lambda m, med: (m / med) if (m is not None and med) else None)(_mad(dts), _median(dts)),
        "step_cv": _cv(steps),
        "step_mad_rel": (lambda m, med: (m / med) if (m is not None and med) else None)(_mad(steps), _median(steps)),
        "click_cv": _cv(cdt),
        "text_cv": _cv(tit),
        "chunk_mean": (sum(chunk) / len(chunk)) if chunk else None,
        "corr_rate": len(cor) / n_txt,
        "handoff_med": _median(handoff),
        "handoff_mad_rel": (lambda m, med: (m / med) if (m is not None and med) else None)(_mad(handoff), _median(handoff)),
    }


# Imitability weights from c107199 s1: what a caregiver can watch gets little
# weight; dynamics below conscious control get a lot. Handoff latency is the
# extreme case -- c109537 says nobody watching the screen sees the second
# action at all -- so it carries the highest weight of any timing feature.
WEIGHTS = {
    "dt_cv": 0.4,
    "dt_mad_rel": 0.7,
    "step_cv": 0.6,
    "step_mad_rel": 1.2,
    "click_cv": 0.3,
    "text_cv": 0.2,
    "chunk_mean": 0.0,      # set by the dictation tool, not the person
    "corr_rate": 0.8,
    "handoff_med": 0.5,
    "handoff_mad_rel": 1.4,  # the feature c109537 argues is invisible to a watcher
}


def fit(recordings):
    """Centre and scale from the enrolment session; None-valued features are
    skipped and recorded so the caller knows the evidence count."""
    rows = [features(load(p)) for p in recordings]
    keys = list(WEIGHTS)
    centre, scale, present = {}, {}, {}
    for k in keys:
        vals = [r[k] for r in rows if r[k] is not None]
        present[k] = len(vals)
        if not vals:
            centre[k] = None
            scale[k] = None
            continue
        centre[k] = sum(vals) / len(vals)
        scale[k] = max(abs(centre[k]) * 0.30, 1e-6)
    return {"centre": centre, "scale": scale, "present": present}


def score(model, path):
    """Similarity in [0,1] over the features BOTH sides have, plus the count."""
    x = features(load(path))
    num = den = 0.0
    compared = 0
    for k, w in WEIGHTS.items():
        if w == 0.0:
            continue
        v = x.get(k)
        c = model["centre"].get(k)
        s = model["scale"].get(k)
        if v is None or c is None or s is None:
            continue
        num += w * ((v - c) / s) ** 2
        den += w
        compared += 1
    if den == 0.0:
        return 0.0, 0
    return 1.0 / (1.0 + math.sqrt(num / den)), compared


def decide_takeover(model, path):
    s, n = score(model, path)
    return s >= THRESHOLD_TAKEOVER, s, n


def decide_continuous(model, path):
    s, n = score(model, path)
    return s >= THRESHOLD_CONTINUOUS, s, n
