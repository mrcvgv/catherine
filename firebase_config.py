import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

class FirebaseManager:
    def __init__(self):
        self.db: Optional[firestore.Client] = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Firebase Admin SDKを初期化"""
        try:
            # Firebase サービスアカウントキーを環境変数から取得
            firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
            if not firebase_key:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable is not set")
            
            # JSON文字列をパース
            service_account_info = json.loads(firebase_key)
            
            # Firebase Admin SDK を初期化
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            
            # Firestore クライアントを取得
            self.db = firestore.client()
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            raise e
    
    def get_db(self) -> firestore.Client:
        """Firestoreクライアントを取得"""
        if self.db is None:
            raise RuntimeError("Firebase is not initialized")
        return self.db

# グローバルインスタンス
firebase_manager = FirebaseManager()
