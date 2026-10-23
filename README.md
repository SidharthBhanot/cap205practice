# Student Academic Obligation Reconciliation System

A complete **CAP205 Next Gen Computing** software prototype for reconciling academic records from multiple manually recorded sources. It preserves the source evidence, explains rule-based comparisons, detects inconsistencies, and leaves verification decisions to a person.

**Stack:** HTML5, CSS3, vanilla JavaScript, Python/FastAPI, SQLite/SQLAlchemy, JSON REST APIs and pytest. No frontend framework, AI/ML, hardware, paid API, portal integration, email reader or PDF parser is used.

## Start here

You need **Python 3.11 or newer** and a modern browser. Python 3.12 was used for verification. Install dependencies once with an internet connection; the application itself then runs locally without external services. No Node.js or frontend build step is required.

If using the downloadable archive, extract it and open a terminal **inside `student-academic-reconciliation`**, the folder containing this README.

To get the project from GitHub instead:

```bash
git clone https://github.com/SidharthBhanot/cap205practice.git
cd cap205practice
```

Run the following commands from that project folder.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m backend.init_db
python -m backend.seed_data
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Windows PowerShell

These commands do not require changing PowerShell's execution policy:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m backend.init_db
.\.venv\Scripts\python.exe -m backend.seed_data
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**. The backend serves the complete frontend at `/app/index.html`. Click **Run reconciliation** to populate the comparison results and verification queue. Stop the server with Ctrl+C.

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The Swagger UI's default JavaScript/CSS assets are delivered by a CDN; API routes and the application interface still run offline after installation. `/openapi.json` is available locally without those assets.

### Start with an empty workspace

Skip `python -m backend.seed_data`. Schema initialization also happens automatically at server startup. Add a course from **Obligations → Add course**, register an information source, and then add records.

The separate seed command adds **12 explicitly synthetic records**, 4 sources and 3 courses. It never runs automatically. Running it again is a no-op. It refuses to mix samples into a nonempty, unseeded database. No real student information is included.

### Serve the frontend separately (optional)

Keep FastAPI running on port 8000. In a second terminal, from the project root:

```bash
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500). `frontend/js/config.js` selects the same-origin API when served under `/app/`, and port 8000 on the frontend’s hostname for the separate frontend. CORS permits `localhost:5500` and `127.0.0.1:5500`. Do not open the HTML files directly using `file://`; browser JavaScript modules and API requests require HTTP.

If you change the API port for the separate-frontend arrangement, add `<meta name="api-base" content="http://localhost:9000">` to each frontend HTML head (using your backend address) and the server's `FRONTEND_ORIGINS` as needed. The recommended same-origin arrangement requires no configuration.

## What is implemented

| Screen | Working operations |
|---|---|
| Overview | Live record/source/course totals, open duplicate pairs, open material conflicts, incomplete records, recent records, issue queue and comparison breakdown |
| Obligations | Create, view, edit and delete; preserve original title; course/type/status/source selection; optional deadline and source URL |
| Record search | Search title, description, course code/name and source; filter course, type, status and deadline range; missing-deadline filter; sorting and pagination |
| Information sources | Register, view, edit and delete unused sources; source types, descriptions, URLs and manual last-checked timestamp |
| Reconciliation | Trigger an atomic rule-based run; view compared records and explanations; filter by classification, course and issue type |
| Verification queue | Review source evidence side by side, view current records, set one of four statuses and save resolution notes |

The interface includes loading/empty/error states, success notifications, deletion confirmations, escaped user text, keyboard-accessible native dialogs, readable responsive layouts and a mobile navigation toggle. All record data comes from the API; there are no hardcoded dashboard totals or browser-only data stores.

Sources always mean **manually registered provenance**. A source named “LMS” does not indicate an active LMS connection. Source links open the recorded reference; the application does not fetch them.

## Required Java-assignment demonstration

The seed creates these exact examples:

| Record | Course | Title | Type | Deadline | Source |
|---|---|---|---|---|---|
| A | Java Programming | Assignment 2 | Assignment | 20 October 2026 | LMS |
| B | Java Programming | Assignment 2 | Assignment | 22 October 2026 | Faculty Notice |

After running reconciliation, their classification is **CONFLICT**, with a **DEADLINE_CONFLICT** issue initially marked **Needs Verification**. Both dates and source details remain visible. Neither date is declared correct. Repeating reconciliation preserves the issue ID and creates no duplicate issue.

On the untouched synthetic sample, one run compares **6 of 66 possible pairs**, with:

