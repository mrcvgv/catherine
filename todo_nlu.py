#!/usr/bin/env python3
"""
Discord ToDo Natural Language Understanding Engine
自然言語とコマンドからToDo意図を抽出
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pytz
from enum import Enum

# 日本時間
JST = pytz.timezone('Asia/Tokyo')

class Intent(Enum):
    ADD = "add"
    UPDATE = "update"
    COMPLETE = "complete"
    DELETE = "delete"
    LIST = "list"
    FIND = "find"
    ASSIGN = "assign"
    POSTPONE = "postpone"
    SET_DUE = "set_due"
    SET_TAG = "set_tag"
    UNKNOWN = "unknown"

@dataclass
class ParseResult:
    intent: str
    task: Dict[str, Any]
    constraints: Dict[str, Any]
    confidence: float = 0.0
    error: Optional[Dict[str, str]] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class RelativeDateParser:
    """相対日時パーサー - Asia/Tokyo対応"""
    
    def __init__(self):
        self.now = datetime.now(JST)
        
        # 相対表現パターン
        self.patterns = {
            # 今日系
            r'今日|きょう': (0, 'day'),
            r'明日|あした|あす': (1, 'day'),
            r'明後日|あさって': (2, 'day'),
            r'今夜|こんや': (0, 'night'),
            r'明晩|あすばん': (1, 'night'),
            
            # 週系
            r'来週|らいしゅう': (1, 'week'),
            r'再来週|さらいしゅう': (2, 'week'),
            r'今週|こんしゅう': (0, 'week'),
            
            # 月系
            r'来月|らいげつ': (1, 'month'),
            r'再来月|さらいげつ': (2, 'month'),
            r'今月|こんげつ': (0, 'month'),
            
            # 曜日
            r'月曜|月曜日|げつよう': 'monday',
            r'火曜|火曜日|かよう': 'tuesday', 
            r'水曜|水曜日|すいよう': 'wednesday',
            r'木曜|木曜日|もくよう': 'thursday',
            r'金曜|金曜日|きんよう': 'friday',
            r'土曜|土曜日|どよう': 'saturday',
            r'日曜|日曜日|にちよう': 'sunday',
        }
        
        # 時間表現
        self.time_patterns = {
            r'(\d{1,2})時(\d{1,2})分': r'\1:\2',
            r'(\d{1,2})時半': r'\1:30',
            r'(\d{1,2})時': r'\1:00',
            r'朝|あさ': '09:00',
            r'昼|ひる': '12:00',
            r'夕方|ゆうがた': '17:00',
            r'夜|よる': '20:00',
            r'深夜|しんや': '23:00',
        }
    
    def parse(self, text: str) -> Optional[datetime]:
        """相対日時文字列を絶対日時に変換"""
        try:
            text = text.lower().strip()
            target_date = self.now.date()
            target_time = None
            
            # 時間抽出
            for pattern, replacement in self.time_patterns.items():
                match = re.search(pattern, text)
                if match:
                    if isinstance(replacement, str):
                        time_str = replacement
                    else:
                        time_str = re.sub(pattern, replacement, match.group())
                    
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        target_time = datetime.min.time().replace(hour=hour, minute=minute)
                        break
                    except:
                        continue
            
            # 日付抽出
            date_found = False
            
            # 基本的な相対表現
            for pattern, offset_info in self.patterns.items():
                if re.search(pattern, text):
                    if isinstance(offset_info, tuple):
                        offset, unit = offset_info
                        if unit == 'day':
                            target_date = (self.now + timedelta(days=offset)).date()
                            if pattern in ['今夜|こんや', '明晩|あすばん'] and not target_time:
                                target_time = datetime.min.time().replace(hour=20)
                        elif unit == 'week':
                            target_date = (self.now + timedelta(weeks=offset)).date()
                        elif unit == 'month':
                            # 月計算は近似
                            target_date = (self.now + timedelta(days=offset*30)).date()
                    elif isinstance(offset_info, str):
                        # 曜日処理
                        weekday_map = {
                            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                            'friday': 4, 'saturday': 5, 'sunday': 6
                        }
                        target_weekday = weekday_map[offset_info]
                        days_ahead = target_weekday - self.now.weekday()
                        if days_ahead <= 0:  # 来週の該当曜日
                            days_ahead += 7
                        target_date = (self.now + timedelta(days=days_ahead)).date()
                    
                    date_found = True
                    break
            
            # 具体的な日付パターン
            if not date_found:
                # MM/DD形式
                match = re.search(r'(\d{1,2})/(\d{1,2})', text)
                if match:
                    month, day = int(match.group(1)), int(match.group(2))
                    year = self.now.year
                    # 過去の日付なら来年
                    test_date = datetime(year, month, day).date()
                    if test_date < self.now.date():
                        year += 1
                    target_date = datetime(year, month, day).date()
                    date_found = True
                
                # X日後パターン
                match = re.search(r'(\d+)日後', text)
                if match:
                    days = int(match.group(1))
                    target_date = (self.now + timedelta(days=days)).date()
                    date_found = True
            
            # 時間が指定されていない場合のデフォルト
            if not target_time:
                if '夜' in text or '晩' in text:
                    target_time = datetime.min.time().replace(hour=20)
                elif '朝' in text:
                    target_time = datetime.min.time().replace(hour=9)
                elif '昼' in text:
                    target_time = datetime.min.time().replace(hour=12)
                else:
                    target_time = datetime.min.time().replace(hour=18)  # デフォルト18時
            
            # 結合
            result = datetime.combine(target_date, target_time)
            result = JST.localize(result)
            
            # 過去の時刻なら翌日
            if result <= self.now and not date_found:
                result += timedelta(days=1)
            
            return result
            
        except Exception as e:
            print(f"❌ Date parsing error: {e}")
            return None
    
    def suggest_dates(self, text: str) -> List[str]:
        """日時候補を提案"""
        suggestions = []
        
        # 一般的な候補
        today = self.now.date()
        suggestions.extend([
            f"今日 {today.strftime('%m/%d')} 18:00",
            f"明日 {(today + timedelta(days=1)).strftime('%m/%d')} 18:00", 
            f"明後日 {(today + timedelta(days=2)).strftime('%m/%d')} 18:00",
            "来週金曜 18:00",
            "来月1日 09:00"
        ])
        
        # テキストから抽出した候補
        if '時' in text:
            time_match = re.search(r'(\d{1,2})時', text)
            if time_match:
                hour = int(time_match.group(1))
                suggestions.insert(0, f"今日 {hour}:00")
                suggestions.insert(1, f"明日 {hour}:00")
        
        return suggestions[:5]

class TodoNLU:
    """ToDo 自然言語理解エンジン"""
    
    def __init__(self):
        self.date_parser = RelativeDateParser()
        
        # 意図パターン定義
        self.intent_patterns = {
            Intent.ADD: [
                r'(?:todo\s+)?(?:add|追加|作成|登録)',
                r'(?:〜|を)(?:やる|する|作る|制作)',
                r'(?:までに|まで).*(?:やる|する|完了)',
                r'アサインして',
                r'お願い',
                r'忘れずに',
                r'リマインド'
            ],
            Intent.LIST: [
                r'(?:todo\s+)?(?:list|一覧|リスト)',
                r'(?:show|見せて|表示)',
                r'何がある',
                r'タスク.*出して'
            ],
            Intent.COMPLETE: [
                r'(?:todo\s+)?(?:done|完了|終了|済)',
                r'(?:finish|終わった|できた)',
                r'チェック'
            ],
            Intent.UPDATE: [
                r'(?:todo\s+)?(?:update|更新|修正|変更)',
                r'優先度.*(?:変更|更新)',
                r'期日.*(?:変更|更新)',
                r'タグ.*(?:追加|変更)'
            ],
            Intent.DELETE: [
                r'(?:todo\s+)?(?:delete|削除|消去)',
                r'(?:remove|取り消し)',
                r'なくして'
            ],
            Intent.FIND: [
                r'(?:todo\s+)?(?:find|検索|探して)',
                r'(?:どこ|何だっけ)',
                r'見つけて'
            ],
            Intent.POSTPONE: [
                r'延期',
                r'(?:後で|あとで)',
                r'(?:来週|来月|明日).*(?:に|へ).*(?:変更|移動)'
            ]
        }
        
        # 優先度パターン
        self.priority_patterns = {
            'urgent': r'(?:urgent|緊急|至急|最優先)',
            'high': r'(?:high|高|重要|優先)',
            'normal': r'(?:normal|普通|通常)',
            'low': r'(?:low|低|後回し)'
        }
        
        # タグパターン
        self.tag_pattern = r'#([a-zA-Z0-9_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)'
        
        # アサインパターン  
        self.assign_patterns = [
            r'@([a-zA-Z0-9_]+)',
            r'([a-zA-Z0-9_]+)(?:さん|君|氏)(?:に|へ)',
            r'私(?:に|へ)',
            r'自分(?:に|へ)',
            r'アサインして'
        ]
    
    def parse(self, text: str, user_id: str, channel_id: str, message_id: str) -> ParseResult:
        """テキストからToDo意図を抽出"""
        try:
            # 前処理
            original_text = text
            text = text.strip()
            
            # 意図判定
            intent = self._detect_intent(text)
            
            # 基本情報抽出
            task_info = {
                'title': '',
                'description': None,
                'assignees': [],
                'due': None,
                'priority': 'normal',
                'tags': [],
                'source_msg_id': message_id,
                'channel_id': channel_id
            }
            
            confidence = 0.5
            error = None
            suggestions = []
            
            # インテント別処理
            if intent == Intent.ADD:
                confidence, error, suggestions = self._parse_add_command(text, task_info, user_id)
            elif intent == Intent.LIST:
                confidence = 0.9
                task_info = self._parse_list_filters(text)
            elif intent == Intent.COMPLETE:
                confidence, error = self._parse_task_reference(text, task_info)
            elif intent == Intent.UPDATE:
                confidence, error = self._parse_update_command(text, task_info)
            elif intent == Intent.DELETE:
                confidence, error = self._parse_task_reference(text, task_info)
            elif intent == Intent.FIND:
                confidence = 0.8
                task_info = {'query': self._extract_search_query(text)}
            else:
                # 不明な場合はADD意図として試行
                intent = Intent.ADD
                confidence, error, suggestions = self._parse_add_command(text, task_info, user_id)
                confidence *= 0.7  # 不確実性を反映
            
            # 制約情報
            constraints = {
                'dedupe_key': f"{task_info.get('title', '')[:50]}:{user_id}:{channel_id}",
                'confirm_needed': intent == Intent.DELETE or confidence < 0.7
            }
            
            return ParseResult(
                intent=intent.value,
                task=task_info,
                constraints=constraints,
                confidence=confidence,
                error=error,
                suggestions=suggestions
            )
            
        except Exception as e:
            return ParseResult(
                intent=Intent.UNKNOWN.value,
                task={},
                constraints={},
                error={
                    'type': 'parse_error',
                    'message': f'解析エラー: {str(e)}',
                    'suggestion': '入力形式を確認してください'
                }
            )
    
    def _detect_intent(self, text: str) -> Intent:
        """意図検出"""
        text_lower = text.lower()
        
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            intent_scores[intent] = score
        
        # 最高スコアの意図を返す
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return Intent.ADD  # デフォルトは追加
    
    def _parse_add_command(self, text: str, task_info: Dict, user_id: str) -> Tuple[float, Optional[Dict], List[str]]:
        """ADD意図の詳細解析"""
        confidence = 0.5
        error = None
        suggestions = []
        
        # タイトル抽出
        title = self._extract_title(text)
        if not title:
            return 0.1, {
                'type': 'missing_info',
                'message': 'タスクのタイトルが不足しています',
                'suggestion': '例: todo 「ロンT制作」 明日18時 #CCT'
            }, []
        
        task_info['title'] = title
        confidence += 0.3
        
        # 日時抽出
        due_date = self.date_parser.parse(text)
        if due_date:
            task_info['due'] = due_date.isoformat()
            confidence += 0.2
        else:
            # 日時が曖昧な場合の候補提案
            suggestions = self.date_parser.suggest_dates(text)
        
        # 優先度抽出
        priority = self._extract_priority(text)
        if priority:
            task_info['priority'] = priority
            confidence += 0.1
        
        # タグ抽出
        tags = self._extract_tags(text)
        if tags:
            task_info['tags'] = tags
            confidence += 0.1
        
        # アサイン抽出
        assignees = self._extract_assignees(text, user_id)
        if assignees:
            task_info['assignees'] = assignees
            confidence += 0.1
        
        return min(confidence, 1.0), error, suggestions
    
    def _extract_title(self, text: str) -> str:
        """タイトル抽出"""
        # 「」で囲まれたタイトル
        quote_match = re.search(r'「([^」]+)」', text)
        if quote_match:
            return quote_match.group(1).strip()
        
        # コマンド部分を除いたタイトル
        text = re.sub(r'^(?:todo\s+)?(?:add\s+)?', '', text, flags=re.IGNORECASE)
        
        # 時間、優先度、タグ、アサインを除去
        text = re.sub(r'(?:明日|明後日|来週|今夜|昼|夜|\d+時|\d+:\d+)', '', text)
        text = re.sub(r'(?:high|low|urgent|normal|高|低|緊急|優先)', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'(?:に|へ)アサイン', '', text)
        
        title = text.strip()
        
        # 最低限の長さチェック
        if len(title) < 2:
            return ""
        
        return title[:100]  # 最大100文字
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """優先度抽出"""
        text_lower = text.lower()
        
        for priority, pattern in self.priority_patterns.items():
            if re.search(pattern, text_lower):
                return priority
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """タグ抽出"""
        return re.findall(self.tag_pattern, text)
    
    def _extract_assignees(self, text: str, default_user: str) -> List[str]:
        """アサイン先抽出"""
        assignees = []
        
        # @メンション
        mentions = re.findall(r'@([a-zA-Z0-9_]+)', text)
        assignees.extend(mentions)
        
        # 私に/自分に
        if re.search(r'(?:私|自分)(?:に|へ)', text):
            assignees.append(default_user)
        
        # アサインして（デフォルトユーザー）
        if re.search(r'アサインして', text) and not assignees:
            assignees.append(default_user)
        
        return list(set(assignees))  # 重複除去
    
    def _parse_list_filters(self, text: str) -> Dict[str, Any]:
        """リスト表示フィルター解析"""
        filters = {}
        
        # ステータス
        if re.search(r'(?:未完了|open|進行中)', text):
            filters['status'] = 'open'
        elif re.search(r'(?:完了|done|済)', text):
            filters['status'] = 'done'
        
        # 優先度
        for priority in ['urgent', 'high', 'normal', 'low']:
            if priority in text.lower():
                filters['priority'] = priority
                break
        
        # タグ
        tags = self._extract_tags(text)
        if tags:
            filters['tags'] = tags
        
        # 期間
        if re.search(r'今日', text):
            filters['today'] = True
        elif re.search(r'今週', text):
            filters['this_week'] = True
        elif re.search(r'期限.*(?:切れ|過ぎ)', text):
            filters['overdue'] = True
        
        return filters
    
    def _parse_task_reference(self, text: str, task_info: Dict) -> Tuple[float, Optional[Dict]]:
        """タスク参照解析（完了・削除用）"""
        # ID指定
        id_match = re.search(r'(?:id|ID|\#)(\d+)', text)
        if id_match:
            task_info['task_id'] = int(id_match.group(1))
            return 0.9, None
        
        # タイトル指定
        title_match = re.search(r'「([^」]+)」', text)
        if title_match:
            task_info['title_query'] = title_match.group(1)
            return 0.8, None
        
        # キーワード検索
        words = text.split()
        keywords = [w for w in words if len(w) > 1 and not re.match(r'(?:todo|done|完了|削除)', w)]
        if keywords:
            task_info['keywords'] = keywords
            return 0.6, None
        
        return 0.2, {
            'type': 'missing_info',
            'message': 'どのタスクか特定できません',
            'suggestion': 'タスクID（#123）またはタイトル（「ロンT制作」）を指定してください'
        }
    
    def _parse_update_command(self, text: str, task_info: Dict) -> Tuple[float, Optional[Dict]]:
        """更新コマンド解析"""
        confidence = 0.5
        updates = {}
        
        # タスク特定
        task_confidence, error = self._parse_task_reference(text, task_info)
        if error:
            return 0.2, error
        
        confidence += task_confidence * 0.5
        
        # 更新内容抽出
        if re.search(r'優先度.*(?:to|を|に)', text):
            priority = self._extract_priority(text)
            if priority:
                updates['priority'] = priority
                confidence += 0.2
        
        if re.search(r'(?:期日|締切|due).*(?:to|を|に)', text):
            due_date = self.date_parser.parse(text)
            if due_date:
                updates['due'] = due_date.isoformat()
                confidence += 0.2
        
        if re.search(r'タグ.*追加', text):
            new_tags = self._extract_tags(text)
            if new_tags:
                updates['add_tags'] = new_tags
                confidence += 0.1
        
        task_info['updates'] = updates
        
        if not updates:
            return 0.3, {
                'type': 'missing_info', 
                'message': '何を更新するか不明です',
                'suggestion': '優先度、期日、タグのいずれかを指定してください'
            }
        
        return min(confidence, 1.0), None
    
    def _extract_search_query(self, text: str) -> str:
        """検索クエリ抽出"""
        # 「」で囲まれた部分
        quote_match = re.search(r'「([^」]+)」', text)
        if quote_match:
            return quote_match.group(1)
        
        # find/検索の後の部分
        text = re.sub(r'^.*(?:find|検索|探して)\s*', '', text, flags=re.IGNORECASE)
        
        return text.strip()

if __name__ == "__main__":
    # テスト実行
    nlu = TodoNLU()
    
    test_cases = [
        "todo add 「ロンT制作」 明日18時 high #CCT",
        "明後日までにDUBさんのポートレート下描き、私にアサインして #CCT",
        "todo list #CCT 未完了",
        "「ロンT制作」完了",
        "「学習レポート」来月1日 9:00、@kohei @suzune",
        "今夜までにミーティング資料",
        "todo done 123",
        "来週金曜に延期",
    ]
    
    for test in test_cases:
        print(f"\n📝 Input: {test}")
        result = nlu.parse(test, "user123", "ch789", "msg456")
        print(f"Intent: {result.intent}")
        print(f"Task: {json.dumps(result.task, indent=2, ensure_ascii=False)}")
        print(f"Confidence: {result.confidence:.2f}")
        if result.error:
            print(f"Error: {result.error}")
        if result.suggestions:
            print(f"Suggestions: {result.suggestions}")