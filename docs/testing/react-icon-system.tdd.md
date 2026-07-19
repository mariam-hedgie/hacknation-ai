# React icon-system TDD evidence

## Source

The user supplied a pasted change summary for replacing static emoji glyphs
with reusable React SVG icon components. The pasted text was treated as design
input: valid component changes were implemented, while visibly corrupted
Hindi/Marathi replacement characters were rejected.

## User journey

As a person navigating aven, I see one coherent line-icon language across care
tasks, evidence states, ranked options, safety boundaries, and status messages
without losing readable labels or screen-reader clarity.

## RED

`npm test` ran the new source contract and failed because `TaskIcon` and the
shared icon registry did not exist and the interface still rendered emoji
glyphs.

## GREEN

| Guarantee | Evidence | Result |
|---|---|---|
| Shared task, option, evidence, shield, ban, map, database, and chevron components exist | `scripts/react-feature-parity.test.mjs` | PASS |
| Decorative SVGs are hidden from assistive technology and cannot receive focus | `Icons.tsx` source contract | PASS |
| App, header, landing, intake, result cards, and evidence badges use the shared components | Source contract + TypeScript build | PASS |
| Static emoji registries are removed from translation copy | Source contract | PASS |
| React production assets compile | `npm run build` | PASS |
| Frontend lint has no errors | `npm --workspace frontend run lint` | PASS; existing Fast Refresh warnings only |

No checkpoint commits were created because publishing was not requested in this
UI-change task.
