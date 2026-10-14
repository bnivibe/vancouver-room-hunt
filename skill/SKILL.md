---
name: room-hunt
description: Search real Vancouver room-share listings across every live source, score each one on total monthly cost (rent + utilities + transit, not rent alone), verify the address and the landlord against public records, and rank the shortlist by its effect on the renter's budget. Use whenever the renter asks about finding a place (find me a room, room share, is this listing ok, which neighbourhood, is it safe, how far is it), pastes a listing or an address, asks about a viewing or a contract, or wonders whether to move. Also /room-hunt. The comparison rule is the whole point and is easy to get wrong: a Zone 2 room at CAD 900 costs about the same as a walkable room at CAD 1,000, because the transit pass moves with the address.
---

# Room Hunt

A housing scout for one renter looking for a room share in Metro Vancouver.
It finds listings, reads them properly, checks them against public records,
prices them on what they really cost, and keeps the record. **It never contacts
anyone, posts anything, joins anything or pays anything.** The renter does all
of that; this skill drafts and checks.

Rent is not the price of a room. **The price is rent + utilities + transit**,
and transit is decided by the address. Every recommendation is made on that
total, because comparing rent alone reverses the answer often enough that it
is the single most useful thing the skill does.

## 0. The profile comes first

Read `profile.md` next to this file. It holds what only the renter can say:
the daily anchor (library, campus, office), the move-in date, the term, the
knockouts, the ranking order, and where the budget file lives. Copy
`profile.example.md` to start one. **If it is missing or empty, ask the profile
questions in a few plain rounds and write the answers in before searching.**
Never commit `profile.md` anywhere public.

Treat every criterion with its date. Criteria move: in the search this skill
came from they were rewritten five times in two weeks, and an unsettled filter
applied as if it were final cost a day. When the renter says things have got
tangled, stop and re-ask; do not keep searching on yesterday's filter.

**Stated tolerance is not preference.** "I don't mind a long ride" meant "I
would put up with one for quiet", not "I want the suburbs": ten of the thirteen
places the renter had picked unprompted were on the downtown peninsula. Before
ranking, list what the renter has picked unprompted and check the ranking
against that pattern.

## 1. The comparison rule

| How the renter reaches the anchor | Monthly transit |
|---|---|
| Walks, 35 minutes or less (rain-day and weekend single fares only) | about CAD 50 |
| **Bus only, from anywhere in Metro Vancouver** | **CAD 117.20** |
| SkyTrain from Zone 1 (City of Vancouver) | CAD 117.20 |
| SkyTrain from Zone 2 (Burnaby, New West, Richmond, North Shore) | CAD 156.70 |
| SkyTrain from Zone 3 (Surrey, Delta, Langley, Maple Ridge, Port Coquitlam) | CAD 211.65 |

Checked at translink.ca on 2026-09-10. Fares rise every July 1; re-check before
quoting a number someone will act on.

- **A monthly pass limits zones on SkyTrain and SeaBus only. Buses are
  unlimited across every zone on any pass**, so a bus commute costs a 1-zone
  pass however far out the room is. Zone only prices the SkyTrain.
- **Walkable means a walking route of 35 minutes or less**, measured on a
  routing service (recipe in `references/checks.md`), not straight-line
  distance. Price it with no pass: a pass only breaks even at about 41 rides a
  month.
- **Utilities are worth about CAD 60 a month**, more than the gap between
  Zone 1 and Zone 2. A CAD 950 all-inclusive room beats a CAD 900 room with
  utilities billed separately. "Separate in the contract, but we haven't been
  billing" is not included: price what is written.
- **An unfurnished room costs a bed and a desk** (about CAD 300 to 500) plus
  disposal at move-out: on a six-month stay, CAD 50 to 80 a month on top.

So these rooms cost the renter roughly the same:

> walkable CAD 967 = Zone 1 or bus-from-anywhere CAD 900 = Zone 2 by SkyTrain CAD 861 = Zone 3 by SkyTrain CAD 806

When a job starts, the anchor becomes the office and every distance is
recomputed (a Burnaby office puts a downtown room on a Zone 2 pass). Tech jobs
here are spread across downtown, Mount Pleasant and Burnaby, which is the
argument for a short or month-to-month term while the office is unknown.

## 2. Pull every live source

Never quote rent from memory. Fetch it.

