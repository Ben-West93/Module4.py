import requests

BASE_URL = "https://jsonplaceholder.typicode.com"

# Helper to print each step clearly
def log_step(step, method, url, status, note=""):
    print(f" Step: {step}: [{method}] {url}")
    print(f"           Status: {status} {note}")

# ============================================================
# STEP 1: CREATE - POST new todo
# Expected: 201 Created
# ============================================================

print("Full CRUD Lifecycle on /todos\n")
print("Step 1: CREATE")

new_todo = {"title": "Complete Module 4", "completed": False, "userId": 1}
response = requests.post(f"{BASE_URL}/todos", json=new_todo, timeout=10)

created = response.json()
todo_id = created["id"]
log_step(1, "POST", f"{BASE_URL}/todos", response.status_code, f"Created ID: {todo_id}")

# Build the item path once - every remaining step targets this resource.
item_url = f"{BASE_URL}/todos/{todo_id}"

# ============================================================
# STEP 2: READ - GET the created todo by ID
# Expected: 200 OK
# ============================================================

print("\nStep 2: READ")

response = requests.get(item_url, timeout=10)
if response.status_code == 200:
    note = f"Title: {response.json()['title']}"
else:
    note = "Not found - sandbox never stored the POST, so id=201 isn't in the collection."
log_step(2, "GET", item_url, response.status_code, note)

# ============================================================
# STEP 3: UPDATE - PATCH to mark completed
# Expected: 200 OK
# ============================================================

print("\nStep 3: UPDATE (PATCH)")
 
response = requests.patch(item_url, json={"completed": True}, timeout=10)
if response.status_code == 200:
    note = f"completed = {response.json().get('completed')}"
else:
    note = "Update rejected"
log_step(3, "PATCH", item_url, response.status_code, note)
 
# ============================================================
# STEP 4: READ AGAIN — verify the update
# ============================================================
print("\nStep 4: READ AGAIN (verify)")
 
response = requests.get(item_url, timeout=10)
if response.status_code == 200:
    note = f"completed = {response.json().get('completed')}"
else:
    note = "Can't verify — the PATCH response is the only record of the change"
log_step(4, "GET", item_url, response.status_code, note)
 
# ============================================================
# STEP 5: DELETE
# Expected: 200 OK or 204 No Content
# ============================================================
print("\nStep 5: DELETE")
 
response = requests.delete(item_url, timeout=10)
if response.status_code in (200, 204):
    note = "Server reports the resource was deleted"
else:
    note = "Delete did not succeed"
log_step(5, "DELETE", item_url, response.status_code, note)
 
# ============================================================
# STEP 6: VERIFY DELETION — GET should return 404 (or sandbox behavior)
# ============================================================
print("\nStep 6: VERIFY DELETION")
 
response = requests.get(item_url, timeout=10)
if response.status_code == 404:
    note = "404 — resource is gone (as a real API would report after a delete)"
elif response.status_code == 200:
    note = "200 — sandbox behavior: the delete was acknowledged but not persisted"
else:
    note = "Unexpected status after delete"
log_step(6, "GET", item_url, response.status_code, note)
 
print("\nLifecycle complete.")
