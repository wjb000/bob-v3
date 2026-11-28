# Bob v3 improvement queue

**North star:** the best mass-market useful home robot — the cheapest reliable humanoid that can do real chores, has a low parts count, looks and feels finished (sleek enough to sit next to Tesla Optimus / Figure / 1X), and can be manufactured at scale. The public site and 3D viewer should match that same standard: clear, polished, and easy to use.

Current state (late 2026): CAD + MuJoCo simulation only. Not yet built. ~$2,600–2,900 BOM. Continuous payload ~0.5 kg. Strong reach and stability limits when the lift is raised.

**Priorities (in order)**
1. Price (target ≤ $1,500–2,000 fully built)
2. Low parts count & simplicity
3. Reliability in real homes
4. Usefulness for actual chores
5. Mass-market potential (ease of use, safety, quiet, self-contained)
6. Sleekness of design (smooth continuous surfaces, hidden fasteners, finished product look)
7. Viewer / site quality (clarity, polish, ease of use)

**Agent rules**

The loop is `agent-loop.sh` → `tools/agent/cycle.py`. It does not take its task from these checkboxes. Each cycle edits the real source for one area: the CAD (`cad/*.py`), the website (`~/Desktop/site-repo/bob-v3/`), the sim, or a factual doc fix. A change is kept only when that area's checks pass. A failed check restores the files.

- One meaningful change per cycle. A paragraph rewrite that does not change the robot, the page, or a wrong number is not a change.
- Design cycles take a measured job: one function whose printed part needs a lot of support. The edit is kept only when that support drops and the part's mass stays close. The status line is already in README.md, ASSEMBLY.md, and the website.
- `cad/*.py` is the source of truth for geometry, actuators, and size. The site and the docs follow it.
- Fix a broken check, a bad fit, or a wrong fact before polishing.
- Keep the CAD export passing. Do not claim the robot has been built or measured.
- Generated files (`BOM.md`, `PRINT.md`, `cad/stl`, `cad/scene.json`) are rewritten by the tools. Edit `docs/bom.py` and the CAD source, not the generated output.

## Phase 0 — Close the reality gap (do these first)
- [x] README.md and ASSEMBLY.md say CAD + simulation only, not yet built. Do not edit them just to repeat this.
- [x] The website's hand-written spec matches the CAD (round 480 mm base, GM-5 arm, 650 mm lift, swivel casters) and says it is not built. Generated BOM and print tables still refresh when the site is published.
- [x] Expand VERIFY.md with a short “First physical prototype checklist” (real servo continuous torque & temperature, real CoM, lift friction, wheel traction on wood/carpet, actual grip force)
- [x] Add a specific servo thermal note to VERIFY.md: measure STS3250/STS3215 case temperature under 40–50 % of rated torque; target ≤ 65 °C. This CAD has no STS3095.
- [x] Document the current safe operating envelope (max continuous 400–500 g, arms-in when lift > 200 mm) in README.md and ASSEMBLY.md
- [x] Add a “hold 500 g for 5 minutes” expected-sag check description to VERIFY.md

## Phase 1 — Price & low parts count
- [ ] Add a “Top cost drivers & reduction opportunities” subsection to BOM.md (5 most expensive lines + cheaper substitutes or “keep for reliability”)
- [ ] Explicitly state the cost goal (≤ $1,500–2,000) and current total in README.md
- [ ] Add a “Minimal viable first build” note: which sensors/cameras can be deferred without breaking basic pick-and-place
- [ ] Start a running “parts count reduction” list and begin consolidating high-count areas (arm covers, base shells, nested tubes, fasteners)
- [ ] Reduce unique fastener / heat-set insert variants where possible
- [ ] Cross-link every major VERIFY.md measurement to the exact parameter(s) it affects in params.py
- [ ] Apply first-principles review to one high-cost or high-part-count subsystem and simplify it

## Phase 2 — Reliability for real home use
- [ ] Add a short “Expected wear items & inspection intervals” section (gripper teeth, TPU fingers, linear bearings, leadscrew nut, ball transfers)
- [ ] Replace or redesign the printed PETG gripper pinion / finger rack with a more durable option (nylon, metal, or simpler non-geared approach)
- [ ] Add a power/thermal budget paragraph and duty-cycle guidance for continuous cleaning tasks
- [ ] Tighten the safety section with limp-arm behavior and the self-locking lift
- [ ] Add concrete failure-mode notes (servo power loss, lift bind, tip-over) with mitigations
- [ ] Improve structural stiffness or joint mounting where sim or analysis shows sag or flex under load

## Phase 3 — Usefulness for real home chores
- [ ] Add a short “Target chore list” to README.md with current sim success rates (floor pick, counter pick, wipe, place-in-bin, self-charge)
- [ ] Document practical reach/payload limits and then improve them where possible (e.g. better shoulder torque path, reach-limit logic, or arm kinematics)
- [ ] Improve gripper design or add simple tool-adapter points for common chores (cloth, sponge, lightweight vacuum head)
- [ ] Strengthen reach-limit enforcement, safer home pose, and clearer failure reporting in the sim checks

## Phase 4 — Sleekness, mass-market feel & manufacturability
- [ ] Redesign arm and body covers for smoother continuous surfaces, fewer seams, and hidden fasteners (move toward Optimus / Figure / 1X aesthetic)
- [ ] Create a short MANUFACTURING.md with DFM notes: injection-mold candidates, wall thicknesses, undercuts, draft, and surface finish goals
- [ ] Consolidate shells and covers to cut part count while keeping the finished look
- [ ] Add a “Production readiness checklist” stub to VERIFY.md (torque specs, tolerance stack-ups, end-of-line tests, noise targets)
- [ ] Identify and mitigate features that hurt mass-market appeal (visible screws, complex assembly, loud components, short battery life under load)

## Phase 5 — Viewer & site UI / UX improvements
- [ ] Improve the overall visual hierarchy and readability of https://www.wyat.dev/bob-v3/ (typography, spacing, section contrast, mobile layout)
- [ ] Make the 3D viewer controls clearer and more discoverable (camera, joints, wiring, X-ray, load, etc.)
- [ ] Tighten the presentation of key specs, cost, status, and limits so a first-time visitor understands the robot in under 30 seconds
- [ ] Improve how simulation results, wiring, and assembly information are displayed (less clutter, better progressive disclosure)
- [ ] Polish the site’s aesthetic so it feels more finished and premium (consistent with the sleek-robot goal)
- [ ] Add or refine small UX details that reduce friction (loading states, clearer labels, better defaults, keyboard shortcuts, etc.)
- [ ] Ensure the “simulation only” status is impossible to miss on the site

## Ongoing (always)
- [ ] Fix all bugs — robot design, CAD, sim checks, viewer, site, docs, wiring, parts, systems. Anything broken, inconsistent, or failing a check gets fixed or clearly flagged.
- [ ] Keep VERIFY.md and the sim check comments in sync whenever a number or design changes
- [ ] After any BOM or cost change, update the total and the stretch-goal sentence
- [ ] Prefer changes that reduce parts count or cost, improve reliability, or make the design (and site) cleaner and more finished-looking
- [ ] Ensure the CAD export and key sim checks still pass after every geometry or parameter change
- [ ] Regularly re-examine major subsystems, parts, systems, and the site with first-principles thinking and simplify wherever the current design is more complex than the fundamental requirement
