#!/usr/bin/env python3
"""
Firebase接続テスト用スクリプト
"""

import os
from firebase_config import firebase_manager

def test_firebase_connection():
    """Firebase接続をテスト"""
    print("Firebase connection test starting...")
    
    # Firebase利用可能性チェック
    if firebase_manager.is_available():
        print("SUCCESS: Firebase connection established!")
        
        # データベース参照テスト
        db = firebase_manager.get_db()
        if db:
            print("SUCCESS: Firestore database accessible")
            
            # 簡単な書き込み・読み込みテスト
            try:
                test_doc = db.collection('test').document('connection_test')
                test_doc.set({'message': 'Hello from Catherine!', 'timestamp': 'test'})
                print("SUCCESS: Data write test passed")
                
                doc = test_doc.get()
                if doc.exists:
                    print(f"SUCCESS: Data read test passed: {doc.to_dict()}")
                    
                    # テストデータを削除
                    test_doc.delete()
                    print("SUCCESS: Test data cleanup completed")
                else:
                    print("ERROR: Data read failed")
                    
            except Exception as e:
                print(f"ERROR: Database operation failed: {e}")
        else:
            print("ERROR: Firestore database access failed")
    else:
        print("WARNING: Firebase unavailable - check environment variables")
        print("Required environment variable: FIREBASE_SERVICE_ACCOUNT_KEY")

if __name__ == "__main__":
    test_firebase_connection()