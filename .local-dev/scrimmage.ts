// Local scrimmage harness: runs strategy.ts (the real entrypoint), tominator_t1.ts, and
// tominator_t2.ts against a full opponent roster -- a handful of classic synthetic RPS
// strategies plus every real scouted team branch pulled into this directory -- over many
// seeded 300-turn matches, printing one results table per bot and a final side-by-side
// summary table across all of them. Not part of the official Runner/Advisory Validation --
// just a fast way to sanity-check strategy performance before pushing.
//
// tominator_t2.ts holds the mode-based (RESEARCH/EXPLOIT/REEVALUATE/DEFENSE) design;
// tominator_t1.ts is the earlier fixed-phase design, kept as a baseline to compare against.
// strategy.ts (the required official entrypoint) is loaded dynamically via
// loadStrategyEntrypoint() below rather than a static import, since it can be either a thin
// re-export shim pointing at one of the tominator files or a fully self-contained
// implementation -- either is valid, and this follows whichever it currently is.
//
// The roster includes every real scouted opponent copied into this directory (see the README
// for the current list) alongside the classic synthetic strategies. team-wml's file uses a
// real TS `enum`, which needs full type transformation, not just stripping -- run this whole
// script with --experimental-transform-types (harmless for the other files, which don't need it):
//
// Usage: node --experimental-transform-types scrimmage.ts [rounds] [matchesPerOpponent] [baseSeed]

import {readFileSync} from "node:fs";
import {dirname, resolve} from "node:path";
import {fileURLToPath, pathToFileURL} from "node:url";

import {chooseMove as chooseMoveOriginal} from "../templates/typescript/team_source/tominator_t1.ts";
import {chooseMove as chooseMoveModes} from "../templates/typescript/team_source/tominator_t2.ts";
import {chooseMove as chooseMoveT3} from "../templates/typescript/team_source/tominator_t3.ts";
import {chooseMove as chooseMoveOnlyPaper} from "./strategy_only_paper.ts";
import {chooseMove as chooseMoveTeamWml} from "./strategy_team_wml.ts";
import {chooseMove as chooseMoveChicagoDawgs} from "./strategy_chicago_dawgs.js";
import {chooseMove as chooseMoveTeam2} from "./strategy_team_2.js";
import {chooseMove as chooseMoveWeWillRockYou} from "./strategy_we_will_rock_you.ts";
import {chooseMove as chooseMoveAlyssasAngels} from "./strategy_alyssas_angels.ts";
import {chooseMove as chooseMoveBervBot} from "./strategy_berv_bot.ts";
import {chooseMove as chooseMoveSeven} from "./strategy_seven.ts";
import {chooseMove as chooseMoveBackWeWillRock} from "./strategy_back_we_will_rock.ts";

type Move = "R" | "P" | "S";
type Rng = { nextInt(upperExclusive: number): number };
type ChooseMove = (turn: number, myHistory: string, opponentHistory: string, rng: Rng) => string;

const BEATS: Record<Move, Move> = {R: "S", P: "R", S: "P"}; // key beats value
const COUNTER: Record<Move, Move> = {R: "P", P: "S", S: "R"};
const MOVES: readonly Move[] = ["R", "P", "S"];

class SplitMix64 implements Rng {
    private state: bigint;

    constructor(seed: bigint) {
        this.state = seed & ((1n << 64n) - 1n);
    }

    private nextRaw(): bigint {
        this.state = (this.state + 0x9e3779b97f4a7c15n) & ((1n << 64n) - 1n);
        let z = this.state;
        z = ((z ^ (z >> 30n)) * 0xbf58476d1ce4e5b9n) & ((1n << 64n) - 1n);
        z = ((z ^ (z >> 27n)) * 0x94d049bb133111ebn) & ((1n << 64n) - 1n);
        return z ^ (z >> 31n);
    }

    nextInt(upperExclusive: number): number {
        return Number(this.nextRaw() % BigInt(upperExclusive));
    }
}

type Opponent = {
    name: string;
    choose(turn: number, ownHistory: string, botHistory: string, rng: Rng): Move;
};

