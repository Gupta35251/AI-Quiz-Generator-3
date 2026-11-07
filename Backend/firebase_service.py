import os
import firebase_admin
from firebase_admin import credentials, firestore, auth

SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    r"D:\PythonProject\QuizWise-Secrets\serviceAccountKey.json"
)

def _init_firebase():
    if not firebase_admin._apps and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            credential = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(credential)
        except Exception:
            pass

_init_firebase()

class LazyDB:
    """Lazily gets the firestore client so importing does not block."""
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None and firebase_admin._apps:
            try:
                self._client = firestore.client()
            except Exception:
                self._client = None
        return self._client

    def collection(self, *args, **kwargs):
        client = self._get_client()
        if client is None:
            raise RuntimeError("Firestore client is not available")
        return client.collection(*args, **kwargs)

    def document(self, *args, **kwargs):
        client = self._get_client()
        if client is None:
            raise RuntimeError("Firestore client is not available")
        return client.document(*args, **kwargs)

db = LazyDB()
