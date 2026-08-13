"use strict";

function chooseMove(turn, myHistory, opponentHistory, rng) {
  const moves = ["R", "P", "S"];
  const rCount = (opponentHistory.match(/R/g)|| []).length
  const pCount = (opponentHistory.match(/P/g)|| []).length
  const sCount = (opponentHistory.match(/S/g)|| []).length
  const turnCount = turn + 1;
  const threshold = 40;

  if (rCount / turnCount > threshold)
    return "P";
  else if (pCount / turnCount > threshold)
    return "S";
  else if (sCount / turnCount > threshold)
    return "R";

  return moves[rng.nextInt(moves.length)];
}

module.exports = { chooseMove };
