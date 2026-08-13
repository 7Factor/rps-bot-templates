export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  const moves = ["R", "P", "S"];

  const lastWinner = whoWonLastTurn(myHistory, opponentHistory);

  if (turn % 3 === 0) {
    return moves[rng.nextInt(moves.length)];
  }

  if (lastWinner == "us") {
    return opponentPercentageBasedStrategy(opponentHistory, moves, rng);
  } else if (lastWinner == "opp") {
    return myPercentageBasedStrategy(myHistory, moves, rng);
  }

  return moves[rng.nextInt(moves.length)];
}

const opponentPercentageBasedStrategy = (opponentHistory: string, moves: string[], rng: { nextInt(upperExclusive: number): number }): string => {
  const percentageOfRock = getPercentageOfLetter(opponentHistory, "R");
  const percentageOfPaper = getPercentageOfLetter(opponentHistory, "P");
  const percentageOfScissors = getPercentageOfLetter(opponentHistory, "S");

  const percentages = {
    R: percentageOfRock,
    P: percentageOfPaper,
    S: percentageOfScissors,
  }

  const highestPercentage = getMax(percentages, moves, rng);

  return getLetterThatBeats(highestPercentage);
}

const myPercentageBasedStrategy = (myHistory: string, moves: string[], rng: { nextInt(upperExclusive: number): number }) => {
  const percentageOfRock = getPercentageOfLetter(myHistory, "R");
  const percentageOfPaper = getPercentageOfLetter(myHistory, "P");
  const percentageOfScissors = getPercentageOfLetter(myHistory, "S");

  const percentages = {
    R: percentageOfRock,
    P: percentageOfPaper,
    S: percentageOfScissors,
  }

  const highestPercentage = getMax(percentages, moves, rng);

  return getLetterThatBeats(highestPercentage);
}

const getPercentageOfLetter = (history: string, letter: string) => {
  const historyArray = history.split("");
  const numOfLetter = historyArray.filter(item => item == letter).length;
  return (numOfLetter / history.length) * 100;
}

const getLetterThatBeats = (letter: string) => {
  if (letter === "R") { return "P"}
  if (letter === "P") { return "S"}
  if (letter === "S") { return "R"}

  return "P";
}

const getMax = (percentages: { R: number, P: number, S: number }, moves: string[], rng: { nextInt(upperExclusive: number): number }) => {
  if (percentages.R > percentages.P && percentages.R > percentages.S) {
    return "R";
  }
  if (percentages.P > percentages.R && percentages.P > percentages.S) {
    return "P";
  }
  if (percentages.S > percentages.P && percentages.S > percentages.R) {
    return "S";
  }

  return moves[rng.nextInt(moves.length)];
}

const whoWonLastTurn = (myHistory: string, oppHistory: string) => {
  const myLastTurn = myHistory.charAt(myHistory.length - 1);
  const oppLastTurn = myHistory.charAt(oppHistory.length - 1);

  if ((myLastTurn === "R" && oppLastTurn == "S") || (myLastTurn == "P" && oppLastTurn == "R") || (myLastTurn == "S" && oppHistory == "P")) {
    return "us";
  }
  if ((oppLastTurn === "R" && myLastTurn == "S") || (oppLastTurn == "P" && myLastTurn == "R") || (oppLastTurn == "S" && myLastTurn == "P")) {
    return "opp";
  }
  return "tie";
}