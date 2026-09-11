# API Documentation — Module 4, Part 1

Documentation of the three public APIs consumed by `api_explorer.py`.
All observations below come from actually running the script, not from reading docs.

**Run date:** September 10, 2026
**Total calls made:** 13 across three APIs

---

## A note on the starter file's third API

The starter file listed **REST Countries v3.1** as API 3. That version has been
deprecated and no longer returns country data. It is documented at the bottom of
this file as a finding, and **Open-Meteo** was substituted in its place — it appears
on the project's own suggested-API list and requires no authentication.

---

## API 1: JSONPlaceholder

**Base URL:** `https://jsonplaceholder.typicode.com`
**Authentication:** None
**Docs:** https://jsonplaceholder.typicode.com/guide/

A fake REST API that accepts writes and pretends to honor them. Ideal for practicing
the full set of HTTP methods without needing a key or damaging real data.

### Endpoints tested

| Method | Path | Description |
|---|---|---|
| GET | `/users` | Retrieve the full user collection |
| GET | `/users/1` | Retrieve one user by id |
| GET | `/posts?userId=3` | Filter the post collection by owner |
| GET | `/users/1/posts` | Nested resource — posts belonging to user 1 |
| POST | `/posts` | Create a new post |
| PUT | `/posts/1` | Replace an existing post |
| DELETE | `/posts/1` | Remove a post |

### Example response shapes

`GET /users` — array of 10 objects, each with nested `address` and `company` objects:

```json
[
  {
    "id": 1,
    "name": "Leanne Graham",
    "email": "Sincere@april.biz",
    "address": {
      "city": "Gwenborough",
      "geo": { "lat": "-37.3159", "lng": "81.1496" }
    },
    "company": { "name": "Romaguera-Crona" }
  }
]
```

`POST /posts` — returns `201 Created` and echoes the submitted body plus a new id:

```json
{ "title": "What I learned about REST", "body": "...", "userId": 1, "id": 101 }
```

`DELETE /posts/1` — returns `200 OK` with an empty object `{}`.

### Rate limits observed

This API is the only one of the three that publishes its limits in response headers:

```
x-ratelimit-limit: 1000
x-ratelimit-remaining: 942
x-ratelimit-reset: 1788817860
```

So 1000 requests per window, with the remaining count decrementing per call and a
Unix timestamp marking the reset. Responses are also served through Cloudflare with
`cache-control: max-age=43200` (12 hours) and `cf-cache-status: HIT`, meaning repeat
requests are often answered from cache rather than the origin server.

### What surprised me

**The write operations are theater.** `POST /posts` returned `201 Created` with
`id: 101`, exactly as a real API would. But `GET /posts/101` afterward returns
`404 Not Found` — the resource was never persisted. The same is true of PUT and
DELETE: they return success statuses, and nothing changes on the server.

This is useful, not a bug. It means the API can teach the request/response cycle for
unsafe methods without maintaining per-user state. But it makes an important point
about REST: **a `201 Created` status is a claim the server makes, not proof.** A real
client should not assume a resource exists because the status code says so.

A second smaller surprise: `id: 101` is hardcoded. Every POST returns 101, no matter
how many times you call it or what you send. A genuine API would return a distinct
identifier per creation.

---

## API 2: PokeAPI

**Base URL:** `https://pokeapi.co/api/v2`
**Authentication:** None
**Docs:** https://pokeapi.co/docs/v2

A large read-only dataset. Notably, it rejects all write methods — it is a genuine
example of an API where GET is the only verb that makes sense.

### Endpoints tested

| Method | Path | Description |
|---|---|---|
| GET | `/pokemon/25` | Retrieve one Pokémon by id (25 = Pikachu) |
| GET | `/type/13/` | Follow a URL supplied by the previous response |
| GET | `/pokemon?limit=5&offset=20` | Paginated slice of the collection |

### Example response shapes

`GET /pokemon/25` — a single object with **21 top-level keys**:

```
abilities, base_experience, cries, forms, game_indices, height, held_items,
id, is_default, location_area_encounters, moves, name, order, past_abilities,
past_stats, past_types, species, sprites, stats, types, weight
```

Most of those keys hold lists of small `{ "name": ..., "url": ... }` objects rather
than embedded data:

```json
{
  "name": "pikachu",
  "height": 4,
  "weight": 60,
  "types": [
    { "slot": 1, "type": { "name": "electric", "url": "https://pokeapi.co/api/v2/type/13/" } }
  ]
}
```

`GET /pokemon?limit=5&offset=20` — a pagination envelope:

```json
{
  "count": 1351,
  "next": "https://pokeapi.co/api/v2/pokemon?offset=25&limit=5",
  "previous": "https://pokeapi.co/api/v2/pokemon?offset=15&limit=5",
  "results": [ { "name": "spearow", "url": "..." } ]
}
```

The `next` and `previous` fields are full URLs, so a client can page through 1,351
records without ever constructing a query string itself. This is HATEOAS in practice.

### Rate limits observed

No `x-ratelimit-*` headers are sent at all. Twelve rapid sequential requests all
returned `200 OK` in under a second with no throttling. PokeAPI instead relies on
aggressive caching — `cache-control: public, max-age=86400` (24 hours) with
`x-cache: HIT` — and asks consumers in its docs to cache locally as a fair-use
courtesy rather than enforcing a hard cap.

