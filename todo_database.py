#!/usr/bin/env python3
"""
Discord ToDo Database Model
SQLite/Postgres両対応のデータベースモデル
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pytz

# 日本時間
JST = pytz.timezone('Asia/Tokyo')

class TaskStatus(Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"

class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    status: str = TaskStatus.OPEN.value
    priority: str = Priority.NORMAL.value
    due_at: Optional[datetime] = None
    assignees: List[str] = None
    tags: List[str] = None
    created_by: str = ""
    source_msg_id: str = ""
    channel_id: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    dedupe_key: str = ""
    
    def __post_init__(self):
        if self.assignees is None:
            self.assignees = []
        if self.tags is None:
            self.tags = []
        if not self.dedupe_key:
            self.dedupe_key = self.generate_dedupe_key()
        if not self.created_at:
            self.created_at = datetime.now(JST)
        if not self.updated_at:
            self.updated_at = datetime.now(JST)
    
    def generate_dedupe_key(self) -> str:
        """重複検出用キー生成"""
        content = f"{self.title.lower().strip()}:{self.created_by}:{self.channel_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        # datetimeをISO文字列に変換
        if self.due_at:
            data['due_at'] = self.due_at.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class AuditLog:
    id: Optional[int] = None
    task_id: int = 0
    actor: str = ""
    intent: str = ""
    payload: Dict[str, Any] = None
    result: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
        if self.result is None:
            self.result = {}
        if not self.created_at:
            self.created_at = datetime.now(JST)

class TodoDatabase:
    """ToDo データベース管理クラス"""
    
    def __init__(self, db_path: str = "todo.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # tasksテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'normal',
                due_at TIMESTAMP,
                assignees TEXT, -- JSON array
                tags TEXT,      -- JSON array
                created_by TEXT NOT NULL,
                source_msg_id TEXT,
                channel_id TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                dedupe_key TEXT UNIQUE NOT NULL
            )
        ''')
        
        # audit_logsテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                actor TEXT NOT NULL,
                intent TEXT NOT NULL,
                payload TEXT, -- JSON
                result TEXT,  -- JSON
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status_due ON tasks (status, due_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks (tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_dedupe ON tasks (dedupe_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_task_id ON audit_logs (task_id)')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def add_task(self, task: Task) -> Optional[Task]:
        """タスク追加（重複チェック付き）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 重複チェック
            cursor.execute('SELECT id FROM tasks WHERE dedupe_key = ?', (task.dedupe_key,))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                raise ValueError(f"Duplicate task detected: {task.title}")
            
            # タスク挿入
            cursor.execute('''
                INSERT INTO tasks (
                    title, description, status, priority, due_at,
                    assignees, tags, created_by, source_msg_id, channel_id,
                    created_at, updated_at, dedupe_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.title, task.description, task.status, task.priority,
                task.due_at.isoformat() if task.due_at else None,
                json.dumps(task.assignees), json.dumps(task.tags),
                task.created_by, task.source_msg_id, task.channel_id,
                task.created_at.isoformat(), task.updated_at.isoformat(),
                task.dedupe_key
            ))
            
            task.id = cursor.lastrowid
            
            # 監査ログ
            self._add_audit_log(cursor, AuditLog(
                task_id=task.id,
                actor=task.created_by,
                intent="add",
                payload=task.to_dict(),
                result={"success": True, "task_id": task.id}
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Task added: {task.title} (ID: {task.id})")
            return task
            
        except Exception as e:
            print(f"❌ Failed to add task: {e}")
            return None
    
    def get_tasks(self, 
                  status: Optional[str] = None,
                  assignee: Optional[str] = None,
                  tags: Optional[List[str]] = None,
                  channel_id: Optional[str] = None,
                  limit: int = 50) -> List[Task]:
        """タスク一覧取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if assignee:
                query += " AND assignees LIKE ?"
                params.append(f'%"{assignee}"%')
            
            if tags:
                for tag in tags:
                    query += " AND tags LIKE ?"
                    params.append(f'%"{tag}"%')
            
            if channel_id:
                query += " AND channel_id = ?"
                params.append(channel_id)
            
            query += " ORDER BY due_at ASC, priority DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                if task:
                    tasks.append(task)
            
            conn.close()
            return tasks
            
        except Exception as e:
            print(f"❌ Failed to get tasks: {e}")
            return []
    
    def update_task(self, task_id: int, updates: Dict[str, Any], actor: str) -> bool:
        """タスク更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 現在のタスク取得
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False
            
            current_task = self._row_to_task(row)
            
            # 更新クエリ構築
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key in ['title', 'description', 'status', 'priority']:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
                elif key == 'due_at':
                    set_clause.append("due_at = ?")
                    params.append(value.isoformat() if value else None)
                elif key in ['assignees', 'tags']:
                    set_clause.append(f"{key} = ?")
                    params.append(json.dumps(value))
            
            set_clause.append("updated_at = ?")
            params.append(datetime.now(JST).isoformat())
            params.append(task_id)
            
            query = f"UPDATE tasks SET {', '.join(set_clause)} WHERE id = ?"
            cursor.execute(query, params)
            
            # 監査ログ
            self._add_audit_log(cursor, AuditLog(
                task_id=task_id,
                actor=actor,
                intent="update",
                payload=updates,
                result={"success": True, "rows_affected": cursor.rowcount}
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Task updated: ID {task_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update task: {e}")
            return False
    
    def delete_task(self, task_id: int, actor: str) -> bool:
        """タスク削除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # タスク存在確認
            cursor.execute('SELECT title FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False
            
            title = row[0]
            
            # 削除実行
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            
            # 監査ログ
            self._add_audit_log(cursor, AuditLog(
                task_id=task_id,
                actor=actor,
                intent="delete",
                payload={"task_id": task_id, "title": title},
                result={"success": True}
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Task deleted: {title} (ID: {task_id})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete task: {e}")
            return False
    
    def find_tasks(self, query: str, channel_id: Optional[str] = None) -> List[Task]:
        """タスク検索"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sql_query = '''
                SELECT * FROM tasks 
                WHERE (title LIKE ? OR description LIKE ?)
            '''
            params = [f'%{query}%', f'%{query}%']
            
            if channel_id:
                sql_query += ' AND channel_id = ?'
                params.append(channel_id)
            
            sql_query += ' ORDER BY updated_at DESC LIMIT 20'
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                if task:
                    tasks.append(task)
            
            conn.close()
            return tasks
            
        except Exception as e:
            print(f"❌ Failed to find tasks: {e}")
            return []
    
    def get_audit_logs(self, task_id: Optional[int] = None, limit: int = 100) -> List[AuditLog]:
        """監査ログ取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if task_id:
                cursor.execute('''
                    SELECT * FROM audit_logs 
                    WHERE task_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (task_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM audit_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            logs = []
            
            for row in rows:
                log = AuditLog(
                    id=row[0],
                    task_id=row[1],
                    actor=row[2],
                    intent=row[3],
                    payload=json.loads(row[4]) if row[4] else {},
                    result=json.loads(row[5]) if row[5] else {},
                    created_at=datetime.fromisoformat(row[6])
                )
                logs.append(log)
            
            conn.close()
            return logs
            
        except Exception as e:
            print(f"❌ Failed to get audit logs: {e}")
            return []
    
    def _add_audit_log(self, cursor, log: AuditLog):
        """監査ログ追加（内部使用）"""
        cursor.execute('''
            INSERT INTO audit_logs (task_id, actor, intent, payload, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            log.task_id, log.actor, log.intent,
            json.dumps(log.payload), json.dumps(log.result),
            log.created_at.isoformat()
        ))
    
    def _row_to_task(self, row) -> Optional[Task]:
        """データベース行をTaskオブジェクトに変換"""
        try:
            return Task(
                id=row[0],
                title=row[1],
                description=row[2],
                status=row[3],
                priority=row[4],
                due_at=datetime.fromisoformat(row[5]) if row[5] else None,
                assignees=json.loads(row[6]) if row[6] else [],
                tags=json.loads(row[7]) if row[7] else [],
                created_by=row[8],
                source_msg_id=row[9],
                channel_id=row[10],
                created_at=datetime.fromisoformat(row[11]),
                updated_at=datetime.fromisoformat(row[12]),
                dedupe_key=row[13]
            )
        except Exception as e:
            print(f"❌ Failed to convert row to task: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # タスク統計
            cursor.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
            status_counts = dict(cursor.fetchall())
            
            cursor.execute('SELECT priority, COUNT(*) FROM tasks WHERE status = "open" GROUP BY priority')
            priority_counts = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE due_at < ? AND status = "open"', 
                         (datetime.now(JST).isoformat(),))
            overdue_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "overdue_count": overdue_count,
                "total_tasks": sum(status_counts.values())
            }
            
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}

if __name__ == "__main__":
    # テスト実行
    db = TodoDatabase("test_todo.db")
    
    # サンプルタスク作成
    task = Task(
        title="ロンT制作",
        description="CCT用のロンTを制作する",
        priority=Priority.HIGH.value,
        due_at=datetime(2025, 8, 13, 18, 0, tzinfo=JST),
        assignees=["kohei"],
        tags=["CCT", "制作"],
        created_by="user123",
        source_msg_id="msg456",
        channel_id="ch789"
    )
    
    # テスト実行
    added_task = db.add_task(task)
    if added_task:
        print(f"Added task: {added_task.to_dict()}")
        
        # 統計表示
        stats = db.get_stats()
        print(f"Stats: {stats}")