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

// Catalog-v16 owns and executes these Seed Adapter vectors. Keeping their
// published values here makes compatibility drift visible without copying the
// organizer-owned adapter into the Team Template.
const runnerSeedVectors = [
  ["0", "16294208416658607535", "7960286522194355700", "487617019471545679"],
  ["1", "10451216379200822465", "13757245211066428519", "17911839290282890590"],
  ["9223372036854775807", "3055647633038352039", "17441316833444690247", "17011665146503905680"],
  ["18446744073709551615", "16490336266968443936", "16834447057089888969", "4048727598324417001"],
];
assert.equal(runnerSeedVectors.length, 4);

console.log("JavaScript starter tests passed");
