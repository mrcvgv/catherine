#!/usr/bin/env python3
"""
Catherine との Google Tasks 統合テスト
実際にタスクの作成と取得を行う
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def get_tasks_service():
    """Google Tasks service を取得"""
    service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not service_account_key:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not found")
    
    credentials_info = json.loads(service_account_key)
    
    credentials = Credentials.from_service_account_info(
        credentials_info, 
        scopes=['https://www.googleapis.com/auth/tasks']
    )
    
    return build('tasks', 'v1', credentials=credentials)

def create_catherine_task(service, title, notes="", due_date=None):
    """Catherineタスクを作成"""
    print(f"Creating task: {title}")
    
    # デフォルトのタスクリストを取得
    tasklists = service.tasklists().list().execute()
    default_list_id = tasklists['items'][0]['id']
    
    # タスクデータを準備
    task = {
        'title': title,
        'notes': f"Created by Catherine Bot\n\n{notes}",
    }
    
    if due_date:
        task['due'] = due_date.isoformat() + 'Z'
    
    # タスクを作成
    result = service.tasks().insert(
        tasklist=default_list_id,
        body=task
    ).execute()
    
    print(f"  Task created with ID: {result['id']}")
    print(f"  Due date: {due_date.strftime('%Y-%m-%d %H:%M') if due_date else 'Not set'}")
    
    return result

def list_catherine_tasks(service):
    """Catherine タスク一覧を取得"""
    print("\nListing current tasks:")
    
    # タスクリスト一覧を取得
    tasklists = service.tasklists().list().execute()
    default_list_id = tasklists['items'][0]['id']
    
    # タスク一覧を取得
    tasks = service.tasks().list(tasklist=default_list_id).execute()
    
    items = tasks.get('items', [])
    if not items:
        print("  No tasks found")
        return []
    
    print(f"  Found {len(items)} tasks:")
    for i, task in enumerate(items, 1):
        status = "✓" if task.get('status') == 'completed' else "○"
        due = ""
        if task.get('due'):
            try:
                due_date = datetime.fromisoformat(task['due'].replace('Z', '+00:00'))
                due = f" (Due: {due_date.strftime('%m/%d %H:%M')})"
            except:
                due = f" (Due: {task.get('due')})"
        
        print(f"  {status} {i}. {task['title']}{due}")
        if task.get('notes') and 'Catherine' in task.get('notes', ''):
            print(f"      Catherine Bot task")
    
    return items

def demo_catherine_integration():
    """Catherine統合のデモンストレーション"""
    print("Catherine Google Tasks Integration Demo")
    print("=" * 50)
    
    try:
        service = get_tasks_service()
        
        # 現在のタスクを表示
        current_tasks = list_catherine_tasks(service)
        
        print(f"\nCreating test tasks for Catherine...")
        
        # テストタスク1: 緊急度高
        task1 = create_catherine_task(
            service,
            "Catherine Bot Test: Review MCP Integration",
            "Check all MCP servers are working properly:\n- Notion integration\n- Google services\n- Mention system\n\nPriority: High",
            datetime.now() + timedelta(hours=2)
        )
        
        # テストタスク2: 明日期限
        task2 = create_catherine_task(
            service,
            "Catherine Bot Test: Update Discord Commands",
            "Add new Discord slash commands:\n- /todo create\n- /todo list\n- /reminder set\n\nPriority: Normal",
            datetime.now() + timedelta(days=1)
        )
        
        # テストタスク3: 来週期限
        task3 = create_catherine_task(
            service,
            "Catherine Bot Test: Gmail Integration",
            "Implement Gmail API integration:\n- Email monitoring\n- Automatic task creation from emails\n- Requires OAuth setup\n\nPriority: Low",
            datetime.now() + timedelta(days=7)
        )
        
        print(f"\nUpdated task list:")
        updated_tasks = list_catherine_tasks(service)
        
        print(f"\nCatherine Tasks Integration Summary:")
        print(f"  - Service Account authentication: Working")
        print(f"  - Task creation: Working") 
        print(f"  - Task listing: Working")
        print(f"  - Due date setting: Working")
        print(f"  - Notes and descriptions: Working")
        
        print(f"\nNext steps:")
        print(f"  1. Integrate this into Catherine's TODO system")
        print(f"  2. Add natural language parsing for task creation")
        print(f"  3. Sync with Notion database")
        print(f"  4. Add Discord commands for task management")
        
        print(f"\nGoogle Tasks URL:")
        print(f"  https://tasks.google.com/")
        
        return True
        
    except Exception as e:
        print(f"Error in demo: {e}")
        return False

if __name__ == "__main__":
    success = demo_catherine_integration()
    if success:
        print(f"\nDemo completed successfully!")
    else:
        print(f"\nDemo failed. Check configuration.")