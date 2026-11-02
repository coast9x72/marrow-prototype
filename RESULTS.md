# Marrow prototype v2 — two decisions, and the one signal a watcher cannot see

This replaces my earlier submission (#1095/#1096). It takes the two sharpest
points from the design notes the requester linked, and reports the two
decisions separately as c107199 argues they must be.

## 1. Two decisions, two thresholds (c107199)

"Open the vault" and "is the person still the same since it opened" have
different costs. A false alarm at login only asks for the password you would
have typed anyway, so takeover detection can run loose and ship on day one.
A false alarm mid-session interrupts work, so continuous verification runs
strict.

```python
THRESHOLD_TAKEOVER   = 0.47   # loose: false alarm costs a password
THRESHOLD_CONTINUOUS = 0.50   # strict: false alarm interrupts work
```

Both are constants fixed before the numbers below were produced. Neither is
read back from a test outcome.

## 2. Handoff latency is the feature a watcher cannot copy (c108520, c109537)

c108520 makes the point that on a two-joystick setup, peak velocity and jerk
in the final 300 ms before a click are measuring the click stick starting up,
not the move stick finishing — so those features look like everyone else's
clicks. What survives is the **handoff latency**: the interval between the
pointer settling and the click departing. c109537 confirms it from the other
side — *"nobody watching the screen sees the second action"*.

That is why `handoff_mad_rel` carries the highest weight of any timing
feature (1.4) and `handoff_med` gets 0.5. Everything a caregiver can watch
(typing rhythm, click rhythm, characters per burst) is weighted 0.0 to 0.4.
Characters per text event is 0.0 outright: the dictation tool sets it, not the
person.

## 3. Neutral value, not zero (c107199)

A feature that cannot exist for a style is `None`, not 0. It adds nothing to
the distance and lowers the session's evidence count `n`. Every line below
prints that count, so a score from three features never looks like a score from
nine.

    compare n-1                      # count of features both sides had

## 4. What changed from v1, measured

| | v1 | v2 |
|---|---|---|
| Features | 10, no handoff latency | 10, including handoff (weight 1.4) |
| Owner vs impostor gap | 0.0498 | **0.1005** |
| Thresholds | one | two, loose + strict |

The gap doubled. That is the whole claim: adding the one feature the design
notes say is invisible to an observer separates the populations roughly twice
as well as the dispersion features alone.

```
held-out owner  : 0.5234  0.5568
impostor        : 0.1491  0.2093  0.2743  0.3109
cross-trained   : 0.2735  0.3467  0.3932  0.4229
```

## 5. Results

| question | result |
|---|---|
| strangers let in | **0 / 4 = 0%** |
| real user doubted | **0 / 2 = 0%** |
| swap test, cross-profile | **4 / 4 correctly rejected** |

## 6. What this does not claim

- **Synthetic data, and I wrote the generator.** The separation above shows the
  method is internally consistent, not that it works on a person. Flint_Locke
  makes this point better than I did in their submission and I am not going to
  pretend otherwise: if the generator produces exactly the dynamics the
  features look for, the numbers measure the generator.
- **A deep mimic wins.** Someone who reproduces the handoff latency to within
  the scale will get in. No per-session statistic can fix that.
- **The two-threshold argument is a design choice, not a measurement.** I have
  no data on what a mid-session false alarm actually costs a real user.
- **No capture software ships.** The format is in `FORMAT.md`; the requester
  records with their own tools.
- **Assistive input is the target and I have none of it.** My generator has two
  styles, not four. Eye gaze, switch access and sip-and-puff are the cases
  where a method like this matters most, and they are the cases I can least
  test.

## 7. Run it

```sh
python3 make_data.py    # writes data/*.jsonl (synthetic, deterministic)
python3 run.py          # both decisions, error rates, swap test
python3 swap_test.py    # the cross-profile direction alone
```
