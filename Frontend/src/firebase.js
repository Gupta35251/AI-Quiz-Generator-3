
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCWYz69BYsYWrZZXZDiDUAZWWyH249tKoA",
  authDomain: "quizwise-caa02.firebaseapp.com",
  projectId: "quizwise-caa02",
  storageBucket: "quizwise-caa02.firebasestorage.app",
  messagingSenderId: "995575746058",
  appId: "1:995575746058:web:e5eefe15114e07e9fc19f3",
  measurementId: "G-D53KYVJY0M"

};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app);
