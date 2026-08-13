import java.util.random.RandomGenerator;

public final class Strategy {
    private Strategy() {}

    /** Returns one legal move using only the wrapper-provided random stream. */
    public static String chooseMove(
        int turn,
        String myHistory,
        String opponentHistory,
        RandomGenerator rng
    ) {
        if (opponentHistory.isEmpty()) {
            String[] moves = {"R", "P", "S"};
            return moves[rng.nextInt(moves.length)];
        }

        int rCount = 0;
        int pCount = 0;
        int sCount = 0;

        for (char c : opponentHistory.toCharArray()) {
            if (c == 'R') rCount++;
            else if (c == 'P') pCount++;
            else if (c == 'S') sCount++;
        }

        if (rCount >= pCount && rCount >= sCount) {
            return "P"; // Beat Rock
        } else if (pCount >= sCount) {
            return "S"; // Beat Paper
        } else {
            return "R"; // Beat Scissors
        }
    }
}
