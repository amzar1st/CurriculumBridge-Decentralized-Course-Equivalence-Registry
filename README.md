# CurriculumBridge

A standalone GenLayer Intelligent Contract that records **directional course-equivalence attestations**: does source Course A satisfy target Course B under one immutable five-competency rubric?

**Educational evidence only. It does not award credit, establish student eligibility, prove course completion, or represent an institution's endorsement.**

## What is implemented

- Immutable course versions containing source URL, full rendered syllabus snapshot and SHA-256 fingerprint.
- Curator-created, content-addressed rubrics with exactly five competencies, weights, mandatory-core flags and optional minimum contact hours.
- Reusable, deduplicated comparison requests keyed by ordered course IDs and rubric hash.
- Independent GenLayer leader/validator semantic evaluations with deterministic scoring and exact agreement on every coverage status and decision-bearing field.
- Numbered evidence anchors resolved into exact syllabus quotations by the contract; no model-generated quotations.
- EQUIVALENT, PARTIAL, NOT_EQUIVALENT and INCONCLUSIVE outcomes.
- Append-only invalidation records with reason and optional replacement; original results remain readable.

## Start

Contract: [`contracts/curriculum_bridge.py`](contracts/curriculum_bridge.py). It is self-contained; constructor takes **no arguments**. Deploy in [GenLayer Studio](https://studio.genlayer.com/) using its inbuilt account and **Normal (Full Consensus)** execution. No external wallet or frontend is required.

See [`docs/DEMO.md`](docs/DEMO.md) for the full public-syllabus workflow and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the observed deployment. The deploying account becomes registry curator. Anyone can register courses, request comparisons and trigger evaluation; only the curator can create rubrics or invalidate results.

```bash
python -m unittest discover -s tests -v
python -m py_compile contracts/curriculum_bridge.py
```

Tests use a small GenLayer boundary double to exercise the actual contract functions. They are not a substitute for hosted GenVM execution or actual multi-provider AI consensus. GitHub Actions runs the behavioral suite and syntax check.

## Decision rules

For each competency: MET earns full weight, PARTIAL half weight, ABSENT and UNKNOWN zero. The integer percentage floors the total only after summation. Weights must total 100.

1. Any UNKNOWN competency, unverified/mismatched source, or missing required contact hours → INCONCLUSIVE.
2. At or above `equivalent_min`, every core competency MET, and hours sufficient → EQUIVALENT.
3. Otherwise, at or above `partial_min` → PARTIAL.
4. Otherwise → NOT_EQUIVALENT.

Known insufficient hours prevent equivalence. A mandatory-core gap prevents equivalence even with a high aggregate score. Missing evidence is distinct from demonstrated absence. The demo rubric disables the contact-hours gate (`min_hours: 0`) because public syllabi may not publish comparable total hours.

## Consensus design

Registration uses `gl.eq_principle.strict_eq` on a bounded rendered-text snapshot. If providers render differently, registration can fail rather than commit ambiguous evidence. Evaluation uses `gl.vm.run_nondet_unsafe`: validators independently repeat the analysis of the same locked snapshots, validate evidence anchors, reconstruct exact quotations, recompute score and verdict, and compare all coverage statuses, score, gaps, missing evidence, hours and authenticity statuses exactly. Validators may choose different relevant line anchors; all anchors must resolve to the locked source evidence. No numeric tolerance crosses a threshold. Invalid leader structures or evaluator failures are rejected. Consensus failure leaves the request unevaluated; it is not silently recorded as INCONCLUSIVE.

## API

All views and structured write results are JSON strings, except registration/request/rubric writes which return content-addressed IDs.

| Method | Arguments | Result |
| --- | --- | --- |
| `register_course` | institution, code, version, source_url | course ID |
| `create_rubric` | rubric_json | rubric hash/ID |
| `request_equivalence` | course_a, course_b, rubric_id | assessment ID |
| `evaluate_equivalence` | assessment_id | structured result JSON |
| `invalidate_assessment` | assessment_id, reason, replacement_id | appends invalidation |
| `get_course` | course_id | metadata + snapshot JSON |
| `get_rubric` | rubric_id | locked rubric JSON |
| `get_equivalence` | assessment_id | request, status, result, invalidation JSON |

The same ordered tuple always has the same assessment ID. A completed result cannot be evaluated again. New evidence or rubric versions produce a new tuple. Invalidating does not erase or reactivate the old tuple. Consumers must read the status and verify that any linked replacement remains valid.

Each snapshot is split into non-empty trimmed lines, with long lines divided into 400-character chunks. The model returns integer `a_line` / `b_line` anchors (or `-1` for missing evidence). The contract derives `a_quote` / `b_quote` from those anchors, so a model cannot paraphrase a quote and present it as exact source text. This checks text provenance, while independent semantic evaluation checks whether the cited material supports coverage.

## Evidence and trust limits

The MVP accepts HTTPS `.edu` sources only and snapshots 100–60,000 rendered characters. PDFs, authenticated pages and institutions outside `.edu` are out of scope. The host restriction is a retrieval constraint, **not proof of authenticity**. Provider redirects and web fetching remain part of the GenLayer provider trust boundary. Institutions, titles and versions are submitter claims checked semantically against the snapshot and URL; no institutional cryptographic signature is verified. The returned OFFICIAL status is an AI-supported source-alignment signal.

Snapshot hashes identify the rendered evidence actually evaluated, not original PDF/file bytes. The record is historical: it does not automatically check subsequent website changes. Register updated evidence and invalidate the old result when appropriate. Broad syllabus outlines can correctly produce INCONCLUSIVE; adding evidence requires a new course version (the MVP snapshots one URL per version). Prompt injection is mitigated by treating all payload fields as untrusted and resolving citations from locked text, but cannot be eliminated by wording alone.

Strict field agreement deliberately favors consistency over liveness. Models can disagree on depth or hours. There is no fabricated fallback verdict, automatic retry loop, token settlement, student record collection or academic-credit issuance.

## References

- [GenLayer equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [GenLayer Studio](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio)
- [MIT 6.0001 syllabus](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/pages/syllabus/)
- [Harvard CS50P syllabus](https://cs50.harvard.edu/python/syllabus/)

MIT and Harvard are example evidence sources and are not affiliated with this project.
