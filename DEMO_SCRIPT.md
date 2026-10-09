# CAP205 demonstration · 5–6 minutes

## Before the presentation

Follow the README installation, initialization and seed commands. Start the backend, open `http://127.0.0.1:8000`, and keep a terminal available for `python -m pytest -q`. Use a fresh synthetic database so the seeded counts match this script. No external university account is needed.

## 0:00–0:40 · Explain the problem

“Our project is the Student Academic Obligation Reconciliation System. Academic information is often spread across LMS entries, faculty notices, email and PDFs. A planner stores deadlines. Our system compares the source records, explains possible duplicates and conflicts, and tells us what needs verification.”

Show the Overview. Point out the synthetic-data label and manual-entry limitation.

“These are synthetic records. We have not connected to a real LMS or inbox. Every total here comes from the SQLite database through the API.”

## 0:40–1:20 · Establish the conflicting evidence

Open **Obligations**. Search for `Assignment 2` and filter Course to **Java Programming**. Open each record.

“The LMS states 20 October 2026. The Faculty Notice states 22 October. The title, course and type agree, but the dates differ. We retain both original records so the evidence is traceable.”

## 1:20–2:10 · Run and explain reconciliation

Open **Reconciliation**, then click **Run reconciliation**. Filter Classification to **Conflict**.

“This is rule-based, not AI. The engine checks course identity, normalizes titles for comparison, calculates an explainable similarity score, and examines type and date evidence. It detected a likely same obligation with a deadline conflict.”

Read the reason and point out **Needs Verification**.

“It does not declare 20 October or 22 October correct. That requires checking the source with a person.”

Clear the classification filter. Expand **How these comparisons are made**.

“The title score is 60% token overlap and 40% character similarity. A high title score is not sufficient by itself. Candidate rules examine 6 pairs instead of all 66 possible pairs in this sample.”

## 2:10–3:10 · Demonstrate the four outcomes

| Filter | What to show and say |
|---|---|
| Match | Prototype project submission: course, specific title, type and known date agree across sources. Punctuation/capitalization changes do not replace the stored original. |
| Potential match | Collections quiz: one source has no date. Missing information creates uncertainty, not an invented date or a deadline conflict. |
| Potential match | Project proposal versus Project proposal draft: similar wording could still describe distinct milestones. |
| Unrelated | Assignment 2 in Java and Assignment 2 in Discrete Mathematics: identical titles do not override different course identities. |

## 3:10–4:10 · Demonstrate human review and deduplication

Open the Java deadline conflict using its issue link. Show both source records, the explanation, and their dates. Set status to **Under Review** and add:

“Presentation demonstration: both synthetic sources inspected; awaiting faculty verification.”

Save the review. Note the issue ID and total issue count. Run reconciliation again and reopen it.

“The same issue ID, status and notes remain. This second run created zero new issues. Stable fingerprints prevent repeated conflict rows.”

Explain the available Resolved and Dismissed statuses without claiming that either sample deadline has actually been verified. If asked to demonstrate resolution, explicitly label the notes as a **simulated classroom decision**, then resolve it manually. Explain that this changes the issue's status only; it does not alter either deadline.

## 4:10–4:50 · Show other validation and traceability

Open **Verification queue** and filter to **Missing deadline**, then **Incomplete information**, then **Possibly outdated**.

“We detect missing dates and incomplete identity information separately. An old active record is only flagged as possibly outdated; age does not prove it is wrong.”

Open **Information sources** to show source descriptions and last-checked dates. Explain that a manual source check is different from an automated portal connection.

## 4:50–5:40 · Show implementation and tests

Open `/docs` to show the REST API if internet access is available for Swagger's assets. Alternatively, show the local `/openapi.json` and code.

Run:

```bash
python -m pytest -q
```

“Tests cover the four relationship classes, missing evidence, database references, API errors, repeated and concurrent runs, review preservation and changed evidence. The comparison and validation rules are separate from the API routes.”

Finish with the limits:

“This prototype runs locally with manual input. It does not automatically decide which source is trustworthy. Future work could add authorized imports, an audit history and better candidate retrieval, while keeping verification explainable.”

## Optional live CRUD demonstration

Create a temporary Manual source, then add an obligation using an existing course. Leave its deadline blank, run reconciliation, and show the resulting missing-deadline issue. Edit the record with a simulated verified date, run again, and show that the old issue becomes historical without being automatically resolved. Delete only your temporary record and source if desired; the interface asks before deletion.

## Likely viva questions

**Why is this more than a to-do list?** It compares independently recorded facts, classifies relationships, preserves provenance and exposes disagreements with reasons and a review workflow.

**Why not match by title alone?** Different courses can use identical assignment titles; different numbered assignments can look almost identical. Course identity and distinguishing evidence prevent these false matches.

**Why not automatically prefer the faculty notice?** Source type does not prove freshness or correctness. The prototype has no evidence-based authority policy, so a person verifies both records.

**What happens on another run?** The latest results are replaced atomically, current issues are upserted by type plus sorted record IDs, and explicit status/notes are preserved.

**What happens when reviewed evidence changes?** The previous decision remains visible, but the issue is flagged for verification again. The system never quietly treats the old review as approval of new evidence.

**What does “unrelated pairs skipped” mean?** Pairs outside the candidate rules are not compared. This improves efficiency but can miss semantic matches with no shared informative token. Skipping is not proof of unrelatedness.
