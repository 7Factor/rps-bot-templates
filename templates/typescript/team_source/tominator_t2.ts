type Mode = "RED_HERRING" | "RESEARCH" | "EXPLOIT" | "REEVALUATE" | "DEFENSE";
type Move = "R" | "P" | "S";
type TurnOutcome = "win" | "loss" | "tie";
type Rng = { nextInt(upperExclusive: number): number };

const MOVES: readonly Move[] = ["R", "P", "S"];
const COUNTER: Record<Move, Move> = { R: "P", P: "S", S: "R" }; // move that beats the key

const CARDS_PER_MOVE = 33;
const EARLY_GAME_TURNS = 3 * CARDS_PER_MOVE; // turns 0-98 draw from the deck; the only window where our own moves are guaranteed decorrelated from the opponent

const RED_HERRING_TURNS = 3; // repeat one fixed move this long before real exploration starts, to bait naive opponent detectors into locking on early
const RED_HERRING_INTERVAL = 100; // repeat the bait at the top of every block this long, not just once at match start

const MIN_SAMPLES = 8; // minimum observations in a context bucket before trusting it
const Z_THRESHOLD = 1.75; // one-sided z-score cutoff vs. a uniform-1/3 null
const MIX_PERCENT = 85; // % chance we throw the predicted counter move outright
const PERFORMANCE_WINDOW = 50; // trailing throws checked by the exploit-confidence gate
const RESEARCH_WINDOW = 100; // trailing throws required before a losing streak triggers a reset; also the self-pattern signal's recency horizon
const DEFENSIVE_ELIGIBLE_TURN = 250; // DEFENSE only considered in the final 50 of 300 turns -- not enough match left there for a RESEARCH reset to pay off
const DEFENSIVE_Z_THRESHOLD = 2; // stricter than Z_THRESHOLD: coasting on a lead for the rest of the match needs stronger evidence than a routine mode switch

function isMoveChar(value: string): value is Move {
  return value === "R" || value === "P" || value === "S";
}

function countMoves(history: string): Record<Move, number> {
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 }; // start every move at zero

  for (const char of history) {
    if (isMoveChar(char)) counts[char] += 1; // only tally real move characters
  }
  return counts;
}

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

function chooseRandomMove(rng: Rng): Move {
  return MOVES[rng.nextInt(MOVES.length)]; // uniform 1/3 chance for each move
}

function lastKMoves(history: string, k: number): string | null {
  return history.length < k ? null : history.slice(history.length - k); // guard avoids a negative slice
}

function trailingWindow(history: string, window: number): string {
  return history.length <= window ? history : history.slice(history.length - window);
}

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

function bestSelfPatternSignal(opponentHistory: string): { move: Move; z: number } | null {
  const recent = trailingWindow(opponentHistory, RESEARCH_WINDOW);
  for (const k of [3, 2, 1]) {
    const context = lastKMoves(recent, k); // their actual current last-k moves
    if (context === null) continue; // not enough live history yet for this order

    const candidate = significantMoveWithScore(selfContextCounts(recent, context, k));
    if (candidate) return candidate; // most specific match with enough evidence wins
  }
  return null;
}

function bestHistorySignal(myHistory: string, opponentHistory: string): { move: Move; z: number } | null {
  if (Math.min(myHistory.length, opponentHistory.length) < EARLY_GAME_TURNS) return null;

  const recentMy = trailingWindow(myHistory.slice(RED_HERRING_TURNS), RESEARCH_WINDOW);
  const recentOpponent = trailingWindow(opponentHistory.slice(RED_HERRING_TURNS), RESEARCH_WINDOW);

  for (const k of [3, 2, 1]) {
    const context = lastKMoves(myHistory, k); // our actual current last-k moves
    if (context === null) continue; // not enough live history yet for this order

    const candidate = significantMoveWithScore(contextCounts(recentMy, recentOpponent, context, k));
    if (candidate) return candidate; // most specific match with enough evidence wins
  }
  return significantMoveWithScore(countMoves(recentOpponent)); // fall back to overall opponent bias
}

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

