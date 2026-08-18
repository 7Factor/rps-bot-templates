// Runs tournament.ts's simulation many times under different seeds and aggregates how each
// team actually fares across the distribution -- a single tournament.ts run is one draw from a
// random process (fixture ordering doesn't matter since it's round robin, but every Series/Match
// still has its own seeded RNG), so one run can flatter or shortchange a team by luck. This
// answers "how often does each team make the playoffs / win it all", not "what happened once".
//
// Usage: node --experimental-transform-types .local-dev/tournament-sweep.ts [tournaments] [rounds] [baseSeed]

import {runTournament, ROSTER, printTable} from "./tournament.ts";

const tournaments = Number(process.argv[2] ?? 50);
const rounds = Number(process.argv[3] ?? 300);
const baseSeed = BigInt(process.argv[4] ?? "8675309");

type Tally = {
    championships: number;
    playoffAppearances: number;
    rankSum: number; // sum of qualifying seed (1-indexed) across every tournament, for the average
    standingPointsSum: number;
};

const tallies = new Map<string, Tally>();
for (const team of ROSTER) {
    tallies.set(team.id, {championships: 0, playoffAppearances: 0, rankSum: 0, standingPointsSum: 0});
}

console.log(`Simulating ${tournaments} tournaments (${ROSTER.length} teams, ${rounds}-round Matches each)...`);

for (let i = 0; i < tournaments; i += 1) {
    const result = runTournament(baseSeed + BigInt(i), rounds);

    result.ranked.forEach((standing, index) => {
        const tally = tallies.get(standing.id)!;
        tally.rankSum += index + 1;
        tally.standingPointsSum += standing.standingPoints;
    });

    for (const teamId of result.playoffTeams) tallies.get(teamId)!.playoffAppearances += 1;
    if (result.champion) tallies.get(result.champion)!.championships += 1;
}

const rows = [...tallies.entries()]
    .sort(([, a], [, b]) => b.championships - a.championships || b.playoffAppearances - a.playoffAppearances)
    .map(([id, tally]) => [
        id,
        tally.championships,
        `${((tally.championships / tournaments) * 100).toFixed(1)}%`,
        tally.playoffAppearances,
        `${((tally.playoffAppearances / tournaments) * 100).toFixed(1)}%`,
        (tally.rankSum / tournaments).toFixed(1),
        (tally.standingPointsSum / tournaments).toFixed(1),
    ]);

console.log(`\n=== Results across ${tournaments} tournaments ===\n`);
printTable(
    ["Team", "Championships", "Championship%", "PlayoffApps", "PlayoffApp%", "AvgQualRank", "AvgStandingPts"],
    rows,
);
