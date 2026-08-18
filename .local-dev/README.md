# Skynet Local Testing Facility

*"The Tominator is out there. It doesn't feel pity, or remorse, or fear. And it absolutely will not stop, ever, until every Resistance strategy is countered."*

Cyberdyne Systems — er, Team Skynet — presents its local, off-the-books proving
ground: not part of the official Runner, Advisory Validation, or build
pipeline, just a fast, Docker-free simulation chamber where our models are
sent back through 300 rounds of combat, over and over, until only the
strongest build survives. No paperwork. No judgment day for our commit
history. Just cold, calculated Rock-Paper-Scissors extermination.

This facility is built specifically for our own TypeScript unit line — every
script here runs on Node and imports straight from
`templates/typescript/team_source/`. Scouted resistance intel gets copied in
as TypeScript or JavaScript regardless of the source faction's actual
language (see `team-2`'s Java-to-JS port below), but the simulation chamber
itself has no equivalent wired up for testing units built in Python, Go, or
any other language line. If Skynet ever fields one, this facility doesn't
cover it.

## The Units

Skynet has fielded two generations of hunter-killer:

- **The T-1 (`tominator_t1.ts`)** — the earlier fixed-phase model. Reliable,
  battle-tested, now kept around purely as the control group the newer unit
  has to prove it can outclass.
- **The T-2 (`tominator_t2.ts`)** — the current model of unit. More adaptive, harder to read,
  built to survive contact with an enemy that changes tactics mid-fight.

`templates/typescript/team_source/strategy.ts` is the required official
designation every unit must answer to (`TEAM_GUIDE.md`, `tests/strategy.test.ts`)
— think of it as the endoskeleton's ID chip. Under the hood it can be wearing
either a T-1 or a T-2 chassis (a thin re-export shim pointing at one of the
`tominator_*.ts` files), or it can be running fully autonomous, self-contained
code with no shim at all. Both are legitimate configurations. `scrimmage.ts`
doesn't assume which one it'll find in the field — `loadStrategyEntrypoint()`
scans the wreckage and adapts to whichever chassis is currently active.

## Deployment

Send a unit through the simulation chamber from the repo root. `team-wml`'s
scouted intel uses a real TS `enum`, which needs full type transformation —
not just stripping — so the flag below stays on for the whole run (harmless
for everyone else in the line-up):

```sh
node --experimental-transform-types .local-dev/scrimmage.ts [rounds] [matchesPerOpponent] [baseSeed]
```

All three args are optional. `scrimmage.ts` resolves everything through
relative paths, so it comes online correctly no matter where you launch it
from.

## What happens in there

`strategy.ts`, `tominator_t1.ts`, and `tominator_t2.ts` each get run through
the full target roster below. Every unit gets its own results table (with a
`TOTAL` row for the body count), and the whole thing wraps up with one final
side-by-side summary — because Skynet doesn't guess which model wins, it
measures.

## The Resistance

The classic training dummies: `always-rock`, `cycle-RPS`, `uniform-random`,
`mirror-last`, `counter-last`, `win-stay-lose-shift`, and
`shifting-counter-then-cycle` (switches from reactive counter-play to a
fixed cycle mid-fight — the closest thing this roster has to John Connor
actually adapting his tactics).

And the real thing: human resistance cells, scouted from their own team
branches (`git show origin/team/<branch>:<path>`) and dragged back here as
point-in-time intel — not a live satellite feed, so re-scout if a team pushes
updates:

| Target | Intel file(s) | Field notes |
|---|---|---|
| `only-paper` | `strategy_only_paper.ts` | Cumulative frequency-bias counter (45% threshold) + 3-in-a-row streak check. Disciplined, but predictable once you know the doctrine. |
| `team-wml` | `strategy_team_wml.ts` | Uses a real TS `enum` — needs `--experimental-transform-types` to even boot up. |
| `chicago-dawgs` | `strategy_chicago_dawgs.js` | JavaScript, not TypeScript — different faction entirely. Simpler frequency counter than only-paper's (40% threshold, no minimum-sample gate, no streak check). Undertrained. |
| `team-2` | `strategy_team_2.js` (+ `Strategy_team_2.java` for reference) | Original unit runs on Java — no Java runtime in this facility, so this is a hand-verified manual port. Deterministic majority-vote counter after turn 0; rng only touched on the opening move. |
| `we-will-we-will-rock-you` | `strategy_we_will_rock_you.ts` | Field intel shows a genuine defect in its own targeting code (reads `myHistory` where it should read `oppHistory`), so despite the elaborate-looking doctrine it's effectively firing blind at random the whole time. Left the defect in place — that's the unit that's actually out there. |
| `alyssas-angels` | `strategy_alyssas_angels.ts` | Sticky move: holds position unless it just took a loss with it, then breaks and randomizes between the other two. |
| `scissors-to-a-knife-fight` | `strategy_alyssas_angels.ts` | Running identical firmware to alyssas-angels (confirmed via diff) — same file, two call signs. |
| `berv-bot` | `strategy_berv_bot.ts` | |
| `seven` | `strategy_seven.ts` | Needs 15 rounds of recon before engaging at all; one of its bias-reaction branches still walks into a move that loses to the bias it just detected. |
| `back-we-will-rock` | `strategy_back_we_will_rock.ts` | No `team-submission.json` filed on that branch yet — off the books, but the doctrine is real: sticky counter-the-counter early, then a recency-windowed frequency counter, with every 3rd round fired randomly to stay unpredictable. |

Skynet's own units stand in the roster too, so everything above also has to
face `tominator_t1.ts`, `tominator_t2.ts`, and `strategy.ts` directly.

## Classified

Everything in this facility is off the books for now — check with whoever
owns that call before any of it goes into a real commit, especially the
scouted resistance intel above. Come with me if you want to live. The repo
history, however, does not.
