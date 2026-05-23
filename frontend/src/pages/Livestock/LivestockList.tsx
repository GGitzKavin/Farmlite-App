import React, { useState, useEffect, useCallback } from 'react';
import LivestockTable from './LivestockTable';
import BatchManagement from './BatchManagement';
import { Tractor, Users, Search, Filter, CheckCircle, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import ErrorBoundary from '../../components/ErrorBoundary';
import { useAuth } from '../../context/AuthContext';

const LivestockList: React.FC = () => {
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'individual' | 'batch'>('individual');
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

  return (
    <div className="space-y-6 relative">
      <ErrorBoundary>
        {/* Toast Notification */}
        {successMessage && (
          <div className="fixed top-6 right-6 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="bg-green-600 text-white px-6 py-3 rounded-lg shadow-xl flex items-center gap-3">
              <CheckCircle className="w-5 h-5" />
              <span className="font-bold">{successMessage}</span>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Livestock Management</h1>
            <p className="text-sm text-gray-500">Manage individual animals and group batches</p>
          </div>
        </div>

        {/* Tabs and Primary Search */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="border-b border-gray-200 flex flex-col md:flex-row md:items-center justify-between px-6 bg-gray-50/50">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('individual')}
                className={`
                  flex items-center py-4 px-1 border-b-2 font-bold text-sm whitespace-nowrap transition-all
                  ${activeTab === 'individual'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                <Tractor className="w-4 h-4 mr-2" />
                Individual Animals
              </button>
              <button
                onClick={() => setActiveTab('batch')}
                className={`
                  flex items-center py-4 px-1 border-b-2 font-bold text-sm whitespace-nowrap transition-all
                  ${activeTab === 'batch'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                `}
              >
                <Users className="w-4 h-4 mr-2" />
                Batch Management
              </button>
            </nav>

            <div className="py-3 flex flex-col sm:flex-row gap-3 md:w-1/2 lg:w-1/3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder={`Search ${activeTab === 'individual' ? 'animals' : 'batches'}...`}
                  className="block w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md bg-white text-sm focus:ring-green-500 focus:border-green-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="relative">
                <select
                  className="block w-full pl-3 pr-10 py-2 text-sm border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 rounded-md bg-white"
                  value={filterSpecies}
                  onChange={(e) => setFilterSpecies(e.target.value)}
                >
                  <option value="">All Species</option>
                  <option value="Cattle (Beef)">Cattle (Beef)</option>
                  <option value="Cattle (Dairy)">Cattle (Dairy)</option>
                  <option value="Poultry">Poultry</option>
                  <option value="Chicken">Chicken</option>
                  <option value="Duck">Duck</option>
                  <option value="Swine">Swine</option>
                  <option value="Sheep/Goats">Sheep/Goats</option>
                </select>
              </div>
            </div>
          </div>

          <div className="p-6 bg-white min-h-[400px]">
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
