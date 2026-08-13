import java.util.random.RandomGenerator

object Strategy {
    /** Returns one legal move using only the wrapper-provided random stream. */
    fun chooseMove(
        turn: Int,
        myHistory: String,
        opponentHistory: String,
        rng: RandomGenerator
    ): String {
        val moves = arrayOf("R", "P", "S")
        return moves[rng.nextInt(moves.size)]
    }
}