function recentWinRateZ(myHistory: string, opponentHistory: string, window: number): number {
  const len = Math.min(myHistory.length, opponentHistory.length);
  const start = Math.max(EARLY_GAME_TURNS, len - window); // last `window` turns, never before turn 99
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
  return recentWinRateZ(myHistory, opponentHistory, PERFORMANCE_WINDOW) > Z_THRESHOLD; // recent wins still well above chance
}

function sustainedlyLosing(myHistory: string, opponentHistory: string): boolean {
  return recentWinRateZ(myHistory, opponentHistory, RESEARCH_WINDOW) < -Z_THRESHOLD;
}

function confidentlyAhead(myHistory: string, opponentHistory: string): boolean {
  return recentWinRateZ(myHistory, opponentHistory, Infinity) > DEFENSIVE_Z_THRESHOLD;
}

function outcomeForOpponent(myMove: Move, oppMove: Move): TurnOutcome {
  if (myMove === oppMove) return "tie";
  return COUNTER[myMove] === oppMove ? "win" : "loss"; // opponent's move beats mine -> opponent won
}

function contextCountsByOutcome(myHistory: string, opponentHistory: string, outcome: TurnOutcome): Record<Move, number> {
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

// Picks the bait move fresh, from the private rng, on the first turn of each burst,
// then repeats it for the rest of that burst by reading it back out of our own history
// -- stays pure/stateless (no memoized "what did we pick last call") while no longer
// being a fixed, publicly-known tell: an opponent who's read this file still knows
// WHEN a burst happens and THAT it repeats, but not WHICH move it'll be, since that's
// drawn from our private per-match seed rather than hardcoded.
function chooseRedHerringMove(turn: number, myHistory: string, rng: Rng): Move {
  const burstStartTurn = turn - (turn % RED_HERRING_INTERVAL);
  if (turn === burstStartTurn) return chooseRandomMove(rng); // first turn of this burst: draw fresh

  const firstMoveOfBurst = myHistory[burstStartTurn]; // already recorded -- repeat it
  return isMoveChar(firstMoveOfBurst) ? firstMoveOfBurst : chooseRandomMove(rng);
}

function chooseResearchMove(turn: number, myHistory: string, rng: Rng): Move {
  return turn < EARLY_GAME_TURNS ? drawFromDeck(myHistory, rng) : chooseRandomMove(rng);
}

function chooseReevaluateMove(myHistory: string, opponentHistory: string, rng: Rng): Move {
  const predicted = predictOpponentMoveWSLS(myHistory, opponentHistory) ?? predictOpponentMove(myHistory, opponentHistory);

  return predicted ? throwWithMix(predicted, rng) : chooseRandomMove(rng);
}

function currentMode(turn: number, myHistory: string, opponentHistory: string): Mode {
  if (turn % RED_HERRING_INTERVAL < RED_HERRING_TURNS) return "RED_HERRING";

  if (turn < EARLY_GAME_TURNS) {
    return bestSelfPatternSignal(opponentHistory) ? "EXPLOIT" : "RESEARCH";
  }

  if (stillPerformingWell(myHistory, opponentHistory)) return "EXPLOIT";

  if (sustainedlyLosing(myHistory, opponentHistory)) {
    if (turn >= DEFENSIVE_ELIGIBLE_TURN && confidentlyAhead(myHistory, opponentHistory)) {
      return "DEFENSE";
    }

    return "RESEARCH";
  }

  return "REEVALUATE";
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
    case "RESEARCH":
      return chooseResearchMove(turn, myHistory, rng);
    case "EXPLOIT":
      return chooseCalculatedMove(myHistory, opponentHistory, rng);
    case "REEVALUATE":
      return chooseReevaluateMove(myHistory, opponentHistory, rng);
    case "DEFENSE":
      return chooseRandomMove(rng);
  }
}
