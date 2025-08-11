#!/usr/bin/env python3
"""
Advanced Context Understanding System
人間のような理解と応答を実現する高度なコンテキストシステム
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from dataclasses import dataclass, asdict
from zoneinfo import ZoneInfo
from openai import OpenAI
from firebase_config import firebase_manager

TZ = ZoneInfo("Asia/Tokyo")

# --- モデル --------------------------------------------------------------

@dataclass
class Action:
    type: str                     # "todo.update", "todo.create", etc.
    title: Optional[str] = None   # 更新後タイトル（変更があれば）
    details: Optional[str] = None # 備考
    priority: Optional[str] = None# "high|medium|low"
    due: Optional[str] = None     # ISO8601
    normalized_date: Optional[str] = None
    assumptions: Optional[List[str]] = None
    confirm_required: bool = False
    id: Optional[str] = None
    tags: Optional[List[str]] = None
    assignee: Optional[str] = None  # チームToDo用
    
    def __post_init__(self):
        if self.assumptions is None:
            self.assumptions = []
        if self.tags is None:
            self.tags = []

def iso(dt: datetime|None) -> Optional[str]:
    return dt.astimezone(TZ).isoformat() if dt else None

PRIORITY_MAP = {
    "最優先":"high","優先度高":"high","高":"high","急ぎ":"high","緊急":"high",
    "普通":"medium","中":"medium","通常":"medium",
    "低":"low","優先度低":"low","後回し":"low","ゆっくり":"low"
}

# --- 日付解釈（拡張版） ---------------------------------------------------

def normalize_when(text: str) -> Optional[datetime]:
    text = text.strip()
    now = datetime.now(TZ)

    # 相対語
    if "明日" in text: base = now + timedelta(days=1)
    elif "明後日" in text: base = now + timedelta(days=2)
    elif "今日" in text: base = now
    elif "来週" in text: base = now + timedelta(weeks=1)
    elif "今週末" in text: 
        days_until_friday = (4 - now.weekday()) % 7
        base = now + timedelta(days=days_until_friday if days_until_friday > 0 else 7)
    else: base = None

    # 時刻
    m = re.search(r'(\d{1,2})[:：](\d{2})', text)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
    elif "朝" in text:
        hh, mm = 9, 0
    elif "昼" in text or "正午" in text:
        hh, mm = 12, 0
    elif "夕方" in text:
        hh, mm = 17, 0
    elif "午後" in text:
        hh, mm = 15, 0
    elif "夜" in text:
        hh, mm = 20, 0
    else:
        hh = mm = None

    # 絶対日付（MM/DD or M/D）
    d = re.search(r'(\d{1,2})[/-](\d{1,2})', text)
    if d:
        month, day = int(d.group(1)), int(d.group(2))
        base = datetime(now.year, month, day, tzinfo=TZ)
        if base < now:  # 過去の日付なら来年と判断
            base = base.replace(year=now.year + 1)

    if base:
        if hh is None: hh, mm = 12, 0
        return base.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return None

# --- タスク特定（拡張版） -------------------------------------------------

def resolve_task_id(user_text: str, tasks: List[Dict]) -> tuple[Optional[str], list]:
    """
    tasks: [{id,title,...}]
    タイトル部分一致で候補を見つける。候補が複数なら確認を促す。
    """
    # 「◯◯の期日を…」「"◯◯"を…」から候補語を抜く
    key = None
    m = re.search(r'「(.+?)」|"(.+?)"|『(.+?)』|\"(.+?)\"', user_text)
    if m:
        key = next(g for g in m.groups() if g)
    else:
        # "◯◯タスク""◯◯の○○" など最後の名詞塊をざっくり拾う
        mm = re.search(r'(.+?)(の|を|を?期日|の期日|の優先度|のタイトル)', user_text)
        if mm: key = mm.group(1).strip()

    if not key:
        return None, []

    cands = [t for t in tasks if key.lower() in t.get("title","").lower()]
    if not cands:
        return None, []
    
    # 最新（created_atがある想定、なければ最後尾）
    cands_sorted = sorted(cands, key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=TZ)), reverse=True)
    return cands_sorted[0].get("todo_id") or cands_sorted[0].get("id"), cands_sorted

class AdvancedContextSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
        
        # コンテキスト理解の層
        self.understanding_layers = {
            'literal': '文字通りの意味',
            'intent': '真の意図',
            'emotion': '感情的な文脈',
            'subtext': '言外の意味',
            'cultural': '文化的背景',
            'personal': '個人的文脈'
        }
        
        # 会話パターン学習
        self.conversation_patterns = {
            'greeting': ['おはよう', 'こんにちは', 'こんばんは', 'やあ', 'どうも'],
            'request': ['して', 'お願い', 'できる？', 'やって'],
            'question': ['なぜ', 'どうして', 'いつ', 'どこ', 'だれ', '何'],
            'emotion': ['嬉しい', '悲しい', '怒', '楽しい', '辛い'],
            'confirmation': ['そう', 'はい', 'うん', 'OK', 'いいよ'],
            'denial': ['いいえ', 'いや', 'ちがう', 'NO', 'だめ']
        }
    
    async def analyze_deep_context(self, user_id: str, message: str, 
                                  conversation_history: List[Dict]) -> Dict:
        """深層コンテキスト分析"""
        try:
            # 多層分析プロンプト
            analysis_prompt = f"""
