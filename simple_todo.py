#!/usr/bin/env python3
"""
Simple Todo System - Catherine AI シンプルTODOシステム
複雑なことはしない、シンプルなTODO管理
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class SimpleTodo:
    def __init__(self):
        self.todo_file = "simple_todos.json"
        self.todos = self.load_todos()
    
    def load_todos(self) -> List[Dict]:
        """TODOを読み込み"""
        try:
            if os.path.exists(self.todo_file):
                with open(self.todo_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def save_todos(self):
        """TODOを保存"""
        try:
            with open(self.todo_file, 'w', encoding='utf-8') as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_todo(self, title: str, user_id: str = 'default') -> str:
        """TODO追加"""
        try:
            todo_id = len(self.todos) + 1
            todo = {
                'id': todo_id,
                'title': title,
                'completed': False,
                'user_id': user_id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.todos.append(todo)
            self.save_todos()
            return f"✅ TODO追加: {title}"
        except Exception as e:
            return f"❌ TODO追加失敗: {str(e)}"
    
    def list_todos(self, user_id: str = 'default') -> str:
        """TODO一覧"""
        try:
            user_todos = [t for t in self.todos if t.get('user_id', 'default') == user_id and not t['completed']]
            
            if not user_todos:
                return "📝 TODOはありません"
            
            result = "📋 **TODOリスト**\n\n"
            for todo in user_todos:
                result += f"{todo['id']}. {todo['title']}\n"
            
            return result
        except Exception as e:
            return f"❌ TODO一覧取得失敗: {str(e)}"
    
    def complete_todo(self, todo_id: int, user_id: str = 'default') -> str:
        """TODO完了"""
        try:
            for todo in self.todos:
                if todo['id'] == todo_id and todo.get('user_id', 'default') == user_id:
                    todo['completed'] = True
                    todo['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.save_todos()
                    return f"✅ TODO完了: {todo['title']}"
            
            return "❌ TODOが見つかりません"
        except Exception as e:
            return f"❌ TODO完了失敗: {str(e)}"
    
    def delete_todo(self, todo_id: int, user_id: str = 'default') -> str:
        """TODO削除"""
        try:
            for i, todo in enumerate(self.todos):
                if todo['id'] == todo_id and todo.get('user_id', 'default') == user_id:
                    deleted_title = todo['title']
                    del self.todos[i]
                    self.save_todos()
                    return f"🗑️ TODO削除: {deleted_title}"
            
            return "❌ TODOが見つかりません"
        except Exception as e:
            return f"❌ TODO削除失敗: {str(e)}"
    
    def get_todo_count(self, user_id: str = 'default') -> int:
        """TODO数取得"""
        return len([t for t in self.todos if t.get('user_id', 'default') == user_id and not t['completed']])