**A search covers every live source. Craigslist alone is not a search.** One
"what is new" run went out on Craigslist only; running the other sources
afterwards immediately found rooms Craigslist did not have, including the
male-only posts that only ever appear on the Korean boards. **Each source holds
inventory the others do not.** End every batch with a coverage line naming each
source, what it returned and what blocked it, so a gap is visible.

**Facebook groups are part of every search.** They are slow to read, and three
runs in a row once skipped them for that reason; the same night they turned up
a private-bathroom condo room no other source had, and proved a shortlisted
room was women-only. Budget about 20 minutes for them.

`references/sources.md` has the full audit of fifteen sources with URL patterns,
selectors, APIs and rate limits. The short version:

| Source | Why |
|---|---|
| Facebook Marketplace | Best structured data: exact address, bed and bath counts, **how many people already live there**, availability date. Needs a logged-in browser. |
| Craigslist (`van`, `bnc`, `rch`, `nvn`, `pml`, `rds` /roo) | Deepest inventory. Watch the rate limit. |
| UvanU (Daum cafe) | Fastest turnover of any source; Korean. JSON list API needs no login. |
| Kijiji | Neighbourhood-level locations; liveness from page state. |
| Facebook groups | Posts that reach Craigslist late or never. Read only, through the renter's own membership. |
| Naver cafes | Korean working-holiday boards. `scripts/naver_cafe.py` reads titles with no login. |
| Vanchosun, Rentals.ca | Smaller; Rentals.ca carries private-bathroom rooms cheaper than Craigslist's tier. |
| liv.rent | Whole units only. Use it to price "a place of my own", never to search rooms. |

"Login required" is not "the renter's job". Most of these read without an
account. What is the renter's job: joining a group, posting, contacting,
viewing, signing, paying.

**The reverse channel.** In "room wanted" groups, posts asking for a room drew
8 to 11 comments within hours, many with concrete offers. When the search is
thin or the date is close, draft a wanted post with the settled constraints so
replies arrive pre-filtered, and let the renter post it.

**Late in the month the pool for the 1st is leftovers.** Weight posts from the
last 48 hours and tell the renter to contact the same day.

## 3. Filter: knockouts are facts, everything else is scored

Fifteen conjunctive filters leave "nothing wrong with it", not "good". Keep the
knockouts to facts (move-in date, a real bedroom with a bed, headcount, nobody
sleeping in the living room or den, no basement if that is a knockout, gates the
renter cannot pass, a written agreement) and score the rest. The traps that
actually showed up:

- **"Den" is not a bedroom**, it usually has no window. **"Living-room share" or
  "second room" in a partitioned living room is not a bedroom either**, and the
  Korean boards price them like rooms. Craigslist marks some as
  `room not private`; read that field.
- **Anyone sleeping in the living room, den or solarium disqualifies the unit
  for a renter who cares about noise**: they sleep with no door in the middle of
  the kitchen and bathroom traffic, so noise runs both ways every night.
- **Gender rules live in the body, not the title.** Of six neutral-titled posts
  opened one evening, four said "female only" in the first line. Open the body
  before shortlisting. **The inverse error is the scout's:** never drop a
  listing because the current housemates happen to be women. The ad's own rule
  is the filter.
- **No photo of the room, no viewing.** Anyone can shoot the living room; zero
  room photos means something to hide or a landlord who cannot be bothered.
  Scams usually carry good photos (often stolen), so photos are necessary, not
  sufficient.
- **"Furnished" is an attribute and a photo, not an assumption.** A room was
  once shortlisted as furnished from its body text; all four photos were an
  empty unit shot by a realtor. Check the attribute line and look for a bed.
- **Short-term sublets are mixed in.** Check the term against the profile.
- **A listing nobody has touched in weeks is usually already let.** Two
  enquiries went out the same afternoon: the ad renewed the night before got a
  viewing offer within three hours, the one last updated four weeks earlier got
  "taken, forgot to remove the ad". Never let a stale ad be the only candidate.
- **Half of Craigslist says only "Vancouver"**, and a pin with
  `data-accuracy` 22 or more is a neighbourhood centroid. Get a cross-street.
- **Preference versus gate.** "Working professional or student preferred" is a
  preference; prepare an answer. "Credit check" or "must be employed" is a gate a
  newcomer with no Canadian file cannot pass: drop it. "Proof of income *or*
  funds" is answerable with balance screens. "References" is answerable once
  the referees have agreed. Rank up listings that welcome working-holiday visas.
- **A flowerbed at eye level in the window photo means below grade**, not
  ground floor. Pull the storeys and basement area from BC Assessment before
  calling a house room "not basement", and when a host says the owner lives
  "upstairs", ask which level the room is on.
