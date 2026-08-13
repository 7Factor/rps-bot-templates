using System;

public sealed class RpsRandom
{
    private const ulong Gamma = 0x9e3779b97f4a7c15UL;
    private ulong state;

    public RpsRandom(ulong seed) => state = seed;

    public ulong NextUInt64()
    {
        state = unchecked(state + Gamma);
        ulong value = state;
        value = unchecked((value ^ (value >> 30)) * 0xbf58476d1ce4e5b9UL);
        value = unchecked((value ^ (value >> 27)) * 0x94d049bb133111ebUL);
        return value ^ (value >> 31);
    }

    public int NextInt(int upperExclusive)
    {
        ulong bound = (ulong)upperExclusive;
        ulong threshold = unchecked(0UL - bound) % bound;
        ulong value;
        do value = NextUInt64(); while (value < threshold);
        return (int)(value % bound);
    }
}

public static class StrategyTests
{
    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    public static void Main()
    {
        var legalRng = new RpsRandom(42UL);
        for (int turn = 0; turn < 100; turn++)
        {
            string move = Strategy.ChooseMove(turn, "", "", legalRng);
            Require(move is "R" or "P" or "S", "returned an illegal move");
        }

        var first = new RpsRandom(ulong.MaxValue);
        var second = new RpsRandom(ulong.MaxValue);
        for (int turn = 0; turn < 100; turn++)
        {
            Require(
                Strategy.ChooseMove(turn, "R", "P", first)
                    == Strategy.ChooseMove(turn, "R", "P", second),
                "same seed produced different moves");
        }
        Console.WriteLine("C# starter tests passed");
    }
}
