public static class Strategy
{
    public static string ChooseMove(
        int turn,
        string myHistory,
        string opponentHistory,
        RpsRandom rng)
    {
        string[] moves = { "R", "P", "S" };
        return moves[rng.NextInt(moves.Length)];
    }
}
