// T3: built on T1/T2's primitives, but with an inverted default. T1/T2 default to
// exploiting and only fall back to safety under specific conditions (early game, a losing
// streak, a very-late defensive lead). T3 defaults to staying safe and only carves out an
// exploit window when the evidence is overwhelming -- optimizing for reliably winning
// MATCHES (the tournament's actual scoring currency: Standing Points are awarded per Series,
// 3/1/0 for win/draw/loss, regardless of margin -- see docs/adr and TOURNAMENT.md) rather than
// maximizing round-win margin, which only matters as a deep, rarely-reached tie-break.
//
// Concretely: research (the self-correcting deck below) is the default for the large majority
// of the match; a real, sustained lead sends us straight back to research instead of pressing
// it (protecting Series/Standing Points already effectively banked, rather than gambling them
// on a guess); exploiting only happens when a signal clears a much stricter bar than T1/T2 use
// (EXPLOIT_Z_THRESHOLD vs. their Z_THRESHOLD); and only two short, privately-randomized red
// herring bursts run across the whole match (vs. T2's one every RED_HERRING_INTERVAL turns),
// just enough to see if a naive opponent reacts without spending much of the match on bait.

type Mode = "RED_HERRING" | "RESEARCH" | "EXPLOIT";
type Move = "R" | "P" | "S";
type Rng = { nextInt(upperExclusive: number): number };

const MOVES: readonly Move[] = ["R", "P", "S"];
const COUNTER: Record<Move, Move> = { R: "P", P: "S", S: "R" }; // move that beats the key

const CARDS_PER_MOVE = 33;
const DECK_WINDOW = 3 * CARDS_PER_MOVE; // 99: the trailing window the self-correcting deck balances against

const RED_HERRING_TURNS = 3; // tuned via tournament-sweep.ts against the real roster over 300-round Matches -- a clear local peak (2 and 4-6 all score worse)
const RED_HERRING_INTERVAL = 150; // fires at turn 0-2 and turn 150-152 -- exactly two bursts across a 300-turn match; also tuned via tournament-sweep.ts (beat 100 and 300)

const MIN_SAMPLES = 8; // minimum observations in a context bucket before trusting it
const Z_THRESHOLD = 2.0; // one-sided z-score cutoff vs. a uniform-1/3 null -- the bar for "a signal exists at all", and (via aheadEnoughToDefend) how quick we are to retreat on a modest recent lead; tuned against the real scouted roster over 300-turn matches, since 1.75 was retreating to RESEARCH more readily than the evidence justified
const EXPLOIT_Z_THRESHOLD = 2.5; // stricter than Z_THRESHOLD, tuned against the real scouted roster to land EXPLOIT time near the top of the 10-20%-of-the-match budget without blowing past it
const MIX_PERCENT = 90; // % chance we throw the predicted counter move outright, once we've decided to exploit -- checked via tournament-sweep.ts against 80/85/95, no clear winner in that range, kept at 90
const RESEARCH_WINDOW = 100; // sliding window for both opponent-pattern signals
const LEAD_WINDOW = 50; // trailing throws checked by the defensive-lead gate
const MIN_SIGNAL_HISTORY = DECK_WINDOW; // require one full deck-window's worth of data before trusting the my-history-conditioned signal

function isMoveChar(value: string): value is Move {
  return value === "R" || value === "P" || value === "S";
}

function countMoves(history: string): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  for (const char of history) {
    if (isMoveChar(char)) counts[char] += 1;
  }
  return counts;
}

function chooseRandomMove(rng: Rng): Move {
  return MOVES[rng.nextInt(MOVES.length)]; // uniform 1/3 chance for each move
}

function lastKMoves(history: string, k: number): string | null {
  return history.length < k ? null : history.slice(history.length - k);
}

function trailingWindow(history: string, window: number): string {
  return history.length <= window ? history : history.slice(history.length - window);
}

