# Phase 6.2 dashboard design

Date: 2026-07-26

## Existing widget inventory

Before Phase 6.2 the Dashboard contained:

- Total Livestock
- Vaccines Overdue
- Low Feed Alerts
- Health Alerts
- Feed Inventory Levels
- Recently Added Livestock

The four overlapping summary cards were reorganized instead of duplicated.
Feed Inventory Levels remains, and Recently Added Livestock is expanded into
Recent Activity.

## Final dashboard sections

### Quick Actions

Links use existing routes only:

- Add Livestock → `/livestock`
- Create Batch → `/livestock?view=batch`
- Record Vaccination → `/vaccinations`
- Generate Feed Recommendation → `/ai-feed`

The livestock page reads the existing route query to open Batch Management;
no route path was renamed.

### Attention Required

This combines actionable counts derived from existing records:

- overdue vaccinations;
- vaccinations due within 30 days;
- livestock with a non-healthy current health status;
- livestock profiles missing an existing critical identity/management field;
  and
- feed items at or below their stored threshold.

Each row retains a text label and link. No diagnosis is generated.

### Upcoming Vaccinations

Existing vaccination records with valid next-due dates are divided into
`Due within 7 days` and `Due within 30 days`. The list shows stored target
name, vaccine name, due date, status, and a relevant existing route.

### Livestock Overview

Existing livestock records are grouped by the application’s existing display
type normalization. The section uses an accessible card list rather than
adding another chart.

### Batch Overview

The available batch data supports:

- total batch records; and
- the sum of manually recorded batch headcounts.

The second value is labelled `Recorded batch headcount`; it is not represented
as verified animal assignment.

### Recent Activity

Recent Activity uses only stored `createdAt` timestamps from livestock and
batch records. It does not create an activity-log collection.

### Feed Inventory Levels

The existing real-data feed chart is retained with FarmLite palette colours,
an accessible description, and an empty state.

## Intentionally skipped widgets and metrics

- Active batches: no reliable active/inactive batch field exists.
- Animals assigned to batches and animals without a batch: the current
  livestock/batch schema has no reliable assignment relationship.
- Vaccination update activity: vaccination records do not provide a reliable
  action timestamp distinct from clinical dates.
- Recommendation activity: no stored recommendation-history source exists.
- Separate Farm Summary: its requested totals would duplicate Attention,
  Livestock Overview, Upcoming Vaccinations, or Batch Overview.
- Additional charts: a card list is clearer at 320 px and avoids empty or
  redundant graphs.

## Data and failure behavior

Dashboard values come from the existing `livestock`, `healthRecords`,
`vaccinations`, `feedInventory`, and `batches` collections and are scoped
using the current user behavior already established in the application.

If a collection cannot be loaded, the Dashboard shows an accessible warning
and renders the available sections. Every section provides a meaningful empty
state.
