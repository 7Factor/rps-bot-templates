// Manual JS port of origin/team/team-2's Strategy.java (see Strategy_team_2.java in this
// same directory for the original) -- there's no Java runtime in this local-dev harness, so
// this reimplements the exact same logic by hand rather than running the real Java source.
// Faithful to the original: majority-vote counter of the OPPONENT's move history (ties go
// R > P > S), with the rng only ever consulted on the very first move.
export function chooseMove(turn, myHistory, opponentHistory, rng) {
  const moves = ["R", "P", "S"];
  if (opponentHistory.length === 0) {
    return moves[rng.nextInt(moves.length)];
  }

  let rCount = 0;
  let pCount = 0;
  let sCount = 0;
  for (const c of opponentHistory) {
    if (c === "R") rCount += 1;
    else if (c === "P") pCount += 1;
    else if (c === "S") sCount += 1;
  }

  if (rCount >= pCount && rCount >= sCount) return "P"; // beat Rock
  if (pCount >= sCount) return "S"; // beat Paper
  return "R"; // beat Scissors
}
