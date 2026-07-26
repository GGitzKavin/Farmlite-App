import React, { useEffect, useState } from 'react';
import {
  addDoc,
  collection,
  deleteDoc,
  doc,
  getDocs,
  query,
  runTransaction,
  serverTimestamp,
  where,
} from 'firebase/firestore';
import { db } from '../firebase/config';
import { useAuth } from '../context/AuthContext';
import type { FeedInventory } from '../types';
import { Wheat, Plus, AlertTriangle, Package, Save, Trash2 } from 'lucide-react';
import {
  MAX_STOCK_QUANTITY,
  calculateFeedStockLevel,
  calculatePercentageStock,
  calculateRestockedStock,
  formatStockQuantity,
  getFeedUnit,
  roundStockQuantity,
  validateRestockQuantity,
  type StockAdjustmentDirection,
} from '../features/feedStock';

type StockDialogMode = StockAdjustmentDirection | 'restock';

interface StockDialogState {
  feedId: string;
  feedName: string;
  mode: StockDialogMode;
  currentQuantity: number;
  previewQuantity: number;
  unit: string;
  lowStockThreshold: number;
}

interface InventoryFeedback {
  type: 'success' | 'error';
  message: string;
}

const FeedInventoryPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [feeds, setFeeds] = useState<FeedInventory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [feedback, setFeedback] = useState<InventoryFeedback | null>(null);
  const [stockDialog, setStockDialog] = useState<StockDialogState | null>(null);
  const [restockQuantity, setRestockQuantity] = useState('');
  const [stockDialogError, setStockDialogError] = useState('');
  const [openingStockControl, setOpeningStockControl] = useState<string | null>(
    null,
  );
  const [savingStock, setSavingStock] = useState(false);

  const [formData, setFormData] = useState({
    feedName: '',
    quantity: '',
    unit: 'kg',
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
        snapshot.forEach((feedDocument) => {
          const feed = {
            id: feedDocument.id,
            ...feedDocument.data(),
          } as FeedInventory;
          const quantity = Number(feed.quantity);
          const threshold = Number(feed.lowStockThreshold);
          const safeQuantity = Number.isFinite(quantity) ? quantity : 0;
          const safeThreshold = Number.isFinite(threshold) ? threshold : 0;

          data.push({
            ...feed,
            quantity: safeQuantity,
            lowStockThreshold: safeThreshold,
            stockLevel: calculateFeedStockLevel(
              safeQuantity,
              safeThreshold,
            ),
          });
        });
        setFeeds(data);
      } catch (error) {
        console.error("Error fetching feed: ", error);
        setFeedback({
          type: 'error',
          message: 'Could not load feed inventory. Please try again.',
        });
      } finally {
        setLoading(false);
      }
    };
    fetchFeeds();
  }, [currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (feedback) setFeedback(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    const qty = Number(formData.quantity);
    const threshold = Number(formData.lowStockThreshold);
    const calculatedStockLevel = calculateFeedStockLevel(qty, threshold);

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
        unit: 'kg',
        targetAnimal: 'Cattle (Beef)',
        stockLevel: 'Medium',
        lowStockThreshold: '',
        notes: ''
      });
      setFeedback({
        type: 'success',
        message: 'Feed inventory added successfully.',
      });
    } catch (error) {
      console.error(error);
      setFeedback({
        type: 'error',
        message: 'Failed to add feed. Please try again.',
      });
    }
  };

  const closeStockDialog = () => {
    if (savingStock) return;
    setStockDialog(null);
    setRestockQuantity('');
    setStockDialogError('');
  };

  const openStockDialog = async (
    feed: FeedInventory,
    mode: StockDialogMode,
  ) => {
    if (!currentUser || !feed.id) return;
    const controlKey = `${feed.id}-${mode}`;
    setOpeningStockControl(controlKey);
    setFeedback(null);
    setStockDialogError('');

    try {
      const feedRef = doc(db, 'feedInventory', feed.id);
      const latestStock = await runTransaction(db, async (transaction) => {
        const feedSnapshot = await transaction.get(feedRef);
        if (!feedSnapshot.exists()) {
          throw new Error('This feed item is no longer available.');
        }

        const data = feedSnapshot.data();
        if (data.userId !== currentUser.uid) {
          throw new Error('You do not have access to this feed item.');
        }

        const currentQuantity = Number(data.quantity);
        if (!Number.isFinite(currentQuantity) || currentQuantity < 0) {
          throw new Error('The stored stock quantity is invalid.');
        }
        if (currentQuantity === 0 && mode !== 'restock') {
          throw new Error(
            'Use Restock to enter the newly received quantity.',
          );
        }

        const unit = getFeedUnit(
          typeof data.unit === 'string' ? data.unit : feed.unit,
        );
        const storedThreshold = Number(data.lowStockThreshold);
        const lowStockThreshold = Number.isFinite(storedThreshold)
          ? storedThreshold
          : feed.lowStockThreshold;
        const previewQuantity =
          mode === 'restock'
            ? roundStockQuantity(currentQuantity, unit)
            : calculatePercentageStock(currentQuantity, mode, unit);

        if (
          !Number.isFinite(previewQuantity) ||
          previewQuantity < 0 ||
          previewQuantity > MAX_STOCK_QUANTITY
        ) {
          throw new Error('The resulting stock quantity is outside the allowed range.');
        }

        return {
          feedId: feedSnapshot.id,
          feedName:
            typeof data.feedName === 'string' && data.feedName.trim()
              ? data.feedName
              : feed.feedName,
          mode,
          currentQuantity,
          previewQuantity,
          unit,
          lowStockThreshold,
        } satisfies StockDialogState;
      });

      setStockDialog(latestStock);
      setRestockQuantity('');
    } catch (error) {
      console.error('Error preparing stock adjustment: ', error);
      setFeedback({
        type: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not prepare the stock adjustment. Please try again.',
      });
    } finally {
      setOpeningStockControl(null);
    }
  };

  const handleRestockQuantityChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const value = event.target.value;
    setRestockQuantity(value);
    if (!stockDialog || stockDialog.mode !== 'restock') return;

    const validation = validateRestockQuantity(value, stockDialog.unit);
    if (!value.trim()) {
      setStockDialogError('');
      setStockDialog({
        ...stockDialog,
        previewQuantity: roundStockQuantity(
          stockDialog.currentQuantity,
          stockDialog.unit,
        ),
      });
      return;
    }

    if (validation.error || validation.value === null) {
      setStockDialogError(validation.error);
      return;
    }

    try {
      const previewQuantity = calculateRestockedStock(
        stockDialog.currentQuantity,
        validation.value,
        stockDialog.unit,
      );
      setStockDialogError('');
      setStockDialog({ ...stockDialog, previewQuantity });
    } catch (error) {
      setStockDialogError(
        error instanceof Error
          ? error.message
          : 'The resulting stock quantity is invalid.',
      );
    }
  };

  const confirmStockAdjustment = async () => {
    if (!currentUser || !stockDialog) return;

    let receivedQuantity: number | null = null;
    if (stockDialog.mode === 'restock') {
      const validation = validateRestockQuantity(
        restockQuantity,
        stockDialog.unit,
      );
      if (validation.error || validation.value === null) {
        setStockDialogError(validation.error);
        return;
      }
      receivedQuantity = validation.value;
    }

    setSavingStock(true);
    setStockDialogError('');
    const dialogAtConfirmation = stockDialog;

    try {
      const feedRef = doc(db, 'feedInventory', dialogAtConfirmation.feedId);
      const result = await runTransaction(db, async (transaction) => {
        const feedSnapshot = await transaction.get(feedRef);
        if (!feedSnapshot.exists()) {
          throw new Error('This feed item is no longer available.');
        }

        const data = feedSnapshot.data();
        if (data.userId !== currentUser.uid) {
          throw new Error('You do not have access to this feed item.');
        }

        const latestQuantity = Number(data.quantity);
        if (!Number.isFinite(latestQuantity) || latestQuantity < 0) {
          throw new Error('The stored stock quantity is invalid.');
        }

        const latestUnit = getFeedUnit(
          typeof data.unit === 'string' ? data.unit : dialogAtConfirmation.unit,
        );
        const storedThreshold = Number(data.lowStockThreshold);
        const latestThreshold = Number.isFinite(storedThreshold)
          ? storedThreshold
          : dialogAtConfirmation.lowStockThreshold;
        const calculateNewQuantity = () =>
          dialogAtConfirmation.mode === 'restock'
            ? calculateRestockedStock(
                latestQuantity,
                receivedQuantity as number,
                latestUnit,
              )
            : calculatePercentageStock(
                latestQuantity,
                dialogAtConfirmation.mode,
                latestUnit,
              );
        const newQuantity = calculateNewQuantity();

        if (
          !Number.isFinite(newQuantity) ||
          newQuantity < 0 ||
          newQuantity > MAX_STOCK_QUANTITY
        ) {
          throw new Error('The resulting stock quantity is outside the allowed range.');
        }

        if (
          latestQuantity !== dialogAtConfirmation.currentQuantity ||
          latestUnit !== dialogAtConfirmation.unit
        ) {
          return {
            status: 'stale' as const,
            dialog: {
              ...dialogAtConfirmation,
              feedName:
                typeof data.feedName === 'string' && data.feedName.trim()
                  ? data.feedName
                  : dialogAtConfirmation.feedName,
              currentQuantity: latestQuantity,
              previewQuantity: newQuantity,
              unit: latestUnit,
              lowStockThreshold: latestThreshold,
            },
          };
        }

        const stockUpdate: Record<string, unknown> = {
          quantity: newQuantity,
        };
        if (Object.prototype.hasOwnProperty.call(data, 'updatedAt')) {
          stockUpdate.updatedAt = serverTimestamp();
        }
        transaction.update(feedRef, stockUpdate);

        return {
          status: 'updated' as const,
          quantity: newQuantity,
          unit: latestUnit,
          lowStockThreshold: latestThreshold,
        };
      });

      if (result.status === 'stale') {
        setStockDialog(result.dialog);
        setStockDialogError(
          'Stock changed since this preview. Review the updated quantity and confirm again.',
        );
        return;
      }

      const newStockLevel = calculateFeedStockLevel(
        result.quantity,
        result.lowStockThreshold,
      );
      setFeeds((previousFeeds) =>
        previousFeeds.map((feed) =>
          feed.id === dialogAtConfirmation.feedId
            ? {
                ...feed,
                quantity: result.quantity,
                unit: result.unit,
                stockLevel: newStockLevel,
              }
            : feed,
        ),
      );

      const formattedQuantity = `${formatStockQuantity(
        result.quantity,
        result.unit,
      )} ${result.unit}`;
      const successMessage =
        dialogAtConfirmation.mode === 'decrease'
          ? `Stock reduced to ${formattedQuantity}.`
          : dialogAtConfirmation.mode === 'increase'
            ? `Stock increased to ${formattedQuantity}.`
            : `Restock completed. Current stock: ${formattedQuantity}.`;

      setStockDialog(null);
      setRestockQuantity('');
      setFeedback({ type: 'success', message: successMessage });
    } catch (error) {
      console.error('Error updating feed stock: ', error);
      setStockDialogError(
        error instanceof Error
          ? `${error.message} The previous quantity was preserved.`
          : 'Could not update stock. The previous quantity was preserved.',
      );
    } finally {
      setSavingStock(false);
    }
  };

  const handleDeleteFeed = async (feedId: string | undefined) => {
    if (!feedId) return;
    if (!window.confirm('Are you sure you want to delete this feed item? This action cannot be undone.')) return;

    try {
      await deleteDoc(doc(db, 'feedInventory', feedId));
      setFeeds(prev => prev.filter(feed => feed.id !== feedId));
      setFeedback({
        type: 'success',
        message: 'Feed item deleted successfully.',
      });
    } catch (error) {
      console.error('Error deleting feed item: ', error);
      setFeedback({
        type: 'error',
        message: 'Could not delete the feed item. Please try again.',
      });
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
          className="inline-flex items-center justify-center rounded-lg border border-transparent bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#606c38]"
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
                <label className="block text-sm font-medium text-gray-700">Initial Quantity (kg)</label>
                <input required type="number" min="0" max={MAX_STOCK_QUANTITY} step="0.01" name="quantity" value={formData.quantity} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 border p-2 shadow-sm focus:border-[#606c38] focus:ring-[#606c38] sm:text-sm" />
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
              <button type="submit" className="inline-flex items-center justify-center rounded-lg border border-transparent bg-[#606c38] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#4f5a2f]">
                <Save className="mr-2 h-4 w-4" />
                Save Feed
              </button>
            </div>
          </form>
        </div>
      )}

      {feedback && (
        <div
          role={feedback.type === 'error' ? 'alert' : 'status'}
          aria-live={feedback.type === 'error' ? 'assertive' : 'polite'}
          className={`rounded-lg border px-4 py-3 text-sm font-medium ${
            feedback.type === 'error'
              ? 'border-[#bc6c25] bg-[#fefae0] text-[#7a4016]'
              : 'border-[#606c38] bg-[#fefae0] text-[#283618]'
          }`}
        >
          {feedback.message}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="grid min-w-0 grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {feeds.length > 0 ? feeds.map((feed) => (
            <div key={feed.id} className={`min-w-0 overflow-hidden rounded-lg border bg-white shadow-sm ${feed.stockLevel === 'Low' || feed.stockLevel === 'Out of Stock' ? 'border-[#bc6c25]' : 'border-gray-200'}`}>
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
                      className={`h-2.5 rounded-full ${feed.stockLevel === 'High' ? 'bg-[#606c38]' : feed.stockLevel === 'Medium' ? 'bg-[#dda15e]' : 'bg-[#bc6c25]'}`}
                      style={{
                        width: `${
                          feed.lowStockThreshold > 0
                            ? Math.min(
                                100,
                                (feed.quantity /
                                  (feed.lowStockThreshold * 3)) *
                                  100,
                              )
                            : feed.quantity > 0
                              ? 100
                              : 0
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="text-gray-600">Current Qty: <strong className="text-gray-900">{formatStockQuantity(feed.quantity, feed.unit)} {getFeedUnit(feed.unit)}</strong></span>
                  <span className="text-gray-500">Threshold: {formatStockQuantity(feed.lowStockThreshold, feed.unit)} {getFeedUnit(feed.unit)}</span>
                </div>

                {feed.stockLevel === 'Low' && (
                  <div className="mt-3 flex items-center text-sm text-red-600 bg-red-50 p-2 rounded">
                    <AlertTriangle className="h-4 w-4 mr-1" />
                    Running low! Please restock soon.
                  </div>
                )}

                {feed.quantity <= 0 && (
                  <p className="mt-3 rounded-md bg-[#fefae0] p-2 text-sm font-medium text-[#283618]">
                    Use Restock to enter the newly received quantity.
                  </p>
                )}

                <div className="mt-5 grid min-w-0 grid-cols-1 gap-2 border-t pt-4 sm:grid-cols-3">
                  <button
                    type="button"
                    onClick={() => void openStockDialog(feed, 'decrease')}
                    disabled={
                      feed.quantity <= 0 ||
                      openingStockControl !== null ||
                      savingStock
                    }
                    className="w-full rounded-lg border border-[#606c38] px-3 py-2 text-sm font-semibold text-[#283618] hover:bg-[#fefae0] focus:outline-none focus:ring-2 focus:ring-[#606c38] focus:ring-offset-2 disabled:cursor-not-allowed disabled:border-gray-300 disabled:text-gray-400 disabled:hover:bg-transparent"
                  >
                    −10%
                  </button>
                  <button
                    type="button"
                    onClick={() => void openStockDialog(feed, 'increase')}
                    disabled={
                      feed.quantity <= 0 ||
                      openingStockControl !== null ||
                      savingStock
                    }
                    className="w-full rounded-lg border border-[#606c38] px-3 py-2 text-sm font-semibold text-[#283618] hover:bg-[#fefae0] focus:outline-none focus:ring-2 focus:ring-[#606c38] focus:ring-offset-2 disabled:cursor-not-allowed disabled:border-gray-300 disabled:text-gray-400 disabled:hover:bg-transparent"
                  >
                    +10%
                  </button>
                  <button
                    type="button"
                    onClick={() => void openStockDialog(feed, 'restock')}
                    disabled={openingStockControl !== null || savingStock}
                    className="w-full rounded-lg border border-transparent bg-[#606c38] px-3 py-2 text-sm font-semibold text-white hover:bg-[#283618] focus:outline-none focus:ring-2 focus:ring-[#606c38] focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400"
                  >
                    {openingStockControl === `${feed.id}-restock`
                      ? 'Loading…'
                      : 'Restock'}
                  </button>
                </div>
                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => void handleDeleteFeed(feed.id)}
                    className="inline-flex w-full items-center justify-center rounded-lg bg-[#c1121f] px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-[#9f0f1a] sm:w-auto"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
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

      {stockDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-[#283618]/60 p-4"
          onKeyDown={(event) => {
            if (event.key === 'Escape') closeStockDialog();
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="stock-adjustment-title"
            aria-describedby="stock-adjustment-description"
            className="w-full max-w-md overflow-hidden rounded-xl border border-[#dda15e] bg-white shadow-xl"
          >
            <div className="border-b border-[#dda15e]/40 bg-[#fefae0] px-5 py-4">
              <h2
                id="stock-adjustment-title"
                className="text-lg font-bold text-[#283618]"
              >
                {stockDialog.mode === 'restock'
                  ? `Restock ${stockDialog.feedName}`
                  : stockDialog.mode === 'decrease'
                    ? 'Confirm 10% stock reduction'
                    : 'Confirm 10% stock increase'}
              </h2>
              <p className="mt-1 text-sm text-[#606c38]">
                Current stock: {formatStockQuantity(
                  stockDialog.currentQuantity,
                  stockDialog.unit,
                )}{' '}
                {stockDialog.unit}
              </p>
            </div>

            <div className="space-y-4 px-5 py-4">
              {stockDialog.mode === 'restock' && (
                <div>
                  <label
                    htmlFor="restock-quantity"
                    className="block text-sm font-semibold text-[#283618]"
                  >
                    Quantity received
                  </label>
                  <input
                    id="restock-quantity"
                    type="number"
                    inputMode="decimal"
                    min="0"
                    max={MAX_STOCK_QUANTITY}
                    step="0.01"
                    value={restockQuantity}
                    onChange={handleRestockQuantityChange}
                    aria-invalid={Boolean(stockDialogError)}
                    aria-describedby="restock-quantity-help restock-quantity-error"
                    autoFocus
                    className="mt-1 block w-full rounded-lg border border-gray-300 p-2.5 shadow-sm focus:border-[#606c38] focus:outline-none focus:ring-2 focus:ring-[#606c38]"
                  />
                  <p
                    id="restock-quantity-help"
                    className="mt-1 text-sm text-gray-600"
                  >
                    Enter the amount of new feed added to the current stock.
                  </p>
                </div>
              )}

              <div
                id="stock-adjustment-description"
                className="rounded-lg border border-[#dda15e] bg-[#fefae0] p-3 text-sm font-medium text-[#283618]"
              >
                {stockDialog.mode === 'decrease' && (
                  <>
                    Reduce {stockDialog.feedName} from{' '}
                    {formatStockQuantity(
                      stockDialog.currentQuantity,
                      stockDialog.unit,
                    )}{' '}
                    {stockDialog.unit} to{' '}
                    {formatStockQuantity(
                      stockDialog.previewQuantity,
                      stockDialog.unit,
                    )}{' '}
                    {stockDialog.unit}?
                  </>
                )}
                {stockDialog.mode === 'increase' && (
                  <>
                    Increase {stockDialog.feedName} from{' '}
                    {formatStockQuantity(
                      stockDialog.currentQuantity,
                      stockDialog.unit,
                    )}{' '}
                    {stockDialog.unit} to{' '}
                    {formatStockQuantity(
                      stockDialog.previewQuantity,
                      stockDialog.unit,
                    )}{' '}
                    {stockDialog.unit}?
                  </>
                )}
                {stockDialog.mode === 'restock' && (
                  <>
                    {restockQuantity &&
                    !stockDialogError &&
                    validateRestockQuantity(
                      restockQuantity,
                      stockDialog.unit,
                    ).value !== null ? (
                      <>
                        Add{' '}
                        {formatStockQuantity(
                          validateRestockQuantity(
                            restockQuantity,
                            stockDialog.unit,
                          ).value as number,
                          stockDialog.unit,
                        )}{' '}
                        {stockDialog.unit} to {stockDialog.feedName}? New stock:{' '}
                        {formatStockQuantity(
                          stockDialog.previewQuantity,
                          stockDialog.unit,
                        )}{' '}
                        {stockDialog.unit}.
                      </>
                    ) : (
                      <>
                        New stock:{' '}
                        {formatStockQuantity(
                          stockDialog.previewQuantity,
                          stockDialog.unit,
                        )}{' '}
                        {stockDialog.unit}
                      </>
                    )}
                  </>
                )}
              </div>

              <p
                id="restock-quantity-error"
                role="alert"
                aria-live="assertive"
                className="min-h-5 text-sm font-medium text-[#bc6c25]"
              >
                {stockDialogError}
              </p>

              <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  onClick={closeStockDialog}
                  disabled={savingStock}
                  className="w-full rounded-lg border border-[#606c38] px-4 py-2 text-sm font-semibold text-[#283618] hover:bg-[#fefae0] focus:outline-none focus:ring-2 focus:ring-[#606c38] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => void confirmStockAdjustment()}
                  disabled={savingStock}
                  autoFocus={stockDialog.mode !== 'restock'}
                  className="w-full rounded-lg bg-[#606c38] px-4 py-2 text-sm font-semibold text-white hover:bg-[#283618] focus:outline-none focus:ring-2 focus:ring-[#606c38] focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-gray-400 sm:w-auto"
                >
                  {savingStock
                    ? 'Saving…'
                    : stockDialog.mode === 'restock'
                      ? 'Confirm Restock'
                      : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedInventoryPage;
