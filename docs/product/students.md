# Students

Students are the fourth unit of analysis in the Kallipolis ontology — the only one of the foundationals who are people. Courses are documents, occupations are categories, employers are organizations; students are human beings, and that distinction has always governed how the product represents them. In the current non-PII configuration the ontology carries **no individual student records at all**: the unit persists as a foundational and as a navigational surface, but the per-student layer that used to populate it has been removed. This document describes what the student layer was, why it was removed, what stands in its place, and the future state the architecture is still building toward.

## The essence

A student, in the original Kallipolis framing, was a represented person whose competency portrait — primary focus, course history, GPA, and occupation alignment — made the supply side of workforce development empirical. Each field answered a facet of one question: is this student equipped to enter the workforce in this area, and at what level? The supply side of workforce development is colleges producing graduates prepared for workforce pathways; the student was the literal carrier of curricular preparation, and the portrait was what made the carrying observable.

That essence still describes what a student *is* in the ontology's conceptual structure. What has changed is that the ontology no longer stores any instances of it.

## The non-PII posture

The student records the ontology used to carry were **synthetic** — produced by a calibrated methodology that approximated a college's enrollment reality without representing any real person. The synthetic layer was a deliberate choice to demonstrate the analytical power of the ontology without taking on FERPA obligations or institutional access agreements. But synthetic individuals carry a standing legibility cost (a reader could mistake the population for a literal headcount) and a large storage cost (the per-student enrollment and competency edges dominated the graph), and they were never real evidence — only an illustration of the art of the possible.

The current architecture removes them entirely. The ontology now holds only **aggregated, institution-authored data**: courses and their institutional `PREPARES_FOR` crosswalk, regional occupational demand, employers, and — for the supply side — the TOP6 **Program** layer, whose award and enrollment measures come directly from Chancellor's Office DataMart MIS. Where a partnership question once asked "how many students at this college are prepared for this occupation," it now draws on program-level enrollment and award aggregates per TOP6 rather than a synthesized per-student count. The supply signal survives; the synthetic people do not.

This is a non-PII posture by construction: the only data in the ontology is data an institution already publishes in aggregate. Nothing the system stores is about an identifiable individual.

## What the Students form is now

The Students node remains on the college atlas and the `/students` route still resolves, so the navigational shape of the product is unchanged. The form renders a placeholder that states plainly that individual student records are not part of this view and points the reader to the program-level enrollment and outcome aggregates surfaced in the Partnerships and Courses views. Retaining the form — rather than deleting the unit — keeps the ontology's vocabulary stable across the stack and leaves a clear seat for the student layer to return in its future form.

## How students will be represented in the future

The architecture still commits to a future state in which students are **anonymized to Kallipolis but identifiable to community college stakeholders** — the direction the synthetic layer was always a placeholder for.

The aspirational architecture extends the system's value to the individual level: matching real people to real employment opportunities, tailoring pathways through programs, supporting advising work that requires knowing who a student actually is. None of that is possible with synthetic data, and none of it is the present non-PII configuration. The way to reach it without making Kallipolis a custodian of sensitive data is to invert the relationship — the system stores enough about each student to do the analytical work but never anything that identifies them, and the institution holds the identification key. When a college user looks at a student through Kallipolis, they would see a real person through their college's identity layer; Kallipolis itself would see only a competency profile and a set of relationships.

This is a privacy stance and an architectural commitment at once: institutional knowledge stays with the institution. The present non-PII configuration is the conservative floor of that commitment — no individual data of any kind — and the anonymized-real-data state is its eventual ceiling. The synthetic-individual layer that sat between them has been retired.