| Classification | Count | Example |
|---|---:|---|
| MATCH | 1 | Prototype project submission from LMS and Course Email |
| POTENTIAL_MATCH | 2 | Collections quiz with one missing deadline; Project proposal versus Project proposal draft |
| CONFLICT | 1 | Java Assignment 2, 20 October versus 22 October |
| UNRELATED | 2 | The Java Assignment 2 records compared with the same title in Discrete Mathematics |

The run creates 9 issues: 1 deadline conflict, 3 duplicate candidates, 2 missing deadlines, 2 incomplete-information issues, and 1 possibly outdated record. The seed's outdated record is dated relative to the seeding time so this demonstration remains reproducible. **Counts are properties of this sample, not hardcoded UI values.**

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a short presentation walkthrough.

## Architecture and project structure

The browser sends JSON to FastAPI. API schemas validate input and enforce enumeration choices. SQLAlchemy persists records to SQLite with foreign-key enforcement enabled on every connection. The pure reconciliation and validation modules produce findings; the service layer persists a run transactionally.

| Path | Responsibility |
|---|---|
| `frontend/*.html` | Five independently navigable pages |
| `frontend/css/styles.css` | Shared responsive visual system |
| `frontend/js/api.js`, `config.js` | JSON requests, errors, API configuration |
| `frontend/js/common.js` | Layout, dialogs, safe rendering and shared controls |
| `frontend/js/dashboard.js`, `obligations.js`, `sources.js`, `results.js`, `conflicts.js` | Page-specific API workflows |
| `backend/main.py` | Application factory, lifespan, error handlers, CORS and static frontend |
| `backend/database.py`, `init_db.py` | Engine/session setup, SQLite FK checks and explicit initialization |
| `backend/models.py` | SQLAlchemy tables and relationships |
| `backend/schemas.py`, `constants.py` | Validated write schemas and controlled values |
| `backend/reconciliation.py` | Normalization, similarity, identity comparison and candidate selection |
| `backend/validation.py` | Missing/incomplete/outdated and pair-issue detection |
| `backend/services.py` | Transactional persistence, stable fingerprints and review preservation |
| `backend/serializers.py` | JSON records and source evidence snapshots |
| `backend/routers/` | Record, issue, reconciliation and dashboard REST endpoints |
| `backend/seed_data.py` | Separate, non-destructive synthetic sample loader |
| `backend/tests/` | pytest unit and API/database integration tests |

### Data model

| Table | Identity and relationships |
|---|---|
| `courses` | Integer PK, unique code; one-to-many obligations |
| `sources` | Non-reused integer PK, unique name; source type, description, URL and timestamps; one-to-many obligations |
| `obligations` | Non-reused integer PK; optional course FK, required source FK; original title, description, type, deadline, status, URL and timestamps |
| `conflicts` | Integer PK, unique fingerprint; issue type, original record IDs, JSON source snapshots, explanation, timestamps, current flag, review status and notes |
| `conflict_obligations` | Composite PK and real FKs linking live obligations to issues; links cascade on record deletion |
| `reconciliation_results` | Unique pair; nullable live-record FKs, classification, similarity, reason, source snapshots, related issue IDs and run timestamp |
| `app_state` | Data revision, reconciled revision, last run/configuration, sample-data marker and latest summary |

Deleting a live obligation removes its association links and nulls result FKs, while issue snapshots retain the original IDs and source details. Deleting a source still used by obligations returns HTTP 409. Course deletion is deliberately not exposed. Results represent the latest run; issues survive across runs.

## Explainable reconciliation rules

### Normalization and title score

`normalize_title()` applies Unicode NFKC, case folding, punctuation-to-space conversion, whitespace collapse and numeric leading-zero removal. Thus `  ASSIGNMENT-02! ` becomes `assignment 2` **only for comparison**. The stored original string is unchanged.

`calculate_title_similarity()` computes:

```text
score = 0.60 × token-set Jaccard
      + 0.40 × symmetric SequenceMatcher ratio on sorted unique tokens
```

The character ratio averages both argument orders to avoid asymmetric results. Empty titles score zero. The score is deterministic evidence, **not a probability or a confidence learned by AI**.

### Candidate selection

`reconcile_obligations()` indexes informative title tokens by course and compares records sharing an informative token within a course. Generic words such as “assignment” alone are not blocking keys. It also audits exact normalized-title collisions globally, allowing the interface to explain why same-titled work in different courses is unrelated. Empty titles produce validation issues; unknown-course records require an exact title collision to enter the candidate set.

This skips most irrelevant pairs without asserting that skipped pairs were inspected. Large buckets can still require quadratic comparisons; this is a small local prototype, not a high-volume search service.

### Classification policy

