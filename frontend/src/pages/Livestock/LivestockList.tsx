import React, { useState, useEffect, useCallback } from 'react';
import LivestockTable from './LivestockTable';
import BatchManagement from './BatchManagement';
import { Tractor, Users, Search, CheckCircle, AlertCircle } from 'lucide-react';
import ErrorBoundary from '../../components/ErrorBoundary';
import { useSearchParams } from 'react-router-dom';
import { ALL_LIVESTOCK_TYPES } from '../../features/livestockTypes';
import { getSpeciesFilterValue } from '../../utils/livestockStatus';

const LivestockList: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'individual' | 'batch'>(() =>
    searchParams.get('view') === 'batch' ? 'batch' : 'individual'
  );
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSpecies, setFilterSpecies] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Auto-hide success message with cleanup
  useEffect(() => {
    if (!successMessage) return;

    const timer = setTimeout(() => setSuccessMessage(''), 3000);
    return () => clearTimeout(timer);
  }, [successMessage]);

  const handleSuccess = useCallback((msg: string) => {
    setSuccessMessage(msg);
  }, []);

  const handleBatchCreated = useCallback(() => {
    setSearchTerm('');
    setFilterSpecies('');
  }, []);

  return (
    <div className="space-y-5 relative">
      <ErrorBoundary>
        {/* Toast Notification */}
        {successMessage && (
          <div className="fixed top-6 right-6 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="bg-[#606c38] text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-3">
              <CheckCircle className="w-5 h-5" />
              <span className="font-bold">{successMessage}</span>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h1 className="text-3xl font-bold text-[#283618]">Livestock Management</h1>
        </div>

        {/* Tabs and Primary Search */}
        <div className="overflow-hidden rounded-xl border border-[#dda15e]/60 bg-white shadow-sm">
          <div className="border-b border-[#dda15e]/40 bg-[#fefae0] px-4 sm:px-5">
            <div className="flex flex-col gap-3 py-3 lg:flex-row lg:items-center lg:justify-between">
            <nav className="-mb-px flex space-x-6" aria-label="Tabs">
              <button
                type="button"
                aria-selected={activeTab === 'individual'}
                onClick={() => setActiveTab('individual')}
                className={`
                  flex items-center py-2.5 px-1 border-b-2 font-semibold text-sm whitespace-nowrap transition-all
                  ${activeTab === 'individual'
                    ? 'border-[#606c38] text-[#606c38]'
                    : 'border-transparent text-gray-600 hover:border-[#dda15e] hover:text-[#283618]'}
                `}
              >
                <Tractor className="w-4 h-4 mr-2" />
                Individual Livestock
              </button>
              <button
                type="button"
                aria-selected={activeTab === 'batch'}
                onClick={() => setActiveTab('batch')}
                className={`
                  flex items-center py-2.5 px-1 border-b-2 font-semibold text-sm whitespace-nowrap transition-all
                  ${activeTab === 'batch'
                    ? 'border-[#606c38] text-[#606c38]'
                    : 'border-transparent text-gray-600 hover:border-[#dda15e] hover:text-[#283618]'}
                `}
              >
                <Users className="w-4 h-4 mr-2" />
                Batch Management
              </button>
            </nav>

            <div className="flex w-full flex-col gap-2 sm:flex-row lg:max-w-xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  aria-label={`Search ${activeTab === 'individual' ? 'livestock' : 'batches'}`}
                  placeholder={`Search ${activeTab === 'individual' ? 'livestock' : 'batches'}...`}
                  className="block h-10 w-full rounded-lg border border-[#dda15e]/70 bg-white pl-10 pr-3 text-sm focus:border-[#606c38] focus:ring-2 focus:ring-[#606c38]"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="relative sm:w-48">
                <label htmlFor="livestock-type-filter" className="sr-only">
                  Livestock type
                </label>
                <select
                  id="livestock-type-filter"
                  aria-label="Filter by livestock type"
                  className="block h-10 w-full rounded-lg border border-gray-300 bg-white pl-3 pr-10 text-sm focus:border-[#606c38] focus:outline-none focus:ring-2 focus:ring-[#606c38]"
                  value={filterSpecies}
                  onChange={(e) => setFilterSpecies(e.target.value)}
                >
                  <option value="">All Livestock</option>
                  {ALL_LIVESTOCK_TYPES.map((livestockType) => (
                    <option
                      key={livestockType}
                      value={getSpeciesFilterValue(livestockType)}
                    >
                      {livestockType}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            </div>
          </div>

          <div className="p-4 sm:p-5 bg-white min-h-[400px]">
            <ErrorBoundary fallback={
              <div className="p-12 text-center">
                <AlertCircle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-gray-900">Failed to load tab content</h3>
                <p className="text-gray-500 mt-2">There was an error rendering this section. Please try switching tabs or refreshing.</p>
              </div>
            }>
              {activeTab === 'individual' ? (
                <LivestockTable
                  searchTerm={searchTerm}
                  filterSpecies={filterSpecies}
                  onSuccess={handleSuccess}
                />
              ) : (
                <BatchManagement
                  searchTerm={searchTerm}
                  filterSpecies={filterSpecies}
                  onSuccess={handleSuccess}
                  onBatchCreated={handleBatchCreated}
                />
              )}
            </ErrorBoundary>
          </div>
        </div>
      </ErrorBoundary>
    </div>
  );
};

export default LivestockList;
