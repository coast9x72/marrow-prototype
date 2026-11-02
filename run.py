#!/usr/bin/env python3
"""Train and evaluate Marrow v2. One command, offline, stdlib only."""
import glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marrow

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")


def main():
    if not os.path.isdir(D) or not glob.glob(os.path.join(D, "*.jsonl")):
        print("no data; run: python3 make_data.py")
        return 2

    print("Marrow v2 — two decisions, not one")
    print("takeover   threshold %.2f (loose: false alarm costs a password)" % marrow.THRESHOLD_TAKEOVER)
    print("continuous threshold %.2f (strict: false alarm interrupts work)" % marrow.THRESHOLD_CONTINUOUS)
    print()

    fa = frr = ni = no = 0
    for style in ("mouse_keyboard", "dictation"):
        own = sorted(glob.glob(os.path.join(D, style + "_owner*.jsonl")))
        imp = sorted(glob.glob(os.path.join(D, style + "_stranger*.jsonl"))) + \
              sorted(glob.glob(os.path.join(D, style + "_mimic*.jsonl")))
        if len(own) < 2 or not imp:
            continue
        m = marrow.fit([own[0]])
        print("== %s ==" % style)
        print("   enrolled on %s" % os.path.basename(own[0]))
        for p in own[1:]:
            ok, s, n = marrow.decide_continuous(m, p)
            no += 1
            if not ok:
                frr += 1
            print("   owner      %-36s %.4f  n=%d  %s" % (
                os.path.basename(p), s, n, "OPEN" if ok else "LOCKED OUT"))
        for p in imp:
            ok, s, n = marrow.decide_continuous(m, p)
            ni += 1
            if ok:
                fa += 1
            print("   impostor   %-36s %.4f  n=%d  %s" % (
                os.path.basename(p), s, n, "LET IN" if ok else "rejected"))
        print()

    print("strangers let in : %d/%d = %.0f%%" % (fa, ni, 100.0 * fa / max(ni, 1)))
    print("real user doubted: %d/%d = %.0f%%" % (frr, no, 100.0 * frr / max(no, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
