# Product Documentation

- [Product requirements document](PRD.md): product objectives and overall scope.
- [Hong Kong FSIE user cases and step-by-step input templates (primary document)](HK_FSIE_USER_CASE_TEMPLATES.md): three fictional cases, each with a detailed question and a step-by-step form.
- [HK FSIE user cases and step-by-step forms (English)](HK_FSIE_USER_CASE_TEMPLATES.en.md): a companion English version of the templates above.

See the corresponding results from six live workflow experiments in the [evaluation report (primary document)](../project/evaluations/HK_FSIE_SIX_EXPERIMENT_REPORT.md) and [English version](../project/evaluations/HK_FSIE_SIX_EXPERIMENT_REPORT.en.md). The cases use synthetic data, and the reports record engineering behavior rather than tax expert acceptance.

## Feedback recorded on 2026-10-22

- Users report that asking for one fact per turn creates too many rounds and delays a useful overall answer. Follow-up work should group related questions, show an interim answer from known facts, and explain which missing facts change the result. This is recorded for a separate change, not part of PDF attachment support.
- Initial PDF attachment scope: one text PDF per message, up to 10 MB, 50 pages and 20,000 extracted characters. Users can preview extracted text before sending. Empty/unreadable pages are flagged. Scans require OCR outside the app for now. Original PDFs are not persisted; extracted text and page references are saved in the case conversation and sent to the configured model under the existing data confirmation. Attachments do not become verified legal sources or automatically confirmed facts.

- Attachment expansion: PDF, Word (.doc/.docx), and Excel (.xls/.xlsx), using an icon-only paperclip entry. One file per message, 10 MB and 20,000 extracted characters. PDF allows 50 pages; Excel allows 20 worksheets and 10,000 populated cells (100,000-cell range per sheet). Word extracts body/table text. Excel preserves sheet names, cell coordinates, formats and saved values; formulas/macros are not executed and cached results may be stale. Originals are not persisted. Legacy .doc uses macOS textutil locally and antiword on Linux; the Render build installs antiword under .tools without root.
