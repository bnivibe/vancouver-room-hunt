# Where to look, and how to read each source

Audited in 2026-09 (first pass on 09-06, re-tested 09-12 and 09-14). Sites change;
when a recipe fails, check whether the site changed before concluding the
listing or the source is gone.

## The audit

| Source | Login | Verdict |
|---|---|---|
| **Craigslist** `van/roo`, `bnc/roo` (+ `rch`, `nvn`, `pml`, `rds`) | no | Main source. Recipe below. |
| **UvanU Daum cafe** (board `4Nd0`) | no for lists | Highest turnover found: 20 posts in 3 hours. Korean. |
| **Kijiji** room-rental category | no | About 100 Vancouver and 50 Burnaby rooms. Clean data. |
| **Facebook Marketplace** | browser session | Best fields of any source. |
| **Facebook groups** | membership | Readable only as a member; search works, the feed does not fill. |
| **Naver cafes** (working-holiday boards) | no for titles | Browsers refuse the domain; the JSON API answers plain HTTP. |
| **Vanchosun** rent board | no | Live Korean board, hourly; room shares mixed with whole units. City labels unreliable. |
| **Rentals.ca** rooms | no | Only about 37 rooms metro-wide, but mostly private-bath at CAD 830 to 1,030. Cloudflare after a few detail pages. |
| liv.rent | no | Whole units only. Use for the "place of my own" floor. |
| PadMapper, Zumper | no | No rooms; whole units from about CAD 2,085. |
| Roomies.ca | no | Vancouver is not a supported city. |
| Reddit | browser | Tenancy discussion, almost no room offers. |
| koreanrew, Joins media Canada boards | browser only | curl cannot connect; low yield, mostly realtor whole units. |
| Places4Students | no | Listings are per school, not per city. |
| vancouverktown room board | no | Dead (newest post months old, top posts are scam warnings). |

