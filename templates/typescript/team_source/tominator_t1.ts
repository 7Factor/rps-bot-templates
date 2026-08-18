type Move = "R" | "P" | "S";
type Rng = { nextInt(upperExclusive: number): number };

const MOVES: readonly Move[] = ["R", "P", "S"];

const TOTAL_TURNS = 300; // whole Match
const EARLY_GAME_TURNS = 99; // turns 0-98 draw from the deck
const LATE_GAME_TURNS = 100; // last 100 turns are "late game"
const LATE_GAME_START = TOTAL_TURNS - LATE_GAME_TURNS; // 200
const CARDS_PER_MOVE = 33; // 33 * 3 = EARLY_GAME_TURNS

const MIN_SAMPLES = 8; // minimum observations in a context bucket before trusting it
const Z_THRESHOLD = 1.75; // one-sided z-score cutoff vs. a uniform-1/3 null
const MIX_PERCENT = 85; // % chance we throw the predicted counter move outright
const PERFORMANCE_WINDOW = 50; // trailing throws checked by the late-game performance gate
const COUNTER: Record<Move, Move> = { R: "P", P: "S", S: "R" }; // move that beats the key

// Type guard: narrows a plain string character to the Move union.
function isMoveChar(value: string): value is Move {
  return value === "R" || value === "P" || value === "S";
}

// Counts how many times each move appears anywhere in a history string.
function countMoves(history: string): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 }; // start every move at zero
  for (const char of history) {
    if (isMoveChar(char)) counts[char] += 1; // only tally real move characters
  }
  return counts;
}

// Derives which cards remain in the 33/33/33 no-replacement deck from
// myHistory itself (its length always equals the current turn), so the deck
// never needs to be cached across calls.
function buildRemainingDeck(myHistory: string): Move[] {
  const counts = countMoves(myHistory); // how many of each move we've already thrown
  const deck: Move[] = [];
  for (const move of MOVES) {
    const remaining = CARDS_PER_MOVE - counts[move]; // cards left = starting 33 minus what we've used
    for (let i = 0; i < remaining; i += 1) deck.push(move); // one entry per remaining copy
  }
  return deck;
}

function drawFromDeck(myHistory: string, rng: Rng): Move {
  const deck = buildRemainingDeck(myHistory); // rebuild the remaining deck fresh every call
  // Shuffle: swap a randomly chosen card into the top slot, then draw it.
  const topIndex = rng.nextInt(deck.length); // pick a random position in the deck
  [deck[0], deck[topIndex]] = [deck[topIndex], deck[0]]; // move that card to the front
  return deck[0]; // draw the top card
}

// Fallback when no opponent pattern is reliable enough to exploit.
function chooseRandomMove(rng: Rng): Move {
  return MOVES[rng.nextInt(MOVES.length)]; // uniform 1/3 chance for each move
}

// Last k of the bot's actual current moves, or null if not enough history yet.
function lastKMoves(history: string, k: number): string | null {
  return history.length < k ? null : history.slice(history.length - k); // guard avoids a negative slice
}

// One-proportion z-test vs. uniform 1/3, returning both the winning move and its
// z-score so competing signals can be ranked by evidence strength; too few
// samples or a tie both count as no signal.
function significantMoveWithScore(counts: Record<Move, number>): { move: Move; z: number } | null {
  const total = counts.R + counts.P + counts.S; // total observations behind this count
  if (total < MIN_SAMPLES) return null; // not enough data to trust any conclusion
  const max = Math.max(counts.R, counts.P, counts.S); // the most-thrown move's count
  const winners = MOVES.filter((move) => counts[move] === max); // every move tied for that max
  if (winners.length !== 1) return null; // an exact tie is ambiguous, not a signal
  // how many standard deviations `max` sits above the count pure chance would give us (total/3)
  const z = (max - total / 3) / Math.sqrt(total * (2 / 9));
  return z > Z_THRESHOLD ? { move: winners[0], z } : null; // only trust it once it clears the significance bar
}

function significantMove(counts: Record<Move, number>): Move | null {
  return significantMoveWithScore(counts)?.move ?? null;
}

