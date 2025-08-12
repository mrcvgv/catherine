#!/usr/bin/env python3
"""
File Cleanup Tool - Catherine AI重複・無駄ファイル整理
必要なファイルのみを残して、プロジェクトをクリーンアップ
"""

import os
import shutil
from typing import List, Dict, Set
from pathlib import Path

class FileCleanupTool:
    """ファイル整理ツール"""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        
        # 必要なコアファイル（残すファイル）
        self.core_files = {
            # メインシステム
            'enhanced_main_v2.py',           # メインボットファイル
            'firebase_config.py',            # Firebase設定
            'requirements.txt',              # 依存関係
            
            # Firebase統合システム
            'firestore_schema.py',           # Firestoreスキーマ
            'firebase_todo_enhanced.py',     # Firebase TODO システム
            'cloud_functions.py',            # Cloud Functions
            'cloud_reminder_system.py',      # Cloud リマインドシステム
            
            # AI・NLU システム
            'smart_intent_classifier.py',    # 決定版意図分類
            'hybrid_intent_detector.py',     # ハイブリッド検出器
            'memory_learning_system.py',     # 学習システム
            
            # デプロイ設定
            'railway_deployment.py',         # Railway デプロイ管理
            'Procfile',                     # Railway Procfile
            'railway.toml',                 # Railway 設定
            'Dockerfile',                   # Docker設定
            '.env.example',                 # 環境変数テンプレート
            
            # Firebase設定ファイル（存在する場合）
            'catherine-9e862-firebase-adminsdk-fbsvc-28368629ce.json'
        }
        
        # 重複・旧バージョンファイル（削除対象）
        self.duplicate_files = {
            'main.py',                      # enhanced_main_v2.py に統合
            'main_basic.py',
            'main_simple.py', 
            'main_memory_focused.py',
            'main_with_voice.py',
            'enhanced_main.py',             # v2 に統合
            
            # 旧システムファイル
            'reminder_system.py',           # cloud_reminder_system.py に移行
            'todo_manager.py',              # firebase_todo_enhanced.py に移行
            'todo_database.py',             # Firestore に移行
            'todo_nlu.py',                  # smart_intent_classifier.py に統合
            'todo_nlu_enhanced.py',
            
            # テスト・デモファイル
            'test_firebase.py',
            'test_firebase_todo.py',
            'memory_demo.py',
            'demo_usage.py',
            'deployment_test.py',
            'startup_check.py',
            'quick_firebase_setup.py',
            
            # 統合済み・重複ファイル
            'final_demo_kouhei.py',
            'kouhei_final_integration.py',
            'todo_integration_patch.py',
            'discord_reminder_system.py',   # cloud_reminder_system.py に統合
            
            # 不要な超高度システム（オーバーエンジニアリング）
            'transcendent_ai_core.py',
            'superhuman_cognitive_engine.py',
            'hyperadaptive_learning_engine.py',
            'metacognitive_system.py',
            'ultimate_intelligence_hub.py',
            'supreme_intelligence_engine.py',
            'phd_level_intelligence.py',
            'enhanced_human_communication.py',
            'evolved_human_ai.py',
            'emotional_intelligence.py',
            'master_communicator.py',
            
            # 重複音声システム
            'voice_channel_system.py',
            'voice_manager.py',
            'voice_channel_alternative.py',
            'voice_optimized_system.py',
            
            # 重複チャットシステム
            'natural_conversation_system.py',
            'mega_human_chat.py',
            'mega_universal_chat.py',
            'ultra_human_communication.py',
            'super_natural_chat.py',
            'simple_human_chat.py',
            'human_level_chat.py',
            'fast_greeting_system.py',
            'instant_response_system.py',
            
            # 重複学習システム
            'adaptive_learning_system.py',
            'dynamic_learning_system.py',
            'advanced_reasoning_engine.py',
            'intelligent_automation_system.py',
            'massive_pattern_brain.py',
            'instant_intent_engine.py',
            
            # 重複管理システム
            'advanced_context_system.py',
            'advanced_context_engine.py',
            'conversation_manager.py',
            'reaction_learning_system.py',
            'team_todo_manager.py',
            'advanced_task_manager.py',
            'advanced_todo_system.py',
            'simple_todo.py',
            
            # その他重複
            'natural_language_engine.py',
            'fast_nlp_engine.py',
            'confidence_guard_system.py',
            'action_summary_system.py',
            'progress_nudge_engine.py',
            'morning_briefing_system.py',
            'attachment_ocr_system.py',
            'proactive_assistant.py',
            'prompt_system.py'
        }
        
        # ディレクトリ構造（必要に応じて）
        self.keep_dirs = {
            '__pycache__',
            '.git',
            'functions'  # Cloud Functions用（将来的に）
        }
    
    def analyze_project(self) -> Dict[str, any]:
        """プロジェクト分析"""
        analysis = {
            'total_files': 0,
            'python_files': 0,
            'core_files_found': [],
            'duplicate_files_found': [],
            'other_files': [],
            'missing_core_files': [],
            'cleanup_recommendations': []
        }
        
        all_files = []
        for file_path in self.project_dir.rglob('*'):
            if file_path.is_file():
                all_files.append(file_path.name)
        
        analysis['total_files'] = len(all_files)
        analysis['python_files'] = len([f for f in all_files if f.endswith('.py')])
        
        # コアファイルチェック
        for core_file in self.core_files:
            if core_file in all_files:
                analysis['core_files_found'].append(core_file)
            else:
                analysis['missing_core_files'].append(core_file)
        
        # 重複ファイルチェック
        for dup_file in self.duplicate_files:
            if dup_file in all_files:
                analysis['duplicate_files_found'].append(dup_file)
        
        # その他ファイル
        for file in all_files:
            if file not in self.core_files and file not in self.duplicate_files:
                if file.endswith('.py') or file in ['.gitignore', 'README.md']:
                    analysis['other_files'].append(file)
        
        # 推奨事項
        if analysis['duplicate_files_found']:
            analysis['cleanup_recommendations'].append(
                f"Remove {len(analysis['duplicate_files_found'])} duplicate files"
            )
        
        if analysis['missing_core_files']:
            analysis['cleanup_recommendations'].append(
                f"Check {len(analysis['missing_core_files'])} missing core files"
            )
        
        return analysis
    
    def create_backup(self, backup_name: str = "backup_before_cleanup"):
        """バックアップ作成"""
        backup_path = self.project_dir.parent / backup_name
        if backup_path.exists():
            shutil.rmtree(backup_path)
        
        shutil.copytree(self.project_dir, backup_path)
        print(f"Backup created: {backup_path}")
        return backup_path
    
    def cleanup_duplicates(self, create_backup: bool = True, dry_run: bool = True) -> Dict[str, any]:
        """重複ファイルクリーンアップ"""
        
        if create_backup and not dry_run:
            self.create_backup()
        
        result = {
            'removed_files': [],
            'errors': [],
            'dry_run': dry_run
        }
        
        for dup_file in self.duplicate_files:
            file_path = self.project_dir / dup_file
            if file_path.exists():
                try:
                    if dry_run:
                        print(f"[DRY RUN] Would remove: {dup_file}")
                        result['removed_files'].append(dup_file)
                    else:
                        file_path.unlink()
                        print(f"Removed: {dup_file}")
                        result['removed_files'].append(dup_file)
                except Exception as e:
                    error_msg = f"Failed to remove {dup_file}: {e}"
                    print(f"Error: {error_msg}")
                    result['errors'].append(error_msg)
        
        return result
    
    def generate_clean_requirements(self) -> str:
        """クリーンアップ済み requirements.txt 生成"""
        clean_requirements = """# Catherine AI - Core Dependencies
discord.py[voice]>=2.3.2
openai>=1.0.0
firebase-admin>=6.5.0
python-dateutil>=2.8.2
pytz>=2023.3

# Cloud Functions & Tasks
aiohttp>=3.8.0
google-cloud-tasks>=2.15.0
google-cloud-firestore>=2.13.0
requests>=2.31.0

# Deployment
gunicorn>=21.2.0

# Optional: Audio processing (if needed)
# PyNaCl>=1.5.0
# SpeechRecognition>=3.10.0
# pydub>=0.25.1
# ffmpeg-python>=0.2.0

# Development
# numpy>=1.24.0
# pyyaml>=6.0
# typing-extensions>=4.0.0
"""
        return clean_requirements
    
    def create_project_structure_doc(self) -> str:
        """プロジェクト構造ドキュメント生成"""
        doc = """# Catherine AI - Clean Project Structure

## Core Files

### Main Application
- `enhanced_main_v2.py` - Main Discord bot application
- `requirements.txt` - Python dependencies

### Firebase Integration  
- `firebase_config.py` - Firebase connection manager
- `firestore_schema.py` - Database schema definitions
- `firebase_todo_enhanced.py` - Firebase TODO system
- `cloud_functions.py` - Cloud Functions (TypeScript guide)
- `cloud_reminder_system.py` - Cloud reminder system

### AI & NLU
- `smart_intent_classifier.py` - Final LLM prompt intent classifier
- `hybrid_intent_detector.py` - Hybrid rule+LLM detector  
- `memory_learning_system.py` - Learning from interactions

### Deployment
- `railway_deployment.py` - Railway deployment manager
- `Procfile` - Railway process definition
- `railway.toml` - Railway configuration
- `Dockerfile` - Docker container setup
- `.env.example` - Environment variables template

## Architecture

```
User Input → Hybrid Intent Detector → Firebase Operations → Cloud Functions
     ↓              ↓                        ↓                  ↓
Smart Classifier → Pending Actions → Cloud Tasks → Discord Response
     ↓              ↓                        ↓                  ↓
Memory Learning → User Preferences → Scheduled Reminders → Confirmation
```

## Removed Files

The following redundant/outdated files were removed during cleanup:
- Multiple main.py variants (consolidated to enhanced_main_v2.py)
- Duplicate reminder systems (consolidated to cloud_reminder_system.py)
- Over-engineered AI systems (simplified to core functionality)
- Test and demo files (moved to production-ready code)

## Next Steps

1. Set environment variables using `.env.example` as template
2. Deploy to Railway using `railway_deployment.py`
3. Configure Cloud Functions using `cloud_functions.py`
4. Monitor and adjust using learning system
"""
        return doc

