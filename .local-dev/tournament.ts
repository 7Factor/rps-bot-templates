// Local tournament simulation: runs the same qualifying-round-robin + best-of-three-Series +
// single-elimination-playoff structure described in
// .core/rps-tournament/docs/TOURNAMENT.md against the current roster of real bots (mirrors
// scrimmage.ts's `run(...)` list, minus strategy.ts -- see "Roster" below for why). Not part of
// the official Runner; a from-scratch reimplementation of the SCORING rules for local
// experimentation, not the real seed-derivation/scheduling machinery (see "Simplifications").
//
// Usage: node --experimental-transform-types .local-dev/tournament.ts [tournamentSeed] [roundsPerMatch]
//
// Scoring, straight from TOURNAMENT.md:
// - A Match win awards 1 Series Point; a drawn Match awards 0.5 Series Point to each side.
// - A Fixture is a best-of-three Series: play Match 1 and 2; if one side already has more
//   Series Points, the Series is decided and Match 3 is skipped; otherwise play Match 3.
// - Standing Points (qualifying): Series win = 3, Series draw = 1 each, Series loss = 0.
// - Qualifying tie-breakers, in order: most Standing Points -> most Series wins -> head-to-head
//   (only when exactly two teams remain tied) -> best Match differential -> best Round
//   differential -> fewest protocol-fault forfeits (never applicable here -- no faults in this
//   sim) -> a deterministic seed-derived tie-break key.
// - Playoffs: top 4 seeds, semis are seed1-vs-seed4 and seed2-vs-seed3, winners meet in the
//   final. Unlike qualifying, a TIED playoff Series doesn't draw -- the higher seed advances.
//
// Simplifications vs. the real Runner (all deliberate, for a fast local approximation):
// - Seeds are derived with a simple deterministic hash-combine, not the real HMAC-SHA-256
//   scheme -- doesn't affect fairness for this purpose, just isn't bit-identical to production.
// - Bot Position (Match 1 vs. Match 2 assignment swap) is a fairness/resource-allocation
//   concept for the real container runner; it has no effect on a pure-logic local simulation
//   where both sides always get their own independent, correctly-labeled history and RNG
//   regardless of "position", so it's omitted entirely.
// - No protocol faults, disqualifications, or infrastructure retries -- every match here always
//   completes normally, so those rules (and their tie-break criterion) never trigger.

import {pathToFileURL} from "node:url";

import {chooseMove as chooseMoveT1} from "../templates/typescript/team_source/tominator_t1.ts";
import {chooseMove as chooseMoveT2} from "../templates/typescript/team_source/tominator_t2.ts";
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
type Rng = {nextInt(upperExclusive: number): number};
type ChooseMove = (turn: number, myHistory: string, opponentHistory: string, rng: Rng) => string;

const BEATS: Record<Move, Move> = {R: "S", P: "R", S: "P"};
const NUMERIC_CELL = /^-?[\d.]+%?$/;

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

// Deterministic string -> bigint hash, used only to combine the tournament seed with team IDs
// and fixture/match ordinals into distinct per-match seeds. Not cryptographic; just needs to be
// stable and well-distributed for this purpose.
function hashSeed(...parts: (string | number)[]): bigint {
    let h = 0xcbf29ce484222325n; // FNV-1a style
    for (const part of parts) {
        for (const ch of String(part)) {
            h = (h ^ BigInt(ch.codePointAt(0) ?? 0)) & ((1n << 64n) - 1n);
            h = (h * 0x100000001b3n) & ((1n << 64n) - 1n);
        }
        h = (h * 0x9e3779b97f4a7c15n + 1n) & ((1n << 64n) - 1n);
    }
    return h;
}