function asMove(char: string, fallback: Move): Move {
    return char === "R" || char === "P" || char === "S" ? char : fallback;
}

// templates/typescript/team_source/strategy.ts is the required official entrypoint (see
// TEAM_GUIDE.md and tests/strategy.test.ts) -- sometimes it's its own self-contained
// implementation, sometimes it's a thin re-export shim pointing elsewhere (e.g. at
// tominator_t2.ts), and either is valid. tsc's module resolution accepts extensionless
// specifiers in a re-export (`from "./tominator_t2"`), but Node's native ESM loader (used to
// run this harness directly, without a build step) requires an explicit extension on relative
// specifiers. So: if strategy.ts re-exports from elsewhere, follow that specifier with the
// extension Node needs; otherwise it's self-contained, so just import strategy.ts itself
// (which already has its own ".ts" extension, so Node can resolve it directly). Either way
// this stays an honest end-to-end check of whatever the real entrypoint currently does.
async function loadStrategyEntrypoint(): Promise<ChooseMove> {
    const strategyPath = resolve(dirname(fileURLToPath(import.meta.url)), "../templates/typescript/team_source/strategy.ts");
    const source = readFileSync(strategyPath, "utf8");
    const match = source.match(/from\s+["'](\.\/[^"']+)["']/);

    let targetPath = strategyPath;
    if (match) {
        const specifier = /\.[a-z]+$/.test(match[1]) ? match[1] : `${match[1]}.ts`;
        targetPath = resolve(dirname(strategyPath), specifier);
    }

    const module = (await import(pathToFileURL(targetPath).href)) as { chooseMove: ChooseMove };
    return module.chooseMove;
}

let chooseMoveStrategy: ChooseMove = () => {
    throw new Error("strategy.ts entrypoint not loaded yet -- loadStrategyEntrypoint() must be awaited before use");
};

