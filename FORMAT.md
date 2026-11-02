# Recording format

One JSON object per line (JSONL), UTF-8, LF. Timestamps are integer
milliseconds from the start of the session. Coordinates are fractions of the
screen in [0,1] so no device or resolution is assumed.

```json
{"t": 0,    "kind": "pointer", "x": 0.512, "y": 0.331}
{"t": 16,   "kind": "click",   "x": 0.512, "y": 0.331, "button": "left"}
{"t": 220,  "kind": "text",    "insert": "hello", "via": "typed"}
{"t": 940,  "kind": "text",    "insert": " wrld", "via": "dictation"}
{"t": 1010, "kind": "correct", "deleted": 4, "insert": "world", "via": "typed"}
{"t": 1500, "kind": "key",     "key": "backspace", "via": "onscreen"}
```

## Fields

| field | meaning |
|---|---|
| `t` | integer milliseconds since session start |
| `kind` | `pointer`, `click`, `text`, `correct`, `key` |
| `x`, `y` | pointer position as a fraction of screen, [0,1] |
| `insert` | the text that arrived (may be a whole word under dictation) |
| `via` | `typed`, `onscreen`, or `dictation` |
| `deleted` | for `correct`: how many characters were removed before `insert` |
| `button` | for `click`: `left`, `right`, `middle` |

## Why it is capture-agnostic

Nothing in the format says where the events came from. A browser, a Mac, a
Windows machine and a synthetic generator produce the same stream, so a model
trained on one recording applies to another. No capture software ships with
this prototype; the requester records with their own tools.
