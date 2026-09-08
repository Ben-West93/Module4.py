import requests

STUDENT_NAME = "Ben"

# ============================================================
# PART 1: Inspect header from 3 endpoints
# ============================================================

endpoints = [
    ("https://jsonplaceholder.typicode.com/posts/1", "JSONPlaceholder /posts/1"),
    ("https://jsonplaceholder.typicode.com/users/1", "JSONPlaceholder /users/1"),
    ("https://httpbin.org/get",                       "httpbin /get"),
]

CACHING_HEADERS = ["Cache-Control", "ETag", "Last-Modified", "Expires", "Age"]
RATELIMIT_HEADERS = [
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Retry-After",
]

print("PART 1: Response header inspection\n")

for url, label in endpoints:
    print(f"  Endpoint: {label}")

    # Make the GET request. A timeout keeps a slow server from hanging the script.
    try:
         response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as error:
        print(f"    Request failed: {error}\n")
        continue

    headers = response.headers
 
    print(f"    Status code:   {response.status_code}")
    print(f"    Total headers: {len(headers)}")
 
    # Content-Type tells the receiver how to parse the body (JSON vs HTML vs image).
    print(f"    Content-Type:  {headers.get('Content-Type', 'Not specified')}")
 
    # Content-Length is often missing when the response is sent chunked or compressed.
    print(f"    Content-Length: {headers.get('Content-Length', 'Not specified')}")
 
    # Caching headers tell clients and proxies whether/how long to reuse this response.
    found_caching = {h: headers[h] for h in CACHING_HEADERS if h in headers}
    if found_caching:
        print("    Caching headers present:")
        for name, value in found_caching.items():
            print(f"      {name}: {value}")
    else:
        print("    Caching headers present: None")
 
    # Rate-limiting headers tell you how many requests you have left before a 429.
    found_ratelimit = {h: headers[h] for h in RATELIMIT_HEADERS if h in headers}
    if found_ratelimit:
        print("    Rate-limiting headers:")
        for name, value in found_ratelimit.items():
            print(f"      {name}: {value}")
    else:
        print("    Rate-limiting headers: None")
 
    print()  # blank line between endpoints
 
# ============================================================
# PART 2: POST to httpbin.org with a custom header
# httpbin echoes back everything it received — great for testing
# ============================================================
 
print("\nPART 2: POST to httpbin.org with custom header\n")
 
payload = {"message": "Hello!", "exercise": "Header Inspector"}
custom_headers = {"X-Student-Name": STUDENT_NAME}
 
try:
    post_response = requests.post(
        "https://httpbin.org/post",
        json=payload,
        headers=custom_headers,
        timeout=10,
    )
 
    print(f"  Status code: {post_response.status_code}")
 
    echoed = post_response.json()
 
    # httpbin returns the body it parsed under "json" and the headers under "headers".
    print(f"  Echoed JSON body: {echoed.get('json')}")
    print(
        "  Echoed X-Student-Name: "
        f"{echoed.get('headers', {}).get('X-Student-Name', 'Not received')}"
    )
except requests.exceptions.RequestException as error:
    print(f"  Request failed: {error}")
    