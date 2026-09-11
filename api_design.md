# Module 4 Project — Part 2: Study Tracker API Design

**Name:** Ben
**Date:**

---

## The App

Study Tracker is a web and mobile app that helps students understand where their study
time actually goes. Students enroll in the courses they are taking, log each study
session with a duration and optional notes, and set a weekly target of study hours per
course. The API then computes progress — hours logged against hours targeted — so a
student can see at a glance which courses they are neglecting before the week is over.

---

## Section 1 — Resources

Five resources. Four are stored; the fifth is computed on request.

| Resource | Key Attributes |
|---|---|
| **Student** | `id` (integer), `email` (string, unique), `display_name` (string), `password_hash` (string, never returned), `timezone` (string, IANA name), `created_at` (datetime) |
| **Course** | `id` (integer), `code` (string, e.g. `CS-210`), `name` (string), `institution` (string, nullable), `is_active` (boolean), `created_at` (datetime) |
| **Enrollment** | `id` (integer), `student_id` (integer, FK), `course_id` (integer, FK), `term` (string, e.g. `Fall 2026`), `created_at` (datetime) |
| **StudySession** | `id` (integer), `student_id` (integer, FK), `course_id` (integer, FK), `started_at` (datetime), `duration_minutes` (integer), `notes` (string, nullable, max 2000), `was_productive` (boolean, nullable), `created_at` (datetime), `updated_at` (datetime) |
| **Goal** | `id` (integer), `student_id` (integer, FK), `course_id` (integer, FK), `week_start_date` (date, always a Monday), `target_minutes` (integer), `created_at` (datetime) |

**Progress** is deliberately *not* on this list. It is a computed view over
StudySessions and Goals, and it is discussed in Section 3 and the appendix.

---

## Section 2 — Relationships

### Student ↔ Course — many-to-many, through Enrollment

A student takes several courses, and a course is taken by many students. Neither side
can hold a foreign key to the other, so a join resource carries the relationship.
`Enrollment` also gives the pairing a place to store its own attributes — `term` is a
fact about *this student in this course*, not about either one alone.

This makes `Course` a **shared catalog**. Two students both taking CS-210 point at the
same course record rather than each creating a private copy. Section 5 and the appendix
explain why that choice drives the authentication design.

### Student ↔ Study Session — one-to-many ✅

**This is the required one-to-many relationship.** One student owns many study
sessions; each study session belongs to exactly one student. `student_id` lives on the
StudySession record, which is the standard place for the foreign key in a one-to-many
pairing: the "many" side points back at the "one."

Deleting a student cascades to their sessions, because a session with no owner is
meaningless.

### Course ↔ Study Session — one-to-many

One course accumulates many sessions across all students; each session names exactly
one course. Deleting a course does **not** cascade. Courses are archived by setting
`is_active` to `false`, since erasing a course would silently destroy the study history
of every student who ever took it.

### Student ↔ Goal — one-to-many, constrained

One student sets many goals. But a goal is really scoped to a *student, course, and
week* together, so the tuple `(student_id, course_id, week_start_date)` carries a
uniqueness constraint. A student cannot hold two competing targets for CS-210 during
the week of September 7. An attempt to create a duplicate returns `409 Conflict`.

Storing `week_start_date` rather than a week number keeps the data unambiguous across
year boundaries, where ISO week numbering gets genuinely confusing.

### Diagram

```
                    ┌──────────────┐
       ┌───many────→│  Enrollment  │←───many───┐
       │            └──────────────┘           │
       │                                       │
       │ 1                                   1 │
 ┌───────────┐                          ┌───────────┐
 │  Student  │                          │  Course   │
 └───────────┘                          └───────────┘
       │ 1                                   1 │
       │            ┌────────────────┐         │
       ├───many────→│  StudySession  │←──many──┤
       │            └────────────────┘         │
       │            ┌────────────────┐         │
       └───many────→│      Goal      │←──many──┘
                    └────────────────┘

 Student ──1:many──→ StudySession        (required one-to-many)
 Student ──many:many──→ Course           (through Enrollment)
 Goal is unique on (student_id, course_id, week_start_date)
```

