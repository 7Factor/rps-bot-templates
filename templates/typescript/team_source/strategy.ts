export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  const moves = ["R", "P", "S"];
  //Naive cheating to start
  let returnValue = opposite(moves[rng.nextInt(moves.length)])
  const [rCount, pCount, sCount] = countOccurence(opponentHistory)
  let rPerc = rCount/turn
  let pPerc = pCount/turn
  let sPerc = sCount/turn
  if(rPerc > .5){
    return "P"
  }
  else if(pPerc > .5) {
    return "S"
  }
  else if(sPerc > .5) {
    return "R"
  }
  if (opponentHistory.slice(turn-4).match("/(.)\\1\\1/")) {
    return opposite(opponentHistory.charAt(turn-1))
  }
  return returnValue;
}

function opposite(thrown: string
) {
  switch (thrown) {
    case "R":
      return "P"
    case "P":
      return "S"
    default:
      return "R"
  }
}

function countOccurence(str: string): [number, number, number] {
  let rCount = 0;
      let sCount = 0;
      let pCount = 0;
  for (let i = 0; i < str.length; i++) {
    if (str[i] === "R") {
      rCount++;
    } else if (str[i] === "S") {
      sCount++;
    } else {
      pCount++;
    }
  }

  return [rCount, pCount, sCount];
}