# CLI実行部分
def main():
    project_dir = "."
    cleanup_tool = FileCleanupTool(project_dir)
    
    print("Catherine AI File Cleanup Tool")
    print("=" * 50)
    
    # プロジェクト分析
    analysis = cleanup_tool.analyze_project()
    print(f"Total files: {analysis['total_files']}")
    print(f"Python files: {analysis['python_files']}")
    print(f"Core files found: {len(analysis['core_files_found'])}")
    print(f"Duplicate files found: {len(analysis['duplicate_files_found'])}")
    print(f"Other files: {len(analysis['other_files'])}")
    
    if analysis['duplicate_files_found']:
        print(f"\nDuplicate files to remove: {analysis['duplicate_files_found'][:5]}...")
    
    if analysis['missing_core_files']:
        print(f"\nMissing core files: {analysis['missing_core_files']}")
    
    print("\nRecommendations:")
    for rec in analysis['cleanup_recommendations']:
        print(f"  - {rec}")
    
    # クリーンアップ実行（ドライラン）
    print("\nRunning cleanup (dry run)...")
    result = cleanup_tool.cleanup_duplicates(dry_run=True)
    print(f"Would remove {len(result['removed_files'])} files")
    
    # ドキュメント生成
    clean_reqs = cleanup_tool.generate_clean_requirements()
    with open('requirements_clean.txt', 'w', encoding='utf-8') as f:
        f.write(clean_reqs)
    print("Generated: requirements_clean.txt")
    
    project_doc = cleanup_tool.create_project_structure_doc()
    with open('PROJECT_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write(project_doc)
    print("Generated: PROJECT_STRUCTURE.md")
    
    print("\nCleanup analysis complete!")
    print("Run with --execute flag to perform actual cleanup")

if __name__ == "__main__":
    main()