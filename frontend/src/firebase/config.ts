import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDA0sRURtRS8NMpsjUn7wGwHHrgdJBRBwM",
  authDomain: "farmlite-66288.firebaseapp.com",
  projectId: "farmlite-66288",
  storageBucket: "farmlite-66288.firebasestorage.app",
  messagingSenderId: "193083325494",
  appId: "1:193083325494:web:096c28a14f1728ee396c97",
  measurementId: "G-NJTENYHBBR"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
