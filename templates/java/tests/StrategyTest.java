import java.util.SplittableRandom;

public final class StrategyTest {
    private StrategyTest() {}

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private static void chooseMoveReturnsOnlyLegalMoves() {
        var rng = new SplittableRandom(42L);
        for (int turn = 1; turn <= 100; turn++) {
            String move = Strategy.chooseMove(turn, "", "", rng);
            require(
                move.equals("R") || move.equals("P") || move.equals("S"),
                "turn " + turn + " returned illegal move " + move
            );
        }
    }

    private static void chooseMoveIsDeterministicForTheBotVisibleSeed() {
        long seed = Long.parseUnsignedLong("18446744073709551615");
        var first = new SplittableRandom(seed);
        var second = new SplittableRandom(seed);
        for (int turn = 1; turn <= 100; turn++) {
            String moveA = Strategy.chooseMove(turn, "R", "P", first);
            String moveB = Strategy.chooseMove(turn, "R", "P", second);
            require(
                moveA.equals(moveB),
                "turn " + turn + " differed for the same bot-visible seed"
            );
        }
    }

    private static void chooseMoveCorrectlyUsesTheRandomGenerator() {
        var rng = new SplittableRandom(12345L);
        String expected = "RSRPRRRRSRSSSSPRRPSRRRSSRRRSPRSRRSSRRRSSRPRRPPSRPRRPPSPSRSSPRPRRSPRRSSRRRRRPPPRSPPSRRSRRSRPSPRRPSPRP";
        String actual = "";
        for (int i = 0; i < 100; i++) {
            int turn = i + 1;
            String move = Strategy.chooseMove(turn, "", "", rng);
            String expectedMove = String.valueOf(expected.charAt(i));
            require(move.equals(expectedMove), "turn " + turn + " expected " + expectedMove + " but got " + move);
            actual += move;
        }

        System.out.println("actual: " + actual);
    }

    private static void chooseMoveCountersOpponentBias() {
        var rng = new SplittableRandom(42L);
        // Opponent has played Rock 10 times, Paper 5 times, Scissors 2 times.
        String opponentHistory = "RRRRRRRRRRPPPPPS S".replace(" ", "");
        String myMove = Strategy.chooseMove(18, "P".repeat(17), opponentHistory, rng);
        require(myMove.equals("P"), "Expected P to beat Rock bias, but got " + myMove);

        // Opponent has played Paper 10 times.
        opponentHistory = "PPPPPPPPPP";
        myMove = Strategy.chooseMove(11, "S".repeat(10), opponentHistory, rng);
        require(myMove.equals("S"), "Expected S to beat Paper bias, but got " + myMove);

        // Opponent has played Scissors 10 times.
        opponentHistory = "SSSSSSSSSS";
        myMove = Strategy.chooseMove(11, "R".repeat(10), opponentHistory, rng);
        require(myMove.equals("R"), "Expected R to beat Scissors bias, but got " + myMove);
    }

    private static void chooseMoveWinsAgainstBiasedOpponent() {
        var myRng = new SplittableRandom(42L);
        var opponentRng = new SplittableRandom(123L);

        int wins = 0;
        int losses = 0;
        int draws = 0;

        StringBuilder myHistory = new StringBuilder();
        StringBuilder opponentHistory = new StringBuilder();

        for (int turn = 1; turn <= 100; turn++) {
            // Biased opponent: 70% Rock, 15% Paper, 15% Scissors
            int r = opponentRng.nextInt(100);
            String opponentMove;
            if (r < 70) opponentMove = "R";
            else if (r < 85) opponentMove = "P";
            else opponentMove = "S";

            String myMove = Strategy.chooseMove(turn, myHistory.toString(), opponentHistory.toString(), myRng);

            if (myMove.equals(opponentMove)) {
                draws++;
            } else if (
                (myMove.equals("R") && opponentMove.equals("S")) ||
                (myMove.equals("P") && opponentMove.equals("R")) ||
                (myMove.equals("S") && opponentMove.equals("P"))
            ) {
                wins++;
            } else {
                losses++;
            }

            myHistory.append(myMove);
            opponentHistory.append(opponentMove);
        }

        System.out.println("Against biased opponent (70% R): Wins=" + wins + ", Losses=" + losses + ", Draws=" + draws);
        require(wins > losses, "Expected more wins than losses against biased opponent, but got wins=" + wins + ", losses=" + losses);
    }

    public static void main(String[] arguments) {
        chooseMoveReturnsOnlyLegalMoves();
        chooseMoveIsDeterministicForTheBotVisibleSeed();
        chooseMoveCorrectlyUsesTheRandomGenerator();
        chooseMoveCountersOpponentBias();
        chooseMoveWinsAgainstBiasedOpponent();
    }
}
