import requests

# Make sure you've activated your virtual environment and installed requirements.txt

BASE_URL = "https://jsonplaceholder.typicode.com"


# ============================================================
# TASK 1: GET all users
# GET requests retrieve data from the server — no body needed.
# ============================================================
print("TASK 1: All Users")
print("-" * 40)

response = requests.get(BASE_URL + "/users")
users = response.json()

print(f"Status code: {response.status_code}")
print(f"Total users: {len(users)}")
print()

for user in users:
    print(f"{user['name']} — {user['email']}")


# ============================================================
# TASK 2: GET posts by user #3
# Query parameters (?key=value) filter the results server-side.
# ============================================================
print("\nTASK 2: Posts by User #3")
print("-" * 40)

response = requests.get(BASE_URL + "/posts", params={"userId": 3})
posts = response.json()

print(f"Status code: {response.status_code}")
print(f"Posts found: {len(posts)}")
print()

# Slicing to [:3] is safe even if fewer than 3 posts come back.
for post in posts[:3]:
    print(post["title"])


# ============================================================
# TASK 3: GET comments on post #1 (nested resource)
# /posts/1/comments means "comments belonging to post 1"
# ============================================================
print("\nTASK 3: Comments on Post #1")
print("-" * 40)

response = requests.get(BASE_URL + "/posts/1/comments")
comments = response.json()

print(f"Status code: {response.status_code}")
print(f"Comments found: {len(comments)}")
print()

for comment in comments[:2]:
    print(comment["email"])
    print(comment["body"][:60])
    print()


# ============================================================
# TASK 4: POST a new post
# POST creates a new resource. Send data in the json= parameter.
# JSONPlaceholder simulates this — returns a realistic response but doesn't persist.
# ============================================================
print("\nTASK 4: Create a New Post (POST)")
print("-" * 40)

new_post = {
    "title": "Learning REST APIs",
    "body": "Today I made my first GET and POST requests with Python.",
    "userId": 1,
}

# json= serializes the dict and sets Content-Type: application/json
response = requests.post(BASE_URL + "/posts", json=new_post)
created = response.json()

print(f"Status code: {response.status_code}")
print(f"Created post id: {created['id']}")
print(f"Created post title: {created['title']}")
