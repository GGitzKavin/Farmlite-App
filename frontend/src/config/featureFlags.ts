import { parsePublicFeatureFlag } from './publicFeatureFlag';

export { parsePublicFeatureFlag } from './publicFeatureFlag';

export const BANGLADESH_CANDIDATE_UI_ENABLED = parsePublicFeatureFlag(
  import.meta.env.VITE_BANGLADESH_CANDIDATE_UI_ENABLED
);