---

## Section 3 — Endpoints

**25 endpoints** across five resources. Full CRUD on `study_sessions` is marked ★.

### Authentication

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| POST | `/students` | Register a new student account | No |
| POST | `/auth/login` | Exchange email and password for a JWT | No |
| POST | `/auth/refresh` | Trade a refresh token for a new access token | No (refresh token in body) |

### Students

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET | `/students/{id}` | Retrieve one student's profile | Yes — self only |
| PATCH | `/students/{id}` | Update display name or timezone | Yes — self only |
| DELETE | `/students/{id}` | Delete an account and all its sessions | Yes — self only |

### Courses

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET | `/courses` | List the course catalog | No — public |
| GET | `/courses/{id}` | Retrieve one course | No — public |
| POST | `/courses` | Add a course to the catalog | Yes — any student |
| PATCH | `/courses/{id}` | Correct a course's name or code | Yes — admin only |

### Enrollments

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET | `/students/{id}/courses` | List the courses a student is enrolled in | Yes — self only |
| POST | `/enrollments` | Enroll the current student in a course | Yes |
| DELETE | `/enrollments/{id}` | Drop a course | Yes — owner only |

### Study Sessions

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET ★ | `/study_sessions` | List the current student's sessions — **supports filtering** | Yes |
| GET ★ | `/study_sessions/{id}` | Retrieve one session | Yes — owner only |
| POST ★ | `/study_sessions` | Log a new study session | Yes |
| PUT ★ | `/study_sessions/{id}` | Replace a session in full | Yes — owner only |
| DELETE ★ | `/study_sessions/{id}` | Delete a session | Yes — owner only |
| PATCH | `/study_sessions/{id}` | Update selected fields of a session | Yes — owner only |
| GET | `/courses/{id}/study_sessions` | Nested — the current student's sessions in one course | Yes |

### Goals

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET | `/goals` | List the current student's goals | Yes |
| POST | `/goals` | Set a weekly target for a course | Yes |
| PUT | `/goals/{id}` | Change a target | Yes — owner only |
| DELETE | `/goals/{id}` | Remove a goal | Yes — owner only |

### Progress

| Method | URI | Description | Auth Required? |
|---|---|---|---|
| GET | `/students/{id}/progress` | Computed hours-logged vs. hours-targeted summary | Yes — self only |

### The filtering endpoint

`GET /study_sessions` accepts these query parameters, all optional and combinable:

| Parameter | Type | Description |
|---|---|---|
| `course_id` | integer | Only sessions for this course |
| `start_date` | date (`YYYY-MM-DD`) | Sessions on or after this date, inclusive |
| `end_date` | date (`YYYY-MM-DD`) | Sessions on or before this date, inclusive |
| `min_duration` | integer | Sessions of at least this many minutes |
| `was_productive` | boolean | Filter by the productivity flag |
| `sort` | string | `started_at`, `-started_at`, `duration_minutes`, `-duration_minutes` |
| `limit` | integer | Page size, default 25, maximum 100 |
| `offset` | integer | Records to skip, default 0 |

Example:

```
GET /study_sessions?course_id=7&start_date=2026-09-07&end_date=2026-09-13&sort=-duration_minutes
```

"My CS-210 sessions from last week, longest first."

Note that filters live in the **query string**, not the path. `/study_sessions` always
identifies the same collection; the parameters narrow which members come back. Contrast
this with `/study_sessions/42`, where the id is part of the resource's identity. This is
the distinction Part 1 exercised with `/posts?userId=3` versus `/posts/1`.

---

## Section 4 — Request/Response Schemas

### 4.1 — POST `/study_sessions` — Create a new session

**Request body:**

