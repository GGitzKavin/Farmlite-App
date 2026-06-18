import { Timestamp } from 'firebase/firestore';

export interface User {
  uid: string;
  name: string;
  email: string;
  createdAt: Timestamp | Date;
}

export interface Livestock {
  id: string; // Firestore document ID
  animalId: string; // User-defined ID/Tag
  animalName: string;
  species: string;
  breed: string;
  gender: string;
  age: number; // in months or years, specify in UI
  weight: number; // in kg or lbs
  birthDate: string;
  vaccinationStatus: 'Up to date' | 'Pending' | 'Overdue';
  healthStatus: 'Healthy' | 'Sick' | 'Recovering';
  feedType: string;
  notes: string;
  createdAt: Timestamp | Date;
  userId: string; // to scope records per user if necessary, though it's single user, it's good practice. Wait, prompt says "single user type only... every registered user has access to all available features without separate admin permissions". We'll tie records to the user who created them or make them global if everyone is one farm. Let's tie it to `userId` so each farmer has their own farm data.
}

export interface Vaccination {
  id?: string;
  vaccineName: string;
  vaccinationDate: string;
  nextDueDate?: string;
  livestockId?: string;
  batchId?: string;
  targetType?: 'Individual Animal' | 'Batch';
  reminderStatus: 'Active' | 'Dismissed';
  notes: string;
  userId: string;
}

export interface FeedInventory {
  id?: string;
  feedName: string;
  quantity: number;
  targetAnimal: string;
  stockLevel: 'High' | 'Medium' | 'Low' | 'Out of Stock';
  lowStockThreshold: number;
  notes: string;
  userId: string;
}

export interface HealthRecord {
  id?: string;
  livestockId: string;
  animalName: string;
  diseaseType: string;
  symptoms: string;
  treatment: string;
  medicine: string;
  vetNotes: string;
  recoveryStatus: 'Recovered' | 'In Treatment' | 'Critical';
  createdAt: Timestamp | Date;
  userId: string;
}

export interface Batch {
  id: string;
  batchName: string;
  species: string;
  headCount: number;
  healthStatus: string;
  vaccinationStatus: string;
  feedType: string;
  createdAt: Timestamp | Date;
}
