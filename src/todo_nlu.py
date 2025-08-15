"""
自然言語でのTODO操作を理解するNLUシステム
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import pytz

class TodoNLU:
    """TODO操作の自然言語理解"""
    
    # アクションキーワード
    ACTION_KEYWORDS = {
        'create': ['追加', '作成', '作って', '登録', 'todo', 'タスク', 'やること', '予定'],
        'list': ['リスト', '一覧', '見せて', '表示', '確認', '何がある', 'todo'],
        'complete': ['完了', '終了', '終わった', 'done', '済み', 'おわり'],
        'delete': ['削除', '消して', '取り消し', 'キャンセル', '中止'],
        'update': ['変更', '修正', '編集', '更新', '名前', 'リネーム'],
        'remind': ['リマインド', 'リマインダー', '通知', '教えて', '忘れないで']
    }
    
    # 優先度キーワード
    PRIORITY_KEYWORDS = {
        'urgent': ['緊急', '至急', 'すぐ', '今すぐ', 'ASAP'],
        'high': ['重要', '大事', '高', '優先'],
        'normal': ['普通', '通常', 'ノーマル'],
        'low': ['低', 'あとで', '後回し', 'いつでも']
    }
    
    # 時間表現パターン
    TIME_PATTERNS = {
        '今日': lambda: datetime.now(pytz.UTC).replace(hour=23, minute=59),
        '明日': lambda: (datetime.now(pytz.UTC) + timedelta(days=1)).replace(hour=23, minute=59),
        '明後日': lambda: (datetime.now(pytz.UTC) + timedelta(days=2)).replace(hour=23, minute=59),
        '来週': lambda: (datetime.now(pytz.UTC) + timedelta(weeks=1)).replace(hour=23, minute=59),
        '今週末': lambda: TodoNLU._get_weekend(),
        '月曜': lambda: TodoNLU._get_next_weekday(0),
        '火曜': lambda: TodoNLU._get_next_weekday(1),
        '水曜': lambda: TodoNLU._get_next_weekday(2),
        '木曜': lambda: TodoNLU._get_next_weekday(3),
        '金曜': lambda: TodoNLU._get_next_weekday(4),
        '土曜': lambda: TodoNLU._get_next_weekday(5),
        '日曜': lambda: TodoNLU._get_next_weekday(6),
    }
    
    @staticmethod
    def _get_weekend():
        """次の週末を取得"""
        now = datetime.now(pytz.UTC)
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        return (now + timedelta(days=days_until_saturday)).replace(hour=23, minute=59)
    
    @staticmethod
    def _get_next_weekday(target_day: int):
        """次の特定曜日を取得"""
        now = datetime.now(pytz.UTC)
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return (now + timedelta(days=days_ahead)).replace(hour=23, minute=59)
    
    def parse_message(self, message: str) -> Dict[str, Any]:
        """メッセージを解析してTODO操作を理解"""
        message_lower = message.lower()
        
        # アクションを判定
        action = self._detect_action(message_lower)
        
        # アクションごとの解析
        if action == 'create':
            return self._parse_create(message)
        elif action == 'list':
            return self._parse_list(message_lower)
        elif action == 'complete':
            return self._parse_complete(message)
        elif action == 'delete':
            return self._parse_delete(message)
        elif action == 'update':
            return self._parse_update(message)
        else:
            return {'action': None, 'confidence': 0}
    
    def _detect_action(self, message: str) -> Optional[str]:
        """メッセージからアクションを検出"""
        max_score = 0
        detected_action = None
        
        for action, keywords in self.ACTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > max_score:
                max_score = score
                detected_action = action
        
        return detected_action if max_score > 0 else None
    
    def _parse_create(self, message: str) -> Dict[str, Any]:
        """TODO作成コマンドを解析"""
        # タイトルを抽出（「」や『』で囲まれている部分を優先）
        title_match = re.search(r'[「『"](.*?)[」』"]', message)
        if title_match:
            title = title_match.group(1)
        else:
            # キーワード後の文字列をタイトルとする
            for keyword in self.ACTION_KEYWORDS['create']:
                if keyword in message.lower():
                    parts = message.lower().split(keyword)
                    if len(parts) > 1:
                        title = parts[1].strip()
                        # 期限などの表現を除去
                        for time_key in self.TIME_PATTERNS.keys():
                            title = title.replace(time_key, '').strip()
                        break
            else:
                title = message
        
        # 優先度を検出
        priority = self._detect_priority(message.lower())
        
        # 期限を検出
        due_date = self._detect_due_date(message.lower())
        
        return {
            'action': 'create',
            'title': title,
            'priority': priority,
            'due_date': due_date,
            'confidence': 0.8
        }
    
    def _parse_list(self, message: str) -> Dict[str, Any]:
        """TODOリスト表示コマンドを解析"""
        # フィルター条件を検出
        include_completed = '完了' in message or '全て' in message or 'すべて' in message
        
        return {
            'action': 'list',
            'include_completed': include_completed,
            'confidence': 0.9
        }
    
    def _parse_complete(self, message: str) -> Dict[str, Any]:
        """TODO完了コマンドを解析"""
        # 番号を検出
        number_match = re.search(r'(\d+)', message)
        todo_number = int(number_match.group(1)) if number_match else None
        
        # タイトルの一部を検出
        title_keywords = None
        for keyword in self.ACTION_KEYWORDS['complete']:
            parts = message.split(keyword)
            if len(parts) > 1:
                title_keywords = parts[0].strip()
                break
        
        return {
            'action': 'complete',
            'todo_number': todo_number,
            'title_keywords': title_keywords,
            'confidence': 0.7
        }
    
    def _parse_delete(self, message: str) -> Dict[str, Any]:
        """TODO削除コマンドを解析"""
        # 複数番号を検出（例: 1,2,3 や 1.2.3 や 1 2 3）
        numbers = re.findall(r'(\d+)', message)
        todo_numbers = [int(num) for num in numbers] if numbers else []
        
        # 単一番号の場合は後方互換性のために維持
        todo_number = todo_numbers[0] if len(todo_numbers) == 1 else None
        
        return {
            'action': 'delete',
            'todo_number': todo_number,
            'todo_numbers': todo_numbers,  # 複数削除対応
            'confidence': 0.7
        }
    
    def _parse_update(self, message: str) -> Dict[str, Any]:
        """TODO更新コマンドを解析"""
        # 番号を検出
        number_match = re.search(r'(\d+)', message)
        todo_number = int(number_match.group(1)) if number_match else None
        
        # 新しい内容を検出
        new_content = None
        
        # 「1は名前を○○にして」パターン
        name_change_match = re.search(r'(\d+)(?:は|を)(?:名前を|)(.+?)(?:にして|に変更)', message)
        if name_change_match:
            todo_number = int(name_change_match.group(1))
            new_content = name_change_match.group(2).strip()
        else:
            # 従来の変更パターン
            for keyword in self.ACTION_KEYWORDS['update']:
                if keyword in message.lower():
                    parts = message.split(keyword)
                    if len(parts) > 1:
                        new_content = parts[1].strip()
                        break
        
        return {
            'action': 'update',
            'todo_number': todo_number,
            'new_content': new_content,
            'confidence': 0.6
        }
    
    def _detect_priority(self, message: str) -> str:
        """メッセージから優先度を検出"""
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    return priority
        return 'normal'
    
    def _detect_due_date(self, message: str) -> Optional[datetime]:
        """メッセージから期限を検出"""
        for pattern, date_func in self.TIME_PATTERNS.items():
            if pattern in message:
                return date_func()
        
        # 日付パターン（例: 12/25, 12月25日）
        date_match = re.search(r'(\d{1,2})[/月](\d{1,2})', message)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year = datetime.now().year
            try:
                due_date = datetime(year, month, day, 23, 59, tzinfo=pytz.UTC)
                # 過去の日付の場合は来年にする
                if due_date < datetime.now(pytz.UTC):
                    due_date = due_date.replace(year=year + 1)
                return due_date
            except ValueError:
                pass
        
        # 「X日後」パターン
        days_match = re.search(r'(\d+)日後', message)
        if days_match:
            days = int(days_match.group(1))
            return (datetime.now(pytz.UTC) + timedelta(days=days)).replace(hour=23, minute=59)
        
        # 「X時間後」パターン
        hours_match = re.search(r'(\d+)時間後', message)
        if hours_match:
            hours = int(hours_match.group(1))
            return datetime.now(pytz.UTC) + timedelta(hours=hours)
        
        return None

# グローバルインスタンス
todo_nlu = TodoNLU()