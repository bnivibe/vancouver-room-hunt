# Checking an address, a building and a landlord

Free or cheap public records that each changed the reading of a real listing.
Run them when an address arrives, not after the viewing.

## BC Assessment: what the building actually is

Free, no login. Search by address, then open the property page (readable in a
browser; the JSON search returns the id):

```
https://www.bcassessment.ca/Property/Search/GetByAddress?addr=<address>
https://www.bcassessment.ca/Property/Info/<id>
```

Unit-level addresses work in the form `201-<number> <STREET> VANCOUVER`. The page
gives year built, storeys, bedroom and bathroom counts, floor areas for the first,
second and basement levels, the PID, the legal description, and notes such as
"Property has more than one structure" or "Property details are for main building
only" (a laneway house is not counted).

What it settled in practice:

- **Headcount.** Three listings in one day each held more people than the ad
  implied, and one had a second structure the ad never mentioned.
- **Size.** Divide a level's area by its bedrooms, subtract kitchen, living,
  hall, stairs and baths: on a four-bedroom level of about 1,200 sq ft the bedrooms
  land around 120 to 170 sq ft, which a queen bed (33 sq ft) and a desk nearly fill.
  Compare with the renter's current place: much more floor area per bedroom leaves
  room for a hall between rooms instead of shared walls on three sides.
- **Basement or not.** A one-storey house with a finished basement and the owner on
  the main floor puts a "ground floor" room below grade with the owner overhead.
- **Strata or freehold.** "STRATA LOT n, PLAN EPS/LMS/NWS..." is a strata; "LOT n,
  PLAN NWP..." is a freehold lot. A second model's review once built its first section
  on strata rules (fobs, move-in fees, concierge) for a freehold house.
- BC Assessment's public search does **not** show owner names.

## LTSA title search: who owns it

The only official record of a BC owner's name. About CAD 15 all in when used in
2026-09 (the title fee was CAD 11.06 on the schedule of 2026-04-01, plus a service
charge and tax; check ltsa.ca for the current schedule), through a single-user LTSA
Explorer account or by mail. It needs the nine-digit PID (from BC Assessment or
ParcelMap BC); it cannot be searched by address, phone or email.

Flow: PID, then Search records, tick only the Title row, choose "Show Current and
Cancelled Charges" (same price, more information), pay. Items download from the
Inbox and **the link expires after 7 days**, so archive the PDF the same day. A title
shows registered owners, the legal description, the owner's mailing address and
registered charges (mortgages, liens, notices); no phone numbers, no past owners.

**It earns its fee by catching the name.** One title came back with a different
given name from the person about to be paid. Everything else was clean (owner's
address is the property, held for years, one bank mortgage, no notations, no liens),
and the answer was ordinary: a spouse on title alone. It still had to be closed
before money moved, with one non-accusatory question ("the title shows X, is that
family? whose name goes on the agreement?"), and then three names had to line up:
the registered owner, the landlord on the agreement, and the e-Transfer recipient.

At a viewing, match photo ID against a document tying that name to that address
(property tax notice, a utility bill, the title). If the person is a tenant, ask for
their own tenancy agreement and the landlord's written consent to sublet.

## Crime data (City of Vancouver only)

VPD publishes one zip per neighbourhood per year:

```
https://geodash.vpd.ca/opendata/crimedata_download/<Neighbourhood>_<YYYY>/crimedata_csv_<Neighbourhood>_<YYYY>.zip
```

(An all-years bulk file existed earlier in 2026-09 and later returned 404; a POST to
the open-data page returns 405.) Columns are TYPE, YEAR, MONTH, DAY, HOUR, MINUTE,
HUNDRED_BLOCK, NEIGHBOURHOOD, X, Y, with X and Y in **UTM zone 10N metres**; project
the address with a zone-10 forward transform and count by radius (200 m and 400 m),
not by neighbourhood totals. Report the per-year trend, the share in the evening
hours, and a previously measured address as a benchmark.

**Say the limits every time.** VPD zeroes the coordinates of offences against a
person, so a radius count answers "how much theft happens here", never "is it safe to
walk at night", and VPD itself says not to judge a specific location with it. Burnaby
is policed by the RCMP and publishes nothing comparable.

Which local area a point is in:

```
https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/local-area-boundary/records?select=name&where=intersects(geom,geom'POINT(<lon> <lat>)')
```

The city's `business-licences` dataset can be checked for a rooming-house licence,
but an absence proves nothing.

**Pair it with the actual sunset.** "Is a 7pm walk dark?" is a fact: on one
September evening sunset was 19:15 and civil twilight ended 19:46.

## Walking time

```
https://routing.openstreetmap.de/routed-foot/route/v1/driving/<lon>,<lat>;<lon>,<lat>?overview=false
```

Keep `/driving/` after `routed-foot`; a `/foot/` segment returns InvalidQuery. Use
curl if a language's TLS stack fails the handshake. Walking minutes, not straight
lines, decide whether a room is "walkable".

## Weekday transit time

Google Maps directions with a fixed departure open without login:

```
https://www.google.com/maps/dir/<from>/<to>/data=!4m6!4m5!2m3!6e0!7e2!8j<epoch>!3e3?hl=en
```

`<epoch>` is the local wall-clock time written as if it were UTC. The page text lists
every route with minutes and route numbers; `!4m2!4m1!3e2` gives walking. **Check the
boarding station's zone**: the fastest route from one address boarded in Zone 2 when
walking to a Zone 1 station took the same minutes and saved about CAD 40 a month.
A keyless multi-stop link for the day of the viewings:
`https://www.google.com/maps/dir/?api=1&origin=...&waypoints=...&destination=...&travelmode=transit`.

## Rail noise and amenities (OpenStreetMap Overpass)

```
way["railway"~"subway|light_rail|rail"](around:900,<lat>,<lon>);out geom tags;
way["building"](around:40,<lat>,<lon>);out geom;
nwr["shop"="supermarket"](around:900,<lat>,<lon>);out center tags;
```

POST to `https://overpass-api.de/api/interpreter` with a User-Agent header (it
returns 406 without one); `overpass.kumi.systems` is a mirror when the main endpoint
errors. Measure point-to-segment from the building footprint to the track;
`bridge=yes` is elevated. Arterials (Kingsway, Hastings) and rooftop plant belong in
the same check. Nominatim geocoding needs a User-Agent and about one request a second.

## Fares

TransLink's fare table is in `window.FARE_CALCULATOR__INITDATA` on the
pricing-and-fare-zones page at www.translink.ca. As of 2026-07-01: stored value
1 zone 2.85, 2 zones 4.20, 3 zones 5.40, day pass 12.55. Monthly passes run the
calendar month with no proration; next month's loads from the 16th.

## Tour videos

A YouTube link in a listing: `https://www.youtube.com/oembed?url=<video>&format=json`
gives title and channel with no key, and `https://i.ytimg.com/vi/<id>/hq1.jpg`
(also `hq2`, `hq3`, `maxresdefault`) gives frames to match against the listing photos.
One title named the street the ad had left out.

## Tenancy-dispute records

openroom.ca indexes tribunal and court orders by name and address, mostly Ontario,
and needs an account (the renter signs up and searches; never create it for them). A
clean result proves little: deposit-and-vanish scams rarely produce an order. CanLII
shows a bot check to automated browsers (do not solve it), and the CRT decision search
did not render in a browser pane, so neither worked for an address search.
