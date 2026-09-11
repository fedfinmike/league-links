# League Links

League Links is a free rugby league player-connections site.

## Live site

https://fedfinmike.github.io/league-links/

## The database we are building

League Links is intended to become one connected rugby league record from **U17 pathways through state cups, NRL, State of Origin and international football**, with history built from **2000 onward wherever reliable records exist**.

The database is being assembled in two layers:

- **Teams first:** competitions and teams are mapped so people can browse the structure of the game.
- **Players match by match:** player appearances are then added from confirmed matches. Only those match records create teammate links, shared-history totals and connection paths.

This means a team can appear in League Links before its full player history is complete, without ever treating a squad list as a played game.

## What people can do

- Search a player and see teammates ranked by games together.
- Click any teammate to open that player's page.
- Open shared history to see when and where two players played together.
- Find the shortest connection between any two players.
- Browse mapped teams from U17 pathways through NRL and representative football.
- Choose international teams including Australia, New Zealand, Tonga, Samoa, Fiji, Cook Islands, Papua New Guinea and other nations.

## Current match-confirmed coverage

NRL 2000–2026 and State of Origin 2000–2026 are included in the live player network using match-confirmed player appearances. The 2026 NRL season is an in-season snapshot.

## Team directory now mapped

The 2026 team directory now includes NRL, State of Origin, international teams, NSW Cup, Queensland Cup, Jersey Flegg, SG Ball, Harold Matthews, Mal Meninga and Cyril Connell. Historical Queensland Colts/U20/U21 and other representative structures are the next mapping layers.

International and lower-grade team directories are kept separate from teammate counts until player-in-match records are confirmed.

## Historical build order

The next major player-history layers are NSW Cup and Queensland Cup, then Jersey Flegg/NYC, SG Ball, Harold Matthews in U17+ seasons, Mal Meninga, Cyril Connell, Queensland Colts/U20/U21, international match histories and other representative teams. The target is to work back toward 2000 wherever the competition existed at U17 or older and reliable sources are available.

## Counting rule

Two players are counted as teammates only when both are recorded for the same team in the same match. A squad list or club list on its own does not count as a game together.

## Design

v0.25 uses a deep Pacific navy, sea-glass teal and warm sand palette. The public interface is deliberately simple: Home, Players, Connect, Teams and Competitions.

## Commercial approach

League Links is intended to remain free. The product design allows for a small number of clearly labelled advertisements rather than subscriptions or paywalls. Ads should never cover content, interrupt searches or block player navigation.

## Data delivery

A GitHub Actions job prepares one compressed data file for the public site. The browser uses that prepared file first and only rebuilds from the public source files if the prepared file is unavailable.