export function printTable(headers: readonly string[], rows: readonly (string | number)[][], footerRow?: readonly (string | number)[]): void {
    const cells = rows.map((row) => row.map(String));
    const footer = footerRow?.map(String);
    const allRows = footer ? [...cells, footer] : cells;
    const widths = headers.map((header, col) => Math.max(header.length, ...allRows.map((row) => row[col].length)));
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

export type Team = {id: string; chooseMove: ChooseMove};

// Roster: mirrors scrimmage.ts's run(...) list, minus strategy.ts. strategy.ts is always
// either a re-export of one of the tominator_*.ts files or a self-contained duplicate of one
// -- either way it would be a guaranteed-identical twin of an entry already in this roster,
// which would just clutter the bracket with a perfectly-correlated duplicate rather than a
// genuinely distinct competitor. scissors-to-a-knife-fight IS included despite being byte-
// identical to alyssas-angels's code, since in the real tournament they're two separate teams
// occupying two separate roster slots, not one team appearing twice.
export const ROSTER: Team[] = [
    {id: "tominator_t1", chooseMove: chooseMoveT1},
    {id: "tominator_t2", chooseMove: chooseMoveT2},
    {id: "tominator_t3", chooseMove: chooseMoveT3},
    {id: "only-paper", chooseMove: chooseMoveOnlyPaper},
    {id: "team-wml", chooseMove: chooseMoveTeamWml},
    {id: "chicago-dawgs", chooseMove: chooseMoveChicagoDawgs},
    {id: "team-2", chooseMove: chooseMoveTeam2},
    {id: "we-will-we-will-rock-you", chooseMove: chooseMoveWeWillRockYou},
    {id: "alyssas-angels", chooseMove: chooseMoveAlyssasAngels},
    {id: "scissors-to-a-knife-fight", chooseMove: chooseMoveAlyssasAngels},
    {id: "berv-bot", chooseMove: chooseMoveBervBot},
    {id: "seven", chooseMove: chooseMoveSeven},
    {id: "back-we-will-rock", chooseMove: chooseMoveBackWeWillRock},
];

function roundOutcome(a: Move, b: Move): "win" | "loss" | "tie" {
    if (a === b) return "tie";
    return BEATS[a] === b ? "win" : "loss";
}

function asMove(char: string): Move {
    return char === "R" || char === "P" || char === "S" ? char : "R";
}

type MatchResult = {winner: "A" | "B" | "tie"; roundsA: number; roundsB: number};

function playMatch(teamA: Team, teamB: Team, rounds: number, seedA: bigint, seedB: bigint): MatchResult {
    const rngA = new SplitMix64(seedA);
    const rngB = new SplitMix64(seedB);
    let historyA = "";
    let historyB = "";
    let roundsA = 0;
    let roundsB = 0;

    for (let turn = 0; turn < rounds; turn += 1) {
        const moveA = asMove(teamA.chooseMove(turn, historyA, historyB, rngA));
        const moveB = asMove(teamB.chooseMove(turn, historyB, historyA, rngB));
        const outcome = roundOutcome(moveA, moveB);
        if (outcome === "win") roundsA += 1;
        else if (outcome === "loss") roundsB += 1;
        historyA += moveA;
        historyB += moveB;
    }

    const winner = roundsA > roundsB ? "A" : roundsB > roundsA ? "B" : "tie";
    return {winner, roundsA, roundsB};
}

type SeriesResult = {
    pointsA: number;
    pointsB: number;
    matchWinsA: number;
    matchWinsB: number;
    matchesPlayed: number;
    roundDiffA: number; // rounds A won minus rounds B won, across every Match actually played
};

// Best-of-three: Match 1, then Match 2; skip Match 3 once one side already holds strictly more
// Series Points than the other could still catch up to (i.e. already has 2 Match wins).
function playSeries(teamA: Team, teamB: Team, rounds: number, fixtureSeed: bigint): SeriesResult {
    let pointsA = 0;
    let pointsB = 0;
    let matchWinsA = 0;
    let matchWinsB = 0;
    let matchesPlayed = 0;
    let roundDiffA = 0;

    for (let matchOrdinal = 1; matchOrdinal <= 3; matchOrdinal += 1) {
        if (matchOrdinal === 3 && Math.max(pointsA, pointsB) >= 2) break; // already decided 2-0

        const seedA = hashSeed(fixtureSeed, teamA.id, matchOrdinal, "A");
        const seedB = hashSeed(fixtureSeed, teamB.id, matchOrdinal, "B");
        const result = playMatch(teamA, teamB, rounds, seedA, seedB);

        matchesPlayed += 1;
        roundDiffA += result.roundsA - result.roundsB;
        if (result.winner === "A") {
            pointsA += 1;
            matchWinsA += 1;
        } else if (result.winner === "B") {
            pointsB += 1;
            matchWinsB += 1;
        } else {
            pointsA += 0.5;
            pointsB += 0.5;
        }
    }

    return {pointsA, pointsB, matchWinsA, matchWinsB, matchesPlayed, roundDiffA};
}

export type Standing = {
    id: string;
    standingPoints: number;
    seriesWins: number;
    seriesDraws: number;
    seriesLosses: number;
    matchWins: number;
    matchLosses: number;
    roundDiff: number;
    tieBreakKey: bigint;
    headToHead: Map<string, "win" | "draw" | "loss">;
};

function runQualifying(tournamentSeed: bigint, rounds: number): Map<string, Standing> {
    const standings = new Map<string, Standing>();
    for (const team of ROSTER) {
        standings.set(team.id, {
            id: team.id,
            standingPoints: 0,
            seriesWins: 0,
            seriesDraws: 0,
            seriesLosses: 0,
            matchWins: 0,
            matchLosses: 0,
            roundDiff: 0,
            tieBreakKey: hashSeed(tournamentSeed, team.id, "tiebreak"),
            headToHead: new Map(),
        });
    }

    for (let i = 0; i < ROSTER.length; i += 1) {
        for (let j = i + 1; j < ROSTER.length; j += 1) {
            const teamA = ROSTER[i];
            const teamB = ROSTER[j];
            const fixtureSeed = hashSeed(tournamentSeed, teamA.id, teamB.id, "fixture");
            const series = playSeries(teamA, teamB, rounds, fixtureSeed);

            const standingA = standings.get(teamA.id)!;
            const standingB = standings.get(teamB.id)!;

            standingA.matchWins += series.matchWinsA;
            standingA.matchLosses += series.matchWinsB;
            standingA.roundDiff += series.roundDiffA;
            standingB.matchWins += series.matchWinsB;
            standingB.matchLosses += series.matchWinsA;
            standingB.roundDiff -= series.roundDiffA;

            if (series.pointsA > series.pointsB) {
                standingA.standingPoints += 3;
                standingA.seriesWins += 1;
                standingB.seriesLosses += 1;
                standingA.headToHead.set(teamB.id, "win");
                standingB.headToHead.set(teamA.id, "loss");
            } else if (series.pointsB > series.pointsA) {
                standingB.standingPoints += 3;
                standingB.seriesWins += 1;
                standingA.seriesLosses += 1;
                standingA.headToHead.set(teamB.id, "loss");
                standingB.headToHead.set(teamA.id, "win");
            } else {
                standingA.standingPoints += 1;
                standingB.standingPoints += 1;
                standingA.seriesDraws += 1;
                standingB.seriesDraws += 1;
                standingA.headToHead.set(teamB.id, "draw");
                standingB.headToHead.set(teamA.id, "draw");
            }
        }
    }

    return standings;
}

// Sorts qualifying standings per TOURNAMENT.md's tie-breaker order. Head-to-head is applied
// per its exact rule ("when exactly two Teams remain tied") -- it's only consulted for a group
// that is precisely size 2 after Standing Points + Series wins; larger tied groups skip it and
// fall through to Match differential.
function rankStandings(standings: Map<string, Standing>): Standing[] {
    const all = [...standings.values()];

    const compareBase = (a: Standing, b: Standing): number =>
        b.standingPoints - a.standingPoints || b.seriesWins - a.seriesWins;

    const groups: Standing[][] = [];
    for (const standing of all) {
        const existingGroup = groups.find((group) => compareBase(group[0], standing) === 0);
        if (existingGroup) existingGroup.push(standing);
        else groups.push([standing]);
    }
    groups.sort((groupA, groupB) => compareBase(groupA[0], groupB[0]));

    const rankedGroups = groups.map((group) => {
        if (group.length === 2) {
            const [a, b] = group;
            const result = a.headToHead.get(b.id);
            if (result === "win") return [a, b];
            if (result === "loss") return [b, a];
        }
        return [...group].sort(
            (a, b) =>
                b.matchWins - b.matchLosses - (a.matchWins - a.matchLosses) ||
                b.roundDiff - a.roundDiff ||
                (a.tieBreakKey < b.tieBreakKey ? -1 : a.tieBreakKey > b.tieBreakKey ? 1 : 0),
        );
    });

    return rankedGroups.flat();
}

type PlayoffSeriesResult = {winnerId: string; loserId: string; pointsWinner: number; pointsLoser: number; decidedByTieBreak: boolean};

// Same best-of-three as qualifying, except a tied Series doesn't draw -- the higher seed
// (teamA, by convention here) advances, per TOURNAMENT.md's playoff tie rule.
function playPlayoffSeries(teamA: Team, teamB: Team, rounds: number, seed: bigint): PlayoffSeriesResult {
    const series = playSeries(teamA, teamB, rounds, seed);
    if (series.pointsA >= series.pointsB) {
        return {winnerId: teamA.id, loserId: teamB.id, pointsWinner: series.pointsA, pointsLoser: series.pointsB, decidedByTieBreak: series.pointsA === series.pointsB};
    }
    return {winnerId: teamB.id, loserId: teamA.id, pointsWinner: series.pointsB, pointsLoser: series.pointsA, decidedByTieBreak: false};
}

function findTeam(id: string): Team {
    const team = ROSTER.find((candidate) => candidate.id === id);
    if (!team) throw new Error(`unknown team id: ${id}`);
    return team;
}

export type TournamentResult = {
    ranked: Standing[]; // qualifying standings, seed 1 first
    playoffTeams: string[]; // the eligible top-N seeds that entered the playoff, seed order
    log: string[]; // human-readable line per playoff Series, in the order they were decided
    champion: string | null; // null only if the roster is empty -- never happens for ROSTER as configured
};

// Runs one full tournament (qualifying round robin, then the playoff bracket) and returns
// structured results instead of printing -- shared by main() (prints one tournament) and
// tournament-sweep.ts (runs many and aggregates). Keeping this print-free is what makes the
// sweep script cheap: it just calls this in a loop and tallies, no output parsing involved.
function runTournament(tournamentSeed: bigint, rounds: number): TournamentResult {
    const standings = runQualifying(tournamentSeed, rounds);
    const ranked = rankStandings(standings);
    const eligible = ranked.slice(0, 4);
    const log: string[] = [];

    if (eligible.length < 1) {
        return {ranked, playoffTeams: [], log: ["No eligible teams -- tournament aborts without a champion."], champion: null};
    }
    if (eligible.length === 1) {
        log.push(`${eligible[0].id} is Tournament Champion (sole eligible team, no playoff Fixture required).`);
        return {ranked, playoffTeams: [eligible[0].id], log, champion: eligible[0].id};
    }
    if (eligible.length === 2) {
        const final = playPlayoffSeries(findTeam(eligible[0].id), findTeam(eligible[1].id), rounds, hashSeed(tournamentSeed, "final"));
        log.push(`Final: seed1 (${eligible[0].id}) vs seed2 (${eligible[1].id}) -> ${final.pointsWinner}-${final.pointsLoser}${final.decidedByTieBreak ? " (tie -> higher seed advances)" : ""}`);
        return {ranked, playoffTeams: eligible.map((s) => s.id), log, champion: final.winnerId};
    }

    const bracket = eligible.length === 3 ? [null, [eligible[1], eligible[2]]] : [[eligible[0], eligible[3]], [eligible[1], eligible[2]]];

    const semifinalWinners: string[] = [];
    if (eligible.length === 3) {
        log.push(`seed1 (${eligible[0].id}) gets a bye to the final (only 3 eligible teams).`);
        semifinalWinners.push(eligible[0].id);
    }

    for (const pairing of bracket) {
        if (!pairing) continue;
        const [higherSeed, lowerSeed] = pairing;
        const seed = hashSeed(tournamentSeed, "semifinal", higherSeed.id, lowerSeed.id);
        const result = playPlayoffSeries(findTeam(higherSeed.id), findTeam(lowerSeed.id), rounds, seed);
        log.push(
            `Semifinal: ${higherSeed.id} vs ${lowerSeed.id} -> ${result.pointsWinner}-${result.pointsLoser}${result.decidedByTieBreak ? " (tie -> higher seed advances)" : ""} -- ${result.winnerId} advances`,
        );
        semifinalWinners.push(result.winnerId);
    }

    const [finalistA, finalistB] = semifinalWinners;
    const final = playPlayoffSeries(findTeam(finalistA), findTeam(finalistB), rounds, hashSeed(tournamentSeed, "final"));
    log.push(`Final: ${finalistA} vs ${finalistB} -> ${final.pointsWinner}-${final.pointsLoser}${final.decidedByTieBreak ? " (tie -> higher seed advances)" : ""}`);

    return {ranked, playoffTeams: eligible.map((s) => s.id), log, champion: final.winnerId};
}

function main() {
    const tournamentSeed = BigInt(process.argv[2] ?? "8675309");
    const rounds = Number(process.argv[3] ?? 300);

    console.log(`=== Qualifying: complete round robin, ${ROSTER.length} teams, best-of-three Series, ${rounds}-round Matches ===\n`);
    const result = runTournament(tournamentSeed, rounds);

    const standingsRows = result.ranked.map((s, index) => [
        index + 1,
        s.id,
        s.standingPoints,
        `${s.seriesWins}-${s.seriesDraws}-${s.seriesLosses}`,
        `${s.matchWins}-${s.matchLosses}`,
        s.roundDiff >= 0 ? `+${s.roundDiff}` : `${s.roundDiff}`,
    ]);
    printTable(["Seed", "Team", "StandingPts", "SeriesW-D-L", "MatchW-L", "RoundDiff"], standingsRows);

    console.log(`\n=== Playoffs: top ${result.playoffTeams.length} seeds ===\n`);
    for (const line of result.log) console.log(line);
    console.log(`\nTournament Champion: ${result.champion}`);
}

// Only run main() when this file is the actual entrypoint (`node tournament.ts`), not when
// tournament-sweep.ts imports runTournament/ROSTER/printTable from it.
if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
    main();
}

export {runTournament};
