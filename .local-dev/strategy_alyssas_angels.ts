export function chooseMove(
    turn: number,
    myHistory: string,
    opponentHistory: string,
    rng: { nextInt(upperExclusive: number): number }
): string {
  const moves = ["R", "P", "S"];
  if (turn <= 1) {
    return moves[rng.nextInt(moves.length)];
  }
  var ourHistoryArray = convert_string_to_move_array(myHistory);
  var theirHistoryArray = convert_string_to_move_array(opponentHistory);
  const currentStrategy = ourHistoryArray[ourHistoryArray.length - 1];

  if (moves.indexOf(currentStrategy) === -1) {
    return moves[rng.nextInt(moves.length)];
  }

  if (turn == 2)
  { return currentStrategy; }
  else {
    if (did_i_lose(ourHistoryArray[ourHistoryArray.length - 2], theirHistoryArray[ourHistoryArray.length - 2])) {
      const index = moves.indexOf(currentStrategy);
      if (index !== -1) {
        moves.splice(index, 1);
        return moves[rng.nextInt(moves.length-1)]
      }
      return currentStrategy;
    }
    return currentStrategy;
  }
}

function convert_string_to_move_array(str: string): string[]
{ return str.split(""); }

function did_i_lose(our_move: string, opponent_move: string): boolean {
  return our_move === "S" && opponent_move === "R" || our_move === "P" && opponent_move === "S" || our_move === "R" && opponent_move === "P";
}