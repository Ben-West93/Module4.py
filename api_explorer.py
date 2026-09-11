"""
Module 4 Project - Part 1: API Exploration
Explore public APIs and document what you find.

APIs used:
  1. JSONPlaceholder - fake REST API for testing (no auth)
  2. PokeAPI         - Pokemon data (no auth)
  3. Open-Meteo      - weather forecasts (no auth)

NOTE ON A SUBSTITUTION:
The starter file listed REST Countries (https://restcountries.com/v3.1) as the
third API. That version has since been deprecated. It still answers with
200 OK, but the body is an error envelope rather than country data:
    {"success": false, "data": null, "errors": [{"message": "This API version
     has been deprecated..."}]}
The current v5 API lives under a different path and rejects keyless requests
with 401 authKeyMissing. Since the project brief allows choosing your own APIs
and lists Open-Meteo as a suggested option, Open-Meteo stands in here. The
original REST Countries findings are written up in api_documentation.md.
"""

import requests

BASE_URLS = {
    "jsonplaceholder": "https://jsonplaceholder.typicode.com",
    "pokeapi": "https://pokeapi.co/api/v2",
    "open_meteo": "https://api.open-meteo.com/v1",
    "open_meteo_geocoding": "https://geocoding-api.open-meteo.com/v1",
}

TIMEOUT = 10


def call_api(method, url, **kwargs):
    """
    Make one HTTP request and report on it.

    Returns the parsed JSON body on success, or None if anything went wrong.
    Every request in this script goes through here, so a 404 or a dead
    connection prints a readable message instead of crashing the program.
    """
    print(f"\n{method} {url}")
    try:
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.RequestException as exc:
        # No response ever arrived -- DNS failure, refused connection, timeout.
        # There is no status code to inspect in this case.
        print(f"  Request failed before a response came back: {exc}")
        return None

    print(f"  Status: {response.status_code} {response.reason}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'not sent')}")

    # raise_for_status() converts any 4xx/5xx into an exception, which lets
    # error handling live in one place instead of at every call site.
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        print(f"  Handled HTTP error: {exc}")
        # Many APIs put a useful explanation in the body of an error response.
        try:
            print(f"  Server said: {response.json()}")
        except ValueError:
            pass
        return None

    try:
        return response.json()
    except ValueError:
        print("  Response body was not valid JSON.")
        return None


# ============================================================
# API 1: JSONPlaceholder
# Documentation: https://jsonplaceholder.typicode.com/guide/
# ============================================================