### What surprised me

**Units are not what they look like.** Pikachu returns `height: 4` and `weight: 60`.
Reading those as metres and kilograms gives you a four-metre-tall Pikachu. The values
are actually decimetres and hectograms, so the real figures are 0.4 m and 6.0 kg.
Nothing in the response body signals this — no unit field, no suffix. You only learn
it from the documentation.

This is a concrete argument for something Part 2 asks about: if your API returns
numbers, either name the unit in the field (`height_dm`) or ship a units object
alongside the data. Open-Meteo does exactly that, and the difference is obvious.

---

## API 3: Open-Meteo

**Base URLs:**
- `https://api.open-meteo.com/v1` (forecasts)
- `https://geocoding-api.open-meteo.com/v1` (place name lookup)

**Authentication:** None for non-commercial use
**Docs:** https://open-meteo.com/en/docs

### Endpoints tested

| Method | Path | Description |
|---|---|---|
| GET | `/search?name=Tokyo&count=3` | Resolve a place name to coordinates |
| GET | `/forecast?latitude=..&longitude=..&current=..&daily=..` | Weather for a point |
| GET | `/forecast?latitude=999&longitude=999` | Deliberate error case |

### Example response shapes

`GET /search?name=Tokyo&count=3` — returns a list even for an apparently unambiguous
name, because names genuinely collide:

```json
{
  "results": [
    { "name": "Tokyo", "country": "Japan",            "latitude": 35.6895, "longitude": 139.69171 },
    { "name": "Tokyo", "country": "Papua New Guinea", "latitude": -8.4,    "longitude": 147.15 },
    { "name": "Tokyo", "country": "Nepal",            "latitude": 29.16998,"longitude": 83.16319 }
  ]
}
```

`GET /forecast` — pairs every data block with a matching units block:

```json
{
  "timezone": "Asia/Tokyo",
  "current_units": { "temperature_2m": "°C", "wind_speed_10m": "km/h" },
  "current":       { "time": "2026-09-11T03:00", "temperature_2m": 18.8, "wind_speed_10m": 4.0 },
  "daily_units":   { "temperature_2m_max": "°C" },
  "daily": {
    "time":              ["2026-09-11", "2026-09-12", "2026-09-13"],
    "temperature_2m_max": [19.6, 26.1, 25.4],
    "temperature_2m_min": [18.8, 19.1, 20.9]
  }
}
```

Note that `daily` is **parallel arrays**, not a list of day objects. Index 0 of every
array describes the same day, so the client has to zip them together. This is a
compactness trade-off: it saves repeating key names 16 times in a 16-day forecast, at
the cost of a less obvious structure.

### Rate limits observed

No rate-limit headers and no `cache-control` header either. The published policy is
10,000 requests per day for free non-commercial use, but nothing in the response
communicates how much of that budget remains. A client has no way to detect it is
approaching the limit until requests start failing.

### What surprised me

**It is barely a REST API in the resource sense.** There is essentially one endpoint,
`/forecast`, and the query string does all the work. Asking for `current=temperature_2m`
versus `daily=temperature_2m_max` changes the shape of the response object itself,
adding and removing top-level keys.

Compare this to JSONPlaceholder, where `/users` and `/posts` are distinct resources
with fixed structures. Open-Meteo's URI does not identify a stored thing — it
describes a computation to run. The response is generated on demand, which is also
why it reports `generationtime_ms` in every payload.

The error handling is the best of the three, though. An out-of-range latitude gets a
proper `400 Bad Request` with an explanation you could show a user directly:

```json
{ "error": true, "reason": "Latitude must be in range of -90 to 90°. Given: 999.0." }
```

---

## Appendix: REST Countries — a deprecated API

**Base URL attempted:** `https://restcountries.com/v3.1`
**Status:** Deprecated, no longer returns data

The starter file's third API no longer works, and the way it fails is instructive.

Requesting `GET /v3.1/name/Japan` returns:

```
Status: 200 OK
Content-Type: application/json
```

```json
{
  "success": false,
  "data": null,
  "errors": [{ "message": "This API version has been deprecated. Please visit
               https://restcountries.com/docs/countries/legacy-api-deprecation
               to migrate to our new version (v5)." }]
}
```

**The status code lies.** The server says `200 OK` while telling you in the body that
nothing is OK. This broke the first version of my script: the code checked the status,
saw success, and then crashed with `KeyError: 0` trying to read `japan[0]` from what
it assumed was a list of countries.

That crash is the whole lesson. `raise_for_status()` catches nothing here, because
from HTTP's perspective the request succeeded. Defensive clients have to validate the
*shape* of a response, not just its status line — which is why the final script checks
`if not places or "results" not in places` before indexing into Open-Meteo's results.

The replacement v5 API requires an API key and returns `401 authKeyMissing` without
one, so it was not usable for a keyless exploration assignment.

**The takeaway for Part 2:** if I ever deprecate an endpoint, it should return a real
error status — `410 Gone` exists precisely for this — rather than a `200` wrapping a
failure. Using `200` for an error makes every client's error handling silently useless.