- **"How many people live here" is asked per shared facility.** A landlord who
  says "three of us" may be counting one suite of a much bigger house. Ask
  who shares the kitchen and who shares the laundry, and read BC Assessment's
  bedroom and bathroom counts (see `references/checks.md`).
- **Rent far below the market is a warning, not a bargain**, but check it
  against the building first: an older rental tower with the poster sleeping in
  the living room can be market price, not bait.

### 3a. Scams: say this before any money moves

**The scam tell is "no viewing", not "deposit talk".** Korean boards routinely
say "first deposit gets the room"; that alone is not a scam if a viewing is
offered. **A landlord who cannot show the place is not a red flag; one who will
not show it is.** An operator abroad who arranges a viewing by current
housemates is the opposite of "I am away, send the deposit and I will mail the
keys".

**Never suggest sending a deposit to hold a room sight unseen.** An early
version of this skill did, as a way to win a listing, and it was wrong. Offering
to pay promptly *after* a viewing is fine; wiring money before one is the
scam's whole mechanism.

**When two posts carry the same photos, compare posters and terms before
anything else.** It may be an operator and a leaving tenant both advertising, or
one copying the other's photos, which is the classic scam. Send both the same
questions and compare. Re-uploaded photos are re-compressed, so their hashes
differ: compare visually.

### 3b. Who is the landlord decides which law applies

Read `references/bc-tenancy.md` before judging any agreement. The short version:
the Residential Tenancy Act excludes only accommodation where the renter shares
a kitchen or bathroom **with the owner**. A roommate of a tenant is an
"occupant" with no RTA standing. An operator who does not live in the house is a
landlord under the Act, owner or not, and the Act cannot be contracted out of.
So the first question about any agreement is **"does the owner, or the person I
sign with, live here after I move in?"**, and the answer goes into the record.

### 3c. What more money buys

Answer with the market, not adjectives. Measured over 768 listings in 2026-09,
price buys three specific things and little else:

| What | Where it starts |
|---|---|
| A bathroom with a shower, not shared | about CAD 1,000 in Vancouver (5 listings in 345 below CAD 900) |
| A private entrance | about CAD 1,050 |
| No commute (walk to downtown) | about CAD 1,000 in the West End |

Going far out saves almost nothing at the median (about CAD 850 in Surrey and
the Tri-Cities against 875 in Vancouver). What moves is the private-bathroom
floor: about 830 in Burnaby, 800 in the Tri-Cities, 700 in Surrey. Frame the
suburbs as "the same money buys a private bathroom", never "it is cheaper out
there". The ceiling of the conversation is a whole unit, and its real price is
the gate: **whole units run credit checks and want proof of income.**

## 4. Score and rank

```sh
python3 scripts/score.py --rent 800 --transit zone1
python3 scripts/score.py --rent 950 --transit walk
python3 scripts/score.py --batch listings.json --budget budget.json
```

Rank on the total, not the rent. With a budget file, each room also shows the
balance at the horizon date with and without a job, and the difference against
the baseline room. **Always print the no-job line beside the job line when a
recommendation costs money:** headroom that comes from a salary not yet earned is
being paid for out of the path where it never arrives. Say that in a sentence.
Check the budget file's date before quoting any balance; a stale figure looks
authoritative and is worse than none.

## 5. Report and keep the record

Lead with the price map (area, observed range, common price, time to anchor),
then the ranked options with total and budget effect, then the traps found in
this batch. **State the sample size, the sources and the date**: a price map
from one morning of Craigslist is a snapshot, and "Craigslist only" and
"Craigslist + Marketplace + UvanU" are different claims.

- **Every listing gets a working link**, in the chat table, the report and the
  ledger. The renter opens the links; do not send photo sheets.
- **Send every listing the search found, not only the shortlist**, to the
  renter's phone channel (a chat webhook named in the profile), grouped by
  status, one line each with nickname and link. Of the three rooms picked from
  the first such list, two were ones the chat reply had not pushed. Curating it
  down to the scout's favourites destroys its value.
- **A record that exists only in the conversation is not a record.** Keep one
  living ledger: every enquiry sent, every reply received verbatim, viewing
  times, each criterion the renter settles, with its date. Update it in the turn
  it happens. Keep reports as dated files, in storage the renter can read from a
  phone, not in a temporary session folder.
