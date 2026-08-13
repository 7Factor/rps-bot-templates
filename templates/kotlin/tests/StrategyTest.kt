import java.util.SplittableRandom

private fun requireThat(condition: Boolean, message: String) {
    if (!condition) throw AssertionError(message)
}

private fun chooseMoveReturnsOnlyLegalMoves() {
    val rng = SplittableRandom(42L)
    repeat(100) { turn ->
        val move = Strategy.chooseMove(turn, "", "", rng)
        requireThat(move in setOf("R", "P", "S"), "turn $turn returned illegal move $move")
    }
}

private fun chooseMoveIsDeterministicForTheSameSeed() {
    val first = SplittableRandom(-1L)
    val second = SplittableRandom(-1L)
    repeat(100) { turn ->
        val moveA = Strategy.chooseMove(turn, "R", "P", first)
        val moveB = Strategy.chooseMove(turn, "R", "P", second)
        requireThat(moveA == moveB, "turn $turn differed for the same seed")
    }
}

fun main() {
    chooseMoveReturnsOnlyLegalMoves()
    chooseMoveIsDeterministicForTheSameSeed()
}
