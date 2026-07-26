# FarmLite Final User Guide

Date: 2026-07-26

## What FarmLite does

FarmLite is an AI-assisted livestock management and decision-support system.
It manages livestock, batches, health and vaccination records, notifications,
feed inventory and cattle feed-and-production recommendations.

FarmLite guidance is advisory. It does not replace a veterinarian or qualified
animal nutritionist.

## Registration

1. Open the registration page from **Register here** on the sign-in screen.
2. Enter a full name, email address, password and matching confirmation.
3. Select **Register**.
4. FarmLite creates the Firebase Authentication account and its user profile,
   then opens the protected dashboard.

If the passwords differ or Firebase rejects the request, FarmLite displays an
error and does not complete registration.

## Login and logout

Enter the registered email address and password on the login page and select
**Sign in**. Invalid credentials produce an error message. Protected pages
redirect an unauthenticated visitor to `/login`, and a restored Firebase
session keeps the user signed in after a refresh.

To log out, select **Sign Out** in the navigation. The Firebase session is
closed and the login page opens.

## Dashboard

The dashboard summarizes stored data belonging to the current farmer:

- Quick Actions;
- Attention Required;
- Upcoming Vaccinations;
- Livestock Overview;
- Batch Overview;
- Recent Activity;
- Feed Inventory Levels.

Cards show loading, empty or error states when appropriate. Dashboard values
come from Firestore records; unavailable values are not replaced with
placeholder statistics. Quick Actions open existing FarmLite pages.

## Individual livestock management

Open **Livestock** and use **Add Animal** for an individual record.

- The individual field is labelled **Livestock**.
- Approved individual choices exclude Chicken and Duck.
- Enter the visible identification and management fields, then save.
- Use the search box and category controls; **All Livestock** removes the type
  filter.
- Open a row or card to view the animal.
- Use the edit action to update it. Historical stored type and gender values
  are preserved when editing.
- Use delete only after checking the confirmation. Associated health and
  vaccination records are removed by the existing animal-delete flow.

An empty account displays an empty state rather than fabricated animals.

## Batch livestock management

Open the batch section on **Livestock** and select **Add Batch**.

- Batch types retain batch-oriented options, including Chicken and Duck.
- A saved batch belongs to the signed-in farmer and appears immediately; no
  browser refresh is required.
- Search and type/status filters can narrow the list.
- Existing actions support edit and delete.
- The real-time listener reconciles a saved document by ID to avoid duplicate
  cards.

If Firestore rejects a listener or write, FarmLite shows an error and does not
pretend the operation succeeded.

## Animal profile

Open an individual animal to see one continuous page:

1. **Animal Profile**
2. **Health Status**
3. **Medical and Vaccinations**

Gender is deliberately not displayed, but it remains preserved in the stored
record and edit form. Health, medical and vaccination actions remain
available from the page. Obsolete detail/medical tabs are not used.

## Health records

Open **Health Tracking** to create, view, edit or delete health/medical
records. Select the correct animal, enter the date and details, and save.
Animals without health records remain valid and display an empty state.

## Vaccination records

Open **Vaccinations** to create or edit a record for an individual animal or
batch. Enter the vaccination date and next due date. FarmLite derives the
status used by vaccination history, dashboard and notifications:

- overdue;
- due soon/upcoming;
- current/completed as represented by the stored record.

Invalid or missing dates must be corrected instead of being treated as a
valid due date. An animal with no vaccination record remains visible without a
fabricated status.

## Notifications

Open **Notifications** to review due vaccinations and other relevant stored
record conditions. Alerts are deduplicated by their record identity and link
to the relevant page. When nothing needs attention, FarmLite displays an
empty state.

## Profile settings and Farm Type

Open **Profile** to load and edit owner and farm information.

**Farm Type** is a free-text field so existing values remain compatible. On
save, FarmLite:

- trims leading and trailing whitespace;
- rejects a whitespace-only value;
- enforces an 80-character maximum;
- exposes validation through accessible error attributes.

The About panel reads:

> About FarmLite
> AI-assisted livestock management and decision-support system.
> © 2026 FarmLite

## Feed and production recommendation

Open **AI Feed Recs** and select an individual lactating cow. Review or enter:

- breed;
- explicit genetic group;
- age and weight;
- lactation stage and days in milk;
- previous-week average milk yield;
- body-condition score;
- temperature and humidity;
- current health status.

Breed never selects genetic group. Choose the group only when it is known.
**Unknown / Not sure** is valid, but it deliberately leaves DMI unavailable.

Select the calculate action. A supported, complete result contains:

- **Expected Milk Yield** in L/day, owned by the FarmLite milk prediction
  model;
- **Predicted Dry-Matter Intake** in kg DM/cow/day, owned by the
  collected-data DMI model;
- **Heat Stress Index**, owned by the backend THI calculation;
- **Advisory Daily Ration**, owned by the FarmLite nutrition rule engine;
- roughage, concentrate, mineral mix, water advice, feeding frequency and
  warnings.

The displayed ration sentence is:

> The FarmLite nutrition rule engine calculated an advisory ration quantity
> of {value} kg/day.

DMI and ration are different. DMI excludes feed moisture. FarmLite does not
convert DMI into total feed, fresh feed, roughage or concentrate.

## Warnings and unavailable values

- Unknown genetic group: milk, ration and valid THI remain; DMI is
  **Unavailable**.
- Invalid weather: no THI is fabricated and a controlled message is shown.
- Candidate service unavailable: the successful FarmLite milk and ration
  result remains; DMI is unavailable.
- Unsupported production status: model output fails closed with a scope
  explanation.
- Local genetic group: the result is marked limited support.
- Disabled candidate flags: the original compatible FarmLite result works;
  DMI/THI candidate cards are not requested or shown.

Unavailable never means zero.

## PDF download

After a recommendation, select **Download PDF Report**. In the controlled
feature-enabled workflow the report title is:

> FarmLite Feed and Production Decision-Support Report

The report contains selected animal details, exactly one farmer-facing milk
prediction, DMI, THI, advisory ration, source labels, warnings, limitations,
page numbers, footer and disclaimer. The internal second milk candidate is
never included.

The DMI technical source is Mendeley Data, DOI `10.17632/954f6g36sb.2`.

## Current limitations

- The collected-data DMI path is feature-gated and has limited declared model
  scope.
- The retained milk model uses publisher-declared synthetic source data and
  is not evidence of unrestricted real-farm accuracy.
- The system has not received unrestricted veterinary, commercial, universal
  or multi-farm validation.
- A missing/unsupported input deliberately produces an unavailable value.
- FarmLite requires reviewed server-side Firestore rules in deployment;
  frontend ownership filtering alone is not a security boundary.