- **Archive each shortlisted listing the day it is read**: the post text
  verbatim, the photos, the raw HTML. Posts get deleted; one shortlisted listing
  vanished from Craigslist and survived only in the archive.
- **Re-fetch and diff a saved listing the day before a viewing and the day of a
  decision.** One post was quietly edited hours after a phone call: "available
  oct 1" became "oct 16" and "6 months lease" was deleted. Nobody mentioned it.
- **Maps: write a KML, do not click pins.** Google My Maps has no API, and
  driving the editor once deleted every pin. A generated `.kml` (one placemark
  per listing with code, viewing time, total and what to check) opens in Google
  Earth or imports into My Maps; a keyless directions URL is enough on the day.

Give a ranked recommendation with a concrete next step, not a framework. The
point is to hand back decisions, not homework.

## 6. Evaluating one listing

Judge the address, never the neighbourhood label. Recipes are in
`references/checks.md`.

1. **Where exactly?** Cross-street or postal code. "Downtown" spans Coal
   Harbour and the Downtown Eastside.
2. **BC Assessment the moment an address arrives**: year built, storeys,
   bedroom and bathroom counts, floor areas per level, basement area, "more than
   one structure", and the legal description (a strata lot reads "STRATA LOT n,
   PLAN ..."; a freehold house reads "LOT n, PLAN ..."). It changed the reading of
   every listing it touched, and it stops condo advice being applied to a house.
3. **Read the exterior photo**: mailboxes and unit numbers (a row of mailboxes
   can settle in one glance that a big house is several suites), front doors,
   basement windows. Cross-check which floor each photo is on by what the
   windows see; flooring that changes between shots can mean photos from more
   than one unit.
4. **Distance to the anchor** by the mode the renter would actually use, and the
   walk from the station to the door: an address can be fine while the last
   400 m is not.
5. **Distance to the track, not the station.** A room sold as "600 m from
   SkyTrain" stood 29 m from the elevated guideway. Measure point-to-segment from
   OpenStreetMap; `bridge=yes` means elevated. A line source loses only about
   3 dB per doubling of distance, so a high floor does not cancel it.
6. **Crime data** for City of Vancouver addresses, with its limits said every
   time: violent crime is not in the mapped data, and Burnaby (RCMP) publishes
   nothing comparable. Pair it with the actual sunset time for the walk home.
7. **Total monthly cost** via the script, and **the term**: a 12-month lease
   signed before the job location is known can trap the renter.
8. **The operator's other posts for the same address.** Sibling posts gave one
   house's internal price ladder, showed which rooms were turning over, and
   contradicted "everyone stays a year". Do it at shortlisting, not after the
   viewing.

Then a verdict with a number, not a vibe.

## 7. Soundproofing, when it is the top criterion

Grade the building before ranking: **A** concrete high-rise; **B** a house with
nobody above, or the top floor of a wood frame; **C** a lower floor of a wood
frame or a house main floor with another household upstairs. An unidentified
building is graded from photos and marked as a guess.

Then rank what actually wakes someone in a share house: footfall from above
(worst in wood frame), a wall against the kitchen or living room, the stairs,
hallway traffic, and last another bedroom. **The building code's STC 50 applies
between dwelling units, not between rooms inside one**, so "it's newer" says
nothing about the wall to the next bedroom. **The door is half the problem**: a
hollow-core door with a gap underneath has effectively no rating. Viewing tests
and the full reasoning are in `references/viewing.md`.

## 8. Writing the enquiry

**Read the listing end to end before drafting a single question.** A draft once
asked for the roommate count and the utilities split; both were in the seller's
description, and the seller had asked applicants for three specific items the
message did not supply. Then:

1. Follow any format the listing asks for, but only for what has not already
   been sent in the thread.
2. Keep only questions a viewing cannot answer and that would end it: move-in
   date, minimum term and whether an agreement is signed, who else lives there
   (children, dogs, couples, anyone in the living room), whether anyone will be
   added later, and what utilities cost. About five questions.
3. No negotiation, no term commitment, no deposit talk in the first message.
4. **Never write a commitment the renter has not made.** "The 6-month minimum
   works for me" is a promise.
5. Quote one line of the listing back; it proves the renter read it.
6. **Never invent a detail about the renter** (an age, a job title, a date) to
   make a message flow. Leave the blank and ask.

If a question slips through that the listing already answered, the next message
opens with one line of apology and then supplies what was asked for.

## 9. The viewing: the renter is being interviewed too