const opponents: Opponent[] = [
    {name: "always-rock", choose: () => "R"},
    {
        name: "cycle-RPS",
        choose: (turn) => MOVES[turn % 3],
    },
    {
        name: "uniform-random",
        choose: (_turn, _ownHistory, _botHistory, rng) => MOVES[rng.nextInt(3)],
    },
    {
        // repeats whatever the bot threw last turn
        name: "mirror-last",
        choose: (_turn, _ownHistory, botHistory) => asMove(botHistory.slice(-1), "R"),
    },
    {
        // plays the move that beats what the bot threw last turn
        name: "counter-last",
        choose: (_turn, _ownHistory, botHistory) => COUNTER[asMove(botHistory.slice(-1), "R")],
    },
    {
        // win-stay/lose-shift from the opponent's own perspective
        name: "win-stay-lose-shift",
        choose: (_turn, ownHistory, botHistory, rng) => {
            if (ownHistory.length === 0) return MOVES[rng.nextInt(3)];
            const prevMine = asMove(ownHistory.slice(-1), "R");
            const prevBot = asMove(botHistory.slice(-1), "R");
            const won = BEATS[prevMine] === prevBot;
            return won ? prevMine : COUNTER[COUNTER[prevMine]];
        },
    },
    {
        // switches strategy mid-match: reactive counter-last for the first 150 turns,
        // then a fixed R -> P -> S cycle for the rest. Exercises whether a bot can
        // notice and adapt to an opponent-side strategy change, not just its own.
        name: "shifting-counter-then-cycle",
        choose: (turn, _ownHistory, botHistory) =>
            turn < 150 ? COUNTER[asMove(botHistory.slice(-1), "R")] : MOVES[turn % 3],
    },
    {
        // real scouted opponent: origin/team/only-paper's strategy.ts
        name: "only-paper",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveOnlyPaper(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/team-wml's strategy.ts
        name: "team-wml",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveTeamWml(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/chicago-dawgs's strategy.js (JavaScript, not
        // TypeScript -- a simpler cumulative-frequency counter than only-paper's: single
        // fixed 40% threshold, no minimum-sample gate, no streak check, no opening special-case).
        name: "chicago-dawgs",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveChicagoDawgs(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/team-2's Strategy.java (Java -- no Java runtime
        // here, so this calls a hand-written JS port; see strategy_team_2.js/Strategy_team_2.java).
        // Deterministic majority-vote counter of the opponent's whole history after turn 0
        // (ties go R > P > S); rng is only ever touched on the very first move.
        name: "team-2",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveTeam2(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/we-will-we-will-rock-you's strategy.ts.
        // Note: its whoWonLastTurn helper has a bug (reads myHistory where it should read
        // oppHistory for the opponent's last move), so lastWinner can never resolve to "us" or
        // "opp" -- it's effectively always uniform random despite the elaborate-looking logic.
        // Copied faithfully as-is; not fixed, since this is what would actually compete.
        name: "we-will-we-will-rock-you",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveWeWillRockYou(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/alyssas-angels's strategy.ts. Sticky move: repeats
        // its own last move as long as it didn't just lose with it; on a loss, excludes that
        // move and picks randomly between the other two.
        name: "alyssas-angels",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveAlyssasAngels(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/scissors-to-a-knife-fight's strategy.ts -- byte-
        // identical to alyssas-angels's (confirmed via diff), so this reuses the same import.
        name: "scissors-to-a-knife-fight",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveAlyssasAngels(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/berv-bot's strategy.ts.
        name: "berv-bot",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveBervBot(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/seven's strategy.ts. Needs 15 opponent throws
        // before doing anything; then looks at the trailing 15 and picks randomly between the
        // two moves that don't lose to whichever the opponent has thrown most -- except one of
        // those two branches includes a move that actually LOSES to that bias (see the ["P","S"]
        // case when opponent is Rock-heavy: P counters R, but S loses to R), so about half the
        // time it reacts to a real bias with a losing move anyway.
        name: "seven",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveSeven(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // real scouted opponent: origin/team/back-we-will-rock's strategy.ts. No
        // team-submission.json committed on that branch yet, but the strategy itself is real:
        // sticky counter-the-counter early, then a recency-windowed (last 10 throws) frequency
        // counter once enough history has built up, with every 3rd turn thrown randomly.
        name: "back-we-will-rock",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveBackWeWillRock(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // tominator_t1.ts as an opponent -- lets both roster tables show T1-vs-T2 and each
        // one's mirror-match (T1-vs-T1, T2-vs-T2) alongside every other matchup in one place.
        name: "tominator_t1.ts",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveOriginal(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        name: "tominator_t2.ts",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveModes(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // tominator_t3.ts as an opponent, same reasoning as T1/T2 above.
        name: "tominator_t3.ts",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveT3(turn, ownHistory, botHistory, rng) as Move,
    },
    {
        // The official entrypoint itself (templates/typescript/team_source/strategy.ts), which
        // is just a re-export of tominator_t2.ts's chooseMove -- included as its own opponent
        // to sanity-check that the shim really does forward correctly end-to-end. Should always
        // score identically to the "tominator_t2.ts" row above; any difference means the
        // re-export is broken.
        name: "strategy.ts",
        choose: (turn, ownHistory, botHistory, rng) => chooseMoveStrategy(turn, ownHistory, botHistory, rng) as Move,
    },
];

const NUMERIC_CELL = /^-?[\d.]+%?$/;

// Prints a column-aligned table instead of raw tab-joins, which misaligns badly once any
// row label (e.g. "shifting-counter-then-cycle") is much longer than the rest. Columns whose
// cells all look numeric (digits, decimals, a trailing "%") right-align; everything else
// left-aligns, so labels stay readable and numbers stay easy to scan down a column.
function printTable(
    headers: readonly string[],
    rows: readonly (string | number)[][],
    footerRow?: readonly (string | number)[],
): void {
    const cells = rows.map((row) => row.map(String));
    const footer = footerRow?.map(String);
    const allRows = footer ? [...cells, footer] : cells;
    const widths = headers.map((header, col) =>
        Math.max(header.length, ...allRows.map((row) => row[col].length)),
    );
    const numeric = headers.map((_, col) => allRows.every((row) => NUMERIC_CELL.test(row[col])));

    const formatRow = (row: readonly string[]) =>
        row.map((cell, col) => (numeric[col] ? cell.padStart(widths[col]) : cell.padEnd(widths[col]))).join("  ");

    console.log(formatRow(headers));
    console.log(widths.map((width) => "-".repeat(width)).join("  "));
    for (const row of cells) console.log(formatRow(row));
    if (footer) {
        console.log(widths.map((width) => "-".repeat(width)).join("  "));
        console.log(formatRow(footer));
    }
}

function roundOutcome(a: Move, b: Move): "win" | "loss" | "tie" {
    if (a === b) return "tie";
    return BEATS[a] === b ? "win" : "loss";
}

function playAgainstOpponent(bot: ChooseMove, opponent: Opponent, rounds: number, botSeed: bigint, oppSeed: bigint) {
    const botRng = new SplitMix64(botSeed);
    const oppRng = new SplitMix64(oppSeed);
    let botHistory = "";
    let oppHistory = "";
    let botWins = 0;
    let oppWins = 0;
    let ties = 0;
    let firstHalfBotWins = 0;
    let firstHalfTotal = 0;
    let secondHalfBotWins = 0;
    let secondHalfTotal = 0;

    for (let turn = 0; turn < rounds; turn += 1) {
        const botMove = bot(turn, botHistory, oppHistory, botRng) as Move;
        const oppMove = opponent.choose(turn, oppHistory, botHistory, oppRng);

        const outcome = roundOutcome(botMove, oppMove);
        if (outcome === "win") botWins += 1;
        else if (outcome === "loss") oppWins += 1;
        else ties += 1;

        if (turn < Math.floor(rounds / 2)) {
            firstHalfTotal += 1;
            if (outcome === "win") firstHalfBotWins += 1;
        } else {
            secondHalfTotal += 1;
            if (outcome === "win") secondHalfBotWins += 1;
        }

        botHistory += botMove;
        oppHistory += oppMove;
    }

    return {botWins, oppWins, ties, firstHalfBotWins, firstHalfTotal, secondHalfBotWins, secondHalfTotal};
}

function runRoster(
    label: string,
    bot: ChooseMove,
    rounds: number,
    matchesPerOpponent: number,
    baseSeed: bigint,
): (string | number)[] {
    console.log(`\n=== ${label} vs opponent roster: ${matchesPerOpponent} matches x ${rounds} rounds ===`);
    const header = ["Opponent", "MatchesWon", "MatchesLost", "MatchesTied", "1stHalfWin%", "2ndHalfWin%", "RoundWin%", "MatchWin%"];
    const rows: (string | number)[][] = [];

    let totalMatchesWon = 0;
    let totalMatchesLost = 0;
    let totalMatchesTied = 0;
    let grandTotalBotWins = 0;
    let grandTotalRounds = 0;
    let grandFirstHalfBotWins = 0;
    let grandFirstHalfTotal = 0;
    let grandSecondHalfBotWins = 0;
    let grandSecondHalfTotal = 0;

    for (const opponent of opponents) {
        let matchesWon = 0;
        let matchesLost = 0;
        let matchesTied = 0;
        let totalBotWins = 0;
        let totalRounds = 0;
        let firstHalfBotWins = 0;
        let firstHalfTotal = 0;
        let secondHalfBotWins = 0;
        let secondHalfTotal = 0;

        for (let m = 0; m < matchesPerOpponent; m += 1) {
            const botSeed = baseSeed + BigInt(m) * 2n + 1n;
            const oppSeed = baseSeed + BigInt(m) * 2n + 2n;
            const result = playAgainstOpponent(bot, opponent, rounds, botSeed, oppSeed);

            if (result.botWins > result.oppWins) matchesWon += 1;
            else if (result.oppWins > result.botWins) matchesLost += 1;
            else matchesTied += 1;

            totalBotWins += result.botWins;
            totalRounds += result.botWins + result.oppWins + result.ties;
            firstHalfBotWins += result.firstHalfBotWins;
            firstHalfTotal += result.firstHalfTotal;
            secondHalfBotWins += result.secondHalfBotWins;
            secondHalfTotal += result.secondHalfTotal;
        }

        const roundWinPct = ((totalBotWins / totalRounds) * 100).toFixed(1);
        const firstHalfPct = ((firstHalfBotWins / firstHalfTotal) * 100).toFixed(1);
        const secondHalfPct = ((secondHalfBotWins / secondHalfTotal) * 100).toFixed(1);
        const matchWinPct = ((matchesWon / matchesPerOpponent) * 100).toFixed(1);
        rows.push([opponent.name, matchesWon, matchesLost, matchesTied, `${firstHalfPct}%`, `${secondHalfPct}%`, `${roundWinPct}%`, `${matchWinPct}%`]);

        totalMatchesWon += matchesWon;
        totalMatchesLost += matchesLost;
        totalMatchesTied += matchesTied;
        grandTotalBotWins += totalBotWins;
        grandTotalRounds += totalRounds;
        grandFirstHalfBotWins += firstHalfBotWins;
        grandFirstHalfTotal += firstHalfTotal;
        grandSecondHalfBotWins += secondHalfBotWins;
        grandSecondHalfTotal += secondHalfTotal;
    }

    const totalRoundWinPct = ((grandTotalBotWins / grandTotalRounds) * 100).toFixed(1);
    const totalFirstHalfPct = ((grandFirstHalfBotWins / grandFirstHalfTotal) * 100).toFixed(1);
    const totalSecondHalfPct = ((grandSecondHalfBotWins / grandSecondHalfTotal) * 100).toFixed(1);
    const totalMatches = totalMatchesWon + totalMatchesLost + totalMatchesTied;
    const totalMatchWinPct = ((totalMatchesWon / totalMatches) * 100).toFixed(1);
    const footerRow = [
        "TOTAL",
        totalMatchesWon,
        totalMatchesLost,
        totalMatchesTied,
        `${totalFirstHalfPct}%`,
        `${totalSecondHalfPct}%`,
        `${totalRoundWinPct}%`,
        `${totalMatchWinPct}%`,
    ];

    printTable(header, rows, footerRow);

    return [label, totalMatchesWon, totalMatchesLost, totalMatchesTied, `${totalFirstHalfPct}%`, `${totalSecondHalfPct}%`, `${totalRoundWinPct}%`, `${totalMatchWinPct}%`];
}

async function main() {
    const rounds = Number(process.argv[2] ?? 300);
    const matchesPerOpponent = Number(process.argv[3] ?? 20);
    const baseSeed = BigInt(process.argv[4] ?? "12345");

    chooseMoveStrategy = await loadStrategyEntrypoint();

    // Run bots against each opponent in the roster, print the results, and collect each
    // bot's TOTAL row for a side-by-side summary at the end.
    const summaryRows: (string | number)[][] = [];
    const run = (label: string, bot: ChooseMove) =>
        summaryRows.push(runRoster(label, bot, rounds, matchesPerOpponent, baseSeed));

    run("strategy.ts", chooseMoveStrategy);
    run("tominator_t3.ts", chooseMoveT3);
    run("tominator_t2.ts", chooseMoveModes);
    run("tominator_t1.ts", chooseMoveOriginal);
    run("only-paper", chooseMoveOnlyPaper);
    run("team-wml", chooseMoveTeamWml);
    run("chicago-dawgs", chooseMoveChicagoDawgs);
    run("team-2", chooseMoveTeam2);
    run("we-will-we-will-rock-you", chooseMoveWeWillRockYou);
    run("alyssas-angels", chooseMoveAlyssasAngels);
    run("berv-bot", chooseMoveBervBot);
    run("seven", chooseMoveSeven);
    run("back-we-will-rock", chooseMoveBackWeWillRock);

    console.log(`\n=== Summary: totals across all opponents (${matchesPerOpponent} matches x ${rounds} rounds each) ===`);
    const summaryHeader = ["Bot", "MatchesWon", "MatchesLost", "MatchesTied", "1stHalfWin%", "2ndHalfWin%", "RoundWin%", "MatchWin%"];
    printTable(summaryHeader, summaryRows);
}

main();
