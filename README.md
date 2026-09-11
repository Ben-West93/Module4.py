# Module 4 Project — API Explorer & API Design

Submission is split into two folders, one per part.

---

## part1/ — API Explorer

Consuming real public APIs.

| File | What it is |
|---|---|
| `api_explorer.py` | **Required.** The script. 13 live calls across three APIs. |
| `api_documentation.md` | **Required.** Documentation of all three APIs. |
| `requirements.txt` | **Required.** The `requests` dependency. |
| `curl_examples.txt` | Optional. The same calls as curl commands. |
| `sample_output.txt` | Optional. Captured output from a real run. |

To run it:

```bash
pip install -r requirements.txt
python api_explorer.py
```

APIs used: JSONPlaceholder, PokeAPI, Open-Meteo. None require a key.

Note: the starter file listed REST Countries v3.1 as the third API. That
version has been deprecated and no longer returns data, so Open-Meteo was
substituted. The failure is documented in the appendix of
`api_documentation.md`.

---

## part2/ — API Design

Designing the Study Tracker API on paper.

| File | What it is |
|---|---|
| `api_design.md` | **Required.** The design document, Sections 1–6. |

Covers 5 resources, 25 endpoints, request/response schemas with data types,
a JWT authentication plan, and error responses for `POST /study_sessions`.

An appendix at the end lays out four design decisions with their trade-offs —
useful for the "explain one design decision" part of the presentation.

---

**Before submitting:** fill in the date at the top of `part2/api_design.md`.
