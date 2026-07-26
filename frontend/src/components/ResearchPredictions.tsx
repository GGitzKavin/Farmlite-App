import React from 'react';
import { CloudSun, Loader2, Wheat } from 'lucide-react';
import type { BangladeshPredictionResponse } from '../api/bangladeshCandidate';
import { formatCandidateNumber } from '../features/bangladeshCandidate';

interface CandidateDmiAndThiCardsProps {
  response: BangladeshPredictionResponse | null;
  loading: boolean;
  error: string;
  notice: string;
}

const unavailableDmiMessage =
  'Dry-matter intake estimate is currently unavailable.';

const CandidateDmiAndThiCards: React.FC<
  CandidateDmiAndThiCardsProps
> = ({ response, loading, error, notice }) => {
  const dmi = response?.ml_predictions.dmi_kg_day ?? null;
  const thi = response?.environment.calculated_thi ?? null;
  const thiCategory = response?.environment.thi_category ?? null;
  const dmiAvailable = dmi !== null && Number.isFinite(dmi);
  const thiAvailable = thi !== null && Number.isFinite(thi);

  return (
    <>
      <article className="min-w-0 rounded-xl border border-[#dda15e]/70 bg-[#fefae0] p-5 shadow-sm">
        <h3 className="flex items-center text-sm font-semibold uppercase tracking-wide text-[#283618]">
          <Wheat aria-hidden="true" className="mr-2 h-5 w-5 text-[#bc6c25]" />
          Predicted Dry-Matter Intake
        </h3>
        {loading ? (
          <p
            role="status"
            className="mt-3 flex items-center text-sm font-medium text-[#606c38]"
          >
            <Loader2 aria-hidden="true" className="mr-2 h-4 w-4 animate-spin" />
            Calculating dry-matter intake...
          </p>
        ) : (
          <>
            <p className="mt-3 break-words text-3xl font-bold text-[#283618]">
              {dmiAvailable
                ? `${formatCandidateNumber(dmi)} kg DM/cow/day`
                : 'Unavailable'}
            </p>
            <p className="mt-2 text-sm text-gray-700">
              {dmiAvailable
                ? 'Estimated amount of feed dry matter consumed after excluding moisture.'
                : notice || error || unavailableDmiMessage}
            </p>
          </>
        )}
        <p className="mt-3 text-xs font-medium text-[#606c38]">
          Source: Collected-data DMI model
        </p>
      </article>

      <article className="min-w-0 rounded-xl border border-[#dda15e]/70 bg-white p-5 shadow-sm">
        <h3 className="flex items-center text-sm font-semibold uppercase tracking-wide text-[#283618]">
          <CloudSun
            aria-hidden="true"
            className="mr-2 h-5 w-5 text-[#bc6c25]"
          />
          Heat Stress Index
        </h3>
        <p className="mt-3 break-words text-3xl font-bold text-[#283618]">
          {thiAvailable
            ? `${formatCandidateNumber(thi)} — ${thiCategory ?? 'Unavailable'}`
            : 'Unavailable'}
        </p>
        <p className="mt-2 text-sm text-gray-700">
          {thiAvailable
            ? 'Calculated from the submitted temperature and humidity.'
            : 'A heat-stress value is available after valid weather inputs are processed.'}
        </p>
        <p className="mt-3 text-xs font-medium text-[#606c38]">
          Source: Backend THI calculation
        </p>
      </article>
    </>
  );
};

export default CandidateDmiAndThiCards;
