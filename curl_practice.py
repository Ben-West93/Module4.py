import requests


# ============================================================
# APIClient base class
#
# The point of this class is that it knows nothing about any particular API.
# It handles the mechanics that every REST client needs — a base URL, a
# reusable session, and error checking — so subclasses only have to describe
# the endpoints that make their API distinctive.
# ============================================================
class APIClient:
    """Base class for API clients. Extend this for each specific API."""

    def __init__(self, base_url: str, default_headers: dict = None):
        # rstrip("/") so "https://api.com" and "https://api.com/" behave the same
        self.base_url = base_url.rstrip("/")

        # A Session reuses the underlying TCP connection across requests instead
        # of doing a fresh DNS lookup + TLS handshake every time. It also holds
        # headers and cookies so we set them once here rather than per call.
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)

    def _url(self, path: str) -> str:
        """Combine base_url with a path."""
        # lstrip("/") means callers can pass "users" or "/users" interchangeably.
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path: str, **kwargs):
        response = self.session.get(self._url(path), **kwargs)
        response.raise_for_status()
        return response

    def post(self, path: str, **kwargs):
        response = self.session.post(self._url(path), **kwargs)
        response.raise_for_status()
        return response

    def patch(self, path: str, **kwargs):
        response = self.session.patch(self._url(path), **kwargs)
        response.raise_for_status()
        return response

    def delete(self, path: str, **kwargs):
        response = self.session.delete(self._url(path), **kwargs)
        response.raise_for_status()
        return response


# ============================================================
# JSONPlaceholderClient
#
# Each method below hides one detail of the API from the caller: which path to
# hit, which query parameter to use, what shape the payload takes. The caller
# writes client.get_user_posts(5) and never has to remember that it's
# GET /posts?userId=5.
# ============================================================
class JSONPlaceholderClient(APIClient):
    """Client for https://jsonplaceholder.typicode.com"""

    def __init__(self):
        super().__init__(
            "https://jsonplaceholder.typicode.com",
            default_headers={"Content-Type": "application/json"},
        )

    def get_user(self, user_id: int) -> dict:
        """Fetch a single user by ID."""
        return self.get(f"/users/{user_id}").json()

    def get_user_posts(self, user_id: int) -> list:
        """Fetch all posts for a specific user."""
        # Server-side filtering: the API does the work and sends back only
        # the matching posts. Same thing as ?userId=3 in the curl exercise.
        return self.get("/posts", params={"userId": user_id}).json()

    def create_post(self, user_id: int, title: str, body: str) -> dict:
        """Create a new post (simulated). Returns the created post dict."""
        payload = {"userId": user_id, "title": title, "body": body}
        # json= (not data=) makes requests serialize the dict and set the
        # Content-Type header for us.
        return self.post("/posts", json=payload).json()

    def search_posts(self, query: str) -> list:
        """
        Client-side filter: fetch all posts and return those whose title
        contains `query` (case-insensitive).
        """
        # Contrast with get_user_posts: there's no search endpoint here, so we
        # pull all 100 posts and filter in Python. Fine for 100 records, a bad
        # idea for 100,000 — that's when you want the server doing the work.
        posts = self.get("/posts").json()
        needle = query.lower()
        return [post for post in posts if needle in post["title"].lower()]


# ============================================================
# Demo (runs when you execute this file)
# ============================================================
if __name__ == "__main__":
    client = JSONPlaceholderClient()

    # 1. User 5's profile
    print("1. User 5 profile:")
    user = client.get_user(5)
    print(f"   Name:  {user['name']}")
    print(f"   Email: {user['email']}")
    # city is nested inside the address object, not top-level
    print(f"   City:  {user['address']['city']}")

    # 2. User 5's posts
    print("\n2. User 5's posts:")
    posts = client.get_user_posts(5)
    print(f"   Count: {len(posts)}")
    print(f"   First: {posts[0]['title']}")

    # 3. Create a post
    print("\n3. Create a new post:")
    new_post = client.create_post(
        user_id=5,
        title="Testing my API client",
        body="Built with the APIClient base class.",
    )
    print(f"   ID:    {new_post['id']}")
    print(f"   Title: {new_post['title']}")
    print("   (Note: JSONPlaceholder fakes writes — nothing is persisted.)")

    # 4. Search
    print("\n4. Search posts for 'qui':")
    matches = client.search_posts("qui")
    print(f"   Matches: {len(matches)}")
    for post in matches[:3]:
        print(f"   - [{post['id']}] {post['title']}")
        