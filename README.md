# League Links

League Links is a free rugby league player-connections site.

## Live site

https://fedfinmike.github.io/league-links/

## What people can do

- Search a player and see teammates ranked by games together.
- Click any teammate to open that player's page.
- Open shared history to see when and where two players played together.
- Find the shortest connection between any two players.
- Browse NRL and State of Origin teams by season.
- Choose international teams including Australia, New Zealand, Tonga, Samoa, Fiji, Cook Islands, Papua New Guinea and other nations.

## Current coverage

NRL 2000–2026 and State of Origin 2000–2026 are included in the live player network using match-confirmed player appearances. The 2026 NRL season is an in-season snapshot.

International teams are now first-class choices in the Teams section. Their team-player catalogues are being populated separately from the confirmed-game network. A national squad or career summary does not create a teammate link. International teammate links will be added only from match-confirmed appearances.

The next historical layers are international match histories, NSW Cup, Queensland Cup, NYC/Jersey Flegg, SG Ball, Harold Matthews where the age is U17 or older, Mal Meninga, Cyril Connell from its U17 era, Queensland Colts/U20/U21 and other representative teams. NSW Cup and Queensland Cup will be taken back toward 2000 where reliable source coverage supports it.

## Counting rule

Two players are counted as teammates only when both are recorded for the same team in the same match. A squad list or club list on its own does not count as a game together.

## Design

v0.24 uses a deep Pacific navy, sea-glass teal and warm sand palette. The public interface is deliberately simple: Home, Players, Connect, Teams and Competitions.

## Commercial approach

League Links is intended to remain free. The product design allows for a small number of clearly labelled advertisements rather than subscriptions or paywalls. Ads should never cover content, interrupt searches or block player navigation.

## Data delivery

A GitHub Actions job prepares one compressed data file for the public site. The browser uses that prepared file first and only rebuilds from the public source files if the prepared file is unavailable.
