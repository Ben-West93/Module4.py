import requests
import json

BASE_URL = "https://jsonplaceholder.typicode.com"

# Response headers worth calling out explicitly when debugging.
KEY_RESPONSE_HEADERS = ["Content-Type", "Content-Length", "ETag", "Cache-Control"]

# Bodies longer than this get truncated in the output.
BODY_LIMIT = 500

# The exercise asks for ALL request headers, so this is off by default.
# Flip it to True before pointing this script at an API that needs auth,
# otherwise your credentials land in the terminal and in any log that
# captures it.
MASK_SECRETS = False

SENSITIVE_HEADERS = {"authorization", "proxy-authorization", "cookie", "x-api-key"}

# Content types we're willing to decode as text.
TEXTUAL_HINTS = ("text/", "json", "xml", "javascript", "x-www-form-urlencoded")


def print_separator(title):
    """Print a section separator."""
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print('=' * 55)


def mask(name, value):
    """Hide the value of a credential-bearing header when masking is on."""
    if MASK_SECRETS and name.lower() in SENSITIVE_HEADERS:
        return f"<masked, {len(value)} chars>"
    return value


def pretty(raw):
    """Pretty-print a JSON payload; fall back to the raw text if it isn't JSON."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if not isinstance(raw, str):
        return str(raw)

    # JSONDecodeError and UnicodeDecodeError are both ValueError subclasses.
    try:
        rendered = json.dumps(json.loads(raw), indent=2)
    except (ValueError, TypeError):
        return raw

    # A shadowed or stubbed `json` module can hand back something that isn't a
    # string. Fall back to the raw text rather than passing it downstream.
    return rendered if isinstance(rendered, str) else raw


def truncate(text, limit=BODY_LIMIT):
    """Cut text off at `limit` characters and note how much was hidden."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    if len(text) <= limit:
        return text
    hidden = len(text) - limit
    return f"{text[:limit]}\n... [truncated, {hidden} more characters]"


def indent(text, prefix="  "):
    """Indent every line of a block of text."""
    return "\n".join(prefix + line for line in text.splitlines())


def is_textual(content_type):
    """Decide whether a Content-Type is safe to print as text."""
    if not content_type:
        # No Content-Type at all: assume text, since printing is recoverable
        # and an empty body is the common case here.
        return True
    return any(hint in content_type.lower() for hint in TEXTUAL_HINTS)


def decode_body(raw, content_type):
    """
    Turn a raw byte body into printable text.

    Servers that omit `charset` make requests fall back to ISO-8859-1, which
    mangles UTF-8. Decoding the bytes ourselves avoids that.
    """
    if raw is None:
        return "(no body)"
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not raw:
        return "(empty body)"
    if not is_textual(content_type):
        return f"<binary content, {len(raw)} bytes — not printed>"

    charset = "utf-8"
    if content_type and "charset=" in content_type.lower():
        charset = content_type.lower().split("charset=")[1].split(";")[0].strip()
    try:
        text = raw.decode(charset, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")

    return truncate(pretty(text))


# ============================================================
# display_anatomy(response, label)
# ============================================================
def display_anatomy(response, label):
    """Display the full anatomy of a request/response pair."""
    req = response.request

    print(f"\n[{label}]")

    # A redirect means `response.request` describes the FINAL hop, not the one
    # we issued — and servers may rewrite POST to GET along the way. Surface
    # the chain so the anatomy below isn't quietly misleading.
    if response.history:
        print("\n--- REDIRECT CHAIN ---")
        for hop in response.history:
            print(f"  {hop.status_code} {hop.request.method} {hop.request.url}")
        print(f"  -> final: {req.method} {req.url}")

    print(f"\n--- REQUEST ---")
    print(f"  {req.method} {req.url}")

    print("\n  Headers:")
    for name, value in req.headers.items():
        print(f"    {name}: {mask(name, value)}")

    print("\n  Body:")
    print(indent(decode_body(req.body, req.headers.get("Content-Type")), "    "))

    print(f"\n--- RESPONSE ---")
    # HTTP/2 servers send no reason phrase, so `reason` can be None or "".
    print(f"  Status: {response.status_code} {response.reason or '(no reason phrase)'}")
    print(f"  Elapsed: {response.elapsed.total_seconds() * 1000:.2f} ms")

    print("\n  Key headers:")
    for name in KEY_RESPONSE_HEADERS:
        print(f"    {name}: {response.headers.get(name, '(not present)')}")

    print("\n  Body:")
    print(indent(decode_body(response.content, response.headers.get("Content-Type")), "    "))


def show(method, url, label, **kwargs):
    """
    Make one request and display its anatomy.

    A network error here shouldn't take down the whole lab — report it and let
    the remaining transactions run.
    """
    kwargs.setdefault("timeout", 10)
    try:
        response = requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as exc:
        print(f"\n[{label}]")
        print(f"\n--- REQUEST FAILED ---")
        print(f"  {method} {url}")
        print(f"  {type(exc).__name__}: {exc}")
        return None

    display_anatomy(response, label)
    return response


# ============================================================
# Make 3 requests and display their anatomy
# ============================================================
def main():
    print_separator("REQUEST 1: GET /users/1")
    show("GET", f"{BASE_URL}/users/1", "GET a single user")

    print_separator("REQUEST 2: POST /posts")
    show(
        "POST",
        f"{BASE_URL}/posts",
        "POST a new post",
        json={
            "title": "Understanding HTTP Anatomy",
            "body": "Every request carries a method, headers, and often a body.",
            "userId": 1,
        },
    )

    print_separator("REQUEST 3: PATCH /posts/1")
    show(
        "PATCH",
        f"{BASE_URL}/posts/1",
        "PATCH an existing post's title",
        json={"title": "Updated Title"},
    )

    print(f"\n{'=' * 55}")
    print("  All three transactions complete.")
    print('=' * 55)


if __name__ == "__main__":
    main()
    