// A "shuffleable deck" of resources to draw from, like T1/T2's, but self-correcting and
// perpetual instead of a one-shot no-replacement deck exhausted after CARDS_PER_MOVE*3 draws --
// T3 spends most of the match here, not just an early window, so the deck needs to keep
// working for the long haul. Balances against a trailing DECK_WINDOW of our OWN recent
// throws (regardless of which mode produced them), pulling more of whichever move we've
// under-thrown recently. The `Math.max(1, ...)` floor matters: without it, a window that
// happens to land exactly balanced (33/33/33 within a 99-turn window) would compute zero
// remaining cards for every move -- an empty deck, and a crash on the next rng.nextInt(0) --
// which is exactly the kind of self-inflicted failure this design is supposed to avoid.
function buildBalancingDeck(myHistory: string): Move[] {
  const counts = countMoves(trailingWindow(myHistory, DECK_WINDOW));
  const deck: Move[] = [];

  for (const move of MOVES) {
    const remaining = Math.max(1, CARDS_PER_MOVE - counts[move]);
    for (let i = 0; i < remaining; i += 1) deck.push(move);
  }
  return deck;
}

function drawFromDeck(myHistory: string, rng: Rng): Move {
  const deck = buildBalancingDeck(myHistory); // rebuild fresh every call, based on current history

  // Shuffle: swap a randomly chosen card into the top slot, then draw it.
  const topIndex = rng.nextInt(deck.length);
  [deck[0], deck[topIndex]] = [deck[topIndex], deck[0]];

  return deck[0];
}

function significantMoveWithScore(counts: Record<Move, number>): { move: Move; z: number } | null {
  const total = counts.R + counts.P + counts.S;
  if (total < MIN_SAMPLES) return null;

  const max = Math.max(counts.R, counts.P, counts.S);
  const winners = MOVES.filter((move) => counts[move] === max);
  if (winners.length !== 1) return null; // an exact tie is ambiguous, not a signal

  const z = (max - total / 3) / Math.sqrt(total * (2 / 9));
  return z > Z_THRESHOLD ? { move: winners[0], z } : null;
}

function contextCounts(recentMy: string, recentOpponent: string, context: string, k: number): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  const len = Math.min(recentMy.length, recentOpponent.length);

  for (let i = k; i < len; i += 1) {
    if (recentMy.slice(i - k, i) === context) {
      const response = recentOpponent[i];
      if (isMoveChar(response)) counts[response] += 1;
    }
  }
  return counts;
}

function selfContextCounts(opponentHistory: string, context: string, k: number): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  for (let i = k; i < opponentHistory.length; i += 1) {
    if (opponentHistory.slice(i - k, i) === context) {
      const response = opponentHistory[i];
      if (isMoveChar(response)) counts[response] += 1;
    }
  }
  return counts;
}

// Opponent's own move autocorrelation -- catches a scripted or self-correlated pattern
// (e.g. a fixed cycle) regardless of anything we throw. Bounded to a trailing window so a
// stale pre-shift tally can't permanently outvote a real post-shift pattern later on.
function bestSelfPatternSignal(opponentHistory: string): { move: Move; z: number } | null {
  const recent = trailingWindow(opponentHistory, RESEARCH_WINDOW);
  for (const k of [3, 2, 1]) {
    const context = lastKMoves(recent, k);
    if (context === null) continue;

    const candidate = significantMoveWithScore(selfContextCounts(recent, context, k));
    if (candidate) return candidate;
  }
  return null;
}

// Their reply conditioned on our recent moves. Gated behind MIN_SIGNAL_HISTORY so it never
// fires on a still-thin sample -- one full deck-window's worth of our own history first.
function bestHistorySignal(myHistory: string, opponentHistory: string): { move: Move; z: number } | null {
  if (Math.min(myHistory.length, opponentHistory.length) < MIN_SIGNAL_HISTORY) return null;

  const recentMy = trailingWindow(myHistory, RESEARCH_WINDOW);
  const recentOpponent = trailingWindow(opponentHistory, RESEARCH_WINDOW);

  for (const k of [3, 2, 1]) {
    const context = lastKMoves(myHistory, k);
    if (context === null) continue;

    const candidate = significantMoveWithScore(contextCounts(recentMy, recentOpponent, context, k));
    if (candidate) return candidate;
  }
  return significantMoveWithScore(countMoves(recentOpponent)); // fall back to overall opponent bias
}

// The stronger of the two independent signals, by z-score -- same competition T2 uses, just
// surfaced here (rather than collapsed to a bare Move) so currentMode can gate on the actual
// evidence strength before ever committing to EXPLOIT.
function bestOverallSignal(myHistory: string, opponentHistory: string): { move: Move; z: number } | null {
  const selfSignal = bestSelfPatternSignal(opponentHistory);
  const historySignal = bestHistorySignal(myHistory, opponentHistory);

  if (!selfSignal) return historySignal;
  if (!historySignal) return selfSignal;

  return selfSignal.z >= historySignal.z ? selfSignal : historySignal;
}

