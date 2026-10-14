# Vancouver geography for a room hunt

Distances below are to an example anchor, **VPL Central Branch, 350 W Georgia St**
(Stadium-Chinatown and Granville stations). Recompute everything for a different
anchor, and again when a job's office becomes the anchor.

## Fare zones

**The whole City of Vancouver is Zone 1**, including Commercial Drive, Main St, all
of East Van, Kitsilano, Marpole, Kerrisdale and UBC. That is the fact that most often
changes the answer: nobody needs to live downtown to stay in Zone 1, and the cheaper
eastern neighbourhoods carry no fare penalty.

**Zone 2** is Burnaby, New Westminster, Richmond, North and West Vancouver. **Zone 3**
is south and east of the Fraser (Surrey, Delta, Langley, White Rock) plus Maple Ridge,
Pitt Meadows and Port Coquitlam. Verify the Coquitlam and Port Moody boundary before
quoting. Boundary Rd, the Zone 1 and 2 line, runs at about longitude -123.0236.

- **Buses are always one zone**, however far they go.
- **Weekdays after 18:30 and all weekend, every trip is a Zone 1 fare.**
- A Zone 1 pass travelling into Zone 2 pays the difference at the exit gate; a Zone 2
  pass covers Zone 1.

## Walking radius: 35 minutes, about 2.5 km

Measured on a walking router to VPL Central in 2026-09:

| Area | Walk |
|---|---|
| Downtown, Yaletown | 8 to 15 min |
| Gastown | 10 to 15 min (the Downtown Eastside on its east edge) |
| Coal Harbour (W Georgia and Bute) | about 19 min |
| Station Place, Main St near the station | about 21 min |
| West End (Nelson and Denman) | 31 to 32 min |
| Fairview (Birch St) | about 42 min, past the radius |
| Olympic Village (W 1st) | about 54 min, past the radius |

The West End route runs along Robson or Georgia, commercial and lit, and does not
pass through the Downtown Eastside. That, more than the price, is why the West End
beats Gastown for a walkable room.

## Safety: block numbers, not neighbourhood names

**The area to avoid is about ten blocks, not a district**: E Hastings 100 to 1400
blocks (Main St to roughly Clark Dr) and the Oppenheimer Park area. This is the
Downtown Eastside: concentrated poverty, homelessness, open drug use, an overdose
crisis. Cheap "downtown" rooms cluster here, so check the cross-street. Also take
care at the north end of Commercial Drive near Hastings; south of Venables is a
different street.

**Not the Downtown Eastside, despite the names:** Hastings-Sunrise (Nanaimo St to
Boundary Rd, 3 to 4 km east, houses and families) and "East Vancouver" in general,
which is everything east of Main; Commercial Drive, Kensington, Renfrew and
Collingwood are separate neighbourhoods.

Be accurate in both directions. Violent crime against strangers is rare in
Vancouver, including near the Downtown Eastside; what is there is the environment,
not the odds of being attacked. Property crime is genuinely higher on the east side.
And "I don't want to walk past that every day" needs no defence: price the
alternative instead of arguing statistics.

## Observed room prices, 2026-09-04

From 230 Craigslist listings on one morning. A snapshot: re-fetch rather than reuse.

| Area | Observed | Common | To anchor | Character |
|---|---|---|---|---|
| West End, Downtown | CAD 920 to 1,500 | 1,200 | walk 20 to 35 min | walkable, but the median is high |
| Yaletown | 1,390 and up | | walk 10 min | |
| Commercial Drive | 800 to 1,100 | 800 to 900 | SkyTrain about 20 min | thick inventory, groceries |
| Joyce, Rupert, Renfrew, 29th Ave | 630 to 985 | 820 to 900 | 15 to 30 min | cheapest Zone 1 on SkyTrain |
| Marpole, Oakridge, Langara | 650 to 1,100 | 800 to 960 | Canada Line about 30 min | quiet, Korean groceries |
| Kitsilano | 750 to 1,300 | 900 to 1,050 | bus about 25 min | no SkyTrain |
| UBC, Dunbar, Kerrisdale | 600 to 1,250 | 800 to 950 | bus 40 min and up | priced for students |
| Gastown, Chinatown | 925 to 950 | | walk 10 to 15 min | check the block |
| Burnaby | 780 to 1,100 | | Zone 2 | needs to be about CAD 40 cheaper to break even |

Only West End rooms at or under about CAD 1,000 beat the eastern Zone 1 options, while
a Commercial Drive room at 800 plus a pass totals less than a 920 West End room plus
rain fares. Theory favours walkable; the market favoured eastern Zone 1. Check both on
totals.

## SkyTrain reach: Zone 1 is not "on the train"

- **Fraser St, Kensington, Sunset** (Fraser and 37th to 49th): bus 8 only, about 2 km to
  a station. Thick, cheap inventory, every one of them a bus commute.
- **Hastings east of Clark**: the R5 RapidBus, about 20 minutes downtown, no station
  within 2.5 km. Fine for safety; the cheapest rooms of the sweep sat here.
- **Kitsilano, Kerrisdale, Marpole west of Cambie**: buses, or a 35-minute walk over the
  Burrard Bridge.

RapidBus lines (R5 on Hastings, R4 on 41st, 99 B-Line on Broadway) are frequent,
limited-stop services whose door-to-door time is close to SkyTrain; local routes are
not. Check with `scripts/stations.py <lat> <lon>`. Station-side clusters that passed a
"SkyTrain" rule in 2026-09: Joyce and 29th Ave, Nanaimo, Renfrew and Rupert, Oakridge
and Langara on the Canada Line, Commercial, and in Zone 2 the 22nd St station houses in
New Westminster.

## UBC as an anchor

UBC's Irving K. Barber Learning Centre has over 1,500 study seats (against about 1,200
in the whole of VPL Central), is open 06:00 to 24:00 every day, is open to the public,
and allows video calls outside two quiet rooms, so an interview can be taken there.
The catch is that UBC has no SkyTrain: downtown is the 99 B-Line or R4, about 40 to 50
minutes. A room within a 35-minute walk of the centre can be scored as walkable if the
day is anchored there; about 8 downtown round trips a month stay under the pass price.
In practice the UBC area rarely beat the same money elsewhere, but it is not off the map.

## Where the jobs are

Vancouver tech is spread across downtown, Yaletown and Gastown, Mount Pleasant, and
Burnaby (Metrotown and Brentwood). A renter who cannot know the office yet should keep
the term short.
