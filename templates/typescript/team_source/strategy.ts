// Maps a move to what beats it
function counter(move: string): string {
  if (move === "R") return "P";
  if (move === "P") return "S";
  return "R";
}

// Strategy 1: Counter-the-counter
// Assumes the opponent will counter our last move, so we counter their counter.
function counterTheCounter(myHistory: string): string {
  const myLast = myHistory[myHistory.length - 1];
  // Opponent expects to beat our last move, so they'll play counter(myLast).
  // We counter that.
  return counter(counter(myLast));
}

// Finds the most-played move in a given history
function mostPlayedMove(history: string): string {
  let r = 0;
  let p = 0;
  let s = 0;
  for (let i = 0; i < history.length; i++) {
    const ch = history[i];
    if (ch === "R") r++;
    else if (ch === "P") p++;
    else s++;
  }
  if (r >= p && r >= s) return "R";
  if (p >= r && p >= s) return "P";
  return "S";
}

// Strategy 2: Counter the opponent's most-played move
function highestPercentageCounter(opponentHistory: string): string {
  return counter(mostPlayedMove(opponentHistory));
}

// Strategy 3: Counter our own most-played move
// Assumes the opponent will try to beat our most frequent move,
// so we counter what they'd play against us.
function counterOwnBias(myHistory: string): string {
  const myMost = mostPlayedMove(myHistory);
  // Opponent will play counter(myMost) to beat us, so we counter that
  return counter(counter(myMost));
}

// Determines who won a single turn
function turnWinner(myMove: string, opponentMove: string): "me" | "opponent" | "tie" {
  if (myMove === opponentMove) return "tie";
  if (counter(opponentMove) === myMove) return "me";
  return "opponent";
}

// Logs the current match standings based on aggregated results
export function logCurrentWinner(myHistory: string, opponentHistory: string): void {
  let myWins = 0;
  let opponentWins = 0;
  let ties = 0;

  for (let i = 0; i < myHistory.length; i++) {
    const result = turnWinner(myHistory[i], opponentHistory[i]);
    if (result === "me") myWins++;
    else if (result === "opponent") opponentWins++;
    else ties++;
  }

  const total = myHistory.length;
  const myPct = total > 0 ? ((myWins / total) * 100).toFixed(1) : "0.0";
  const oppPct = total > 0 ? ((opponentWins / total) * 100).toFixed(1) : "0.0";
  const tiePct = total > 0 ? ((ties / total) * 100).toFixed(1) : "0.0";

  let leader: string;
  if (myWins > opponentWins) leader = "ME";
  else if (opponentWins > myWins) leader = "OPPONENT";
  else leader = "TIED";

  console.log(`--- Match Status (${total} turns) ---`);
  console.log(`  Me:       ${myWins} wins (${myPct}%)`);
  console.log(`  Opponent: ${opponentWins} wins (${oppPct}%)`);
  console.log(`  Ties:     ${ties} (${tiePct}%)`);
  console.log(`  Leader:   ${leader}`);
}

// Strategy 4: Recency-weighted counter
// Looks at the opponent's last N moves instead of all-time history.
// Adapts faster to pattern shifts mid-match.
const RECENCY_WINDOW = 10;

function recentMostPlayed(opponentHistory: string): string {
  const recent = opponentHistory.slice(-RECENCY_WINDOW);
  return mostPlayedMove(recent);
}

function recencyCounter(opponentHistory: string): string {
  return counter(recentMostPlayed(opponentHistory));
}

export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  // Every 3rd turn (0, 3, 6, 9...) play randomly to stay unpredictable
  if (turn % 3 === 0) {
    const moves = ["R", "P", "S"];
    return moves[rng.nextInt(moves.length)];
  }

  // Not enough data yet — counter our own bias
  if (opponentHistory.length < 3) {
    return counterOwnBias(myHistory);
  }

  // Once we have enough history, use recency-weighted analysis
  // (last 10 moves tell us more than all-time averages)
  if (opponentHistory.length >= RECENCY_WINDOW) {
    return recencyCounter(opponentHistory);
  }

  // Mid-early game: use full history counter
  return highestPercentageCounter(opponentHistory);
}
