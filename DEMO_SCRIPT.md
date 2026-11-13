# CAP205 demonstration · Student Academic Obligation Reconciliation System

## Before the presentation

Start the local FastAPI application by following the README commands. Open `http://127.0.0.1:8000`. The sample database contains synthetic records only. The prototype does not connect to live university ERP/LMS systems, does not parse documents or email, and does not make official clearance decisions.

## 0:00–0:40 · Explain the problem

“Our project is the Student Academic Obligation Reconciliation System. Students may need to confirm that obligations recorded by university departments have been cleared before requesting academic services. The proposed portal brings obligation records together, shows what is pending and explains what needs attention.”

Show the Academic Overview. Explain that the counts are read from the local database and that sample records are synthetic.

## 0:40–1:30 · Show the student obligations

Open **Departmental obligations**. Explain that each record is linked to a student/course context, an issuing department or source, an obligation type, a status and an optional deadline.

“The important point is that the original record is preserved. We do not silently overwrite one department’s information with another source’s version.”

## 1:30–2:20 · Show source and department records

Open **Departments and information sources**. Show how a record's origin is registered, with its type, description, reference URL and manual last-checked time.

“These are manually registered records. A source named LMS or Faculty Notice does not mean we have a live integration. The prototype uses the information entered by the user.”

## 2:20–3:20 · Run rule-based reconciliation

Open **Reconciliation results** and click **Run reconciliation**.

“The system compares records using course identity, normalized titles, obligation type and recorded deadlines. It classifies the relationship as Match, Potential Match, Conflict or Unrelated. The title similarity score is deterministic evidence, not an AI prediction or probability.”

Show a deadline conflict using the synthetic Java Programming Assignment 2 example: LMS says 20 October 2026, while Faculty Notice says 22 October 2026.

“The system does not decide which date is correct. It preserves both records and flags the discrepancy for human verification.”

## 3:20–4:20 · Show verification and status history

Open **Verification and status history**. Open the example issue and show both pieces of evidence and the explanation.

Set the status to **Under Review** and save a note such as:

“Both synthetic records inspected during the classroom demonstration. Awaiting confirmation from the responsible department.”

Explain the available statuses: Needs Verification, Under Review, Resolved and Dismissed. A review status changes the issue only; it does not alter the original obligation or create an official university clearance.

## 4:20–5:10 · Explain architecture and database

“The browser interface sends requests to the backend API. The backend validates inputs, applies deterministic reconciliation rules and stores the records and review history in a relational database. The proposed architecture in our report separates the student-facing interface, application logic and data storage.”

For technical accuracy, the current repository is implemented with HTML, CSS and JavaScript, Python FastAPI, SQLAlchemy and SQLite. The submitted report lists Node.js/Express and MySQL as its proposed stack. Do not claim those technologies are already implemented in this repository.

## 5:10–5:50 · Explain limitations and next steps

“The current prototype uses manual input and a local database. It has no verified live ERP integration, no automatic payment processing and no authority to approve or deny university services. The next step is to complete and test the departmental workflow, validate rules with authorized stakeholders and only then consider approved university-system integration.”

## Likely viva questions

**What problem does the system solve?** It consolidates manually recorded departmental obligations and explains how unresolved records may affect academic services.

**Who uses the system?** The report proposes student users, authorized departmental officers and a portal administrator. The current local prototype is a single-user demonstration and does not yet implement authenticated roles.

**What is an obligation?** A recorded pending or cleared item associated with a student and an issuing department, such as a library or accounts obligation.

**How does reconciliation work?** The rule engine compares records using course identity, title similarity, obligation type and deadlines. It returns an explained classification and related verification issues.

**Does the system automatically clear a student?** No. It is a demonstrable prototype and does not replace an official registrar or university ERP decision.

**Does it connect to the university ERP?** No verified live ERP integration exists. Records are entered manually.

**What happens when sources disagree?** Both records are preserved, the difference is explained and the issue is left for human verification.

**What is the current technology stack?** The GitHub implementation uses HTML/CSS/vanilla JavaScript, Python FastAPI, SQLAlchemy and SQLite. The report lists Node.js/Express and MySQL as the proposed stack, so describe that difference transparently.

**What remains to be done?** Complete the prototype, validate it with real authorized departmental workflows, test the service-specific rules and assess usability before any live integration.
