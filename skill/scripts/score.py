#!/usr/bin/env python3
"""Score a Vancouver room on what it really costs per month.

Rent is not the price of a room. The price is rent + utilities + the transit
pass its address forces, plus any furniture you have to buy for it. Compared
on rent alone, the ranking flips often enough that this total is the single
most useful number in a room search.

Usage
-----
    python3 score.py --rent 900 --transit zone1
    python3 score.py --rent 950 --transit walk
    python3 score.py --rent 850 --transit zone2 --utilities 60
    python3 score.py --rent 800 --transit bus --furniture 400 --stay 6
    python3 score.py --batch listings.json
    python3 score.py --batch listings.json --budget budget.json

Transit modes
-------------
    walk   the daily anchor is a walk of 35 minutes or less, so no pass;
           only rain-day and weekend single fares
    bus    the commute is bus only; buses ignore zones, so a 1-zone pass
    zone1  SkyTrain inside the City of Vancouver
    zone2  SkyTrain from Burnaby, New Westminster, Richmond, the North Shore
    zone3  SkyTrain from Surrey, Delta, Langley, the Tri-Cities edge

Batch file: a JSON list with the same keys as the flags, for example
    [{"label": "A", "rent": 800, "transit": "zone1", "utilities": "included"},
     {"label": "B", "rent": 950, "transit": "walk"}]

Budget file (optional): adds a runway projection so each room shows its effect
on your balance at a horizon date, with and without a job. See
examples/budget.example.json for every key.
"""
import argparse
import json
import sys

# translink.ca, checked 2026-09-10. Fares rise every July 1: re-check before
# quoting a number someone will act on. A monthly pass limits zones on SkyTrain
# and SeaBus only; buses are unlimited across all zones on any pass.
FARES_CHECKED = "2026-09-10"
TRANSIT = {
    "walk": 50.0,      # about 17 single fares a month for rain days and weekends
    "bus": 117.20,
    "zone1": 117.20,
    "zone2": 156.70,
    "zone3": 211.65,
}
UTILITIES_DEFAULT = 60.0   # typical share when utilities are billed separately
FURNITURE_STAY_DEFAULT = 6  # months over which a furniture purchase is spread


def parse_utilities(value):
    """'included' (or similar) means zero; anything else is a monthly amount."""
    if value is None:
        return 0.0
    text = str(value).strip().lower()
    if text in ("included", "inc", "incl", "yes", "y", "true", "0", ""):
        return 0.0
    if text in ("separate", "extra", "no", "n", "false"):
        return UTILITIES_DEFAULT
    return float(text)


def resolve(item, fares=None):
    """Turn one listing (flags or batch row) into the numbers the score needs."""
    fares = dict(TRANSIT, **(fares or {}))
    mode = str(item.get("transit", "zone1")).lower()
    if item.get("walk"):
        mode = "walk"
    if mode not in fares:
        sys.exit(f"transit must be one of {', '.join(fares)} (got {mode!r})")
    furniture = float(item.get("furniture", 0) or 0)
    stay = int(item.get("stay", FURNITURE_STAY_DEFAULT) or FURNITURE_STAY_DEFAULT)
    return dict(
        label=str(item.get("label", "")),
        rent=float(item["rent"]),
        transit_mode=mode,
        transit=fares[mode],
        utilities=parse_utilities(item.get("utilities", "included")),
        furniture=furniture / stay if furniture else 0.0,
        furniture_once=furniture,
    )


def monthly_total(room):
    return room["rent"] + room["transit"] + room["utilities"] + room["furniture"]


def _months(start, end):
    """Inclusive list of (year, month) from 'YYYY-MM' to 'YYYY-MM'."""
    y, m = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _ym(text):
    return tuple(map(int, text.split("-"))) if text else None


