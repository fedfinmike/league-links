# League Links

**Every career is a network.**

League Links is an interactive rugby league player-connections product. It lets users explore exact teammate relationships, season-by-season shared playing history, shortest player-to-player connection paths, and club-season appearance rosters.

## Live prototype

https://fedfinmike.github.io/league-links/

## Current public build — v0.22

The GitHub Pages prototype now includes:

- Dynamic Player Ledgers with every teammate name clickable
- Shared Playing History with season, club and games-together breakdowns
- Player career timelines
- Season filtering inside each teammate ledger
- Connection Finder with clickable path nodes and relationship strength
- Club & Season roster exploration
- Recent-player history and saved favourites stored in the browser
- Shareable player and connection URLs
- IndexedDB caching for much faster repeat visits
- Mobile-specific bottom navigation
- Data coverage and evidence-methodology screens
- Installable web-app metadata and League Links icon

## Evidence rule

A confirmed teammate relationship requires both players to appear for the same team in the same match. Squad membership, team-list-only selection, and same-season club overlap are not counted as games together.

The current public prototype derives its NRL spine from the public `uselessnrlstats` dataset for 2008–2026. The 2026 season is treated as a current-season partial snapshot. Third-party source licensing and terms should be reviewed before a commercial production release.

## Version safety

The pre-v0.22 public prototype has been preserved on the `v21-backup` branch so the live app can be rolled back if required.
