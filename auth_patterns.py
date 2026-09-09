"""
Demonstrates three things:
   1. A protected endpoint rejecting an unauthenticated request (401)
   2. A public endpoint serving an unauthenticated request (200)
   3. A factory that builds the right auth header for a given auth scheme
   
Run: python auth_patterns.py
"""

from datetime import datetime, timezone

import requests

# --- Configuration -------------------------------------------------------------
# Kept at module level so the URLs and timeout are changed in one place rather
# than hunted for inside the functions below.

API_ROOT = "https://api.github.com"
PROTECTED_ENDPOINT = f"{API_ROOT}/user"  # your own profile - needs a token
PUBLIC_ENDPOINT = f"{API_ROOT}/users/octocat"  # anyone's public profile - no token needed

# requests has NO default timeout. WIthout this, a hung connection blocks forever.
# Always set one on a real request.
TIMEOUT_SECONDS = 10


# --- Helpers -------------------------------------------------------------------

def safe_json(response: requests.Response) -> dict:
    """
    Parse a JSON body, returning {} instead of raising if the body isn't JSON.

    A 200 status does not guarantee a JSON body. Proxies, captive portals, and
    gateway errors return HTML with an HTTP status attached, and .json() raises
    ValueError on those.
    """
    try:
        parsed = response.json()
    except ValueError:
        return {}
    # A few endpoints return a JSON list rather than an object; callers here
    # expect a dict, so normallize anything else to empty.
    return parsed if isinstance(parsed, dict) else {}


def print_rate_limit(response: requests.Response) -> None:
    """Print the rate limit headers GitHub attaches to every response."""
    limit = response.headers.get("X-RateLimit-Limit")
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset = response.headers.get("X-RateLimit-Reset")
 
    print(f"   X-RateLimit-Limit:     {limit}")
    print(f"   X-RateLimit-Remaining: {remaining}")
 
    # X-RateLimit-Reset is a Unix timestamp, not a duration. Converting it is
    # the difference between "1789234800" and knowing when to retry.
    if reset:
        reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc)
        print(f"   X-RateLimit-Reset:     {reset_at:%Y-%m-%d %H:%M:%S} UTC")


# ============================================================
# EXPERIMENT 1: Unauthenticated request to a PROTECTED endpoint
# GET /user shows your own profile — requires a token.
# ============================================================
 
def experiment_1_protected() -> None:
    print("1. GET /user (protected — requires auth)")
 
    try:
        response = requests.get(PROTECTED_ENDPOINT, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        # DNS failure, refused connection, TLS error, timeout. None of these
        # produce a response object, so there is no status code to read.
        print(f"   Request failed before reaching GitHub: {exc}")
        return
 
    print(f"   Status code: {response.status_code}")
    print(f"   Message: {safe_json(response).get('message', '(no message)')}")
 
    # Expect 401. A 403 here means the 60/hour unauthenticated limit for this
    # IP is already spent — GitHub checks the rate limit BEFORE it checks
    # credentials, so a throttled client never sees the 401.
    if response.status_code == 403:
        print("   Note: 403, not 401 — rate limited. The auth check never ran.")
 
 
# ============================================================
# EXPERIMENT 2: Unauthenticated request to a PUBLIC endpoint
# GET /users/octocat is public — works without auth
# ============================================================
 
def experiment_2_public() -> None:
    print("\n2. GET /users/octocat (public — no auth needed)")
 
    try:
        response = requests.get(PUBLIC_ENDPOINT, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        print(f"   Request failed before reaching GitHub: {exc}")
        return
 
    print(f"   Status code: {response.status_code}")
 
    if response.status_code == 200:
        user = safe_json(response)
        # .get() rather than [] throughout: a rate-limited body has a "message"
        # key and none of these, and GitHub returns null for "name" on accounts
        # that never filled in a display name.
        print(f"   login:        {user.get('login')}")
        print(f"   name:         {user.get('name') or '(not set)'}")
        print(f"   public_repos: {user.get('public_repos')}")
    else:
        print(f"   No profile data. Message: {safe_json(response).get('message')}")
 
    print_rate_limit(response)
 
 
# ============================================================
# AUTH HEADER FACTORY
# ============================================================
 
def create_auth_headers(api_key: str, auth_type: str) -> dict:
    """
    Return the correct auth headers for a given auth type.
 
    Args:
        api_key: The token or key value
        auth_type: "bearer" → Authorization: Bearer <key>
                   "api-key" → X-API-Key: <key>
 
    Returns: headers dict ready for requests
    Raises: ValueError for unknown auth_type
    """
    # Validate before branching. A key that is None, empty, or all whitespace
    # would otherwise produce a header like "Bearer " that fails at the server
    # with a confusing 401 instead of here with a clear error.
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("api_key must be a non-empty string")
 
    if not isinstance(auth_type, str):
        raise ValueError(f"auth_type must be a string, got {type(auth_type).__name__}")
 
    # Strip the key too — a token pasted from a file or env var often carries a
    # trailing newline, and that byte travels in the header and breaks the call.
    api_key = api_key.strip()
 
    # Normalize so "Bearer", "BEARER", and " bearer " all behave like "bearer".
    normalized = auth_type.strip().lower()
 
    if normalized == "bearer":
        return {"Authorization": f"Bearer {api_key}"}
    elif normalized == "api-key":
        return {"X-API-Key": api_key}
    else:
        raise ValueError(
            f"Unknown auth_type: {auth_type!r}. Expected 'bearer' or 'api-key'."
        )
 
 
def demo_auth_factory() -> None:
    print("\n3. Auth header factory demo")
 
    print(f"   bearer:  {create_auth_headers('ghp_example123', 'bearer')}")
    print(f"   api-key: {create_auth_headers('sk-example456', 'api-key')}")
 
    # Edge cases, kept in a loop so the failure paths sit together instead of
    # stacking near-identical try/except blocks.
    edge_cases = [
        ("some_key", "oauth"),      # unsupported scheme  → raises
        ("some_key", "BEARER "),    # messy casing/spacing → normalized, accepted
        ("", "bearer"),             # empty key           → raises
        ("   ", "bearer"),          # whitespace-only key → raises
        (None, "bearer"),           # wrong type          → raises
    ]
 
    for key, kind in edge_cases:
        try:
            headers = create_auth_headers(key, kind)
            print(f"   ({key!r}, {kind!r}) → accepted: {headers}")
        except ValueError as exc:
            print(f"   ({key!r}, {kind!r}) → ValueError: {exc}")
 
 
def main() -> None:
    experiment_1_protected()
    experiment_2_public()
    demo_auth_factory()
 
 
# Guard so the file can be imported — e.g. `from auth_patterns import
# create_auth_headers` in a test — without firing off two network requests.
if __name__ == "__main__":
    main()