1. Different known course IDs are **UNRELATED**, even with identical titles. Distinct numbers in both titles are also unrelated. Low title scores are unrelated.
2. Missing course identity, a generic title, an identifier present in only one title, a score below the strong threshold, or an unspecified type produces **POTENTIAL_MATCH** where sufficient candidate evidence exists.
3. Strong course/title identity with differing known dates or incompatible specific types produces **CONFLICT**. Both material differences are listed when present. Type disagreements create `INCOMPLETE_INFORMATION` issues because the requested issue taxonomy has no separate type-conflict category.
4. A missing deadline is uncertainty: **POTENTIAL_MATCH** plus a per-record `MISSING_DEADLINE` issue. Two absent dates never establish a confident match, and absence is never a deadline conflict.
5. Strong course/title/type evidence with equal known deadlines produces **MATCH**. Fuzzy titles from one source remain potential matches; exact duplicates within one source can still match.

Descriptions and student progress statuses are preserved but are not interpreted as semantic identity evidence. A title number is treated as an identifier, which is conservative and can miss renamed or renumbered work. Course IDs are authoritative registry identities; the prototype does not infer course aliases.

### Issue policy and human review

- `DEADLINE_CONFLICT`: strong same-obligation evidence with two different recorded dates.
- `DUPLICATE`: a match or potential match that a human should review; this is a **pair**, not an automatically merged obligation.
- `MISSING_DEADLINE`: no due date is recorded.
- `INCOMPLETE_INFORMATION`: absent course, empty/punctuation-only title, absent/“Other” type, or inconsistent types across a strongly identified pair. A blank description alone is allowed.
- `OUTDATED_INFORMATION`: an active record for which neither the record update nor the source's manual last-check time is within the configured age window. Completed/cancelled records are exempt. Age is a prompt to verify, not proof the data is wrong. Being overdue alone is insufficient.

Statuses: **Needs Verification**, **Under Review**, **Resolved**, **Dismissed**. Only an explicit API/UI review changes a status. There is no automatic winner, merge, deadline correction or resolution.

Fingerprints are `ISSUE_TYPE:sorted_record_ids`. Repeated runs update the same issue. `BEGIN IMMEDIATE` serializes competing SQLite writes before reconciliation reads the records; run persistence is all-or-nothing. Notes, review status and initial detection time survive unchanged evidence. If material evidence changes after a review, `evidence_changed` requests verification again while preserving the prior status and notes. The result's effective verification becomes Needs Verification. If a condition disappears, the issue becomes historical; it is **not** silently resolved. Use “Include historical issues” to view it.

Evidence snapshots are refreshed when that issue is detected again. This is not a full event-sourced audit log: older versions of an issue's evidence and earlier edits to notes are not retained.

## Configuration

Set environment variables before starting the backend. `.env.example` documents them; it is **not automatically loaded**.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | Absolute path to `backend/data/academic.db` | SQLite connection string. Parent directories for custom file paths must already exist. |
| `MATCH_THRESHOLD` | `0.90` | Minimum title score for strong identity evidence |
| `POTENTIAL_THRESHOLD` | `0.62` | Minimum title score for a possible identity |
| `STALE_DAYS` | `30` | Minimum age window for possible outdated information |
| `FRONTEND_ORIGINS` | `http://localhost:5500,http://127.0.0.1:5500` | Comma-separated permitted separate-frontend origins |

Require `0 <= POTENTIAL_THRESHOLD < MATCH_THRESHOLD <= 1` and `STALE_DAYS >= 1`. Invalid settings stop startup with a clear error. The active values are visible in the results page and `GET /reconciliation/config`.

Linux/macOS example:

```bash
export MATCH_THRESHOLD=0.92
export POTENTIAL_THRESHOLD=0.65
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell example:

```powershell
$env:MATCH_THRESHOLD = "0.92"
$env:POTENTIAL_THRESHOLD = "0.65"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Changing data or active rule settings marks previous results as stale. Reconciliation is manual, so time-dependent findings are refreshed only when you run it. Dates are calendar dates without a time zone or submission-hour precision. Record/check timestamps are stored in UTC and displayed in your browser's local time.

## API reference

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | API and database availability |
| GET, POST | `/courses` | List or create courses |
| GET, POST | `/sources` | Search/list or create information sources |
| GET, PUT, DELETE | `/sources/{id}` | View, fully update, or delete an unused source |
| GET, POST | `/obligations` | Search/filter/sort/list or create records |
| GET, PUT, DELETE | `/obligations/{id}` | View, fully update, or delete a record |
| GET | `/conflicts` | List/filter issues, optionally include historical issues |
| GET | `/conflicts/{id}` | Evidence snapshots and current live records |
| PUT | `/conflicts/{id}/status` | Explicit review status and notes |
| POST | `/reconcile` | Run reconciliation and return summary |
| GET | `/reconciliation/results` | Filtered latest comparison results |
| GET | `/reconciliation/config` | Active thresholds and method description |
| GET | `/dashboard` | API-derived overview and recent/priority records |

