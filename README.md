# League Links

League Links is a free rugby league player-connections site.

## Live site

https://fedfinmike.github.io/league-links/

## What people can do

- Search a player and see teammates ranked by games together.
- Click any teammate to open that player's page.
- Open shared history to see when and where two players played together.
- Find the shortest connection between any two players.
- Browse a team by competition and season.

## Current coverage

NRL 2008–2026 and State of Origin 2008–2026 are included in the live player network. The 2026 NRL season is an in-season snapshot.

The next historical layers are NSW Cup, Queensland Cup, NYC/Jersey Flegg, SG Ball, Harold Matthews where the age is U17 or older, Mal Meninga, Cyril Connell from its U17 era, Queensland Colts/U20/U21 and other representative teams.

## Counting rule

Two players are counted as teammates only when both are recorded for the same team in the same match. A squad list or club list on its own does not count as a game together.

## Commercial approach

League Links is intended to remain free. The product design allows for a small number of clearly labelled advertisements rather than subscriptions or paywalls. Ads should never cover content, interrupt searches or block player navigation.

## Data delivery

A GitHub Actions job prepares one compressed data file for the public site. The browser uses that prepared file first and only rebuilds from the public source files if the prepared file is unavailable.
