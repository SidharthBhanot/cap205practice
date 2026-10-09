# Verification record

Verified on 9 October 2026 using Python 3.12.14, FastAPI 0.115.12, SQLAlchemy 2.0.41 and pytest 8.4.1.

## Automated backend checks

Command, from the project root:

```bash
python -m pytest -q
```

Result: **67 passed in 2.57 seconds**. One third-party deprecation warning was emitted by Starlette's TestClient about the installed AnyIO `BlockingPortal` alias. It did not affect the test result. The six direct dependencies are pinned in `backend/requirements.txt`; indirect dependencies may differ on a later installation.

The tests use isolated temporary SQLite files. They cover:

- Unicode/punctuation/whitespace normalization, leading-zero numbers, empty titles, bounded symmetric similarity and invalid thresholds.
- Matching, conflicting dates, potential matches, different courses, different assignment numbers, generic titles, type disagreement and missing evidence.
- Candidate blocking, deterministic ordering, incomplete information and the explicit outdated-record rule.
- Health, static frontend serving, OpenAPI/Swagger routes, full CRUD, reference updates, search, filters, sorting and pagination.
- HTTP 404, 409 and 422 errors, invalid dates/URLs/statuses, extra fields and nonexistent references.
- Real SQLite foreign-key enforcement, protected source deletion, non-reused source IDs and retained evidence after deleting live records.
- Repeated and concurrent reconciliation without duplicate issues.
- All four review statuses, notes preserved across runs, changed evidence flagged after review, and historical issues never automatically resolved.
- Separate initialization and seed commands, repeat-safe seeding and refusing to mix samples with pre-existing user data.

## Seeded scenario checks

The required Java Programming Assignment 2 pair produced a DEADLINE_CONFLICT with Needs Verification, preserving LMS / 20 October 2026 and Faculty Notice / 22 October 2026.

The untouched sample produced 6 comparisons: 1 MATCH, 2 POTENTIAL_MATCH, 1 CONFLICT and 2 UNRELATED. It skipped 60 other possible pairs and created 9 issues. A second run created zero new issues and retained issue IDs.

## Frontend/API workflow checks

All eight frontend JavaScript modules passed `node --check` during authoring. This was a syntax check only; Node is not a runtime dependency of the delivered application.

An additional **17 DOM-level workflow checks passed** against a real locally running Uvicorn/FastAPI server and a freshly seeded SQLite database. The checks exercised the actual frontend modules and JSON requests:

1. Dashboard totals load from the API.
2. Dashboard reconciliation displays both conflicting deadlines.
3. Results show verification status.
4. Classification filtering displays the relevant sources.
5. Missing deadlines are displayed as uncertainty.
6. Issue details display both source snapshots.
7. The review form persists status to SQLite.
8. Notes survive another run triggered through the frontend.
9. The source form creates a real source.
10. The source form edits a real source.
11. The course form creates a course.
12. The obligation form creates a traceable record.
13. HTML-like titles are escaped as text.
14. Editing an obligation saves the changed deadline.
15. Cancelling deletion preserves the record.
16. Confirming deletion removes the record.
17. An unused source can be deleted.

These authoring checks used a DOM simulation with native-dialog behaviour shimmed; **they are not visual or full-browser tests**. The delivered automated test suite is pytest, as requested. The browser preview was unavailable in this environment, so rendered layout, responsive appearance, native-dialog focus behaviour and cross-browser accessibility have not been visually verified.

## Local browser acceptance checklist

After following README setup, use your actual browser to check:

- Open all five pages and run reconciliation.
- Verify the Java conflict's two deadlines and Needs Verification status.
- Open a form with the keyboard, tab through fields and close it with Escape.
- Resize to a narrow/mobile viewport and open the navigation toggle.
- Check the two-column evidence cards stack on narrow screens.
- Set browser zoom to 200% and confirm text/controls remain usable.
- Try a failed operation, such as deleting a referenced source, and verify the error message.

All sample data is synthetic. No real university service was connected or private student data used during verification.
