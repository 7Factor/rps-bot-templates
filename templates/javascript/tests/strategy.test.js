"use strict";

const assert = require("node:assert/strict");
const { chooseMove } = require("../team_source/strategy");

class DeterministicRandom {
  constructor(seed) {
    this.state = BigInt(seed);
  }

  nextInt(upperExclusive) {
    this.state =
      (this.state * 6364136223846793005n + 1442695040888963407n) &
      ((1n << 64n) - 1n);
    return Number(this.state % BigInt(upperExclusive));
  }
}

const legal = new Set(["R", "P", "S"]);
const legalRng = new DeterministicRandom(42n);
for (let turn = 0; turn < 100; turn += 1) {
  assert(legal.has(chooseMove(turn, "", "", legalRng)), "returned an illegal move");
}

const first = new DeterministicRandom(18446744073709551615n);
const second = new DeterministicRandom(18446744073709551615n);
for (let turn = 0; turn < 100; turn += 1) {
  assert.equal(
    chooseMove(turn, "R", "P", first),
    chooseMove(turn, "R", "P", second),
    "same seed produced different moves",
  );
}

console.log("JavaScript starter tests passed");
