type Move = "R" | "P" | "S";
type Rng = { nextInt(upperExclusive: number): number };

const MOVES: readonly Move[] = ["R", "P", "S"];

// Move that defeats the given move (R beats S, P beats R, S beats P).
const COUNTER: Record<Move, Move> = { R: "P", P: "S", S: "R" };

const HISTORY_MODE_START_TURN = 50;
const FREQUENCY_WINDOW = 100;
const COUNTER_STREAK_LENGTH = 5;

// Bias detection during the default random-mode window.
const RANDOMNESS_CHECK_WINDOW = 51;
const MIN_SAMPLES_FOR_BIAS_CHECK = 10;
const BIAS_THRESHOLD = 0.37;

enum Mode {
  Random,
  CounterMostFrequent,
}

// True if any single move already exceeds BIAS_THRESHOLD of the opponent's
// throws so far this game, which is unlikely under a fair 1/3-1/3-1/3 split.
// Requires MIN_SAMPLES_FOR_BIAS_CHECK throws first, so a percentage over a
// handful of throws can't trigger a false positive.
function opponentAppearsBiased(opponentHistory: string): boolean {
  const window = opponentHistory.slice(0, RANDOMNESS_CHECK_WINDOW);
  if (window.length < MIN_SAMPLES_FOR_BIAS_CHECK) return false;

  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  for (const char of window) {
    if (isMove(char)) counts[char] += 1;
  }

  const topCount = Math.max(counts.R, counts.P, counts.S);
  return topCount / window.length > BIAS_THRESHOLD;
}

function selectMode(turn: number, opponentHistory: string): Mode {
  if (turn >= HISTORY_MODE_START_TURN) return Mode.CounterMostFrequent;
  return opponentAppearsBiased(opponentHistory) ? Mode.CounterMostFrequent : Mode.Random;
}

function isMove(value: string): value is Move {
  return value === "R" || value === "P" || value === "S";
}

// Picks a uniformly random move so each of R/P/S lands at 33.3%.
function chooseRandomMove(rng: Rng): Move {
  return MOVES[rng.nextInt(MOVES.length)];
}

// Counters the opponent's most frequent move over their last 100 throws,
// re-evaluating only once every COUNTER_STREAK_LENGTH turns so the same
// counter-move holds for the full streak instead of flickering turn to turn.
function chooseCounterMove(turn: number, opponentHistory: string, rng: Rng): Move {
  // Round turn down to the start of its 5-turn streak (0, 5, 10, ...) so the
  // counter-move stays fixed for all 5 turns instead of being recomputed every turn.
  const streakStartTurn = Math.floor(turn / COUNTER_STREAK_LENGTH) * COUNTER_STREAK_LENGTH;
  // Snapshot the opponent's history as it stood at the start of this streak,
  // ignoring any moves thrown after that point.
  const historyAtStreakStart = opponentHistory.slice(0, streakStartTurn);
  // Keep only the most recent FREQUENCY_WINDOW throws from that snapshot.
  const window = historyAtStreakStart.slice(-FREQUENCY_WINDOW);

  // Tally how many times each move appears in the window.
  const counts: Record<Move, number> = { R: 0, P: 0, S: 0 };
  for (const char of window) {
    if (isMove(char)) counts[char] += 1;
  }

  // Find the highest tally among the three moves.
  const topCount = Math.max(counts.R, counts.P, counts.S);
  // Collect every move that hit that highest tally (there may be a tie).
  const mostFrequentCandidates = MOVES.filter((move) => counts[move] === topCount);
  // If there's a single most-frequent move, use it; otherwise break the tie
  // with the deterministic rng so the choice stays reproducible.
  const mostFrequent =
    mostFrequentCandidates.length === 1
      ? mostFrequentCandidates[0]
      : mostFrequentCandidates[rng.nextInt(mostFrequentCandidates.length)];

  // Throw the move that beats the opponent's most frequent move.
  return COUNTER[mostFrequent];
}

export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  switch (selectMode(turn, opponentHistory)) {
    case Mode.Random:
      return chooseRandomMove(rng);
    case Mode.CounterMostFrequent:
      return chooseCounterMove(turn, opponentHistory, rng);
  }
}
