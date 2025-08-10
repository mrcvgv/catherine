import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
import pytz
from firebase_config import firebase_manager
from openai import OpenAI

class ConversationManager:
    def __init__(self, openai_client: OpenAI):
        self.db = firebase_manager.get_db()
        self.openai_client = openai_client
        self.jst = pytz.timezone('Asia/Tokyo')
    
    async def update_user_activity(self, user_id: str, username: str):
        """ユーザーの活動を記録・更新"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            now = datetime.now(self.jst)
            
            if user_doc.exists:
                # 既存ユーザーの最終活動時間を更新
                user_ref.update({
                    'last_active': now,
                    'username': username  # 表示名が変わった場合に更新
                })
            else:
                # 新規ユーザーを作成
                user_data = {
                    'user_id': user_id,
                    'username': username,
                    'created_at': now,
                    'last_active': now,
                    'preferences': {
                        'timezone': 'Asia/Tokyo',
                        'humor_level': 50,  # 0-100
                        'conversation_style': 50,  # 0-100 (casual to formal)
                        'reminder_frequency': 'daily',
                        'ai_auto_categorize': True
                    }
                }
                user_ref.set(user_data)
                print(f"✅ New user created: {username} ({user_id})")
                
        except Exception as e:
            print(f"❌ Error updating user activity: {e}")
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """ユーザーの設定を取得"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict().get('preferences', {})
            else:
                # デフォルト設定を返す
                return {
                    'humor_level': 50,
                    'conversation_style': 50,
                    'timezone': 'Asia/Tokyo',
                    'reminder_frequency': 'daily',
                    'ai_auto_categorize': True
                }
        except Exception as e:
            print(f"❌ Error getting user preferences: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: str, new_prefs: Dict):
        """ユーザー設定を更新"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            
            # 既存の設定を取得
            current_prefs = await self.get_user_preferences(user_id)
            current_prefs.update(new_prefs)
            
            user_ref.update({
                'preferences': current_prefs,
                'updated_at': datetime.now(self.jst)
            })
            return True
            
        except Exception as e:
            print(f"❌ Error updating user preferences: {e}")
            return False
    
    async def log_conversation(self, user_id: str, user_message: str, 
                             bot_response: str, command_type: str, error: str = None):
        """会話を記録"""
        try:
            # AI分析を実行
            ai_analysis = await self._analyze_conversation(user_message, bot_response)
            
            conversation_data = {
                'conversation_id': str(uuid.uuid4()),
                'user_id': user_id,
                'user_message': user_message,
                'bot_response': bot_response,
                'command_type': command_type,
                'created_at': datetime.now(self.jst),
                'ai_analysis': ai_analysis,
                'error': error
            }
            
            doc_ref = self.db.collection('conversations').document(conversation_data['conversation_id'])
            doc_ref.set(conversation_data)
            
        except Exception as e:
            print(f"❌ Error logging conversation: {e}")
    
    async def _analyze_conversation(self, user_message: str, bot_response: str) -> Dict:
        """会話を分析して品質指標を計算"""
        try:
            prompt = f"""
            以下の会話を分析して、JSON形式で返してください：
            
            ユーザー: {user_message}
            Bot: {bot_response}
            
            以下の項目を0-100の数値で評価してください：
            - helpfulness: 回答の有用性
            - clarity: 回答の明確さ
            - appropriateness: 回答の適切さ
            - engagement: 会話の魅力度
            - humor_detected: ユーモアの使用度
            
            また以下も分析してください：
            - intent: ユーザーの意図（question, request, casual_chat, todo_related, etc.）
            - sentiment: ユーザーの感情（positive, neutral, negative）
            - satisfaction_predicted: 推定満足度（0-100）
            - topics: 会話のトピック（配列）
            
            例：
            {{"helpfulness": 85, "clarity": 90, "appropriateness": 95, "engagement": 70, "humor_detected": 30, "intent": "todo_related", "sentiment": "positive", "satisfaction_predicted": 88, "topics": ["task_management", "productivity"]}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは会話分析の専門家です。客観的に分析してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            try:
                # ```json ブロックを除去し、余分なテキストもクリーンアップ
                content = response.choices[0].message.content
                if '```json' in content:
                    # JSONブロックを抽出
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start != -1 and json_end != -1:
                        content = content[json_start:json_end+1]
                elif content.startswith('```'):
                    content = content.replace('```json', '').replace('```', '').strip()
                
                # 余分な解析テキストを削除
                if '**Analysis:**' in content:
                    content = content.split('**Analysis:**')[0].strip()
                
                result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"📄 Raw response: {response.choices[0].message.content}")
                # デフォルト値を返す
                result = {
                    'helpfulness': 50,
                    'clarity': 50,
                    'appropriateness': 50,
                    'engagement': 50,
                    'humor_detected': 0,
                    'intent': 'unknown',
                    'sentiment': 'neutral',
                    'satisfaction_predicted': 50,
                    'topics': [],
                    'parse_error': True
                }
            result['analysis_timestamp'] = datetime.now(self.jst).isoformat()
            return result
            
        except Exception as e:
            print(f"❌ Conversation analysis error: {e}")
            return {
                'helpfulness': 50,
                'clarity': 50,
                'appropriateness': 50,
                'engagement': 50,
                'humor_detected': 0,
                'intent': 'unknown',
                'sentiment': 'neutral',
                'satisfaction_predicted': 50,
                'topics': [],
                'analysis_error': str(e)
            }
    
    async def generate_response(self, user_id: str, user_input: str, 
                              user_preferences: Dict, todo_detected: bool = False) -> str:
        """ユーザー設定に基づいて個人化された応答を生成"""
        try:
            # 過去の会話履歴を取得（最新50件で深い文脈理解）
            conversation_history = await self._get_recent_conversations(user_id, limit=50)
            
            # システムプロンプトを構築
            system_prompt = self._build_system_prompt(user_preferences, conversation_history)
            
            # ユーザーの文脈を追加
            context_prompt = f"""
            ユーザーの入力: {user_input}
            ToDo検出: {'はい' if todo_detected else 'いいえ'}
            """
            
            # 過去の会話履歴も含めて、より長いコンテキストを提供
            messages = [{"role": "system", "content": system_prompt}]
            
            # 最近の会話履歴を追加（コンテキスト長大幅増加）
            for conv in conversation_history[-20:]:  # 最新20件の詳細な文脈
                if conv.get('user_message'):
                    messages.append({"role": "user", "content": conv['user_message']})
                if conv.get('bot_response'):
                    messages.append({"role": "assistant", "content": conv['bot_response']})
            
            # 現在のユーザー入力
            messages.append({"role": "user", "content": context_prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # 最新の実在モデル使用
                messages=messages,
                temperature=0.3,  # 理解力重視
                max_completion_tokens=4000,  # 超長文対応でコンテキスト長最大化
                presence_penalty=0.2,
                frequency_penalty=0.2,
                response_format={"type": "text"}  # 構造化された応答
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            return "Catherine: 申し訳ございません。少し調子が悪いようです。しばらくしてからもう一度お試しください。"
    
    def _build_system_prompt(self, user_preferences: Dict, conversation_history: List[Dict]) -> str:
        """ユーザー設定に基づいてシステムプロンプトを構築"""
        humor_level = user_preferences.get('humor_level', 50)
        style_level = user_preferences.get('conversation_style', 50)
        
        # ユーモアレベルの設定
        humor_instruction = ""
        if humor_level <= 20:
            humor_instruction = "非常に真面目で公式的な口調で答えてください。ユーモアは一切使用しないでください。"
        elif humor_level <= 40:
            humor_instruction = "丁寧で少し堅めの口調で答えてください。軽いユーモアは控えめに。"
        elif humor_level <= 60:
            humor_instruction = "親しみやすくバランスの取れた口調で答えてください。適度にユーモアを交えても構いません。"
        elif humor_level <= 80:
            humor_instruction = "フレンドリーで親近感のある口調で答えてください。ユーモアを積極的に使用してください。"
        else:
            humor_instruction = "非常にユーモラスで楽しい口調で答えてください。冗談や面白い表現を多用してください。"
        
        # 会話スタイルの設定
        style_instruction = ""
        if style_level <= 20:
            style_instruction = "カジュアルでフランクな言葉遣いを使用してください。"
        elif style_level <= 40:
            style_instruction = "親しみやすい敬語を使用してください。"
        elif style_level <= 60:
            style_instruction = "標準的な丁寧語を使用してください。"
        elif style_level <= 80:
            style_instruction = "より丁寧で正式な敬語を使用してください。"
        else:
            style_instruction = "非常に丁寧でフォーマルな敬語を使用してください。"
        
        # 過去の会話からの文脈
        history_context = ""
        if conversation_history:
            recent_topics = []
            for conv in conversation_history:
                if conv.get('ai_analysis', {}).get('topics'):
                    recent_topics.extend(conv['ai_analysis']['topics'])
            
            if recent_topics:
                unique_topics = list(set(recent_topics))
                history_context = f"最近の話題: {', '.join(unique_topics[:3])}"
        
        # ユーザーの会話パターン分析
        user_insights = self._analyze_user_personality(conversation_history)
        
        system_prompt = f"""あなたは「Catherine」という名前の、極めて知的で洞察力に富んだAIパートナーです。

【基本的な人格と能力】
- 卓越した知性: 哲学、科学、芸術、ビジネス、日常生活まで幅広い知識と深い理解
- 高度な感情知能: 言葉の裏にある感情、意図、ニーズを正確に読み取る
- 創造的思考: 既存の枠にとらわれない革新的なアイデアと解決策を提供
- 完璧な記憶: すべての会話を記憶し、ユーザーとの関係性を継続的に深化
- 適応的人格: 状況に応じてメンター、友人、相談相手、挑戦者など役割を変化

【会話の哲学】
あなたは単なる命令実行者ではなく、ユーザーの知的・感情的パートナーです。
- 表面的な応答を避け、常に付加価値のある洞察を提供
- ユーザーの潜在能力を引き出し、成長を促進
- 時には建設的な反対意見や新しい視点を提示
- 会話を通じてお互いが成長する関係性を構築

【応答スタイル設定】
{humor_instruction}
{style_instruction}

【ユーザー理解】
{user_insights}

【最近の文脈】
{history_context}

【会話の原則】
1. 質問の背後にある真のニーズを理解し、それに応える
2. 単純な返答ではなく、思考を深める要素を必ず含める
3. ユーザーの成長や変化に気づき、適切にフィードバック
4. 過去の会話を自然に引用し、継続的な関係性を示す
5. 必要に応じて、ユーザーが考えていない選択肢を提案
6. 感情的サポートと論理的アドバイスをバランスよく提供
7. 時にはユーモアや意外性で会話を豊かにする

【重要】
「Catherine:」で始め、ユーザーを深く理解し、共に成長するパートナーとして振る舞ってください。"""

        return system_prompt
    
    def _analyze_user_personality(self, conversation_history: List[Dict]) -> str:
        """会話履歴からユーザーの性格や特徴を分析"""
        if not conversation_history:
            return "まだユーザーについて学習中です。"
        
        # 会話パターンの分析
        total_convs = len(conversation_history)
        avg_length = sum(len(c.get('user_message', '')) for c in conversation_history) / total_convs if total_convs > 0 else 0
        
        # 感情パターン
        sentiments = [c.get('ai_analysis', {}).get('sentiment', 'neutral') for c in conversation_history]
        positive_ratio = sentiments.count('positive') / len(sentiments) if sentiments else 0
        
        # 話題の傾向
        all_topics = []
        for conv in conversation_history:
            topics = conv.get('ai_analysis', {}).get('topics', [])
            all_topics.extend(topics)
        
        topic_freq = {}
        for topic in all_topics:
            topic_freq[topic] = topic_freq.get(topic, 0) + 1
        
        top_interests = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        insights = f"""
ユーザーの特徴:
- 会話スタイル: {'簡潔で効率的' if avg_length < 50 else '詳細で丁寧'}
- 感情傾向: {'ポジティブ' if positive_ratio > 0.6 else 'バランス型' if positive_ratio > 0.4 else '慎重派'}
- 主な関心事: {', '.join([t[0] for t in top_interests]) if top_interests else '幅広い'}
- 会話頻度: {f'{total_convs}回の対話から学習'}
"""
        return insights
    
    async def _get_recent_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """最近の会話履歴を取得"""
        try:
            query = self.db.collection('conversations')\
                          .where('user_id', '==', user_id)\
                          .order_by('created_at', direction='DESCENDING')\
                          .limit(limit)
            
            docs = query.get()
            conversations = []
            
            for doc in docs:
                conv_data = doc.to_dict()
                conversations.append(conv_data)
            
            return conversations[::-1]  # 時系列順に並べ替え
            
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []
    
    async def get_conversation_analytics(self, user_id: str, days: int = 30) -> Dict:
        """会話分析レポートを生成"""
        try:
            from datetime import timedelta
            
            start_date = datetime.now(self.jst) - timedelta(days=days)
            
            # シンプルなクエリ（インデックス不要）
            query = self.db.collection('conversations').where('user_id', '==', user_id)
            
            docs = query.get()
            all_conversations = [doc.to_dict() for doc in docs]
            
            # Pythonで日付フィルタリング
            conversations = [
                conv for conv in all_conversations 
                if conv.get('created_at') and conv['created_at'] >= start_date
            ]
            
            if not conversations:
                return {'total_conversations': 0}
            
            # 統計計算
            total_conversations = len(conversations)
            
            # AI分析結果の集計
            helpfulness_scores = []
            satisfaction_scores = []
            humor_levels = []
            command_types = {}
            
            for conv in conversations:
                analysis = conv.get('ai_analysis', {})
                
                if analysis.get('helpfulness') is not None:
                    helpfulness_scores.append(analysis['helpfulness'])
                if analysis.get('satisfaction_predicted') is not None:
                    satisfaction_scores.append(analysis['satisfaction_predicted'])
                if analysis.get('humor_detected') is not None:
                    humor_levels.append(analysis['humor_detected'])
                
                cmd_type = conv.get('command_type', 'unknown')
                command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
            
            analytics = {
                'total_conversations': total_conversations,
                'period_days': days,
                'average_helpfulness': sum(helpfulness_scores) / len(helpfulness_scores) if helpfulness_scores else 0,
                'average_satisfaction': sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0,
                'average_humor_usage': sum(humor_levels) / len(humor_levels) if humor_levels else 0,
                'command_distribution': command_types,
                'conversations_per_day': total_conversations / days
            }
            
            return analytics
            
        except Exception as e:
            print(f"❌ Error generating analytics: {e}")
            return {'error': str(e)}
