# Public syllabus demonstration

Deploy `contracts/curriculum_bridge.py` in Studio, with no constructor arguments, using the inbuilt account and full consensus. Keep this account selected for rubric creation/invalidation.

1. Call `create_rubric(rubric_json)` with the exact JSON from `examples/programming_rubric.json`. Save the returned rubric ID.
2. Call `register_course` for source A:
   - institution: `Massachusetts Institute of Technology`
   - code: `6.0001 Introduction to Computer Science and Programming in Python`
   - version: `Fall 2016`
   - source_url: `https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/pages/syllabus/`
3. Call `register_course` for target B:
   - institution: `Harvard University`
   - code: `CS50P Introduction to Programming with Python`
   - version: `Public syllabus snapshot 2026-11-19`
   - source_url: `https://cs50.harvard.edu/python/syllabus/`
4. Save both returned course IDs. Call `get_course` to inspect each locked snapshot and `syllabus_hash`.
5. Call `request_equivalence(course_a, course_b, rubric_id)` and save the assessment ID.
6. Call `evaluate_equivalence(assessment_id)`. Wait for the transaction's execution success and finality. Consensus failure means no assessment was written; inspect logs before retrying the same request.
7. Call `get_equivalence(assessment_id)`. The result includes verdict, score, gaps, missing evidence, five coverage rows, source quotations, source hashes, rubric hash and `academic_credit_awarded: false`.
8. Optionally compare the reverse direction as a separate request. Equivalence is not symmetric.
9. To demonstrate versioning, register changed course evidence or a changed rubric and create a new request. The curator may call `invalidate_assessment(old_id, reason, replacement_id)` only after the replacement is evaluated; use an empty replacement ID when none exists. The original result remains readable with INVALIDATED status.

Do not preselect a desired verdict: the public pages may omit assessment detail, course duration or target competencies. An INCONCLUSIVE result is a meaningful evidence-gap finding. Test fixtures intentionally contain synthetic snippets; they are not claims about these institutions.
