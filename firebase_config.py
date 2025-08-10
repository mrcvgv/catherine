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
            # 1. 環境変数から読み込み（優先）
            firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
            if firebase_key:
                print("INFO: Using Firebase key from environment variable")
                service_account_info = json.loads(firebase_key)
            else:
                # 2. JSONファイルから読み込み
                json_files = [f for f in os.listdir('.') if 'firebase-adminsdk' in f and f.endswith('.json')]
                
                if not json_files:
                    print("WARNING: No Firebase service account key found")
                    self.db = None
                    return
                
                # 最初に見つかったファイルを使用
                key_file = json_files[0]
                print(f"INFO: Using Firebase key from file: {key_file}")
                
                with open(key_file, 'r', encoding='utf-8') as f:
                    service_account_info = json.load(f)
            
            # Firebase Admin SDK を初期化
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred)
            
            # Firestore クライアントを取得
            self.db = firestore.client()
            print("SUCCESS: Firebase initialized successfully")
            
        except Exception as e:
            print(f"ERROR: Firebase initialization error: {e}")
            print("WARNING: Continuing without Firebase features")
            self.db = None
    
    def get_db(self) -> Optional[firestore.Client]:
        """Firestoreクライアントを取得"""
        return self.db
    
    def is_available(self) -> bool:
        """Firebaseが利用可能かチェック"""
        return self.db is not None

# グローバルインスタンス
firebase_manager = FirebaseManager()