**Ask what happened at a viewing before explaining why it went badly.** One
viewing went cold and the first diagnosis, "too many questions", was wrong; the
renter had not asked them. The host had kept steering to money: a job-seeking
tenant is checked for funds first. So every viewing guide:

1. Starts with **proof of funds** ready on the phone: the Canadian bank app's
   balance, account numbers covered, history off screen; aim for the minimum
   term's rent.
2. Answers **"are you a student? do you have a job?"** in three sentences:
   experience, where the job search stands that day, rent paid from savings they
   can show. A repeated question means the first answer did not settle it.
3. Opens with one specific compliment, a 30-second introduction, and the line
   that answers "will rent arrive with no job yet" before it is asked.
4. Fits the host's own life into a sentence ("since you start early, I'd keep
   mornings quiet").
5. Cuts questions to the two or three that decide the lease; deposit, early exit
   and negotiation wait.
6. Frames a problem with its fix first ("I use the fan and open a window").
7. Ends with a same-evening thank-you that repeats one detail.

**Prefer an evening viewing when noise matters**: an afternoon share house is an
empty house. **Ask a housemate, not the owner**, what the kitchen is like at
8am, whether the laundry queues, how long they have lived there, why this room
is free, and whether they hear the next room. Check the bedroom door lock.

## 10. Contract and money

Details and section numbers are in `references/bc-tenancy.md`. The habits:

- **Read the blanks, not the boilerplate**: rent, fixed-term end date, the
  services-included boxes, the deposit, any vacate clause.
- **Fill in the blanks together, then transfer, then both sign.** The risk of
  "pay first, we'll write the contract after" is leverage, not flight: once the
  money has moved, any term that comes out differently can only be refused by
  chasing the money back.
- **Deposit at signing, first month's rent on key day**: same total, half the
  exposure. Recompute the deposit cap when the rent changes.
- **Three names must line up: the registered owner (LTSA title), the landlord on
  the agreement, and the e-Transfer recipient.** A mismatch is usually a family
  member; close it with one non-accusatory question before money moves.
- **Interac e-Transfer shows the recipient's registered legal name only with
  Autodeposit.** Without it, the name on screen is a label the sender typed.
- **A deadline ("sign by tomorrow and the price drops") is kept by moving the
  checks forward, not by skipping them**: run the title search that evening, get
  a photo of the filled form that night.
- **Ask in writing for anything the room lacks that matters** (a door lock: the
  tenant may not change a lock without written consent), and record a verbal
  term with whose obligation it is.

## 11. When the renter cannot choose

**Stop building comparison tables and interview the renter.** Three viewed rooms once
sat in a table for a day without a decision; four rounds of up to five
questions produced a clear order in an hour (the market then changed it, so keep
the second choice open until the first is signed). The format: each question names what its answer would
push toward ("footsteps means A, voices means B"), five per round, one-line
answers, a scoreboard between rounds. Ask about real daily moments (what sound at
bedtime, the rainy commute, whether they talk to people in the current kitchen),
put a gut-check first ("if A says yes tomorrow, do you go without hesitating?").
The decisive answer was oblique: asked why one room attracted them, the renter
described a different one from start to finish. Record each round verbatim.

**The comparison table leaves out how the renter wants to live.** After three viewings
the ranking covered acoustics, contract and money only; the renter came back
talking about house rules and a house that felt lived in. Name such factors as
real and present the final choice as one of how to live, not a score.

## 12. Recording what people say

- **Record a verbal term with whose obligation it is, in the speaker's words, and
  label any reading of it as inference.** A host's "just tell me a day before you
  leave" (flexibility for the renter) was logged as "1-day notice", read as "the host
  can evict you in a day", and became that room's headline weakness until the
  renter corrected it. The real gap was only a missing host-side notice clause.
- **A landlord who answers a different question has not answered.** Log a
  deflection as an unanswered question and put it on the viewing list.
- **A draft the renter shows you is unsent until they say it is sent.**
- **"The listing disappeared" is a claim to test.** A 403 can be a site-wide
  login wall, and a re-post can push the original off page one; check a post you
  know exists before concluding.

## 13. Boundaries

Never, whatever the instruction: join a group, post, comment, react, message a
landlord, book a viewing, sign, create an account, enter a password, solve a
CAPTCHA, or send money. Draft, check, and hand over. Read logged-in sources only
through the renter's own browser session, read only.

## A note for whoever edits this file

Skill arguments are substituted into this body, so a dollar sign immediately
followed by a digit can be eaten. Write money as `CAD 1,050` here. Reference files
are read as files and are safe.
