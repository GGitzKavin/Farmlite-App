# Phase 6 existing frontend flow audit

Audit date: 2026-07-26. This document records the pre-Phase 6 behavior before
candidate UI edits.

## Package and application structure

- Frontend: React 19, TypeScript 6, Vite 8, Tailwind CSS 4.
- HTTP: Axios.
- Forms: local controlled React state; `react-hook-form` is installed but is
  not used by the recommendation page.
- PDF: jsPDF, invoked directly by the recommendation page.
- Authentication/data: Firebase context and Firestore reads.
- Routing: React Router.
- Icons: lucide-react.
- Tests: no frontend test framework, test files, or `npm test` script exist.
- Existing scripts: `dev`, `build`, `lint`, and `preview`.

## Current ownership and flow

| Concern | Existing owner / behavior |
|---|---|
| Cow inputs | `frontend/src/pages/FeedRecommendation.tsx` and its local `FeedFormData` state |
| Livestock/health loading | Same page; Firestore reads in `fetchPageData` |
| Form validation | Same page; `validateForm` checks selected cow, breed, age, weight, and lactation stage |
| Existing API request | Same page; direct `axios.post` to `${VITE_FLASK_API_URL or localhost}/api/ai/feed-recommendation` |
| Existing response type | Page-local `FeedRecommendationResponse` |
| Recommendation display | Same page; rule output and retained milk prediction cards |
| Loading/error state | One `submitting` flag plus page-level validation, request, and PDF error strings |
| PDF data | Page-local `recommendation`, `formData`, and selected-animal state |
| PDF generation | Same page; `handleDownloadPdf` creates jsPDF content and saves it |

The v1 request is sent directly rather than through a reusable API service.
The current submit operation clears the previous recommendation, posts a
camel-case payload, then renders the existing milk prediction and
rule-generated feed quantities. Candidate data does not exist in the
pre-Phase 6 page.

## Existing behavior and accessibility patterns

- Inputs are controlled and use native input/select elements.
- Labels are visually adjacent but generally lack explicit `htmlFor`/`id`
  associations.
- Focus styling uses the existing green palette.
- Loading uses a disabled submit button and animated spinner.
- Request errors are displayed in bordered, colored panels with text and an
  icon.
- The page uses responsive one/two-column Tailwind grids and globally hides
  horizontal body overflow.
- PDF layout has margin, wrapping, and page-space helpers.

## Phase 6 insertion points

The least disruptive design is:

1. Keep the current v1 payload, call, result state, display, and PDF sections.
2. Add a small feature-configuration module and an isolated typed v2 client.
3. Add `geneticGroup` to local form state only; never populate it from a cow
   breed or Firestore breed text.
4. When the frontend flag is enabled and explicit candidate prerequisites
   pass, start v1 and v2 independently and retain separate result/error state.
5. Add a visually separate research card after the existing recommendation.
6. Append an optional research section to the existing PDF generator.

No behavior was changed while producing this audit.
