"""
Lists the 3 most-starred public repositories owned by "google", then reports
the remaining rate limit.


WHY THE SEARCH ENDPOINT

The starter file points at GET /users/google/repos. That endpoint cannot do
what the exercise asks: its `sort` parameter accepts only created, updated,
pushed, and full_name. There is no stars option. Sorting by stars exists only
on GET /search/repositories, so that is what this script calls.


DOCUMENTATION REFERENCES

Each answer below came from a specific page of docs.github.com/en/rest:

  Endpoint and parameters
      REST API > Search > Search > "Search repositories" > Parameters
  Accept header
      Headers table under Parameters on any endpoint page
  Rate limits (general)
      Using the REST API > Rate limits
  Rate limits (search-specific)
      REST API > Search > Search > "About search" > Rate limit


LIMITS WORTH KNOWING

  - Search has its own rate limit bucket, separate from the general REST
    limit: 10 requests/minute unauthenticated, 30/minute authenticated.
    That is why this script reports "of 10" rather than "of 60".
  - `order` is ignored unless `sort` is also supplied.
  - `per_page` maxes out at 100.
  - Any single search returns at most 1,000 results in total.
"""

import requests


# ----------------------------------------------------------------------------
# Request configuration
# ----------------------------------------------------------------------------

URL = "https://api.github.com/search/repositories"

# `user:` matches both organization and personal accounts. `org:` would also
# work for google specifically, but would silently return nothing if this
# script were pointed at a personal account.
PARAMS = {
    "q": "user:google",          # restrict the search to google's repos
    "sort": "stars",             # stars | forks | help-wanted-issues | updated
    "order": "desc",             # most-starred first
    "per_page": 3,               # results per page (max 100)
}

HEADERS = {
    "Accept": "application/vnd.github+json",   # the header GitHub recommends
    "X-GitHub-Api-Version": "2026-03-10",      # the REST API is versioned now
}

TIMEOUT_SECONDS = 10


# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------

def print_repo(repo):
    """Print one repository's name, description, star count, and language."""
    # description and language are null for some repos, so both need a
    # fallback rather than printing "None".
    description = repo["description"] or "(no description)"
    language = repo["language"] or "(not specified)"

    print(repo["name"])
    print(f"  Description: {description}")
    print(f"  Stars:       {repo['stargazers_count']:,}")
    print(f"  Language:    {language}")
    print()


def report_rate_limit(response):
    """
    Print rate limit status.

    Every response carries these headers, so checking the limit costs nothing
    extra. Calling GET /rate_limit instead would spend a request to learn how
    many requests are left.
    """
    limit = response.headers.get("X-RateLimit-Limit", "unknown")
    remaining = response.headers.get("X-RateLimit-Remaining", "unknown")

    print(f"Rate limit: {remaining} of {limit} requests remaining")
    print("(Search bucket: 10/min unauthenticated, 30/min authenticated.)")


def explain_forbidden(response):
    """
    Explain a 403 or 429.

    GitHub uses these two statuses for three different problems, and only the
    response headers tell them apart. Reporting every 403 as "rate limited"
    sends the caller off to wait for a reset that will never arrive.

      X-RateLimit-Remaining: 0  ->  primary rate limit, wait for the reset
      Retry-After present       ->  secondary rate limit, slow down
      neither                   ->  genuinely forbidden, waiting will not help
    """
    remaining = response.headers.get("X-RateLimit-Remaining")
    retry_after = response.headers.get("Retry-After")
    reset = response.headers.get("X-RateLimit-Reset")

    if remaining == "0":
        print("Primary rate limit reached -- no results returned.")
        if reset:
            print(f"  Resets at: {reset} (UTC epoch seconds)")
        print()
        print("Unauthenticated search is capped at 10 requests per minute.")
        print("Wait for the reset, or authenticate to raise the cap to 30/min.")

    elif retry_after:
        print("Secondary rate limit reached -- too many requests too quickly.")
        print(f"  Retry after: {retry_after} seconds")
        print()
        print("This limit is separate from the primary one and authenticating")
        print("does not raise it. Slow the request rate down instead.")

    else:
        print(f"Request forbidden (HTTP {response.status_code}) -- not a rate limit.")
        message = read_json(response, {}).get("message", "")
        if message:
            print(f"  GitHub says: {message}")
        print()
        print("Waiting will not help. Check the query, the headers, and whether")
        print("network policy is blocking api.github.com.")


# ----------------------------------------------------------------------------
# Request handling
# ----------------------------------------------------------------------------

def read_json(response, default=None):
    """
    Parse a JSON body, returning `default` if it is not valid JSON.

    A 200 status does not guarantee JSON. Corporate proxies and GitHub outage
    pages both return HTML, and calling .json() on that raises ValueError.
    """
    try:
        return response.json()
    except ValueError:
        return default


def fetch_repos():
    """
    Call the search endpoint.

    Returns the response object, or None if the request never completed.
    """
    try:
        return requests.get(
            URL,
            params=PARAMS,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        print(f"Request timed out after {TIMEOUT_SECONDS} seconds.")
    except requests.exceptions.RequestException as error:
        # Covers DNS failures, refused connections, TLS errors, and so on.
        print(f"Request failed: {error}")

    return None


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    print("Google's 3 Most-Starred Repos\n")

    response = fetch_repos()
    if response is None:
        return

    if response.status_code in (403, 429):
        explain_forbidden(response)
        return

    if response.status_code != 200:
        print(f"Unexpected response: HTTP {response.status_code}")
        print(response.text[:300])
        return

    payload = read_json(response)
    if payload is None:
        print("Response was not valid JSON. First 300 characters:")
        print(response.text[:300])
        return

    repos = payload.get("items", [])
    if not repos:
        print("No repositories matched the query.\n")
        report_rate_limit(response)
        return

    for repo in repos:
        print_repo(repo)

    # Fewer results than asked for is legitimate, but worth stating so the
    # short output does not look like a bug.
    if len(repos) < PARAMS["per_page"]:
        print(f"Note: found {len(repos)} repos, fewer than the "
              f"{PARAMS['per_page']} requested.\n")

    # A search that exceeds GitHub's internal time limit returns partial
    # results with a 200 status. This flag is the only warning.
    if payload.get("incomplete_results"):
        print("Warning: incomplete_results is true. The search timed out, so")
        print("these may not be the true top 3. Re-run for a complete result.\n")

    report_rate_limit(response)


if __name__ == "__main__":
    main()
    