// Tallies the opponent's early-game reply every time our own last-k moves matched context.
function contextCounts(earlyMy: string, earlyOpponent: string, context: string, k: number): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  const len = Math.min(earlyMy.length, earlyOpponent.length); // stay in bounds of both strings
  for (let i = k; i < len; i += 1) {
    // does our own k-move sequence ending right before turn i match the context we're testing?
    if (earlyMy.slice(i - k, i) === context) {
      const response = earlyOpponent[i]; // what the opponent threw right after that sequence
      if (isMoveChar(response)) counts[response] += 1;
    }
  }
  return counts;
}

// Tallies what the opponent played next, every time their own last-k moves
// (earlier in the match) matched context. A pure self-pattern signal: it
// never looks at what we threw, so a scripted or turn-driven sequence (e.g. a
// fixed R -> P -> S cycle) shows up even though it has nothing to do with us.
function selfContextCounts(opponentHistory: string, context: string, k: number): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  for (let i = k; i < opponentHistory.length; i += 1) {
    if (opponentHistory.slice(i - k, i) === context) {
      const response = opponentHistory[i]; // what the opponent played right after that same sequence
      if (isMoveChar(response)) counts[response] += 1;
    }
  }
  return counts;
}

// n-gram backoff over the opponent's own move sequence: order-3 -> order-2 -> order-1.
// Uses the whole running history (not just the early-game window) since this
// signal needs no correlation with our moves and can be trusted as soon as it
// clears the significance bar, including mid-exploration.
function bestSelfPatternSignal(opponentHistory: string): { move: Move; z: number } | null {
  for (const k of [3, 2, 1]) {
    const context = lastKMoves(opponentHistory, k); // their actual current last-k moves
    if (context === null) continue; // not enough live history yet for this order
    const candidate = significantMoveWithScore(selfContextCounts(opponentHistory, context, k));
    if (candidate) return candidate; // most specific match with enough evidence wins
  }
  return null;
}

function predictOpponentSelfPattern(opponentHistory: string): Move | null {
  return bestSelfPatternSignal(opponentHistory)?.move ?? null;
}

// n-gram backoff over the early-game training window: order-3 -> order-2 -> order-1 -> marginal.
function bestHistorySignal(myHistory: string, opponentHistory: string): { move: Move; z: number } | null {
  const earlyMy = myHistory.slice(0, EARLY_GAME_TURNS); // training data: only the early-game window
  const earlyOpponent = opponentHistory.slice(0, EARLY_GAME_TURNS);
  for (const k of [3, 2, 1]) {
    const context = lastKMoves(myHistory, k); // our actual current last-k moves
    if (context === null) continue; // not enough live history yet for this order
    const candidate = significantMoveWithScore(contextCounts(earlyMy, earlyOpponent, context, k));
    if (candidate) return candidate; // most specific match with enough evidence wins
  }
  return significantMoveWithScore(countMoves(earlyOpponent)); // fall back to overall opponent bias
}

// The stronger of two independent signals wins: a pattern in the opponent's own
// sequence (self signal) vs. their reply conditioned on our recent moves
// (history signal). Both scores come from the same one-proportion z-test, so
// comparing them directly ranks evidence strength instead of favoring one
// signal type by fixed priority.
function predictOpponentMove(myHistory: string, opponentHistory: string): Move | null {
  const selfSignal = bestSelfPatternSignal(opponentHistory);
  const historySignal = bestHistorySignal(myHistory, opponentHistory);
  if (!selfSignal) return historySignal?.move ?? null;
  if (!historySignal) return selfSignal.move;
  return (selfSignal.z >= historySignal.z ? selfSignal : historySignal).move;
}

function throwWithMix(predicted: Move, rng: Rng): Move {
  const counter = COUNTER[predicted]; // the move that beats our prediction
  if (rng.nextInt(100) < MIX_PERCENT) return counter; // usually commit to the predicted counter

  const others = MOVES.filter((move) => move !== counter); // the other two moves
  return others[rng.nextInt(2)]; // split the remaining chance evenly between the other two
}

function chooseCalculatedMove(myHistory: string, opponentHistory: string, rng: Rng): Move {
  const predicted = predictOpponentMove(myHistory, opponentHistory);
  return predicted ? throwWithMix(predicted, rng) : chooseRandomMove(rng); // no signal -> stay unpredictable
}

