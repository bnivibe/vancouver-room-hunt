#!/usr/bin/env python3
"""Nearest SkyTrain station for a coordinate: the "is it really on the train" check.

A Zone 1 address can still be bus-only (Fraser St, Hastings east of Clark,
Kitsilano), and listing neighbourhood labels hide that. Feed it the lat/lon from
a posting's map pin, or a batch file of rows.

    python3 stations.py 49.2359 -123.1166            # Oakridge-41st  0.29 km  ok
    python3 stations.py rows.json                     # [{"id", "lat", "lon"}, ...]
    python3 stations.py 49.25 -123.05 --ok-km 0.9     # stricter walking radius

Straight-line distance, so it understates the walk; use a routing service for
the real minutes (see references/checks.md). Craigslist pins with
data-accuracy 22 or more are neighbourhood centroids, not the house: use the
cross-street in the text instead. Station list is all 53 stations of the Expo,
Millennium and Canada Lines as of 2026-10; the Broadway Subway extension is not
included until it opens.
"""
import argparse
import json
import math
import sys

STATIONS = {
    "Waterfront": (49.2856, -123.1117), "Burrard": (49.2856, -123.1200), "Granville": (49.2833, -123.1163),
    "Stadium-Chinatown": (49.2794, -123.1094), "Main St-Science World": (49.2733, -123.1002),
    "Commercial-Broadway": (49.2626, -123.0690), "Nanaimo": (49.2483, -123.0560), "29th Ave": (49.2443, -123.0462),
    "Joyce-Collingwood": (49.2383, -123.0318), "Patterson": (49.2299, -123.0126), "Metrotown": (49.2258, -123.0039),
    "Royal Oak": (49.2202, -122.9884), "Edmonds": (49.2122, -122.9592), "22nd St": (49.2000, -122.9490),
    "New Westminster": (49.2014, -122.9127), "Columbia": (49.2048, -122.9059), "VCC-Clark": (49.2659, -123.0790),
    "Renfrew": (49.2588, -123.0453), "Rupert": (49.2609, -123.0329), "Gilmore": (49.2650, -123.0135),
    "Brentwood": (49.2665, -123.0017), "Holdom": (49.2648, -122.9820), "Sperling": (49.2593, -122.9640),
    "Lake City": (49.2555, -122.9392), "Production Way": (49.2534, -122.9182), "Lougheed": (49.2484, -122.8970),
    "Vancouver City Centre": (49.2820, -123.1187), "Yaletown-Roundhouse": (49.2745, -123.1216),
    "Olympic Village": (49.2664, -123.1157), "Broadway-City Hall": (49.2630, -123.1148),
    "King Edward": (49.2491, -123.1157), "Oakridge-41st": (49.2333, -123.1166), "Langara-49th": (49.2264, -123.1163),
    "Marine Drive": (49.2096, -123.1166), "Bridgeport": (49.1966, -123.1275),
    # Expo Line east of Columbia and in Surrey, the Millennium Line's Evergreen section, the
    # Canada Line's Richmond and airport branches (OpenStreetMap via Nominatim, 2026-10-14).
    "Sapperton": (49.2246, -122.8895), "Braid": (49.2331, -122.8828), "Scott Road": (49.2044, -122.8741),
    "Gateway": (49.1991, -122.8506), "Surrey Central": (49.1895, -122.8479), "King George": (49.1828, -122.8447),
    "Burquitlam": (49.2614, -122.8899), "Moody Centre": (49.2779, -122.8455), "Inlet Centre": (49.2772, -122.8277),
    "Coquitlam Central": (49.2749, -122.8009), "Lincoln": (49.2804, -122.7940),
    "Lafarge Lake-Douglas": (49.2855, -122.7917), "Aberdeen": (49.1840, -123.1363), "Lansdowne": (49.1746, -123.1365),
    "Richmond-Brighouse": (49.1681, -123.1363), "Templeton": (49.1967, -123.1465),
    "Sea Island Centre": (49.1930, -123.1580), "YVR-Airport": (49.1943, -123.1783),
}


def haversine_km(a, b):
    r = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def nearest(lat, lon):
    name, point = min(STATIONS.items(), key=lambda kv: haversine_km((lat, lon), kv[1]))
    return name, haversine_km((lat, lon), point)


def verdict(km, ok_km=1.3, long_km=1.8):
    """Default radii: about a 15-minute walk is ok, 1.3 to 1.8 km is long, beyond that a bus to the station."""
    return "ok" if km <= ok_km else ("long walk" if km <= long_km else "bus to station")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("where", nargs="+", help="LAT LON, or one JSON file of rows")
    ap.add_argument("--ok-km", type=float, default=1.3)
    ap.add_argument("--long-km", type=float, default=1.8)
    a = ap.parse_args(argv)
    if len(a.where) == 2:
        name, km = nearest(float(a.where[0]), float(a.where[1]))
        print(f"{name}  {km:.2f} km  {verdict(km, a.ok_km, a.long_km)}")
    elif len(a.where) == 1:
        with open(a.where[0], encoding="utf-8") as f:
            rows = json.load(f)
        for row in rows:
            if row.get("lat") and row.get("lon"):
                name, km = nearest(float(row["lat"]), float(row["lon"]))
                print(f"{row.get('id', '')}  {name:22s} {km:.2f} km  {verdict(km, a.ok_km, a.long_km)}")
            else:
                print(f"{row.get('id', '')}  no coordinates")
    else:
        ap.error("give LAT LON or a JSON file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
