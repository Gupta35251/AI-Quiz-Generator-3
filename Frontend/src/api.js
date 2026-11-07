
import { auth, googleProvider } from "./firebase.js";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const USER_KEY = "quizwise_user";

function formatUser(firebaseUser) {
  if (!firebaseUser) return null;

  return {
    id: firebaseUser.uid,
    uid: firebaseUser.uid,
    email: firebaseUser.email,
    name: firebaseUser.displayName || "",
  };
}

export function subscribeToAuth(callback) {
  return onAuthStateChanged(auth, (firebaseUser) => {
    callback(formatUser(firebaseUser));
  });
}

export function saveLogin(data) {
  if (data?.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  }
}

export function clearLogin() {
  localStorage.removeItem(USER_KEY);
  return signOut(auth);
}

export function getSavedToken() {
  return null;
}

export function getSavedUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  const firebaseUser = auth.currentUser;
  const token = firebaseUser
    ? await firebaseUser.getIdToken()
    : null;

  let response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  } catch {
    throw new Error(
      "Can't connect to the backend. Check that FastAPI is running on port 8000."
    );
  }

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401 && token) {
      await clearLogin();
      window.dispatchEvent(new Event("quizwise:logout"));
    }

    const detail = payload.detail;

    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request failed with status ${response.status}. Please try again.`
    );
  }

  return payload;
}

export const api = {
  health: () => request("/api/health"),

  signup: async ({ email, password }) => {
    const credential = await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );
    return { user: formatUser(credential.user) };
  },

  login: async ({ email, password }) => {
    const credential = await signInWithEmailAndPassword(
      auth,
      email,
      password
    );
    return { user: formatUser(credential.user) };
  },

  googleLogin: async () => {
    const credential = await signInWithPopup(auth, googleProvider);
    return { user: formatUser(credential.user) };
  },

  logout: () => clearLogin(),

  me: () => request("/api/auth/me"),

  generateQuiz: (data) =>
    request("/api/quiz/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  submitQuiz: (data) =>
    request("/api/quiz/submit", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  history: () => request("/api/history"),

  historyItem: (id) => request(`/api/history/${id}`),

  weakConcepts: () => request("/api/weak-concepts"),

  generateWeeklyQuiz: () =>
    request("/api/weekly-quiz/generate", {
      method: "POST",
    }),
};
