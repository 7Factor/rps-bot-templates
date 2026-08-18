export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  const moves = ["R", "P", "S"];
  if(turn <= 1)
    return "P"
  //Naive cheating to start
  let returnValue = opposite(moves[rng.nextInt(moves.length)])
  const [rCount, pCount, sCount] = countOccurence(opponentHistory)
  let rPerc = rCount/turn
  let pPerc = pCount/turn
  let sPerc = sCount/turn
  if(rPerc > .45){
    return "P"
  }
  else if(pPerc > .45) {
    return "S"
  }
  else if(sPerc > .45) {
    return "R"
  }
  if (/(.)\1\1/.test(opponentHistory.slice(-3))) {
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
