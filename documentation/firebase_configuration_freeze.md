# Firebase configuration freeze

Date: 2026-07-26

## Status

This is a documentation-only configuration freeze. No Firebase
Authentication user, Firestore document, Security Rule, index, client
configuration value, or deployed Firebase resource was changed while
preparing this record.

## Locally observable configuration

The frontend initializes its existing Firebase application from these
environment variables:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

The application continues to use the configured Firebase Authentication
instance and Firestore database exported by
`frontend/src/firebase/config.ts`. No environment value is reproduced in
this document.

The existing Firestore collection paths observed in the frontend are:

- `users`
- `livestock`
- `batches`
- `healthRecords`
- `vaccinations`
- `feedInventory`

Farm-owned records use the existing `userId` ownership field. User profile
documents use the authenticated Firebase UID as the document ID under
`users`. Phase 6.3 continues to write batches to
`/batches/{documentId}` with `userId` set to the current authenticated UID.
These paths and ownership conventions are frozen.

## Firestore Security Rules visibility

The repository does not contain a `firestore.rules`,
`firestore.indexes.json`, `firebase.json`, `.firebaserc`, or another local
Firebase rules/deployment artifact. Consequently, the exact deployed
Firestore Security Rules text, version, deployment time, and project-side
index configuration cannot be verified or reproduced from this workspace.

Frontend `userId` filters are application behavior and are not a substitute
for server-enforced Firestore Security Rules. Functional checks against the
currently configured Firebase environment can demonstrate the behavior
observed by the signed-in test accounts, but they cannot prove the complete
deployed ruleset.

This missing source-controlled rules snapshot is a deployment limitation.
No Firestore rule was retrieved, edited, relaxed, or deployed as part of
this freeze.

## Frozen operations

Without separate explicit authorization, the following remain prohibited:

- changing Firebase Authentication behavior or users;
- changing Firebase client configuration or environment values;
- changing Firestore Security Rules or deploying rules;
- changing collection paths or ownership fields;
- deleting test accounts or stored records;
- migrating or rewriting Firebase data;
- weakening user isolation or enabling universal Firestore access.

Any future functional validation must use the currently configured Firebase
environment and preserve all existing accounts and stored data.