// z-score of our recent win rate vs. a uniform-1/3 null, over the trailing window
// (floored at EARLY_GAME_TURNS so early-game exploration never counts). Infinity
// when there's not enough recent data yet, so we default to "still fine."
function recentWinRateZ(myHistory: string, opponentHistory: string): number {
  const len = Math.min(myHistory.length, opponentHistory.length);
  const start = Math.max(EARLY_GAME_TURNS, len - PERFORMANCE_WINDOW); // last PERFORMANCE_WINDOW turns, never before turn 99
  let wins = 0;
  let total = 0;
  for (let i = start; i < len; i += 1) {
    const my = myHistory[i];
    const opp = opponentHistory[i];
    if (!isMoveChar(my) || !isMoveChar(opp)) continue;
    total += 1;
    if (COUNTER[opp] === my) wins += 1; // my move beats opponent's move
  }
  if (total < MIN_SAMPLES) return Infinity; // not enough recent data to judge - assume it's fine
  return (wins - total / 3) / Math.sqrt(total * (2 / 9)); // same z-test shape as significantMove
}

function stillPerformingWell(myHistory: string, opponentHistory: string): boolean {
  return recentWinRateZ(myHistory, opponentHistory) > Z_THRESHOLD; // recent wins still well above chance
}

// Was the given round a win, loss, or tie from the OPPONENT's point of view?
function outcomeForOpponent(myMove: Move, oppMove: Move): "win" | "loss" | "tie" {
  if (myMove === oppMove) return "tie";
  return COUNTER[myMove] === oppMove ? "win" : "loss"; // opponent's move beats mine -> opponent won
}

// Tallies the opponent's reply, over the WHOLE match so far, every time the
// PREVIOUS round's outcome (for the opponent) matched `outcome`.
function contextCountsByOutcome(myHistory: string, opponentHistory: string, outcome: "win" | "loss" | "tie"): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  const len = Math.min(myHistory.length, opponentHistory.length);
  for (let i = 1; i < len; i += 1) {
    const prevMy = myHistory[i - 1]; // our move the round before
    const prevOpp = opponentHistory[i - 1]; // opponent's move the round before
    const response = opponentHistory[i]; // what the opponent did next
    if (!isMoveChar(prevMy) || !isMoveChar(prevOpp) || !isMoveChar(response)) continue;
    if (outcomeForOpponent(prevMy, prevOpp) === outcome) counts[response] += 1; // only matching-outcome rounds count
  }
  return counts;
}

function predictOpponentMoveWSLS(myHistory: string, opponentHistory: string): Move | null {
  const len = Math.min(myHistory.length, opponentHistory.length);
  if (len < 1) return null; // need at least one completed round to know the last outcome
  const prevMy = myHistory[len - 1]; // our most recent move
  const prevOpp = opponentHistory[len - 1]; // opponent's most recent move
  if (!isMoveChar(prevMy) || !isMoveChar(prevOpp)) return null;
  // look up how the opponent has historically responded after this exact outcome
  return significantMove(contextCountsByOutcome(myHistory, opponentHistory, outcomeForOpponent(prevMy, prevOpp)));
}

function chooseLateGameMove(myHistory: string, opponentHistory: string, rng: Rng): Move {
  if (stillPerformingWell(myHistory, opponentHistory)) {
    return chooseCalculatedMove(myHistory, opponentHistory, rng); // keep coasting
  }

  // re-evaluate: try the win-stay/lose-shift signal first, then fall back to the move-sequence chain
  const predicted = predictOpponentMoveWSLS(myHistory, opponentHistory) ?? predictOpponentMove(myHistory, opponentHistory);
  return predicted ? throwWithMix(predicted, rng) : chooseRandomMove(rng);
}

export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: Rng
): string {
  if (turn < EARLY_GAME_TURNS) {
    const selfPattern = predictOpponentSelfPattern(opponentHistory);
    if (selfPattern) return throwWithMix(selfPattern, rng); // an obvious opponent pattern is worth exploiting even mid-exploration
    return drawFromDeck(myHistory, rng); // otherwise keep exploring via the no-replacement deck
  }

  if (turn < LATE_GAME_START) {
    return chooseCalculatedMove(myHistory, opponentHistory, rng); // mid game: exploit early-game patterns
  }

  return chooseLateGameMove(myHistory, opponentHistory, rng); // late game: keep coasting or re-evaluate
}
