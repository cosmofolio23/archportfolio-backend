import firebase_admin
from firebase_admin import credentials, auth
from config import settings
import os
import json

# Firebase service account key from environment
firebase_key = None

try:
    # Try to load from environment variable
    firebase_key_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

    if firebase_key_str:
        # Parse the JSON from environment variable
        firebase_key = json.loads(firebase_key_str)
    else:
        print("⚠️ FIREBASE_SERVICE_ACCOUNT_KEY not set")
except Exception as e:
    print(f"⚠️ Error loading Firebase key: {e}")

# Initialize Firebase Admin SDK
firebase_app = None

try:
    if firebase_key:
        cred = credentials.Certificate(firebase_key)
        firebase_app = firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    else:
        print("⚠️ Firebase Admin SDK not initialized - FIREBASE_SERVICE_ACCOUNT_KEY not provided")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    import traceback
    traceback.print_exc()

def get_firebase_app():
    return firebase_app

def verify_firebase_token(token: str):
    """Verify Firebase ID token"""
    try:
        if not firebase_app:
            raise Exception("Firebase not initialized")
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise Exception(f"Token verification failed: {e}")
