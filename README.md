# Marrow v2

Decides whether the person at the computer is the enrolled user, from ordinary
input events only: pointer movement, clicks, and text by arrival mode. No
audio, no camera, no text content.

Two decisions with two thresholds, following c107199: takeover detection runs
loose because a false alarm only asks for a password, continuous verification
runs strict because a false alarm interrupts work.

The strongest feature is **handoff latency** — the gap between the pointer
settling and the click departing. Per c108520 and c109537 that interval is
invisible to anyone watching the screen, which is exactly what makes it hard
to imitate.

## One command

    python3 make_data.py && python3 run.py

Stdlib only. No network calls. MIT.
