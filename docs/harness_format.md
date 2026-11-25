# Harness format (data.json `wiring`)

`docs/harness.py` routes every `docs/wiring.py` wire through the CAD openings, writes `sim/harness.json`, and
`tools/publish.py` merges the routes into `data.json` under `wiring.wires`. There is no separate `harness` key.

Each wire:

| key | meaning |
|---|---|
| `id` | `"<from>-<to>"`, unique |
| `from`, `to` | node keys in `wiring.nodes` (same as the old `a`, `b`) |
| `kind` | key into `wiring.colors` |
| `volts`, `amps`, `peak` | design values from `wiring.elec()` |
| `awg` | wire size as a number (USB cables: 28, the data pair) |
| `len_mm` | wiring.py length; `route_mm` is the 3D route + 8 % |
| `bundle` | optional shared id: `column`, `neck`, `arm_l`, `arm_r` |
| `radius_mm` | optional; for a bundle it is on the first wire of the bundle and covers the whole bundle |
| `path` | list of `{item, pts, loop?}` |

`path` entries: `item` is a moving link name the viewer animates (`base`, `lift`, `head_pan`, `head_tilt`,
`l_link1`..`l_link6`, `r_link1`..`r_link6`) or a CAD item id. `pts` are mm in that item's zero-pose frame, CAD axes
(z up), so the viewer applies the link matrix. Consecutive entries on different links are joined across the joint.
`loop: true` marks a service loop on the child side of a joint. The base→lift crossing has no loop: its slack is the
serpentine inside the cable trough (base entry).

Old keys `a`, `b`, `what`, `gauge`, `conn`, `fuse` stay for older viewers.

## Check

`sim/cables.py` (run by `sim/check.py cables`): at every named pose, the lift at 0, ½ and full travel, and each arm
and head joint at both limits, every densified path point must be at least `radius_mm + 1 mm` from all servo and
shell surfaces (the wire's own two end parts excepted), and every joint/lift crossing must keep 3 mm of slack.
Wire ODs are typical PVC hook-up sizes (12 AWG 3.8 mm … 28 AWG 1.0 mm, USB 4.0 mm); bundle radius assumes 60 % fill.