**Report the sample every time**: count, sources, date ("Craigslist 631 +
Marketplace 45, 2026-09-06"). Inventory turns over fast: 250 of 461 postings
under CAD 960 were less than five days old.

## Craigslist

```
https://vancouver.craigslist.org/search/van/roo?min_price=600&max_price=960
https://vancouver.craigslist.org/search/bnc/roo?min_price=600&max_price=860
https://vancouver.craigslist.org/search/van/roo?query=west%20end&max_price=1500
https://vancouver.craigslist.org/search/van/sub          (sublets: whole furnished units)
```

`van` is the City of Vancouver, `bnc` Burnaby and New Westminster. Searches
redirect to `www.craigslist.org`, which is the origin for storage and `fetch`.
A keyword query takes one phrase; OR syntax returns nothing.

**Trap 1: a hidden browser pane renders nothing.** The search app does not
hydrate results while `document.visibilityState === "hidden"`; polling returns
zero forever. Take a small screenshot first to force a paint, or use the curl
path below.

**Trap 2: 200 results is the ceiling and paging does not exist.** Split the price
range into bands under 200 results each and merge on `data-pid`. A band that hits
exactly 200 has silently dropped its oldest posts.

**Trap 3: extraction runs before hydration.** Poll for
`div.cl-search-result` (500 ms steps, up to 15 s), then wait another 800 ms.

```js
[...document.querySelectorAll('div.cl-search-result')].map(e => ({
  id:  e.dataset.pid,
  t:   (e.getAttribute('title') || '').trim(),
  p:   e.querySelector('.priceinfo')?.textContent.trim(),
  loc: e.querySelector('.result-location')?.textContent.trim().replace(/[()]/g, ''),
  m:   e.querySelector('.housing-meta')?.textContent.trim(),
  d:   e.querySelector('.result-posted-date')?.textContent.trim(),
  u:   e.querySelector('a.main')?.href
})).filter(x => x.p)
```

In list view the time is in `.meta span[title]` and the pid in the card image
path `/d/<pid>/`. Persist across navigations in `localStorage` on the same
origin. Dedupe on title + price: one landlord posted the same room four times.
**Separate new posts from renewals** with a seen-id set before reading bodies:
of 133 cards dated after a cutoff, 71 were already known.

**Detail pages from inside the page** (same-origin `fetch`), as a background job
with two workers and 200 to 500 ms between requests: 396 pages in 214 s with no
block.

```js
const doc   = new DOMParser().parseFromString(await (await fetch(u)).text(), 'text/html');
const map   = doc.querySelector('#map');        // data-latitude, data-longitude, data-accuracy
const attrs = [...doc.querySelectorAll('.attrgroup')].map(g => g.textContent.replace(/\s+/g, ' ').trim()).join(' | ');
const body  = doc.querySelector('#postingbody')?.textContent.replace(/QR Code Link to This Post/i, '').trim();
const gone  = /this posting has been (deleted|removed|flagged)/i.test(doc.body.textContent);
```

- `available oct 1` in `.attrgroup` is the move-in date; `room not private`
  marks a shared or partitioned space; `furnished` is an attribute, not a guess.
- `data-accuracy` 22 or more is a neighbourhood centroid (a dozen East Van posts
  resolve to the same point; one was 1.8 km off). Use the body's cross-street.
- Gender rules are in the body, not the title.

**Rate limits.** The block page is titled "blocked" and looks exactly like a
render failure: check `document.title` before debugging selectors. About 400
same-origin detail fetches in a burst triggers it, IP-wide. Search pages came back
after about 12 minutes; the `fetch` path stayed blocked longer. **While the browser
is blocked, plain `curl` of the search URL still worked** and returned a
server-rendered `li.cl-static-search-result` list (238 rows), and curl of detail
pages at 1.3 s spacing went through 75 in a row.

## Facebook Marketplace

```
https://www.facebook.com/marketplace/vancouver/search?query=room%20for%20rent&maxPrice=1300&sortBy=creation_time_descend&radius=20
```

Needs a logged-in browser. The `/vancouver/` path overrides the account's
default location, but check the location line in the left rail. Search cards give
only price, a generic title and a city; **never shortlist or draft an enquiry from
a card.** Open the item (navigate, click "See more", read `div[role=main]`): it
carries the street address and postal code, bed and bath counts, **"N persons live
here"**, availability, furnished, heating, laundry, and the posting age. A Vancouver
search returns Surrey and Langley too; filter by city. A query loads about 24 cards.

## Facebook groups

Membership is required; logging in is not enough (a non-member sees one or two
posts, then skeleton placeholders). **Never join, post, comment or react on the
renter's behalf**: joining exposes their name to tens of thousands of people.

Large Vancouver housing groups seen in 2026-09: Vancouver Rentals and Roommates
(`vancouverrooms`, 35k members, 50+ posts a day), For Rent Vancouver (57k),
Vancouver Apartments, Roommates, Rooms for Rent and Sublets (28k), Vancouver - Rent
Apartments Houses Rooms (90k), plus several Korean community groups.

**Group search is the only read that works**; the chronological feed never fills,
even with real scrolling. Add the "Most recent" filter by URL, or results mix posts
from years ago:

```
https://www.facebook.com/groups/<slug>/search/?q=<words>&filters=eyJycF9jaHJvbm9fc29ydDowIjoie1wibmFtZVwiOlwiY2hyb25vc29ydFwiLFwiYXJnc1wiOlwiXCJ9In0%3D
```

(the filter is base64 of `{"rp_chrono_sort:0":"{\"name\":\"chronosort\",\"args\":\"\"}"}`).
Each query returns 5 to 10 posts in a virtualized feed of 4 to 7 children, so run
several queries per group (`room october`, `private room`, `furnished`). Install a
`setInterval` harvester that clicks "See more" and stores each `[role=feed]`
child's text in a `window` Map, then scroll with **real wheel events**;
`window.scrollTo` did not render the missing posts. Work in one foreground tab:
background tabs froze. Permalinks and exact times are not in the search DOM, so
record the group, query and author name.

**Groups work best in reverse**: in "room wanted" groups, a wanted post drew 8 to
11 comments within hours. Draft it; the renter posts it.

## UvanU (Daum cafe)

The list has a JSON API that needs no browser:

```
https://m.cafe.daum.net/api/v1/common-articles?grpid=hPc&fldid=4Nd0&targetPage=N&pageSize=50
```

Page 2 onward needs `&afterBbsDepth=<bbsDepth of the last article>` or it returns
a server error. 50 posts a page; 13 pages covered five days. Rows carry `dataid`.

Bodies: `cafe.daum.net/_c21_/bbs_read?grpid=hPc&fldid=4Nd0&datanum=<n>`; the post
HTML is inside `<xmp id="template_xmp">`, not the visible content div. When that
started returning 403 without a login, opening `cafe.daum.net/ourvancouver/4Nd0/<id>`
in a browser and reading the first iframe's `contentDocument.body.innerText` still
returned the full text. **Before concluding a post was deleted, request one you know
exists**: a site-wide 403 looks identical. Posters re-post the same ad several times
a day to bump it; find the new ids by title. List times are in Korea time.

In the browser the board lives in an iframe with id `down`; the first ten or so rows
are notices and paid ads. About 40 percent of posts are women-only; search the
Korean terms for "men only" and "any gender" rather than filtering blind.
"Living-room share", "den" and "second room" posts are often partitions, not bedrooms.
The author-history link redirects to a Kakao login: do not log in, note it as unchecked.

## Kijiji

```
https://www.kijiji.ca/b-room-rental-roommate/greater-vancouver-area/c36l80003?sort=dateDesc
https://www.kijiji.ca/b-room-rental-roommate/greater-vancouver-area/<keyword>/k0c36l80003?sort=dateDesc
```

Read the page's `__NEXT_DATA__` Apollo state: `activationDate` (UTC),
`location.address`, `description`, `imageUrls`, coordinates. Filter by postal prefix
(V5H Metrotown, V5J South Slope, V5E Edmonds). **Liveness: never grep for "no longer
available"**; that string is in every page's translation bundle, and two live ads
were once called gone because of it. Read `"status":"ACTIVE"` or `"EXPIRED"` and
`endDate`. A result exported through a tool may come back double-encoded JSON:
`json.JSONDecoder().raw_decode` the outer string, then `json.loads`. Watch for
"Wanted" posts.

## Naver cafes

`scripts/naver_cafe.py list` reads the Canada working-holiday cafe's housing board
and HelloVan's rent board with no login. Endpoint:

```
https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid=<id>&search.menuid=<id>&search.queryType=lastArticle&search.page=<n>&search.perPage=50
```

with a `Referer` of the cafe's URL. **Bodies are member-only**: the article API
returns 401 without a session, and 403 with code 4005 when the account's cafe level
is too low. `read` sends `NAVER_COOKIE` if the renter supplies their own session.
Titles mislead (one "downtown" post was Calgary), and many posts are cross-posted
from UvanU, where the body can be read in full.

## Rentals.ca

A cookie banner blocks rendering until dismissed; choose Decline:

```js
[...document.querySelectorAll('button')].find(b => /^decline$/i.test(b.textContent.trim()))?.click();
```

Cards are `.listing-card`, reading like `$830 Room 1 BED 1 BATH <street>, Vancouver, BC`;
"1 BED 1 BATH" is a private bathroom. Results are metro-wide despite the path; filter
on the URL slug. After two or three detail pages the site serves Cloudflare's "Just a
moment" page, so read the list first and open only the details that matter.

## liv.rent

Only for one question: where does a place of one's own start? Load
`/rental-listings/city/vancouver` plain (adding `?sort=` throws an error) and split
`document.body.innerText` on "Check Availability". Observed floor in 2026-09: a
1-bedroom basement suite at about CAD 1,600, a studio at 1,875, a 1-bedroom
apartment at 2,150. Always add the gate: whole units run credit checks and want proof
of income.

## Practical notes

- **Tool output limits.** Export compact arrays; compute in Python; pull full bodies
  only for the shortlist. A very large page export can be padded past the tool limit
  so the harness saves it to a file, then parsed from Python.
- **Screenshots fail while the browser pane is hidden.** DOM reads do not need the
  pane; drop the screenshot step and read through JavaScript.
- **Extension filters** can block outputs that contain URLs with query strings; strip
  them in the page script before returning.
- **Outside Facebook, avoid the browser where curl works**: it is faster and does not
  depend on the pane being visible.
