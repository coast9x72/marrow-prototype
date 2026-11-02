import sys, glob, os
sys.path.insert(0, '/tmp/marrow2')
import marrow

print("SWAP TEST (v2): train on a different person, test against the owner")
worst = 0.0
for style in ("mouse_keyboard", "dictation"):
    owner = "data/%s_owner.jsonl" % style
    for trainer in ("stranger", "mimic"):
        m = marrow.fit(["data/%s_%s.jsonl" % (style, trainer)])
        ok, s, n = marrow.decide_continuous(m, owner)
        worst = max(worst, s)
        print("%-14s trained on %-9s -> owner %.4f  %s" % (
            style, trainer, s, "WRONGLY OPEN" if ok else "correctly rejected"))
print()
print("worst cross-profile: %.4f | takeover threshold %.2f | continuous %.2f" % (
    worst, marrow.THRESHOLD_TAKEOVER, marrow.THRESHOLD_CONTINUOUS))
print("PASS" if worst < marrow.THRESHOLD_TAKEOVER else "FAIL")
