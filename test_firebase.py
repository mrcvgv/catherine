# test_firebase.py
import os
from firebase_config import firebase_manager
from dotenv import load_dotenv

load_dotenv()

print("Firebase manager available:", firebase_manager.is_available())

if firebase_manager.is_available():
    try:
        db = firebase_manager.get_db()
        # Test write
        doc_ref = db.collection("healthcheck").document("ping")
        doc_ref.set({"timestamp": "test", "status": "ok"})
        print("✅ Firebase write ok")
        
        # Test read
        doc = doc_ref.get()
        if doc.exists:
            print("✅ Firebase read ok:", doc.to_dict())
        else:
            print("⚠️ Document not found after write")
            
    except Exception as e:
        print("❌ Firebase operation failed:", e)
else:
    print("❌ Firebase not available")
    print("Available env vars with 'FIREBASE':", [k for k in os.environ.keys() if "FIREBASE" in k])
    
    # Check for service account files
    import glob
    json_files = glob.glob("*firebase*.json")
    print("Firebase JSON files found:", json_files)