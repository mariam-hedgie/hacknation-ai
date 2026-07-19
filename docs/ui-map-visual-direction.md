# Aven map-first visual direction

## Outcome

The results experience should feel polished, calm, and intentional: Apple-like
clarity, Claude-like warmth, and NeetCode-like information hierarchy. It must
not look like a generic AI dashboard. The map is a decision surface, not
decoration and not the first screen before Aven understands the care need.

## Signature demo view

After the user confirms the request, transition into a responsive map-and-plan
workspace:

- Desktop: interactive map on roughly 60% of the viewport and a 40% route rail.
- Mobile: full-width map with a draggable results sheet; the selected facility
  summary remains readable without manipulating the map.
- Selecting a route card highlights exactly one pin and route. Selecting a pin
  scrolls its matching card into view.
- Use a muted/desaturated basemap so Aven's evidence states, selected route, and
  facility markers remain legible.
- The first route card still starts with `What to do next`; the map must never
  hide evidence, unknowns, or the call-before-travel action.

The memorable demo transition is:

`confirmed request -> India map settles on the origin -> three honest options
appear -> one route draws -> evidence receipt opens without leaving the map`

## Visual system

Use a warm, editorial foundation with one strong geographic accent:

| Role | Colour | Use |
|---|---|---|
| Porcelain | `#F7F5EF` | Main background |
| Ink | `#171A21` | Primary text and selected outlines |
| Cobalt | `#315CFF` | Primary action, selected route, active pin |
| Signal coral | `#FF5A4E` | Sparse brand moments and urgent action only |
| Deep teal | `#087A74` | Documented-evidence status |
| Amber | `#A65F00` | Conflict / call-first state |
| Slate | `#667085` | Unknown or secondary information |

Do not use rainbow gradients, glassmorphism on every card, neon glows, or
multiple competing accent colours. Reserve cobalt for the current decision and
coral for moments that truly need attention. Colour is always paired with an
icon and text label.

## Interaction and motion

- Use 180-240 ms ease-out transitions for card selection, sheet expansion, and
  route drawing. No looping motion.
- Preserve spatial continuity: a selected card should not jump to a different
  part of the page when details expand.
- Keep navigation quiet and predictable; supporting chrome should recede once
  the user reaches the plan.
- Respect reduced-motion preferences and keep every action keyboard reachable.
- Minimum touch target: 44 by 44 CSS pixels.

## Map content hierarchy

1. User origin, clearly labelled.
2. Selected facility and route.
3. Two alternative facilities.
4. Optional travel mode comparison.
5. Everything else stays visually subdued.

Never imply live traffic, live availability, a live fare, or a medically
superior facility unless a source actually supports that claim. Cluster pins
when they overlap, and always provide the same information as cards/text for
screen-reader and low-connectivity use.

## Components that make it feel built, not generated

- One consistent 8 px spacing system and a restrained radius scale (10/16 px).
- A single type family with a compact display weight and highly readable body.
- Exact icon set throughout; no emoji as product icons.
- Skeleton states that preserve the final layout instead of spinners that move
  the page.
- Purposeful empty/error/offline states with the next available action.
- Map attribution, a visible text alternative, and a small `Map unavailable`
  fallback that leaves the care plan usable.

## Build order

1. Results split view plus selected-card/pin synchronization.
2. Text fallback and honest offline/no-route states.
3. Origin-to-facility route for providers already supported by `src/maps.py`.
4. Mobile bottom sheet and responsive polish.
5. Motion, reduced-motion behavior, loading skeletons, and final visual QA.

Do not block the trusted-care golden path on map credentials. When a provider
is unavailable, show static coordinates or a simple geographic overview only
if they are real; otherwise show the text comparison and say the map is not
connected.

## Inspiration translated into Aven rules

- [Apple map guidance](https://developer.apple.com/design/human-interface-guidelines/maps): familiar interaction, a muted map under information-rich overlays, clear selection, and clustered overlapping points.
- [Apple interface fundamentals](https://developer.apple.com/design/tips/): readable contrast, alignment, proximity, and 44-point touch targets.
- [Linear's calmer-interface principles](https://linear.app/now/behind-the-latest-design-refresh): navigation recedes and the user's current task earns the visual weight.
- [GOV.UK accessible map guidance](https://brand.design-system.service.gov.uk/data/maps/): every important map fact also needs a written/table alternative; colour alone is never meaning.