def explore_jsonplaceholder():
    print("\n" + "=" * 60)
    print("=== API 1: JSONPlaceholder ===")
    print("=" * 60)
    base = BASE_URLS["jsonplaceholder"]

    # TODO 1: GET all users
    # REST CONCEPT -- COLLECTION RESOURCE. The plural noun /users identifies the
    # entire set. GET is a safe method: it retrieves data and changes nothing
    # on the server, so it can be repeated freely.
    users = call_api("GET", f"{base}/users")
    if users:
        print(f"  Retrieved {len(users)} users:")
        for user in users:
            print(f"    - {user['name']} <{user['email']}>")

    # TODO 1b: GET one specific user
    # REST CONCEPT -- MEMBER RESOURCE. Same collection, single item. The id sits
    # in the path because it is part of what identifies the resource, not a
    # filter applied to a search.
    user_one = call_api("GET", f"{base}/users/1")
    if user_one:
        print(f"  User 1: {user_one['name']}")
        print(f"  Company: {user_one['company']['name']}")
        print(f"  City: {user_one['address']['city']}")

    # TODO 2: GET posts by a specific user
    # REST CONCEPT -- QUERY PARAMETERS. The resource is still the whole /posts
    # collection; ?userId=3 narrows which members are returned. Note the
    # difference from the path-based id above: this is filtering, not identity.
    filtered = call_api("GET", f"{base}/posts", params={"userId": 3})
    if filtered:
        print(f"  User 3 has {len(filtered)} posts")
        print(f"  First title: {filtered[0]['title']}")

    # TODO 2b: GET a nested resource
    # REST CONCEPT -- NESTED RESOURCE. Ownership is expressed in the path
    # itself. /users/1/posts reads as "the posts belonging to user 1."
    nested = call_api("GET", f"{base}/users/1/posts")
    if nested:
        print(f"  User 1 owns {len(nested)} posts. First three:")
        for post in nested[:3]:
            print(f"    [{post['id']}] {post['title']}")

    # TODO 3: POST a new post
    # REST CONCEPT -- POST is UNSAFE and NON-IDEMPOTENT. Sending it twice would
    # create two separate resources. Status 201 Created means the server built
    # a new resource and assigned it an identifier.
    created = call_api(
        "POST",
        f"{base}/posts",
        json={
            "title": "What I learned about REST",
            "body": "Resources are the nouns and HTTP methods are the verbs.",
            "userId": 1,
        },
    )
    if created:
        print("  Status 201 means the resource was created")
        print(f"  Server assigned id: {created['id']}")
        print(f"  Echoed title: {created['title']}")

    # TODO 3b: PUT an update
    # REST CONCEPT -- PUT is IDEMPOTENT. It replaces the resource at a URI the
    # client already knows, so running it ten times leaves the same end state
    # as running it once.
    updated = call_api(
        "PUT",
        f"{base}/posts/1",
        json={"id": 1, "title": "Updated title", "body": "Replaced body", "userId": 1},
    )
    if updated:
        print(f"  Post 1 now reads: {updated['title']}")

    # TODO 3c: DELETE a resource
    # DELETE is idempotent too -- a second call is a no-op because the resource
    # is already gone.
    deleted = call_api("DELETE", f"{base}/posts/1")
    if deleted is not None:
        print(f"  Delete returned: {deleted} (empty object, nothing left to send back)")


# ============================================================
# API 2: PokeAPI
# Documentation: https://pokeapi.co/docs/v2
# ============================================================

def explore_pokeapi():
    print("\n" + "=" * 60)
    print("=== API 2: PokeAPI ===")
    print("=" * 60)
    base = BASE_URLS["pokeapi"]

    # TODO 4: GET a specific Pokemon
    pokemon = call_api("GET", f"{base}/pokemon/25")
    if not pokemon:
        return

    # Height ships in decimetres and weight in hectograms, so divide by 10.
    print(f"  Name: {pokemon['name']}")
    print(f"  Height: {pokemon['height'] / 10} m")
    print(f"  Weight: {pokemon['weight'] / 10} kg")
    abilities = [a["ability"]["name"] for a in pokemon["abilities"]]
    print(f"  Abilities: {', '.join(abilities)}")

    # TODO 5: Follow the first type URL out of the Pokemon response
    # REST CONCEPT -- HATEOAS (hypermedia as the engine of application state).
    # The response handed the client a complete URL, so the client follows a
    # link rather than hardcoding how a type endpoint is assembled. If PokeAPI
    # reorganized its URIs tomorrow, this code would still work.
    type_url = pokemon["types"][0]["type"]["url"]
    type_data = call_api("GET", type_url)
    if type_data:
        print(f"  Type: {type_data['name']}")
        members = [p["pokemon"]["name"] for p in type_data["pokemon"][:5]]
        print(f"  First 5 {type_data['name']}-type Pokemon: {', '.join(members)}")

    # TODO 5b: GET a paginated collection
    # PokeAPI caps collection responses and exposes navigation through "next"
    # and "previous" links plus a total "count."
    page = call_api("GET", f"{base}/pokemon", params={"limit": 5, "offset": 20})
    if page:
        print(f"  Total Pokemon available: {page['count']}")
        print(f"  This page: {', '.join(p['name'] for p in page['results'])}")
        print(f"  Next page link: {page['next']}")

    # TODO 6: Document the response structure
    # Top-level keys in the /pokemon/<id> response:
    #   abilities, base_experience, cries, forms, game_indices, height,
    #   held_items, id, is_default, location_area_encounters, moves, name,
    #   order, past_abilities, past_stats, past_types, species, sprites,
    #   stats, types, weight
    # Most of these are lists of small objects carrying a "name" plus a "url"
    # pointing at another endpoint. The API is heavily cross-linked rather than
    # returning one deeply embedded blob, which keeps any single response small
    # but means richer questions take several round trips.
    print(f"\n  Response structure: {len(pokemon.keys())} top-level keys")
    print(f"  {', '.join(sorted(pokemon.keys()))}")