Obligation, conflict and result lists return `{items, total, offset, limit}`. Their default limit is 100, maximum 500. Course/source lists are arrays. Use Swagger UI for typed parameters and request schemas.

Examples of list filters:

```text
/obligations?q=Assignment&course_id=1&obligation_type=Assignment&sort_by=deadline&order=asc
/obligations?deadline_from=2026-10-01&deadline_to=2026-10-31&status=Planned
/obligations?missing_deadline=true&offset=0&limit=20
/conflicts?status=Needs%20Verification&conflict_type=DEADLINE_CONFLICT&current_only=true
/reconciliation/results?classification=CONFLICT&course_id=1&issue_type=DEADLINE_CONFLICT
```

Create an obligation (course/source IDs must exist):

```json
{
  "course_id": 1,
  "source_id": 1,
  "title": "Assignment 2",
  "description": "Deadline copied from the recorded source.",
  "obligation_type": "Assignment",
  "deadline": "2026-10-20",
  "status": "Planned",
  "reference_url": null
}
```

Allowed obligation statuses are Planned, In Progress, Completed and Cancelled. PUT endpoints replace editable fields; omitted optional fields receive schema defaults, so API callers should send the complete editable record. IDs and timestamps are not writable. Source IDs are mandatory; incomplete title/course/type/deadline fields are intentionally permitted and flagged during reconciliation.

Success codes: 200 reads/updates, 201 creates, 204 deletes. Errors: 404 missing record, 409 duplicate key or protected relationship, 422 invalid input/reference, 503 busy/unavailable database. Error payloads contain `detail`. All writes use validated schemas and SQLAlchemy queries, and URLs must use HTTP(S) without embedded credentials.

## Tests and verification

From the project root, with the environment activated:

```bash
python -m pytest -q
```

Windows without activation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use temporary SQLite databases and do not modify your application database. They cover normalization, similarity, classifications, missing and incomplete evidence, staleness, candidate selection, repeated and concurrent reconciliation, explicit decisions, changed evidence, historical issues, CRUD, API validation, filters, source immutability and actual database foreign keys. See [VERIFICATION.md](VERIFICATION.md) for the executed checks and their limits.

## Local data, troubleshooting and limitations

- Data persists in `backend/data/academic.db`. The archive contains source and the reproducible seed script, not a pre-populated mutable database. To back up, stop the server and copy the database file. Retain related journal/WAL files if present before assuming a live copy is complete.
- For a separate demonstration database, set `DATABASE_URL=sqlite:///demo.db` (or `$env:DATABASE_URL = "sqlite:///demo.db"` in PowerShell), then initialize and seed. Stop/restart the backend with the same variable. This avoids deleting your existing work.
- “Cannot reach the API”: verify the server is running and open `/health`. Use HTTP, not a direct file open. If using the optional separate frontend, check its API base and allowed origin.
- “Address already in use”: stop the other local process you started, or choose another API port and update the separate frontend configuration if applicable.
- “Source is used by obligations”: reassign those obligations or deliberately delete them before deleting the source. Existing issue snapshots remain.
- This is a **single-user local academic prototype** without login, roles or internet-facing deployment hardening. Keep the server bound to `127.0.0.1`. It does not send reminders, scrape portals, parse documents, read email or automatically verify facts.
- The rule engine cannot resolve ambiguous language, renamed courses or semantic synonyms. Candidate blocking trades recall for lower comparison cost. A human must examine the original evidence.
- Results are the latest run, not full run history. Issue IDs/notes persist, but every historical edit is not logged. No schema migration framework is included; schema initialization is for a fresh prototype database.
- Dashboard duplicate counts represent open issue pairs, and conflict counts represent open material-conflict issues. They do not claim a count of unique “true” assignments. Missing-information counts are calculated from live records; reconciliation totals reflect the latest run and are labelled stale when needed.
- SQLite and list processing suit a modest local dataset; large same-title buckets and in-memory result filters are not designed for an institution-wide deployment.

Reference documentation: [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy SQLite foreign-key support](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support), [pytest](https://docs.pytest.org/).

Optional frontend API regression checks (Node.js 18+, development only):

```bash
node --test frontend/tests/api.test.mjs
```

Sources includes Refresh, Clear filters, and in-place retries. A failed request displays the API address and distinguishes a connection failure from a static server returning HTML. Use the FastAPI-served URL above if opening the HTML directly leaves the loading message visible.