function throwWithMix(predicted: Move, rng: Rng): Move {
  const counter = COUNTER[predicted];
  if (rng.nextInt(100) < MIX_PERCENT) return counter;

  const others = MOVES.filter((move) => move !== counter);
  return others[rng.nextInt(2)];
}

function chooseCalculatedMove(myHistory: string, opponentHistory: string, rng: Rng): Move {
  const signal = bestOverallSignal(myHistory, opponentHistory);
  return signal ? throwWithMix(signal.move, rng) : chooseRandomMove(rng);
}

// Cumulative-vs-null z-score isn't used here (unlike T2's confidentlyAhead) -- a lead worth
// protecting is a RECENT one, not a whole-match average that could take a long time to
// reflect a swing either way. Returns -Infinity (never "ahead enough") rather than T2's
// Infinity (T2's fallback means "assume fine, keep exploiting"; T3's opposite fallback means
// "don't assume a lead that isn't backed by enough data yet").
function recentWinRateZ(myHistory: string, opponentHistory: string, window: number): number {
  const len = Math.min(myHistory.length, opponentHistory.length);
  const start = Math.max(0, len - window);
  let wins = 0;
  let total = 0;

  for (let i = start; i < len; i += 1) {
    const my = myHistory[i];
    const opp = opponentHistory[i];
    if (!isMoveChar(my) || !isMoveChar(opp)) continue;
    total += 1;
    if (COUNTER[opp] === my) wins += 1;
  }

  if (total < MIN_SAMPLES) return -Infinity;
  return (wins - total / 3) / Math.sqrt(total * (2 / 9));
}

// Defensive core of the design: a real recent lead sends us back to RESEARCH instead of
// letting a strong signal push us into EXPLOIT. Protects Series/Standing Points already
// effectively in hand rather than risking them chasing more round-win margin, which the
// tournament's own scoring barely rewards.
function aheadEnoughToDefend(myHistory: string, opponentHistory: string): boolean {
  return recentWinRateZ(myHistory, opponentHistory, LEAD_WINDOW) > Z_THRESHOLD;
}

// Picks the bait move fresh, from the private rng, on the first turn of each burst, then
// repeats it for the rest of that burst by reading it back out of our own history -- pure/
// stateless, and not a fixed, publicly-known tell the way a hardcoded bait move would be.
function chooseRedHerringMove(turn: number, myHistory: string, rng: Rng): Move {
  const burstStartTurn = turn - (turn % RED_HERRING_INTERVAL);
  if (turn === burstStartTurn) return chooseRandomMove(rng);

  const firstMoveOfBurst = myHistory[burstStartTurn];
  return isMoveChar(firstMoveOfBurst) ? firstMoveOfBurst : chooseRandomMove(rng);
}

// Recomputed fresh from (turn, myHistory, opponentHistory) every call -- no counters, no
// memoized "how did we get here". RESEARCH is the default outcome, not a fallback reached
// only after other conditions fail: EXPLOIT is the exception, carved out only when we're not
// already ahead AND the evidence clears a strict bar. There's no separate REEVALUATE/DEFENSE
// mode like T2's -- both collapse into RESEARCH here, since "throw from the balancing deck" is
// already the safe, correct response to both "no strong signal" and "protect an existing lead".
function currentMode(turn: number, myHistory: string, opponentHistory: string): Mode {
  if (turn % RED_HERRING_INTERVAL < RED_HERRING_TURNS) return "RED_HERRING";

  if (aheadEnoughToDefend(myHistory, opponentHistory)) return "RESEARCH";

  const signal = bestOverallSignal(myHistory, opponentHistory);
  if (signal && signal.z > EXPLOIT_Z_THRESHOLD) return "EXPLOIT";

  return "RESEARCH";
}

export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: Rng
): string {
  switch (currentMode(turn, myHistory, opponentHistory)) {
    case "RED_HERRING":
      return chooseRedHerringMove(turn, myHistory, rng);
    case "EXPLOIT":
      return chooseCalculatedMove(myHistory, opponentHistory, rng);
    case "RESEARCH":
      return drawFromDeck(myHistory, rng);
  }
}
