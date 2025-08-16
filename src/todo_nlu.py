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
        'list': ['リスト', '一覧', '見せて', '表示', '確認', '何がある', 'todo', 'だして', 'くれ', '出して'],
        'complete': ['完了', '終了', '終わった', 'done', '済み', 'おわり'],
        'delete': ['削除', '消して', '取り消し', 'キャンセル', '中止'],
        'update': ['変更', '修正', '編集', '更新', '名前', 'リネーム'],
        'priority': ['優先度', '激高', '重要度'],
        'remind': ['リマインド', 'リマインダー', '通知', '教えて', '忘れないで']
    }
    
    # 優先度キーワード（激高、高、普通、低）
    PRIORITY_KEYWORDS = {
        'urgent': ['激高', '最高優先度', '最優先', '超緊急', '超重要', '緊急', '至急', 
                  'すぐ', '今すぐ', 'ASAP', 'クリティカル', '最重要', '即座', '即時'],
        'high': ['高優先度', '高い', '高め', '重要', '大事', '優先', '急ぎ', 
                '早め', '重視', '大切'],
        'normal': ['普通', '通常', 'ノーマル', '中', '中程度', '標準', 
                  'デフォルト', 'ふつう', '並'],
        'low': ['低優先度', '低い', '低め', 'あとで', '後回し', 'いつでも', 
               '余裕', 'ゆっくり', '時間がある時', '暇な時', '後で']
    }
    
    # 時間表現パターン（東京時間ベース）
    TIME_PATTERNS = {
        '今日': lambda: datetime.now(pytz.timezone('Asia/Tokyo')).replace(hour=23, minute=59).astimezone(pytz.UTC),
        '明日': lambda: (datetime.now(pytz.timezone('Asia/Tokyo')) + timedelta(days=1)).replace(hour=23, minute=59).astimezone(pytz.UTC),
        '明後日': lambda: (datetime.now(pytz.timezone('Asia/Tokyo')) + timedelta(days=2)).replace(hour=23, minute=59).astimezone(pytz.UTC),
        '来週': lambda: (datetime.now(pytz.timezone('Asia/Tokyo')) + timedelta(weeks=1)).replace(hour=23, minute=59).astimezone(pytz.UTC),
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
        """次の週末を取得（東京時間ベース）"""
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        weekend = (now + timedelta(days=days_until_saturday)).replace(hour=23, minute=59)
        return weekend.astimezone(pytz.UTC)
    
    @staticmethod
    def _get_next_weekday(target_day: int):
        """次の特定曜日を取得（東京時間ベース）"""
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_day = (now + timedelta(days=days_ahead)).replace(hour=23, minute=59)
        return next_day.astimezone(pytz.UTC)
    
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
        elif action == 'priority':
            return self._parse_priority(message)
        elif action == 'remind':
            return self._parse_remind(message)
        else:
            return {'action': None, 'confidence': 0}
    
    def _detect_action(self, message: str) -> Optional[str]:
        """メッセージからアクションを検出"""
        # リマインダー関連の最優先チェック（時間指定があるパターン）
        if any(word in message for word in ['リマインド', 'リマインダー', '通知', '忘れないで']):
            # 番号が含まれているか、全リストの場合、または時間指定がある場合
            has_number = re.search(r'(\d+)', message)
            has_list = any(word in message for word in ['全リスト', 'リスト', '一覧'])
            has_time = any(word in message for word in ['毎日', '毎朝', '毎晩', '時', '：', ':']) or re.search(r'\d+[：:]\d+', message)
            
            if has_number or has_list or has_time:
                return 'remind'
        
        # 優先度変更の優先チェック（「5は優先度激高に」パターン）
        if re.search(r'(\d+).*(?:優先度|激高|高|普通|低)', message):
            if any(word in message for word in ['優先度', '激高', '高め', '低め', '変えて', 'にして', 'に変更']):
                return 'priority'
        
        # リスト表示のチェック（リマインダーでない場合）
        if any(word in message for word in ['全リスト', 'リスト', '一覧', 'だして', 'くれ', '出して']):
            if not any(word in message for word in ['追加', '作成', '作って', '登録', 'リマインド', '通知']):
                return 'list'
        
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
            title = message  # デフォルト値
            for keyword in self.ACTION_KEYWORDS['create']:
                if keyword in message.lower():
                    # 元のメッセージを使って分割（大文字小文字保持）
                    keyword_pos = message.lower().find(keyword)
                    if keyword_pos != -1:
                        if keyword_pos == 0:
                            # キーワードが先頭にある場合、後ろの部分を取得
                            title = message[len(keyword):].strip()
                        else:
                            # キーワードが後ろにある場合、前の部分を取得
                            title = message[:keyword_pos].strip()
                        
                        # 期限などの表現を除去
                        for time_key in self.TIME_PATTERNS.keys():
                            title = title.replace(time_key, '').strip()
                        break
            
            # タイトルが空の場合はメッセージ全体を使用
            if not title:
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
        """メッセージから優先度を検出（長いキーワードを優先）"""
        # 「激高」が「高」より優先されるよう、長いキーワードから順にチェック
        message_lower = message.lower()
        
        # urgent（激高）を最初にチェック - 最も具体的なキーワードから
        urgent_keywords = ['激高', '最高優先度', '最優先', '超緊急', '超重要', 'クリティカル', 
                          '最重要', '即座', '即時', '緊急', '至急', 'すぐ', '今すぐ', 'asap']
        if any(keyword in message_lower for keyword in urgent_keywords):
            return 'urgent'
        
        # low（低）をチェック - 「高」の誤認識を防ぐため先にチェック
        low_keywords = ['低優先度', '低い', '低め', 'あとで', '後回し', 'いつでも', 
                       '余裕', 'ゆっくり', '時間がある時', '暇な時', '後で']
        if any(keyword in message_lower for keyword in low_keywords):
            return 'low'
        
        # high（高）をチェック（「激高」「低」が含まれていないことを確認）
        if '激高' not in message_lower and '低' not in message_lower:
            high_keywords = ['高優先度', '高い', '高め', '高', '重要', '大事', '優先', 
                           '急ぎ', '早め', '重視', '大切']
            if any(keyword in message_lower for keyword in high_keywords):
                return 'high'
        
        # normal（普通）をチェック
        normal_keywords = ['普通', '通常', 'ノーマル', '中程度', '標準', 
                         'デフォルト', 'ふつう', '並', '中']
        if any(keyword in message_lower for keyword in normal_keywords):
            return 'normal'
        
        return 'normal'  # デフォルト
    
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
                if due_date < datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC):
                    due_date = due_date.replace(year=year + 1)
                return due_date
            except ValueError:
                pass
        
        # 「X分後」パターン
        minutes_match = re.search(r'(\d+)分後', message)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            return datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC) + timedelta(minutes=minutes)
        
        # 「X日後」パターン
        days_match = re.search(r'(\d+)日後', message)
        if days_match:
            days = int(days_match.group(1))
            jst_time = (datetime.now(pytz.timezone('Asia/Tokyo')) + timedelta(days=days)).replace(hour=23, minute=59)
            return jst_time.astimezone(pytz.UTC)
        
        # 「X時間後」パターン
        hours_match = re.search(r'(\d+)時間後', message)
        if hours_match:
            hours = int(hours_match.group(1))
            return datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC) + timedelta(hours=hours)
        
        # 毎日の時間指定パターン（例: 毎朝8:30、毎日8:30、毎日毎朝8:30、8:30、8 30）
        daily_time_match = re.search(r'(?:毎日|毎朝|毎晩).*?(\d{1,2})[：:時\s](\d{1,2})', message)
        if daily_time_match:
            hour = int(daily_time_match.group(1))
            minute = int(daily_time_match.group(2))
            # 東京時間で次回の指定時刻を計算
            now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
            target_time_today = now_jst.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 今日の時刻が過ぎていれば明日に設定
            if target_time_today <= now_jst:
                target_time = target_time_today + timedelta(days=1)
            else:
                target_time = target_time_today
            
            return target_time.astimezone(pytz.UTC)
        
        # 日付パターン（例: 12/25, 12月25日）- 東京時間ベース
        date_match = re.search(r'(\d{1,2})[/月](\d{1,2})', message)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            now_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
            year = now_jst.year
            try:
                due_date = datetime(year, month, day, 23, 59, tzinfo=pytz.timezone('Asia/Tokyo'))
                # 過去の日付の場合は来年にする
                if due_date < now_jst:
                    due_date = due_date.replace(year=year + 1)
                return due_date.astimezone(pytz.UTC)
            except ValueError:
                pass
        
        return None
    
    def _parse_priority(self, message: str) -> Dict[str, Any]:
        """優先度変更コマンドを解析"""
        # 番号を検出
        number_match = re.search(r'(\d+)', message)
        todo_number = int(number_match.group(1)) if number_match else None
        
        # 新しい優先度を検出
        new_priority = self._detect_priority(message.lower())
        
        return {
            'action': 'priority',
            'todo_number': todo_number,
            'new_priority': new_priority,
            'confidence': 0.8
        }
    
    def _parse_remind(self, message: str) -> Dict[str, Any]:
        """リマインド設定コマンドを解析"""
        # カスタムメッセージを検出（「。」の後、または特定のパターン）
        custom_message = None
        todo_number = None
        
        # パターン1: 「。」区切り
        if '。' in message:
            parts = message.split('。', 1)
            if len(parts) > 1 and parts[1].strip():
                custom_message = parts[1].strip()
                time_part = parts[0]
        else:
            # パターン2: 「リマインド」の後にカスタムメッセージ
            remind_match = re.search(r'リマインド[　\s]*(.+)', message)
            if remind_match:
                potential_custom = remind_match.group(1).strip()
                # カスタムメッセージのキーワードを拡張
                custom_keywords = [
                    '起こして', '起きて', '起こしてくれ', '起きてくれ', '教えて', '知らせて', '呼んで',
                    '何してる', '何してる？', '何してるか', '何してるの', '何しててる', '何しててる？',
                    '確認して', '聞いて', '連絡して', '伝えて', '声かけて', 'チェックして'
                ]
                # より柔軟な検出：メンション先が含まれていて、かつカスタムキーワードがあるか、または明らかにメッセージっぽい
                has_custom_keyword = any(keyword in potential_custom for keyword in custom_keywords)
                has_mention = any(word in potential_custom for word in ['supy', 'mrc', '@'])
                is_question = '？' in potential_custom or '?' in potential_custom
                
                if has_custom_keyword or (has_mention and len(potential_custom) > 3) or is_question:
                    custom_message = potential_custom
                    # カスタムメッセージ部分を除いた部分から時間を検出
                    time_part = message.replace(remind_match.group(0), 'リマインド')
                else:
                    time_part = message
            else:
                time_part = message
        
        # 時間部分から番号を検出（時間表現の文脈かTODO番号かを判定）
        if custom_message:
            # カスタムメッセージがある場合は時間部分のみから番号を検出
            number_match = re.search(r'(\d+)', time_part)
            if number_match and any(time_word in time_part for time_word in ['分後', '時間後', '日後', '時', '：', ':']):
                # 時間指定の数字なのでTODO番号ではない
                todo_number = None
            else:
                todo_number = int(number_match.group(1)) if number_match else None
        else:
            # 通常のパターン（カスタムメッセージなし）
            number_match = re.search(r'(\d+)', message)
            todo_number = int(number_match.group(1)) if number_match else None
        
        # 時間指定を検出
        remind_time = self._detect_due_date(message.lower())
        
        # カスタムメッセージがあって時間指定がない場合は即座実行
        if custom_message and not remind_time:
            remind_time = datetime.now(pytz.timezone('Asia/Tokyo')).astimezone(pytz.UTC) + timedelta(seconds=1)
        
        # 時間の種類を判定
        remind_type = 'custom'
        if '今すぐ' in message or 'すぐ' in message or (custom_message and not any(word in message for word in ['分後', '時間後', '日後', '毎日', '毎朝', '毎晩'])):
            remind_type = 'immediate'
        elif any(word in message for word in ['毎日', '毎朝', '毎晩', '毎日毎朝']):
            remind_type = 'recurring'
        
        # 全リスト通知の判定
        is_list_reminder = any(word in message for word in ['全リスト', 'リスト', '一覧'])
        if is_list_reminder:
            todo_number = None  # 全リスト通知の場合は番号なし
        
        # メンション先を検出
        mention_target = 'everyone'  # デフォルト
        if '@mrc' in message.lower() or 'mrc' in message.lower():
            mention_target = 'mrc'
        elif '@supy' in message.lower() or 'supy' in message.lower():
            mention_target = 'supy'
        elif '@' in message:
            # その他のメンション指定があれば抽出
            mention_match = re.search(r'@(\w+)', message)
            if mention_match:
                mention_target = mention_match.group(1)
        
        # チャンネル指定を検出
        channel_target = 'todo'  # デフォルト
        if 'todo' in message.lower() or '#todo' in message.lower():
            channel_target = 'todo'
        elif '#' in message:
            channel_match = re.search(r'#(\w+)', message)
            if channel_match:
                channel_target = channel_match.group(1)
        
        return {
            'action': 'remind',
            'todo_number': todo_number,
            'remind_time': remind_time,
            'remind_type': remind_type,
            'mention_target': mention_target,
            'channel_target': channel_target,
            'is_list_reminder': is_list_reminder,
            'custom_message': custom_message,
            'confidence': 0.7
        }

# グローバルインスタンス
todo_nlu = TodoNLU()