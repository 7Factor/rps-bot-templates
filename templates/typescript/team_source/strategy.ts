export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  if (opponentHistory?.length < 15) {
    return randomMove(rng);
  }
  const moves = getDesiredMoveSet(opponentHistory.substring(opponentHistory.length - 15));
  return moves[rng.nextInt(moves.length)];
}

function getDesiredMoveSet(history: string): string[] {
  const rockCount = (history.match(/R/g) || []).length;
  const paperCount = (history.match(/P/g) || []).length;
  const scissorsCount = (history.match(/S/g) || []).length;

  if (rockCount > paperCount && rockCount > scissorsCount) {
    return ["P", "S"];
  } else if (paperCount > rockCount && paperCount > scissorsCount) {
    return ["S", "R"];
  } else if (scissorsCount > rockCount && scissorsCount > paperCount) {
    return ["R", "P"];
  }
  return ["P", "S"];
}

function randomMove(rng: { nextInt(upperExclusive: number): number }): string {
  const moves = ["R", "P", "S"];
  return moves[rng.nextInt(moves.length)];
}
