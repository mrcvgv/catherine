#!/usr/bin/env python3
"""
Deployment Test Script for Catherine AI
デプロイ前の最終チェック
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    errors = []
    
    print("[TEST] Checking critical imports...")
    
    try:
        import discord
        print("[OK] discord")
    except ImportError as e:
        errors.append(f"discord: {e}")
    
    try:
        import openai
        print("[OK] openai")
    except ImportError as e:
        errors.append(f"openai: {e}")
    
    try:
        import firebase_admin
        print("[OK] firebase_admin")
    except ImportError as e:
        errors.append(f"firebase_admin: {e}")
    
    try:
        import pytz
        print("[OK] pytz")
    except ImportError as e:
        errors.append(f"pytz: {e}")
    
    try:
        import numpy
        print("[OK] numpy")
    except ImportError as e:
        errors.append(f"numpy: {e}")
    
    try:
        import yaml  # pyyaml package
        print("[OK] yaml (pyyaml)")
    except ImportError as e:
        errors.append(f"yaml (pyyaml): {e}")
    
    return errors

def test_env_vars():
    """Test required environment variables"""
    required = ['DISCORD_TOKEN', 'OPENAI_API_KEY']
    optional = ['FIREBASE_SERVICE_ACCOUNT_KEY', 'PORT', 'AUTO_RESPONSE_CHANNELS']
    
    print("\n[TEST] Checking environment variables...")
    
    missing = []
    for var in required:
        if os.getenv(var):
            print(f"[OK] {var} is set")
        else:
            print(f"[MISSING] {var} is not set")
            missing.append(var)
    
    for var in optional:
        if os.getenv(var):
            print(f"[OK] {var} is set (optional)")
        else:
            print(f"[INFO] {var} is not set (optional)")
    
    return missing

def test_file_imports():
    """Test local file imports"""
    errors = []
    
    print("\n[TEST] Checking local module imports...")
    
    modules = [
        'firebase_config',
        'todo_manager',
        'conversation_manager',
        'transcendent_ai_core',
        'superhuman_cognitive_engine',
        'hyperadaptive_learning_engine'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except Exception as e:
            errors.append(f"{module}: {e}")
            print(f"[ERROR] {module}: {e}")
    
    return errors

def main():
    print("=" * 60)
    print("Catherine AI Deployment Test")
    print("=" * 60)
    
    # Test imports
    import_errors = test_imports()
    
    # Test environment variables
    missing_env = test_env_vars()
    
    # Test local imports
    file_errors = test_file_imports()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_errors = len(import_errors) + len(missing_env) + len(file_errors)
    
    if total_errors == 0:
        print("[SUCCESS] All tests passed!")
        print("Catherine AI is ready for deployment.")
        return 0
    else:
        print(f"[FAILED] {total_errors} issues found:")
        
        if import_errors:
            print("\nImport Errors:")
            for err in import_errors:
                print(f"  - {err}")
        
        if missing_env:
            print("\nMissing Environment Variables:")
            for var in missing_env:
                print(f"  - {var}")
        
        if file_errors:
            print("\nLocal Module Errors:")
            for err in file_errors:
                print(f"  - {err}")
        
        print("\nPlease fix these issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())