```json
{
  "course_id": 7,
  "started_at": "2026-09-10T14:30:00Z",
  "duration_minutes": 90,
  "notes": "Worked through the recursion problem set, sections 3 and 4.",
  "was_productive": true
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `course_id` | integer | Yes | Must reference a course the student is enrolled in |
| `started_at` | datetime | Yes | ISO 8601 with timezone offset; cannot be in the future |
| `duration_minutes` | integer | Yes | Between 1 and 1440 |
| `notes` | string | No | Maximum 2000 characters; `null` allowed |
| `was_productive` | boolean | No | Defaults to `null` if omitted |

`student_id` is **not** in the request body. The server reads it from the JWT. Accepting
it from the client would let anyone log sessions to another student's account by
changing one number.

**Success response — `201 Created`:**

```
Location: /study_sessions/1042
```

```json
{
  "id": 1042,
  "student_id": 3,
  "course_id": 7,
  "course_code": "CS-210",
  "started_at": "2026-09-10T14:30:00Z",
  "duration_minutes": 90,
  "notes": "Worked through the recursion problem set, sections 3 and 4.",
  "was_productive": true,
  "created_at": "2026-09-10T16:02:11Z",
  "updated_at": "2026-09-10T16:02:11Z"
}
```

The response echoes the full stored resource, including the server-assigned `id` and
the timestamps the client never sent. `course_code` is denormalized into the response
so a client rendering a list does not have to fetch each course separately — this is
the round-trip problem PokeAPI has, noted in the Part 1 documentation.

---

### 4.2 — POST `/goals` — Set a weekly target

**Request body:**

```json
{
  "course_id": 7,
  "week_start_date": "2026-09-07",
  "target_minutes": 600
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `course_id` | integer | Yes | Must reference an enrolled course |
| `week_start_date` | date | Yes | `YYYY-MM-DD`, must be a Monday |
| `target_minutes` | integer | Yes | Between 1 and 10080 (minutes in a week) |

**Success response — `201 Created`:**

```json
{
  "id": 88,
  "student_id": 3,
  "course_id": 7,
  "course_code": "CS-210",
  "week_start_date": "2026-09-07",
  "week_end_date": "2026-09-13",
  "target_minutes": 600,
  "target_hours": 10.0,
  "created_at": "2026-09-07T08:14:02Z"
}
```

`target_minutes` is what gets stored; `target_hours` is a convenience field computed for
display. Storing the integer and deriving the decimal avoids floating-point drift when
summing many records — a 1.5-hour session stored as `90` is exact, stored as `1.5` is
not.

---

### 4.3 — GET `/students/{id}/progress` — Weekly progress summary

**Request:**

```
GET /students/3/progress?week_start=2026-09-07
Authorization: Bearer <jwt>
```

**Response — `200 OK`:**

```json
{
  "student_id": 3,
  "week_start_date": "2026-09-07",
  "week_end_date": "2026-09-13",
  "generated_at": "2026-09-10T16:45:00Z",
  "totals": {
    "sessions_logged": 9,
    "minutes_logged": 612,
    "target_minutes": 900,
    "percent_complete": 68.0,
    "on_track": false
  },
  "by_course": [
    {
      "course_id": 7,
      "course_code": "CS-210",
      "course_name": "Data Structures",
      "goal_id": 88,
      "target_minutes": 600,
      "minutes_logged": 480,
      "percent_complete": 80.0,
      "sessions_logged": 5,
      "on_track": true
    },
    {
      "course_id": 12,
      "course_code": "MATH-165",
      "course_name": "Calculus I",
      "goal_id": 91,
      "target_minutes": 300,
      "minutes_logged": 132,
      "percent_complete": 44.0,
      "sessions_logged": 4,
      "on_track": false
    }
  ],
  "courses_without_goals": [
    { "course_id": 19, "course_code": "ENG-105", "minutes_logged": 45 }
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `student_id` | integer | |
| `week_start_date` / `week_end_date` | date | Bounds the reporting window |
| `generated_at` | datetime | This resource is computed, not stored — this is when |
| `totals.sessions_logged` | integer | |
| `totals.minutes_logged` | integer | Sum across all courses |
| `totals.percent_complete` | decimal | One decimal place |
| `totals.on_track` | boolean | True when pace meets the elapsed share of the week |
| `by_course` | array of objects | One entry per course with a goal this week |
| `courses_without_goals` | array of objects | Time logged where no target was set |

`courses_without_goals` exists because the honest answer to "what is my progress" has to
include effort that no goal accounts for. Omitting it would let a student log four hours
on ENG-105 and see it vanish from their summary.

---

### 4.4 — GET `/study_sessions` — Filtered list

**Request:**

```
GET /study_sessions?course_id=7&start_date=2026-09-07&limit=2
Authorization: Bearer <jwt>
```

**Response — `200 OK`:**

```json
{
  "data": [
    {
      "id": 1042,
      "course_id": 7,
      "course_code": "CS-210",
      "started_at": "2026-09-10T14:30:00Z",
      "duration_minutes": 90,
      "notes": "Worked through the recursion problem set, sections 3 and 4.",
      "was_productive": true
    },
    {
      "id": 1038,
      "course_id": 7,
      "course_code": "CS-210",
      "started_at": "2026-09-09T09:00:00Z",
      "duration_minutes": 45,
      "notes": null,
      "was_productive": false
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 2,
    "offset": 0,
    "next": "/study_sessions?course_id=7&start_date=2026-09-07&limit=2&offset=2",
    "previous": null
  },
  "filters_applied": {
    "course_id": 7,
    "start_date": "2026-09-07"
  }
}
```

Three deliberate choices here:

The results are wrapped in a `data` key rather than returned as a bare array. A bare
array leaves nowhere to put pagination metadata without changing the response type
later — a breaking change.

`pagination.next` is a **complete URL**, so the client follows a link instead of
rebuilding the query string with a new offset. PokeAPI does exactly this, and it was the
easiest part of Part 1 to consume.

`filters_applied` echoes what the server understood. If a client sends `start_date` and
the server silently ignores a typo like `startdate`, the client sees an unfiltered list
and has no way to tell. Echoing the filters makes that failure visible.

---

## Section 5 — Authentication

### Method: JWT (JSON Web Tokens)

**Rationale.** The three realistic options each fit a different shape of problem:

**API keys** are static, long-lived, and identify an *application* rather than a person.
They fit server-to-server integrations. Study Tracker needs to know *which student* is
calling, and a key that never expires is a liability on a mobile device that might be
lost.

**OAuth 2.0** exists so a user can grant a third party limited access to their data on
another service — the "sign in with Google" flow. Study Tracker owns its own accounts
and has no third parties requesting delegated access. OAuth here would mean implementing
an authorization server, consent screens, and scope management to solve a problem the
app does not have.

**JWT** fits. A student posts credentials to `/auth/login` once and receives a signed
token carrying their `student_id` and an expiry. Every later request sends it in an
`Authorization: Bearer <token>` header. The server verifies the signature and reads the
student id without a database lookup, which matters because ownership has to be checked
on nearly every endpoint.

Access tokens expire after 30 minutes; a longer-lived refresh token obtains new ones via
`/auth/refresh`. This bounds the damage from a stolen token, and refresh tokens are
stored server-side so they can be revoked — something a plain JWT cannot do on its own.

### Required table

| Endpoint | Auth Required | Notes |
|---|---|---|
| `GET /courses` | **No** | The catalog is public. Students need to browse it before registering, and course codes are not sensitive. |
| `POST /study_sessions` | **Yes** | Any authenticated student. `student_id` comes from the token, never the body, so a student can only log sessions to their own account. |
| `GET /students/{id}/progress` | **Yes — self only** | The `{id}` in the path must match the `student_id` in the token. A mismatch returns `403 Forbidden`. |
| `DELETE /study_sessions/{id}` | **Yes — owner only** | Only the student who created the session may delete it. Anyone else gets `404 Not Found` rather than `403` (see below). |

### Full access matrix

| Endpoint | Public | Any authenticated student | Owner only | Admin |
|---|---|---|---|---|
| `POST /students` | ✅ | | | |
| `POST /auth/login` | ✅ | | | |
| `POST /auth/refresh` | ✅ | | | |
| `GET /courses` | ✅ | | | |
| `GET /courses/{id}` | ✅ | | | |
| `POST /courses` | | ✅ | | |
| `PATCH /courses/{id}` | | | | ✅ |
| `GET /students/{id}` | | | ✅ | ✅ |
| `PATCH /students/{id}` | | | ✅ | |
| `DELETE /students/{id}` | | | ✅ | |
| `GET /students/{id}/courses` | | | ✅ | |
| `POST /enrollments` | | ✅ | | |
| `DELETE /enrollments/{id}` | | | ✅ | |
| `GET /study_sessions` | | ✅ | | |
| `GET /study_sessions/{id}` | | | ✅ | |
| `POST /study_sessions` | | ✅ | | |
| `PUT /study_sessions/{id}` | | | ✅ | |
| `PATCH /study_sessions/{id}` | | | ✅ | |
| `DELETE /study_sessions/{id}` | | | ✅ | |
| `GET /courses/{id}/study_sessions` | | ✅ | | |
| `GET /goals` | | ✅ | | |
| `POST /goals` | | ✅ | | |
| `PUT /goals/{id}` | | | ✅ | |
| `DELETE /goals/{id}` | | | ✅ | |
| `GET /students/{id}/progress` | | | ✅ | |

### Two rules that apply everywhere

**Collections are implicitly scoped to the caller.** `GET /study_sessions` never means
"all sessions in the database." It means "the sessions belonging to whoever holds this
token." There is no way to widen it, because there is no query parameter for
`student_id`.

**404 instead of 403 for another student's records.** Requesting
`GET /study_sessions/999` when session 999 belongs to someone else returns
`404 Not Found`, not `403 Forbidden`. A `403` would confirm the record exists, letting
someone enumerate ids to learn how many sessions other students have logged. `403` is
reserved for cases where the caller can already see the resource exists — for example,
requesting `/students/8/progress` while holding student 3's token, where the path itself
gives it away.

---

## Section 6 — Error Responses for POST `/study_sessions`

Every error uses the same body shape, so a client can parse failures with one code path:

```json
{
  "error": {
    "status": 422,
    "code": "validation_failed",
    "message": "duration_minutes must be between 1 and 1440.",
    "field": "duration_minutes"
  }
}
```

| Status Code | When it occurs |
|---|---|
| **201 Created** | The session was logged. Response carries the full resource including the new `id`, and a `Location` header pointing at `/study_sessions/{id}`. |
| **400 Bad Request** | The request is malformed *as a request*: body is not valid JSON, `Content-Type` is not `application/json`, or a required field (`course_id`, `started_at`, `duration_minutes`) is missing entirely. |
| **401 Unauthorized** | No `Authorization` header, a malformed token, a bad signature, or an expired access token. The name is a misnomer — this means "unauthenticated." The client should refresh its token and retry once. |
| **403 Forbidden** | Authentication succeeded but the action is not permitted — for example, the account is suspended. Distinct from 401: retrying with a fresh token will not help. |
| **404 Not Found** | The `course_id` in the body does not correspond to any course, or names a course the student is not enrolled in. Enrollment is treated as a visibility boundary, so an unenrolled course is indistinguishable from a nonexistent one. |
| **409 Conflict** | The session overlaps in time with one the student already logged. You cannot study two courses in the same 90 minutes, and silently accepting the overlap would inflate the progress totals. |
| **422 Unprocessable Entity** | The JSON is well-formed and every required field is present, but a value is semantically invalid: `duration_minutes` is 0, negative, or above 1440; `started_at` is in the future; `notes` exceeds 2000 characters; `started_at` is not parseable as ISO 8601. |
| **429 Too Many Requests** | Rate limit exceeded — more than 100 writes per minute from one account. Includes a `Retry-After` header. Guards against a buggy client looping. |
| **500 Internal Server Error** | Something broke on the server. The client did nothing wrong and should not modify the request before retrying. |
| **503 Service Unavailable** | Database unreachable or the service is in maintenance. Retriable, with `Retry-After`. |

### The 400 / 422 distinction

This is the pairing most often collapsed into a single status, and keeping them separate
carries real information.

**400** means *I could not understand your request.* Parsing failed. The server never
got as far as looking at the values.

**422** means *I understood your request perfectly and it is still wrong.* Parsing
succeeded, the fields are present and correctly typed, but a value violates a business
rule.

The difference tells a client where the bug is. A 400 points at request construction —
serialization, headers, a missing field. A 422 points at the data itself, and its
`field` key names exactly which input to highlight in the UI. Returning 400 for both
tells a client something failed without telling it where to look.

---

## Appendix — Design decisions worth defending

*Three decisions where a reasonable person could have chosen otherwise.*

### 1. Courses are a shared catalog, not per-student records

**The alternative:** every student creates their own private `Course` rows. Simpler —
no join table, no many-to-many, and `GET /courses` becomes owner-scoped like everything
else.

**Why I chose the catalog.** With private courses, forty students in CS-210 create forty
unlinked records, half of them spelled differently — "CS 210," "cs-210," "Data
Structures." Any future feature that compares across students, or even reports how many
people are tracking a course, becomes impossible after the fact. Shared courses also
make `GET /courses` genuinely public, which gives a new student something to browse
before registering.

**The cost, stated honestly.** `POST /courses` lets any authenticated student write to
shared data, which invites duplicates and typos. Mitigations: a uniqueness constraint on
`code`, a search endpoint so students find existing courses before adding one, and
`PATCH /courses/{id}` restricted to admins so corrections are controlled.

### 2. Progress is computed, not stored

`GET /students/{id}/progress` has no table behind it. The server sums sessions and
compares them to goals at request time.

**Why.** A stored progress record would need updating on every session create, update,
and delete, and on every goal change. Any missed path leaves a permanently wrong number
with no way to detect the drift. Computing on read means progress cannot disagree with
the sessions it summarizes — it is derived from them by definition.

This is also why progress is read-only. There is no `POST /progress`, because progress
is not a thing you can assert. It is a consequence of the sessions you logged.

Part 1 surfaced the reverse of this problem: Open-Meteo is entirely computed and reports
`generationtime_ms` on every response. This design borrows that idea with
`generated_at`, so a client can tell how fresh a summary is.

### 3. `duration_minutes` instead of `ended_at`

**The alternative:** store `started_at` and `ended_at`, derive duration.

**Why duration won.** Students log sessions retroactively — "I studied about two hours
last night." That produces an honest duration and a guessed end time. Storing
`ended_at` would force the client to invent a precise timestamp to represent an
imprecise memory, and that fabricated value would look identical to a real one.

Storing an integer count of minutes also keeps summation exact, which matters when a
progress report adds up dozens of sessions.

**The cost:** overlap detection has to compute `started_at + duration_minutes` rather
than compare two stored timestamps. That is a small amount of arithmetic in exchange for
not storing a number the student never actually knew.

### 4. Naming: `study_sessions` over `study-sessions`

The template uses snake_case, so this document follows it for consistency. Worth noting
for the presentation, though: kebab-case (`/study-sessions`) is the more common
convention in public APIs, because URIs are case-insensitive in the hostname but
case-sensitive in the path, and hyphens avoid the underscore's habit of disappearing
under text underlining. Either is defensible. What matters is that a single API picks
one and never mixes them.