def runway(room_cost, budget, job_start="default", furniture_once=0.0):
    """Month-by-month balance. Returns (balance at horizon, lowest balance, first month below zero).

    Spending is the room's monthly cost (rent, transit, utilities) plus everything
    else the budget lists; furniture is paid once, in the first month. Income
    arrives from job_start (a 'YYYY-MM' string, or None for no job).
    """
    if job_start == "default":
        job_start = budget.get("job_start")
    start, horizon = budget["start"], budget["horizon"]
    other = float(budget.get("other_monthly", 0))
    income = float(budget.get("monthly_income", 0))
    one_off = {_ym(k): float(v) for k, v in budget.get("one_off", {}).items()}
    job = _ym(job_start)
    bal = float(budget["savings"])
    low, broke = bal, None
    for n, t in enumerate(_months(start, horizon)):
        bal -= room_cost + other + one_off.get(t, 0.0) + (furniture_once if n == 0 else 0.0)
        if job and t >= job:
            bal += income
        if bal < low:
            low = bal
        if bal < 0 and broke is None:
            broke = f"{t[0]}-{t[1]:02d}"
    return bal, low, broke


def score(room, budget=None):
    total = monthly_total(room)
    out = dict(room, total=total)
    if budget:
        base = resolve(budget["baseline"], budget.get("fares")) if budget.get("baseline") else None
        cost, once = total - room["furniture"], room["furniture_once"]
        out["job"] = runway(cost, budget, furniture_once=once)
        out["no_job"] = runway(cost, budget, job_start=None, furniture_once=once)
        if base:
            base_cost = monthly_total(base) - base["furniture"]
            out["delta"] = out["job"][0] - runway(base_cost, budget, furniture_once=base["furniture_once"])[0]
    return out


def money(x):
    return ("" if x >= 0 else "-") + f"CAD {abs(x):,.0f}"


def render(s, budget=None):
    head = f"  {s['label']}" if s["label"] else ""
    print(f"\n- rent {money(s['rent'])} | transit {s['transit_mode']} {s['transit']:.2f}"
          f" | utilities {s['utilities']:.0f}{head}")
    if s["furniture"]:
        print(f"  furniture spread {s['furniture']:.0f}/month")
    print(f"  monthly total      {money(s['total'])}")
    if budget:
        horizon = budget["horizon"]
        for name, key in (("job from " + str(budget.get("job_start")), "job"), ("no job", "no_job")):
            bal, low, broke = s[key]
            line = f"  {name:<18} at {horizon} {money(bal):>12}   lowest {money(low):>12}"
            if broke:
                line += f"   below zero from {broke}"
            print(line)
        if "delta" in s:
            word = "better" if s["delta"] > 0 else ("same" if s["delta"] == 0 else "worse")
            print(f"  vs baseline room   {money(s['delta'])} at {horizon} ({word})")
            income = float(budget.get("monthly_income", 0))
            if income and abs(s["delta"]) >= 0.15 * income:
                print(f"                     = {abs(s['delta']) / income:.1f} months of income")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rent", type=float, help="monthly rent, CAD")
    p.add_argument("--transit", default="zone1", help="walk, bus, zone1, zone2 or zone3 (default zone1)")
    p.add_argument("--walk", action="store_true", help="shorthand for --transit walk")
    p.add_argument("--utilities", default="included", help="'included' (default), 'separate', or a monthly amount")
    p.add_argument("--furniture", type=float, default=0, help="one-off furniture cost for an unfurnished room")
    p.add_argument("--stay", type=int, default=FURNITURE_STAY_DEFAULT, help="months to spread furniture over")
    p.add_argument("--batch", help="JSON list of listings; printed cheapest total first")
    p.add_argument("--budget", help="JSON budget for the runway projection")
    a = p.parse_args(argv)
    if not (a.batch or a.rent):
        p.error("give --rent or --batch")

    budget = load(a.budget) if a.budget else None
    fares = (budget or {}).get("fares")
    print(f"fares checked {FARES_CHECKED} at translink.ca; re-check after July 1")
    if a.batch:
        items = [resolve(i, fares) for i in load(a.batch)]
    else:
        items = [resolve(dict(rent=a.rent, transit=a.transit, walk=a.walk, utilities=a.utilities,
                              furniture=a.furniture, stay=a.stay), fares)]
    scored = [score(i, budget) for i in items]
    for s in sorted(scored, key=lambda x: x["total"]):
        render(s, budget)
    return 0


if __name__ == "__main__":
    sys.exit(main())