あなたは人間の心理と会話を深く理解するAIです。
以下の会話を多層的に分析してください。

【現在のメッセージ】
{message}

【会話履歴】
{self._format_history(conversation_history[-10:])}

【分析項目】
1. 表面的な意味（literal_meaning）
2. 真の意図（true_intent）
3. 感情状態（emotional_state）
4. 暗黙の要求（implicit_request）
5. 期待される応答タイプ（expected_response_type）
6. 緊急度（urgency: 1-5）
7. 重要度（importance: 1-5）
8. 文脈の連続性（context_continuity: 前の会話との関連性）

以下のJSON形式で回答してください：
{{
    "literal_meaning": "文字通りの意味",
    "true_intent": "本当に伝えたいこと",
    "emotional_state": {{
        "primary": "主要な感情",
        "intensity": 1-5,
        "nuances": ["微妙な感情のニュアンス"]
    }},
    "implicit_request": "言葉にしていない要求",
    "expected_response_type": "共感/解決策/情報/確認/その他",
    "urgency": 1-5,
    "importance": 1-5,
    "context_continuity": {{
        "is_continuation": true/false,
        "topic_shift": "話題の変化",
        "reference_points": ["参照している過去の話題"]
    }},
    "cultural_context": "文化的・社会的文脈",
    "personal_context": "個人的な背景や状況",
    "suggested_tone": "推奨される返答のトーン"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": analysis_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # ユーザーの傾向を学習
            await self._learn_user_patterns(user_id, message, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Context analysis error: {e}")
            return self._get_default_analysis()
    
    async def generate_human_like_response(self, user_id: str, 
                                          context_analysis: Dict,
                                          user_profile: Dict) -> str:
        """人間らしい応答生成"""
        try:
            # ユーザープロファイルから好みを取得
            preferences = user_profile.get('preferences', {})
            communication_style = preferences.get('communication_style', 'friendly')
            humor_level = preferences.get('humor_level', 50)
            formality = preferences.get('formality', 'casual')
            
            response_prompt = f"""
あなたはCatherineという名前の、非常に人間らしいAI秘書です。
以下の分析結果を基に、自然で共感的な返答を生成してください。

【コンテキスト分析】
- 真の意図: {context_analysis.get('true_intent')}
- 感情状態: {context_analysis.get('emotional_state')}
- 暗黙の要求: {context_analysis.get('implicit_request')}
- 期待される応答: {context_analysis.get('expected_response_type')}
- 推奨トーン: {context_analysis.get('suggested_tone')}

【ユーザーの好み】
- コミュニケーションスタイル: {communication_style}
- ユーモアレベル: {humor_level}%
- フォーマリティ: {formality}

【応答ガイドライン】
1. 相手の感情に共感を示す
2. 真の意図に応える
3. 自然な日本語で話す
4. 適度な相槌や感情表現を入れる
5. 必要に応じて具体的な提案をする
6. 相手のペースに合わせる
7. 押し付けがましくない

この条件で、人間らしく温かみのある返答を生成してください。
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "system", "content": response_prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            return "申し訳ございません、うまく返答できませんでした。"
    
    async def _learn_user_patterns(self, user_id: str, message: str, 
                                   analysis: Dict) -> None:
        """ユーザーの会話パターンを学習"""
        try:
            # ユーザーパターンドキュメント取得/作成
            doc_ref = self.db.collection('user_patterns').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                patterns = doc.to_dict()
            else:
                patterns = {
                    'user_id': user_id,
                    'created_at': datetime.now(),
                    'patterns': {},
                    'preferences': {},
                    'vocabulary': {},
                    'topics': {}
                }
            
            # パターン更新
            emotion = analysis.get('emotional_state', {}).get('primary', 'neutral')
            if emotion not in patterns['patterns']:
                patterns['patterns'][emotion] = {
                    'count': 0,
                    'typical_intents': [],
                    'common_words': []
                }
            
            patterns['patterns'][emotion]['count'] += 1
            
            # 語彙分析
            words = re.findall(r'\w+', message)
            for word in words:
                if word not in patterns['vocabulary']:
                    patterns['vocabulary'][word] = 0
                patterns['vocabulary'][word] += 1
            
            # 話題追跡
            if 'topic' in analysis:
                topic = analysis['topic']
                if topic not in patterns['topics']:
                    patterns['topics'][topic] = {
                        'count': 0,
                        'last_mentioned': datetime.now(),
                        'sentiment': []
                    }
                patterns['topics'][topic]['count'] += 1
                patterns['topics'][topic]['last_mentioned'] = datetime.now()
            
            # 保存
            doc_ref.set(patterns)
            
        except Exception as e:
            print(f"❌ Pattern learning error: {e}")
    
    def _format_history(self, history: List[Dict]) -> str:
        """会話履歴のフォーマット"""
        formatted = []
        for item in history:
            role = "ユーザー" if item.get('is_user') else "Catherine"
            formatted.append(f"{role}: {item.get('content', '')}")
        return "\n".join(formatted)
    
    def _get_default_analysis(self) -> Dict:
        """デフォルトの分析結果"""
        return {
            'literal_meaning': '',
            'true_intent': '',
            'emotional_state': {
                'primary': 'neutral',
                'intensity': 3,
                'nuances': []
            },
            'implicit_request': '',
            'expected_response_type': 'general',
            'urgency': 3,
            'importance': 3,
            'context_continuity': {
                'is_continuation': False,
                'topic_shift': None,
                'reference_points': []
            },
            'suggested_tone': 'friendly'
        }
    
    async def extract_actionable_items(self, message: str, 
                                      context_analysis: Dict) -> List[Dict]:
        """メッセージから実行可能なアクションを抽出"""
        actions = []
        
        # ToDoの可能性をチェック
        if any(keyword in message for keyword in ['して', 'やって', 'お願い', 'しなきゃ', 'する予定']):
            actions.append({
                'type': 'todo',
                'confidence': 0.8,
                'content': message
            })
        
        # リマインダーの可能性をチェック
        if any(keyword in message for keyword in ['明日', '後で', '時に', '忘れないで', 'リマインド']):
            actions.append({
                'type': 'reminder',
                'confidence': 0.7,
                'content': message
            })
        
        # 質問への回答
        if context_analysis.get('expected_response_type') == '情報':
            actions.append({
                'type': 'search',
                'confidence': 0.6,
                'content': context_analysis.get('true_intent', message)
            })
        
        return actions
    
    # --- ToDo更新機能 ---------------------------------------------------
    
    def build_update_actions(self, user_text: str, tasks: List[Dict]) -> Dict:
        """自然言語からToDo更新アクションを構築"""
        a = Action(type="todo.update", tags=["update"])

        # 1) 対象タスク
        task_id, cands = resolve_task_id(user_text, tasks)
        if task_id is None:
            talk = "対象タスクが特定できませんでした。タイトルを「」や『』で囲んで教えてください。"
            return {"talk": talk, "actions": []}

        a.id = task_id
        if len(cands) > 1:
            a.confirm_required = True
            a.assumptions.append(f"候補が{len(cands)}件。最新1件を対象にする想定。")

        # 2) 期日変更
        if re.search(r'(期日|締切|デッドライン|締め切り|期限).*(変|延長|延期|移動|更新)|までに', user_text):
            dt = normalize_when(user_text)
            if dt:
                a.due = iso(dt)
                a.normalized_date = a.due
            else:
                a.confirm_required = True
                a.assumptions.append("期限の解釈が曖昧。確認が必要。")

        # 3) 優先度変更
        pr = None
        for k,v in PRIORITY_MAP.items():
            if k in user_text:
                pr = v
                break
        if pr:
            a.priority = pr

        # 4) タイトル更新
        m = re.search(r'(タイトル|名前|件名).*(?:を|は|に)(.+?)(?:に|へ|$)', user_text)
        if m:
            new_title = m.group(2).strip()
            # 引用符を除去
            new_title = re.sub(r'^[「『"]|[」』"]$', '', new_title)
            a.title = new_title

        # 5) 詳細追記
        md = re.search(r'(メモ|詳細|備考|説明).*(?:を|に)(.+)', user_text)
        if md:
            a.details = md.group(2).strip()

        # 6) 担当者変更（チームToDo用）
        if '@mrc' in user_text.lower():
            a.assignee = 'mrc'
        elif '@supy' in user_text.lower():
            a.assignee = 'supy'
        elif '担当' in user_text and '解除' in user_text:
            a.assignee = 'unassigned'

        # フォールバック：何も変化なし
        if not any([a.due, a.priority, a.title, a.details, a.assignee]):
            return {
                "talk": "更新内容が読み取れませんでした。『期日を明後日17:00に』『優先度を高に』『担当を@mrcに』のように指示してください。",
                "actions": []
            }

        talk_parts = []
        if a.due: talk_parts.append(f"期限→{a.normalized_date[:16]}")
        if a.priority: 
            pr_jp = {"high":"高", "medium":"中", "low":"低"}.get(a.priority, a.priority)
            talk_parts.append(f"優先度→{pr_jp}")
        if a.title: talk_parts.append(f"タイトル→「{a.title}」")
        if a.details: talk_parts.append("詳細を更新")
        if a.assignee: talk_parts.append(f"担当→{a.assignee}")
        
        talk = "了解。" + "、".join(talk_parts) + " に更新します。"
        if a.confirm_required:
            talk += "\n⚠️ 候補が複数あるので確認してください。"
        
        return {"talk": talk, "actions": [asdict(a)]}
    
    def build_create_action(self, user_text: str) -> Dict:
        """自然言語からToDo作成アクションを構築"""
        a = Action(type="todo.create", tags=["create"])
        
        # タイトル抽出
        # 「〜を作成」「〜をToDo」「〜を追加」パターン
        m = re.search(r'「(.+?)」|『(.+?)』|"(.+?)"', user_text)
        if m:
            a.title = next(g for g in m.groups() if g)
        else:
            # コマンド部分を除去してタイトルとする
            title = re.sub(r'^(todo|タスク|ToDo|やること)[\s　]*', '', user_text, flags=re.IGNORECASE)
            title = re.sub(r'(を?作成|を?追加|を?登録|を?todo)', '', title)
            a.title = title.strip()
        
        if not a.title:
            return {"talk": "ToDoの内容を教えてください。", "actions": []}
        
        # 期日
        dt = normalize_when(user_text)
        if dt:
            a.due = iso(dt)
            a.normalized_date = a.due
        
        # 優先度
        for k,v in PRIORITY_MAP.items():
            if k in user_text:
                a.priority = v
                break
        
        # 担当者
        if '@mrc' in user_text.lower():
            a.assignee = 'mrc'
        elif '@supy' in user_text.lower():
            a.assignee = 'supy'
        
        talk_parts = [f"「{a.title}」を作成"]
        if a.due: talk_parts.append(f"期限: {a.normalized_date[:16]}")
        if a.priority:
            pr_jp = {"high":"高", "medium":"中", "low":"低"}.get(a.priority, a.priority)
            talk_parts.append(f"優先度: {pr_jp}")
        if a.assignee: talk_parts.append(f"担当: {a.assignee}")
        
        talk = "了解。" + "、".join(talk_parts) + "します。"
        return {"talk": talk, "actions": [asdict(a)]}