import React, { useEffect, useState } from 'react';
import { collection, query, where, getDocs, addDoc, serverTimestamp, doc, updateDoc } from 'firebase/firestore';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import type { FeedInventory } from '../types';
import { Wheat, Plus, AlertTriangle, Package } from 'lucide-react';

const FeedInventoryPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [feeds, setFeeds] = useState<FeedInventory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  const [formData, setFormData] = useState({
    feedName: '',
    quantity: '',
    targetAnimal: 'Cattle (Beef)',
    stockLevel: 'Medium',
    lowStockThreshold: '',
    notes: ''
  });

  useEffect(() => {
    const fetchFeeds = async () => {
      if (!currentUser) return;
      try {
        const q = query(
          collection(db, 'feedInventory'),
          where('userId', '==', currentUser.uid)
        );
        const snapshot = await getDocs(q);
        const data: FeedInventory[] = [];
        snapshot.forEach((doc) => data.push({ id: doc.id, ...doc.data() } as FeedInventory));
        setFeeds(data);
      } catch (error) {
        console.error("Error fetching feed: ", error);
      } finally {
        setLoading(false);
      }
    };
    fetchFeeds();
  }, [currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const calculateStockLevel = (qty: number, threshold: number) => {
    if (qty <= 0) return 'Out of Stock';
    if (qty <= threshold) return 'Low';
    if (qty <= threshold * 2) return 'Medium';
    return 'High';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    
    const qty = Number(formData.quantity);
    const threshold = Number(formData.lowStockThreshold);
    const calculatedStockLevel = calculateStockLevel(qty, threshold);

    try {
      const docRef = await addDoc(collection(db, 'feedInventory'), {
        ...formData,
        quantity: qty,
        lowStockThreshold: threshold,
        stockLevel: calculatedStockLevel,
        userId: currentUser.uid,
        createdAt: serverTimestamp()
      });
      
      setFeeds(prev => [...prev, { id: docRef.id, ...formData, quantity: qty, lowStockThreshold: threshold, stockLevel: calculatedStockLevel, userId: currentUser.uid } as FeedInventory]);
      setShowAddForm(false);
      setFormData({
        feedName: '',
        quantity: '',
        targetAnimal: 'Cattle (Beef)',
        stockLevel: 'Medium',
        lowStockThreshold: '',
        notes: ''
      });
    } catch (error) {
      console.error(error);
      alert("Failed to add feed.");
    }
  };

  const handleUpdateQuantity = async (id: string, currentQty: number, threshold: number, amount: number) => {
    const newQty = Math.max(0, currentQty + amount);
    const newStockLevel = calculateStockLevel(newQty, threshold);

    try {
      const feedRef = doc(db, 'feedInventory', id);
      await updateDoc(feedRef, {
        quantity: newQty,
        stockLevel: newStockLevel
      });

      setFeeds(prev => prev.map(f => f.id === id ? { ...f, quantity: newQty, stockLevel: newStockLevel } as FeedInventory : f));
    } catch (error) {
      console.error(error);
      alert("Failed to update quantity.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <Wheat className="h-6 w-6 mr-2 text-green-600" />
          Feed Inventory
        </h1>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          {showAddForm ? 'Cancel' : <><Plus className="-ml-1 mr-2 h-5 w-5" /> Add Feed</>}
        </button>
      </div>

      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-green-200">
          <h2 className="text-lg font-medium mb-4">Add Feed Inventory</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Feed Name</label>
                <input required type="text" name="feedName" value={formData.feedName} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Target Animal Type</label>
                <select name="targetAnimal" value={formData.targetAnimal} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm">
                  <option>Cattle (Beef)</option>
                  <option>Cattle (Dairy)</option>
                  <option>Poultry</option>
                  <option>Swine</option>
                  <option>Sheep/Goats</option>
                  <option>Equine</option>
                  <option>All</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Initial Quantity (kg/lbs)</label>
                <input required type="number" min="0" name="quantity" value={formData.quantity} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Low Stock Threshold</label>
                <input required type="number" min="0" name="lowStockThreshold" value={formData.lowStockThreshold} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Notes</label>
              <textarea name="notes" value={formData.notes} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm" rows={2}></textarea>
            </div>
            <div className="flex justify-end">
              <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700">
                Save Feed
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {feeds.length > 0 ? feeds.map((feed) => (
            <div key={feed.id} className={`bg-white rounded-lg shadow-sm border ${feed.stockLevel === 'Low' || feed.stockLevel === 'Out of Stock' ? 'border-red-300' : 'border-gray-200'}`}>
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{feed.feedName}</h3>
                    <p className="text-sm text-gray-500">For: {feed.targetAnimal}</p>
                  </div>
                  <Package className="h-6 w-6 text-gray-400" />
                </div>
                
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">Stock Level</span>
                    <span className={`text-sm font-bold ${feed.stockLevel === 'High' ? 'text-green-600' : feed.stockLevel === 'Medium' ? 'text-yellow-600' : 'text-red-600'}`}>
                      {feed.stockLevel}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full ${feed.stockLevel === 'High' ? 'bg-green-600' : feed.stockLevel === 'Medium' ? 'bg-yellow-400' : 'bg-red-600'}`} 
                      style={{ width: `${Math.min(100, (feed.quantity / (feed.lowStockThreshold * 3)) * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="mt-4 flex justify-between items-center text-sm">
                  <span className="text-gray-600">Current Qty: <strong className="text-gray-900">{feed.quantity}</strong></span>
                  <span className="text-gray-500">Threshold: {feed.lowStockThreshold}</span>
                </div>

                {feed.stockLevel === 'Low' && (
                  <div className="mt-3 flex items-center text-sm text-red-600 bg-red-50 p-2 rounded">
                    <AlertTriangle className="h-4 w-4 mr-1" />
                    Running low! Please restock soon.
                  </div>
                )}

                <div className="mt-5 flex justify-between gap-2 border-t pt-4">
                  <button 
                    onClick={() => handleUpdateQuantity(feed.id!, feed.quantity, feed.lowStockThreshold, -10)}
                    className="flex-1 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    -10
                  </button>
                  <button 
                    onClick={() => handleUpdateQuantity(feed.id!, feed.quantity, feed.lowStockThreshold, 10)}
                    className="flex-1 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    +10
                  </button>
                  <button 
                    onClick={() => handleUpdateQuantity(feed.id!, feed.quantity, feed.lowStockThreshold, 50)}
                    className="flex-1 py-1.5 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700"
                  >
                    Restock
                  </button>
                </div>
              </div>
            </div>
          )) : (
            <div className="col-span-full text-center py-12 bg-white rounded-lg border border-gray-200 border-dashed">
              <p className="text-gray-500">No feed inventory records found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FeedInventoryPage;
