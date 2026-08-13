"use strict";

function chooseMove(turn, myHistory, opponentHistory, rng) {
  const moves = ["R", "P", "S"];
  return moves[rng.nextInt(moves.length)];
}

module.exports = { chooseMove };
