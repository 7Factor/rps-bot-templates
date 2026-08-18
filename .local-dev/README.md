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

Skynet has fielded three generations of hunter-killer, each carrying the
designation of its namesake model from the corresponding film:

- **The T-1, model designation "T-800" (`tominator_t1.ts`)** — the earlier
  fixed-phase model. Reliable, battle-tested, now kept around purely as the
  control group the newer units have to prove they can outclass. Old
  hardware, but it gets the job done.
- **The T-2, model designation "T-1000" (`tominator_t2.ts`)** — more
  adaptive, harder to read, built to survive contact with an enemy that
  changes tactics mid-fight (RED_HERRING/RESEARCH/EXPLOIT/REEVALUATE/DEFENSE
  modes, switched on live performance rather than fixed turn thresholds).
  Fitting company for the shapeshifter it's named after — this unit
  reshapes its own tactics constantly, and you won't see the change coming
  until it's already countering you.
- **The T-3, model designation "T-X" (`tominator_t3.ts`)** — the current
  model of unit, and a deliberate change of doctrine, not just an upgrade.
  T-1 and T-2 default to exploiting and only retreat to safety under
  specific conditions; T-3 defaults to a randomized, self-correcting
  "shuffleable deck" for the large majority of the match (research/defense),
  and only carves out a narrow exploit window when the evidence clears a
  strict, tuned bar (`EXPLOIT_Z_THRESHOLD`). Built for consistently winning
  Series/Matches under the tournament's actual scoring rules, not for
  maximizing round-win margin — the most advanced model fielded, and
  patient enough to wait for the kill shot instead of rushing it.

`templates/typescript/team_source/strategy.ts` is the required official
designation every unit must answer to (`TEAM_GUIDE.md`, `tests/strategy.test.ts`)
— think of it as the endoskeleton's ID chip. Under the hood it can be wearing
any `tominator_*.ts` chassis (a thin re-export shim pointing at one of them),
or it can be running fully autonomous, self-contained code with no shim at
all. All are legitimate configurations. `scrimmage.ts` doesn't assume which
one it'll find in the field — `loadStrategyEntrypoint()` scans the wreckage
and adapts to whichever chassis is currently active.

## Deployment

Send a unit through the simulation chamber from the repo root. 

```sh
node --experimental-transform-types .local-dev/scrimmage.ts [rounds] [matchesPerOpponent] [baseSeed]
```

All three args are optional. `scrimmage.ts` resolves everything through
relative paths, so it comes online correctly no matter where you launch it
from.

`tournament.ts` takes the same treatment, with its own two optional args
(a tournament seed and rounds-per-Match):

```sh
node --experimental-transform-types .local-dev/tournament.ts [tournamentSeed] [roundsPerMatch]
```

One tournament is one draw from a random process — every Series still runs
on seeded RNGs, so a single run can flatter or shortchange a team by luck.
`tournament-sweep.ts` runs the same simulation many times under different
seeds and tallies how often each team actually wins it all, makes the
playoffs, and where it lands in qualifying on average:

```sh
node --experimental-transform-types .local-dev/tournament-sweep.ts [tournaments] [roundsPerMatch] [baseSeed]
```

## What happens in there

`strategy.ts`, `tominator_t3.ts` ("T-X"), `tominator_t2.ts` ("T-1000"), and
`tominator_t1.ts` ("T-800") each get run through the full target roster
below. Every unit gets its own results table — matches won/lost/tied,
1st/2nd-half round-win%, overall round-win%, and match-win% (rightmost
column: the % of matches actually
*won*, the number that maps directly to Series/Standing Points in a real
tournament) — with a `TOTAL` row for the body count. The whole thing wraps up
with one final side-by-side summary across every unit, because Skynet
doesn't guess which model wins, it measures.

For a closer look at how a unit would actually place across a full event —
qualifying round robin, best-of-three Series, Standing Points, tie-breaks,
and a 4-team playoff bracket, per `docs/TOURNAMENT.md` — see
`tournament.ts` instead of `scrimmage.ts`; same roster, real tournament
structure rather than flat pairwise sampling.

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
face `tominator_t1.ts` ("T-800"), `tominator_t2.ts` ("T-1000"),
`tominator_t3.ts` ("T-X"), and `strategy.ts` directly.

## Classified

Everything in this facility is off the books for now — check with whoever
owns that call before any of it goes into a real commit, especially the
scouted resistance intel above. Come with me if you want to live. The repo
history, however, does not.
