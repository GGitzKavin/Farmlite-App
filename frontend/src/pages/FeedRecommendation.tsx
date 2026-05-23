import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Bot, Activity, Wheat, AlertCircle } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { doc, getDoc } from 'firebase/firestore';
import { db } from '../firebase/config';

const FeedRecommendation: React.FC = () => {
  const { currentUser } = useAuth();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recommendation, setRecommendation] = useState<any>(null);

  const [formData, setFormData] = useState({
    breed: 'Holstein',
    weight: '',
    healthStatus: 'Healthy',
    age: '',
    milkProductionStage: 'Lactating'
  });

  useEffect(() => {
    const fetchAnimalData = async () => {
      const animalId = searchParams.get('id');
      if (animalId && currentUser) {
        try {
          const docRef = doc(db, 'livestock', animalId);
          const docSnap = await getDoc(docRef);
          if (docSnap.exists() && docSnap.data().userId === currentUser.uid) {
            const data = docSnap.data();
            setFormData({
              breed: data.breed || 'Holstein',
              weight: data.weight?.toString() || '',
              healthStatus: data.healthStatus || 'Healthy',
              age: data.age?.toString() || '',
              milkProductionStage: data.species.includes('Dairy') ? 'Lactating' : 'Dry'
            });
          }
        } catch (err) {
          console.error("Error fetching animal for recommendation:", err);
        }
      }
    };
    fetchAnimalData();
  }, [searchParams, currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    setLoading(true);
    setError('');
    setRecommendation(null);

    try {
      const response = await axios.post('http://localhost:5000/api/ai/feed-recommendation', formData);
      setRecommendation(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error || 'Failed to connect to the AI service. Ensure the Flask backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Bot className="h-6 w-6 mr-2 text-green-600" />
          AI Feed Recommendation
        </h1>
      </div>

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              This AI feature is designed specifically for <strong>Dairy Cattle</strong>. It analyzes the cow's profile to suggest optimal feed nutrition and quantities.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Cow Profile</h3>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Breed</label>
              <select name="breed" value={formData.breed} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                <option>Holstein</option>
                <option>Jersey</option>
                <option>Guernsey</option>
                <option>Ayrshire</option>
                <option>Brown Swiss</option>
                <option>Other Dairy</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Weight (kg)</label>
                <input required type="number" min="0" step="0.1" name="weight" value={formData.weight} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Age (Months)</label>
                <input required type="number" min="0" name="age" value={formData.age} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Health Status</label>
              <select name="healthStatus" value={formData.healthStatus} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                <option>Healthy</option>
                <option>Sick</option>
                <option>Recovering</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Milk Production Stage</label>
              <select name="milkProductionStage" value={formData.milkProductionStage} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                <option>Early Lactation</option>
                <option>Mid Lactation</option>
                <option>Late Lactation</option>
                <option>Dry</option>
              </select>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex justify-center items-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-green-400 w-full"
              >
                {loading ? 'Analyzing...' : <><Bot className="w-5 h-5 mr-2" /> Get AI Recommendation</>}
              </button>
            </div>

            {error && (
              <div className="mt-4 bg-red-50 p-4 rounded-md border border-red-200">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
          </form>
        </div>

        <div>
          {recommendation ? (
            <div className="bg-white shadow-lg rounded-lg border border-green-200 overflow-hidden transform transition-all">
              <div className="bg-gradient-to-r from-green-600 to-green-500 px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-white flex items-center">
                  <Activity className="h-5 w-5 mr-2 text-white" />
                  Recommendation Results
                </h3>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 uppercase">Suggested Feed</h4>
                  <p className="mt-1 text-2xl font-bold text-gray-900 flex items-center">
                    <Wheat className="h-6 w-6 mr-2 text-green-500" />
                    {recommendation.recommendedFeed}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-500 uppercase">Quantity / Day</h4>
                    <p className="mt-1 text-xl font-bold text-gray-900">{recommendation.quantity} kg</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-md">
                    <h4 className="text-sm font-medium text-gray-500 uppercase">Nutrition Score</h4>
                    <p className="mt-1 text-xl font-bold text-gray-900">{recommendation.nutritionScore}/100</p>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-md border border-green-100">
                  <h4 className="text-sm font-medium text-green-800 uppercase mb-2">AI Summary</h4>
                  <p className="text-sm text-green-700 italic">
                    "{recommendation.summary}"
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full bg-gray-50 rounded-lg border border-dashed border-gray-300 flex flex-col items-center justify-center p-12 text-center">
              <Bot className="h-16 w-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Awaiting Input</h3>
              <p className="mt-1 text-sm text-gray-500 max-w-sm">
                Fill out the cow's profile and click the button to generate a smart feed recommendation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedRecommendation;
