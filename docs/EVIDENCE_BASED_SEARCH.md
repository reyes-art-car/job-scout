# Evidence-based job search

JobScout connects offer requirements, candidate evidence, learning progress, and application records.
These workflows run in the browser and work with both API-backed offers and the static demo.

## Explainable matching

Open **Adaptar CV** and expand **Revisar y corregir el análisis**. Each recognized technology
shows its original source, its weight, the candidate level, and supporting profile statements or
user-supplied evidence. You can change whether a requirement is mandatory, desirable, mentioned,
or irrelevant, and restore the original detection. Corrections are scoped to the offer and data mode.

Technical coverage uses mandatory = 3, desirable = 1, and unclassified text = 1.5. English has a
special weight of 0.5. A declared skill counts fully, a partial skill counts half, and a gap counts zero.
No recognized requirements means zero coverage, not a perfect match. Unrecognized requirements
are outside the calculation. This is neither an ATS score nor a probability of an interview.

The search rubric score remains separate from technical coverage. Experience, location, remote
preferences, and senior role titles produce review warnings; they do not change coverage or discard
offers automatically. The experience filter in Offers is opt-in. Parsing is heuristic: verify the original
posting, particularly alternatives, negation, remote restrictions, and unusual experience wording.

## Evidence and learning

**Mi experiencia** lets you set preferences, attach a project, achievement, or certificate to a
technology, and review competency levels. Evidence requires a title and explanation; an optional
link must use HTTP or HTTPS without embedded credentials. Evidence is self-reported, not externally verified.
Existing profile statements remain clearly distinguishable from separately attached evidence.

**Brecha de skills** ranks practice suggestions using demand and the number of offers where a
technology is the only missing mandatory technical requirement. Related offers are linked directly.
Practice states are independent of competency levels. Completing a practice never automatically
adds skills to the CV. Explicit confirmation and an attached evidence item are required.

Confirmed evidence contributes its own statements and skill names to CV tailoring. Removing the
last attached evidence downgrades the manually confirmed skill to partial. Correcting a competency
to partial or missing removes contradictory tagged profile achievements from generated content.
The dashboard, learning page, CV, and cover letter use the same reviewed profile levels.

## Application records

From **Adaptar CV**, save a draft or register an application you have already sent. Registering an
application does not submit it to an employer. A pending offer moves to Applied only after the gateway
accepts the change. Existing later-stage statuses are preserved. A registered application gets a date
and a suggested follow-up date seven days later; future and impossible dates are rejected.

**Mi historial** displays snapshots and status transitions recorded after this feature is enabled.
Snapshots freeze the edited CV text and generated Word-compatible HTML at save time. Later edits do
not alter older versions. The UI renders archived text as text and offers a plain-text download;
imported HTML is never rendered or executed. The backup preserves the generated HTML as data.

Counts describe recorded activity, not causal evidence that one CV performs better. An offer's latest
status may correspond to several CV versions. Follow-up dates are reminders to review the response,
not scheduled messages or email notifications.

## Storage, backup, and limits

The workspace is local to one browser/origin and assumes one candidate. It is not synchronized to the
backend or between devices, even when offers come from the API. Offer-specific corrections, events,
and snapshots distinguish demo from API data. Skills and preferences belong to the candidate workspace.
Resetting demo offers does not delete evidence or application archives.

Export a JSON backup from **Mi experiencia**. Restoring requires an explicit replacement confirmation,
validates the full payload before changing current data, and rejects unsafe evidence links. Backups can
contain personal information and full CVs. Store them privately. Browser storage failures show an alert;
the current in-memory workspace remains exportable.

Limits: 1,000 evidence items, 300 CV snapshots, 1,000 offer correction maps, a 10 MB import file, and
5,000 recent status transitions. Browser storage quotas can be lower. No server-side multi-user account
or cloud synchronization is provided by this feature.
