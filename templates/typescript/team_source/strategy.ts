  const moves = ["R", "P", "S"];

export function chooseMove(
  turn: number,
  myHistory: string,
  opponentHistory: string,
  rng: { nextInt(upperExclusive: number): number }
): string {
  var myLastMove = getLastMove(myHistory);
  var oppLastMove = getLastMove(myHistory); 

  var didTie3Times = lastFiveMatch(opponentHistory, myHistory);

  if(didTie3Times) {
    var index = ((myLastMove + 1) % 3)
    return moves[index]
  }

  if(tie(oppLastMove, myLastMove)){
    return moves[myLastMove];
  }
 
  if(opponentHistory.length >= 2){
    var loseCount = 0;
    for (let i: number = 0; i < 3; i++) {
      
      if(lost(moves.indexOf(opponentHistory[opponentHistory.length - i]), moves.indexOf(myHistory[myHistory.length - i]))){
        loseCount++
        opponentHistory = opponentHistory.substring(0, opponentHistory.length - 1);
        myHistory = myHistory.substring(0, myHistory.length - 1);
      }
    }
    if(loseCount == 3){
      return moves[rng.nextInt(moves.length)];
    }
  }

  if(lost(oppLastMove, myLastMove)){
    return moves[oppLastMove];
  }


  return moves[1];
}

function lastFiveMatch(str1: string, str2: string): boolean {
    try {
        // Validate inputs
        if (typeof str1 !== "string" || typeof str2 !== "string") {
            throw new Error("Both inputs must be strings.");
        }

        // If either string is shorter than 5 characters, compare the whole string
        const minLength = 3;
        const sub1 = str1.slice(-minLength);
        const sub2 = str2.slice(-minLength);

        return sub1 === sub2;
    } catch (error) {
        console.error("Error:", (error as Error).message);
        return false;
    }
}

function getLastMove(movesList: string) {
  return movesList.indexOf(movesList[movesList.length])
}

function getMoveIndex(move: string){
  return moves.indexOf(move);
}

function tie(opponentLastMove: number, myLastMove: number) {
  return opponentLastMove == myLastMove;
}

function lost(opponentLastMove: number, myLastMove: number) {
  return opponentLastMove = ((myLastMove + 1) % 3);
}