# ============================================================
# API 3: Open-Meteo
# Documentation: https://open-meteo.com/en/docs
# Substituted for the deprecated REST Countries API (see module docstring).
# ============================================================

def explore_openmeteo():
    print("\n" + "=" * 60)
    print("=== API 3: Open-Meteo ===")
    print("=" * 60)
    forecast_base = BASE_URLS["open_meteo"]
    geo_base = BASE_URLS["open_meteo_geocoding"]

    # TODO 7: Look up a place by name
    # This is a search endpoint, so it returns a LIST even when one result is
    # obvious -- a name can legitimately match several places.
    places = call_api("GET", f"{geo_base}/search", params={"name": "Tokyo", "count": 3})
    if not places or "results" not in places:
        print("  No geocoding results, skipping the forecast lookup.")
        return

    print(f"  Matches for 'Tokyo': {len(places['results'])}")
    for place in places["results"]:
        print(f"    - {place['name']}, {place.get('country', 'unknown')} "
              f"({place['latitude']}, {place['longitude']})")

    top = places["results"][0]
    lat, lon = top["latitude"], top["longitude"]

    # TODO 8: Get current conditions and a multi-day forecast
    # REST CONCEPT -- Open-Meteo is a single resource whose SHAPE is driven
    # entirely by query parameters. Asking for different variables changes what
    # comes back, unlike JSONPlaceholder where each URI has a fixed structure.
    weather = call_api(
        "GET",
        f"{forecast_base}/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "forecast_days": 3,
            "timezone": "auto",
        },
    )
    if weather:
        current = weather["current"]
        units = weather["current_units"]
        print(f"\n  Current conditions in {top['name']}:")
        print(f"    Time: {current['time']} ({weather['timezone']})")
        print(f"    Temperature: {current['temperature_2m']}{units['temperature_2m']}")
        print(f"    Wind: {current['wind_speed_10m']}{units['wind_speed_10m']}")

        # Daily data arrives as PARALLEL ARRAYS rather than a list of objects,
        # so index 0 of each list describes the same day. zip() lines them up.
        daily = weather["daily"]
        print(f"  {len(daily['time'])}-day forecast:")
        for date, high, low in zip(
            daily["time"], daily["temperature_2m_max"], daily["temperature_2m_min"]
        ):
            print(f"    {date}: high {high}, low {low}")

    # TODO 9: Handle an error
    # REST CONCEPT -- a 4xx status means the CLIENT sent something wrong. Here
    # the latitude is out of range, so the server answers 400 Bad Request with
    # an explanation. The helper catches it and the script keeps running.
    print("\n  Now deliberately sending an invalid latitude:")
    broken = call_api(
        "GET",
        f"{forecast_base}/forecast",
        params={"latitude": 999, "longitude": 999, "current": "temperature_2m"},
    )
    if broken is None:
        print("  Bad request was caught and the script continued normally.")


# ============================================================
# Run all explorations
# ============================================================

if __name__ == "__main__":
    explore_jsonplaceholder()
    explore_pokeapi()
    explore_openmeteo()
    print("\n=== Exploration complete! ===")
