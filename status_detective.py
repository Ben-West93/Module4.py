import requests

BASE_URL = "https://jsonplaceholder.typicode.com"

# ============================================================
# BONUS: Write a reusable report() function first
# It should: make a request, determine the status category, return a report dict
# ============================================================

# Category labels keyed by the first digit of the status code
CATEGORIES = {
    1: ("1xx", "Informational"),
    2: ("2xx", "Success"),
    3: ("3xx", "Redirection"),
    4: ("4xx", "Client Error"),
    5: ("5xx", "Server Error")
}

# Short explanations for the codes this exercise actually produces.
DESCRIPTIONS = {
    200: "OK - request succeeded, resource returned",
    201: "Created - a new resource was created",
    204: "No content - succeeded, nothing to return",
    400: "Bad request - the server could not parse the request",
    401: "Unauthorized - authentication required or failed",
    403: "Forbidden - authenticated but not permitted",
    404: "Not found - no resource exists at this URL",
    500: "Internal Server Error - the server failed to handle the request",
}


def report(method, url, **kwargs):
    """Make a request and return a formatted report."""
    response = requests.request(method, url, timeout=10, **kwargs)

    family = response.status_code // 100
    category, label = CATEGORIES.get(family, ("?xx", "Unknown"))

    description = DESCRIPTIONS.get(
        response.status_code,
        f"{response.reason} - see the HTTP spec for this code",
    )

    return {
        "method": method.upper(),
        "url": url,
        "status_code": response.status_code,
        "category": category,
        "label": label,
        "description": description,
        "response": response,
    }


def print_report(r):
    """Print a formatted report dict."""
    icon = {"2xx": "✅", "3xx": "↪️", "4xx": "⚠️", "5xx": "❌"}.get(r["category"], "❓")

    print(f"  {r['method']:<6} {r['url']}")
    print(f"         {r['status_code']}  {icon} {r['label']} ({r['category']})")
    print(f"         {r['description']}")


# ============================================================
# Make 5 requests and report each
# ============================================================

print("Status Code Detective\n")

# 1. Successful GET (200)
print("1. Successful GET /posts/1")
print_report(report("GET", f"{BASE_URL}/posts/1"))

# 2. Nonexistent resource (404)
print("\n2. GET /posts/99999 (nonexistent)")
print_report(report("GET", f"{BASE_URL}/posts/99999"))

# 3. POST with valid data (201)
print("\n3. POST /posts with valid data")
new_post = {"title": "Status Code Detective", "body": "Testing the API.", "userId": 1}
r3 = report("POST", f"{BASE_URL}/posts", json=new_post)
print_report(r3)
print(f"         Created id={r3['response'].json().get('id')}")
 
# 4. DELETE (200)
print("\n4. DELETE /posts/1")
print_report(report("DELETE", f"{BASE_URL}/posts/1"))
 
# 5. Invalid endpoint (404)
print("\n5. GET /invalidendpoint")
print_report(report("GET", f"{BASE_URL}/invalidendpoint"))
 
# 6. Nested resource (200)
print("\n6. GET /users/1/todos")
r6 = report("GET", f"{BASE_URL}/users/1/todos")
print_report(r6)
print(f"         Returned {len(r6['response'].json())} todos for user 1")
 
print("\nAll six requests complete.")
