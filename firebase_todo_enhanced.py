#!/usr/bin/env python3
"""
Firebase ToDo System - Enhanced Version
番号指定での削除・完了に対応したFirebase版TODOシステム
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pytz
from firebase_config import firebase_manager
from todo_nlu_enhanced import TodoNLUEnhanced, Intent, ParseResult
from discord_reminder_system import ReminderSystem, Reminder
from hybrid_intent_detector import HybridIntentDetector, IntentSpec

# 日本時間
JST = pytz.timezone('Asia/Tokyo')

class FirebaseTodoEnhanced:
    """Firebase連携TODO管理システム - 強化版"""
    
    def __init__(self, openai_client=None):
        self.db = firebase_manager.get_db()
        self.nlu = TodoNLUEnhanced()
        self.reminder_system = ReminderSystem()
        self.collection_name = 'todos'
        self.audit_collection = 'todo_audit_logs'
        self.last_listed_todos = []  # 最後に表示したTODOリスト
        self.pending_confirmations = {}  # 確認待ちアクション
        
        # ハイブリッド意図検出器
        self.hybrid_detector = HybridIntentDetector(openai_client)
        if openai_client:
            print("SUCCESS: Hybrid Intent Detection (Rule+LLM) enabled")
        else:
            print("WARNING: Hybrid Intent Detection (Rule only) - no OpenAI client")
        
    def generate_dedupe_key(self, title: str, user_id: str, channel_id: str) -> str:
        """重複検出用キー生成"""
        content = f"{title.lower().strip()}:{user_id}:{channel_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def process_message(self, message_text: str, user_id: str, 
                            channel_id: str, message_id: str) -> Dict[str, Any]:
        """Discord メッセージを処理 - ハイブリッド意図検出対応"""
        try:
            # ハイブリッド意図検出（ルール＋LLM）
            context = {
                'last_list': self.last_listed_todos,
                'current_time': datetime.now(JST).isoformat(),
                'user_timezone': 'Asia/Tokyo'
            }
            
            detection_result = await self.hybrid_detector.detect(
                message_text, user_id, channel_id, context
            )
            
            action = detection_result.get('action')
            
            # 確認が必要な場合
            if action in ['clarify', 'confirm']:
                return {
                    'success': True,
                    'message': detection_result['message'],
                    'response_type': action,
                    'pending_id': detection_result.get('pending_id')
                }
            
            # タイムアウト
            if action == 'expired':
                return {
                    'success': False,
                    'message': detection_result['message'],
                    'response_type': 'expired'
                }
            
            # 実行可能な場合
            if action == 'execute':
                spec = detection_result['spec']
                intent = spec['intent']
                
                # 意図別処理実行
                result = await self._execute_intent(spec, user_id, channel_id, message_id)
                
                # ポストアクション: リスト表示
                if intent in ['todo.delete', 'todo.complete'] and result.get('success'):
                    list_result = await self._handle_list_simple(user_id, channel_id)
                    if list_result.get('message'):
                        result['message'] += f"\n\n{list_result['message']}"
                
                # 自動補完フィールドの確認提案
                memory_info = detection_result.get('memory_info', {})
                auto_filled = memory_info.get('auto_filled', [])
                if auto_filled and result.get('success'):
                    result['message'] += f"\n\n💡 自動補完: {', '.join(auto_filled)}"
                    result['auto_filled_info'] = memory_info
                
                return result
            
            # 予期しないアクション
            return {
                'success': False,
                'message': f"処理できませんでした: {action}",
                'response_type': 'error'
            }
                    
        except Exception as e:
            print(f"Error processing message: {e}")
            return {
                'success': False,
                'message': f'処理中にエラーが発生しました: {str(e)}',
                'response_type': 'error'
            }
    
    async def _execute_intent(self, spec: Dict[str, Any], user_id: str, 
                             channel_id: str, message_id: str) -> Dict[str, Any]:
        """意図に基づいて実際の処理を実行"""
        intent = spec['intent']
        
        if intent == 'todo.add':
            return await self._handle_add_from_spec(spec, user_id, channel_id, message_id)
        
        elif intent == 'todo.delete':
            if spec.get('indices'):
                return await self._handle_bulk_delete_indices(spec['indices'], user_id, channel_id)
            else:
                return await self._handle_natural_delete_from_spec(spec, user_id, channel_id)
        
        elif intent == 'todo.complete':
            if spec.get('indices'):
                return await self._handle_bulk_complete_indices(spec['indices'], user_id, channel_id)
            else:
                return await self._handle_natural_complete_from_spec(spec, user_id, channel_id)
        
        elif intent == 'todo.list':
            return await self._handle_list_simple(user_id, channel_id)
        
        elif intent.startswith('remind.'):
            return await self._handle_reminder_from_spec(spec, user_id, channel_id, message_id)
        
        elif intent == 'chitchat':
            return await self._handle_chitchat(spec, user_id, channel_id)
        
        else:
            return {
                'success': False,
                'message': f'未対応の意図: {intent}',
                'response_type': 'unsupported'
            }
    
    async def _handle_add_from_spec(self, spec: Dict, user_id: str, channel_id: str, message_id: str) -> Dict:
        """仕様からTODO追加"""
        if not spec.get('what'):
            return {
                'success': False,
                'message': 'タスクの内容が指定されていません',
                'response_type': 'missing_content'
            }
        
        entities = {
            'title': spec['what'],
            'time': spec.get('time'),
            'mention': spec.get('mention'),
            'priority': 'normal'
        }
        
        return await self._handle_add_with_entities(entities, user_id, channel_id, message_id)
    
    async def _handle_list_simple(self, user_id: str, channel_id: str) -> Dict:
        """シンプルなTODOリスト表示"""
        entities = {}
        return await self._handle_list_with_filters(entities, user_id, channel_id)
    
    async def _handle_natural_delete_from_spec(self, spec: Dict, user_id: str, channel_id: str) -> Dict:
        """仕様から自然言語削除"""
        entities = {'query': spec.get('what', '')}
        return await self._handle_natural_delete(entities, user_id, channel_id)
    
    async def _handle_natural_complete_from_spec(self, spec: Dict, user_id: str, channel_id: str) -> Dict:
        """仕様から自然言語完了"""
        entities = {'query': spec.get('what', '')}
        return await self._handle_natural_complete(entities, user_id, channel_id)
    
    async def _handle_reminder_from_spec(self, spec: Dict, user_id: str, channel_id: str, message_id: str) -> Dict:
        """仕様からリマインド処理"""
        reminder_data = {
            'content': spec.get('what', ''),
            'time': spec.get('time'),
            'mention': spec.get('mention', '@everyone'),
            'repeat': spec.get('repeat')
        }
        return await self._handle_reminder(reminder_data, user_id, channel_id, message_id)
    
    async def _handle_chitchat(self, spec: Dict, user_id: str, channel_id: str) -> Dict:
        """雑談対応"""
        text = spec.get('raw_text', '')
        
        if 'うさぎ' in text or 'うさぎ' in text:
            return {
                'success': True,
                'message': 'うさぎかわいいですね！',
                'response_type': 'chitchat'
            }
        
        return {
            'success': True,
            'message': 'お疲れさまです！何かお手伝いできることはありますか？',
            'response_type': 'chitchat'
        }
    
    async def handle_user_correction(self, log_id: str, correct_intent: str, 
                                   user_id: str, feedback: str = "修正") -> Dict[str, Any]:
        """ユーザー修正処理 - 学習システム連携"""
        try:
            correction_result = await self.hybrid_detector.handle_correction(
                log_id, correct_intent, feedback
            )
            
            return {
                'success': True,
                'message': correction_result.get('message', '修正を記録しました'),
                'response_type': 'correction_learned',
                'learning_applied': correction_result.get('learning_applied', False)
            }
        except Exception as e:
            print(f"[ERROR] User correction handling failed: {e}")
            return {
                'success': False,
                'message': f'修正処理エラー: {str(e)}',
                'response_type': 'error'
            }
    
    async def get_learning_suggestions(self, user_id: str) -> Dict[str, Any]:
        """学習改善提案取得"""
        try:
            # 最近の操作履歴を取得（簡易版）
            interaction_history = []  # 実際にはDBから取得
            
            suggestions = await self.hybrid_detector.suggest_learning_improvement(
                user_id, interaction_history
            )
            
            return {
                'success': True,
                'suggestions': suggestions,
                'response_type': 'learning_suggestions'
            }
        except Exception as e:
            print(f"[ERROR] Learning suggestions failed: {e}")
            return {
                'success': False,
                'message': f'学習提案取得エラー: {str(e)}',
                'response_type': 'error'
            }
    
    async def _handle_reminder(self, reminder_result: Dict, user_id: str, channel_id: str, message_id: str) -> Dict:
        """リマインド処理"""
        try:
            # エラーチェック
            if reminder_result.get('error'):
                error = reminder_result['error']
                
                if error['type'] == 'missing_time':
                    # 時刻未指定 - 確認フロー
                    self.pending_confirmations[f"{user_id}:{channel_id}"] = {
                        'type': 'reminder_time_needed',
                        'message': reminder_result['message'],
                        'mentions': reminder_result['mentions'],
                        'user_id': user_id,
                        'channel_id': channel_id
                    }
                    return {
                        'success': True,
                        'message': error['message'],
                        'suggestion': error['suggestion'],
                        'response_type': 'reminder_time_needed'
                    }
                
                elif error['type'] == 'missing_message':
                    return {
                        'success': False,
                        'message': error['message'],
                        'suggestion': error['suggestion'],
                        'response_type': 'error'
                    }
            
            # メンション未指定の場合は確認
            if not reminder_result['mentions']:
                self.pending_confirmations[f"{user_id}:{channel_id}"] = {
                    'type': 'reminder_mention_needed',
                    'message': reminder_result['message'],
                    'remind_at': reminder_result['remind_at'],
                    'user_id': user_id,
                    'channel_id': channel_id
                }
                return {
                    'success': True,
                    'message': f"📨 リマインド対象を指定してください。\n内容: 「{reminder_result['message']}」\n時刻: {reminder_result['remind_at'].strftime('%m/%d %H:%M')}\n\n誰に通知しますか？ @everyone / @mrc / @supy",
                    'response_type': 'reminder_mention_needed'
                }
            
            # リマインド登録実行
            reminder = Reminder(
                message=reminder_result['message'],
                remind_at=reminder_result['remind_at'],
                mentions=reminder_result['mentions'],
                created_by=user_id,
                channel_id=channel_id
            )
            
            result = await self.reminder_system.register_reminder(reminder)
            return result
            
        except Exception as e:
            print(f"Error in _handle_reminder: {e}")
            return {'success': False, 'message': f'リマインド処理エラー: {str(e)}'}
    
    async def _handle_confirmation(self, message_text: str, user_id: str, channel_id: str) -> Dict:
        """確認待ち処理（はい/いいえ）"""
        try:
            key = f"{user_id}:{channel_id}"
            
            if key not in self.pending_confirmations:
                return {
                    'success': False,
                    'message': '確認待ちの操作がありません',
                    'response_type': 'no_pending'
                }
            
            pending = self.pending_confirmations[key]
            is_yes = message_text.lower() in ['はい', 'yes', 'y', 'ok']
            
            # 確認完了後はpendingを削除
            del self.pending_confirmations[key]
            
            if pending['type'] == 'reminder_mention_needed':
                if is_yes:
                    # @everyone を設定してリマインド登録
                    reminder = Reminder(
                        message=pending['message'],
                        remind_at=pending['remind_at'],
                        mentions=['@everyone'],
                        created_by=user_id,
                        channel_id=channel_id
                    )
                    return await self.reminder_system.register_reminder(reminder)
                else:
                    return {
                        'success': False,
                        'message': '❌ リマインド登録をキャンセルしました',
                        'response_type': 'cancelled'
                    }
            
            elif pending['type'] == 'bulk_delete':
                if is_yes:
                    return await self.execute_pending_delete(
                        pending['indices'], user_id, channel_id
                    )
                else:
                    return {
                        'success': False,
                        'message': '❌ 削除をキャンセルしました',
                        'response_type': 'cancelled'
                    }
            
            elif pending['type'] == 'bulk_complete':
                if is_yes:
                    return await self._execute_pending_complete(
                        pending['indices'], user_id, channel_id
                    )
                else:
                    return {
                        'success': False,
                        'message': '❌ 完了をキャンセルしました',
                        'response_type': 'cancelled'
                    }
            
            else:
                return {
                    'success': False,
                    'message': '不明な確認タイプです',
                    'response_type': 'unknown_confirmation'
                }
                
        except Exception as e:
            print(f"Error in _handle_confirmation: {e}")
            return {'success': False, 'message': f'確認処理エラー: {str(e)}'}
    
    async def _execute_pending_complete(self, indices: List[int], user_id: str, channel_id: str) -> Dict:
        """確認後の完了実行"""
        try:
            completed = []
            failed = []
            
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo = self.last_listed_todos[idx-1]
                    todo_data = todo.to_dict()
                    todo_id = todo.id
                    
                    try:
                        # ステータス更新
                        self.db.collection(self.collection_name).document(todo_id).update({
                            'status': 'done',
                            'updated_at': datetime.now(JST),
                            'completed_at': datetime.now(JST)
                        })
                        
                        completed.append(f"#{idx}")
                        
                        # 監査ログ
                        await self._add_audit_log(todo_id, user_id, 'complete', {'index': idx})
                        
                    except Exception as e:
                        failed.append(f"#{idx}")
                else:
                    failed.append(f"#{idx}(無効)")
            
            # レスポンス生成
            message = ""
            if completed:
                message += f"✅ 完了: {', '.join(completed)}（{len(completed)}件）"
            if failed:
                if message:
                    message += "｜"
                message += f"失敗: {', '.join(failed)}"
            
            # ポストアクション
            if len(completed) > 0:
                updated_list = await self._get_updated_list(user_id, channel_id)
                if updated_list:
                    message += "\n\n" + updated_list
                else:
                    message += "\n\n🎉 全部片付きました！"
            
            return {
                'success': len(completed) > 0,
                'message': message,
                'completed_count': len(completed),
                'failed_count': len(failed),
                'response_type': 'bulk_complete_executed'
            }
            
        except Exception as e:
            print(f"Error in _execute_pending_complete: {e}")
            return {'success': False, 'message': f'完了実行エラー: {str(e)}'}
    
    async def _handle_add(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """TODO追加処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            task = parse_result.task
            
            # 重複チェック
            dedupe_key = self.generate_dedupe_key(task['title'], user_id, channel_id)
            
            # 既存タスクチェック
            existing = self.db.collection(self.collection_name).where(
                'dedupe_key', '==', dedupe_key
            ).where('status', '==', 'open').limit(1).get()
            
            if existing:
                return {
                    'success': False,
                    'message': f'❗ 重複検出: 「{task["title"]}」は既に存在します',
                    'response_type': 'duplicate'
                }
            
            # 新規TODO作成
            todo_id = str(uuid.uuid4())
            todo_doc = {
                'todo_id': todo_id,
                'user_id': user_id,
                'channel_id': channel_id,
                'title': task['title'],
                'description': task.get('description'),
                'status': 'open',
                'priority': task.get('priority', 'normal'),
                'due_at': task.get('due'),
                'assignees': task.get('assignees', []),
                'tags': task.get('tags', []),
                'source_msg_id': task.get('source_msg_id'),
                'created_at': datetime.now(JST),
                'updated_at': datetime.now(JST),
                'dedupe_key': dedupe_key
            }
            
            # Firestoreに保存
            self.db.collection(self.collection_name).document(todo_id).set(todo_doc)
            
            # 監査ログ
            await self._add_audit_log(todo_id, user_id, 'add', {'task': todo_doc})
            
            # レスポンス生成
            response = f"✅ 追加｜『{task['title']}』"
            if task.get('due'):
                due_dt = datetime.fromisoformat(task['due'])
                response += f" 〆{due_dt.strftime('%m/%d %H:%M')}"
            if task.get('assignees'):
                response += f" ｜担当: {', '.join(task['assignees'])}"
            if task.get('tags'):
                response += f" ｜#{' #'.join(task['tags'])}"
            
            return {
                'success': True,
                'message': response,
                'todo_id': todo_id,
                'response_type': 'add',
                'suggestions': parse_result.suggestions
            }
            
        except Exception as e:
            print(f"Error in _handle_add: {e}")
            return {'success': False, 'message': f'追加エラー: {str(e)}'}
    
    async def _handle_list(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """TODO一覧表示"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            filters = parse_result.task
            
            # クエリ構築
            query = self.db.collection(self.collection_name)
            query = query.where('channel_id', '==', channel_id)
            query = query.where('status', '==', filters.get('status', 'open'))
            
            # タグフィルタ
            if filters.get('tags'):
                for tag in filters['tags']:
                    query = query.where('tags', 'array_contains', tag)
            
            # 優先度フィルタ  
            if filters.get('priority'):
                query = query.where('priority', '==', filters['priority'])
            
            # 並び替えと制限
            query = query.order_by('priority', direction='DESCENDING')
            query = query.order_by('created_at').limit(20)
            
            # 取得
            todos = query.get()
            self.last_listed_todos = list(todos)
            
            # NLUにリスト件数を設定
            self.nlu.set_last_list_count(len(self.last_listed_todos))
            
            if not self.last_listed_todos:
                return {
                    'success': True,
                    'message': '📝 TODOはありません',
                    'response_type': 'list_empty'
                }
            
            # フォーマット
            message = "📋 **TODOリスト**\n"
            for i, todo in enumerate(self.last_listed_todos, 1):
                todo_data = todo.to_dict()
                status_emoji = '✅' if todo_data['status'] == 'done' else '⬜'
                priority_emoji = {
                    'urgent': '🔴',
                    'high': '🟠',
                    'normal': '🟡',
                    'low': '🟢'
                }.get(todo_data.get('priority', 'normal'), '⚪')
                
                message += f"{i}. {status_emoji} {priority_emoji} {todo_data['title']}"
                
                if todo_data.get('due_at'):
                    due_dt = todo_data['due_at']
                    if isinstance(due_dt, str):
                        due_dt = datetime.fromisoformat(due_dt)
                    message += f" 〆{due_dt.strftime('%m/%d')}"
                
                if todo_data.get('assignees'):
                    message += f" @{','.join(todo_data['assignees'])}"
                
                if todo_data.get('tags'):
                    message += f" #{' #'.join(todo_data['tags'])}"
                
                message += "\n"
            
            message += "\n💡 番号指定で操作: `1,3,5削除` `2-4完了` など"
            
            return {
                'success': True,
                'message': message,
                'count': len(self.last_listed_todos),
                'response_type': 'list'
            }
            
        except Exception as e:
            print(f"Error in _handle_list: {e}")
            return {'success': False, 'message': f'一覧取得エラー: {str(e)}'}
    
    async def _handle_bulk_complete(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """複数TODO完了処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            if not self.last_listed_todos:
                return {
                    'success': False,
                    'message': '❌ 先にTODO一覧を表示してください',
                    'suggestion': '`todo list` でTODO一覧を表示後、番号指定してください',
                    'response_type': 'no_list'
                }
            
            indices = parse_result.target_indices
            if not indices:
                return {
                    'success': False,
                    'message': '❌ 完了する番号を指定してください',
                    'response_type': 'no_indices'
                }
            
            # 確認が必要な場合
            if parse_result.constraints.get('confirm_needed'):
                titles = []
                for idx in indices:
                    if 1 <= idx <= len(self.last_listed_todos):
                        todo_data = self.last_listed_todos[idx-1].to_dict()
                        titles.append(f"{idx}. {todo_data['title']}")
                
                return {
                    'success': True,
                    'message': f"⚠️ 以下のタスクを完了しますか？\n{chr(10).join(titles)}\n\n確認: `はい` / `いいえ`",
                    'response_type': 'confirm_complete',
                    'pending_action': {
                        'type': 'bulk_complete',
                        'indices': indices
                    }
                }
            
            # 完了処理実行
            completed = []
            failed = []
            
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo = self.last_listed_todos[idx-1]
                    todo_data = todo.to_dict()
                    todo_id = todo.id
                    
                    try:
                        # ステータス更新
                        self.db.collection(self.collection_name).document(todo_id).update({
                            'status': 'done',
                            'updated_at': datetime.now(JST),
                            'completed_at': datetime.now(JST)
                        })
                        
                        completed.append(f"#{idx}")
                        
                        # 監査ログ
                        await self._add_audit_log(todo_id, user_id, 'complete', {'index': idx})
                        
                    except Exception as e:
                        failed.append(f"#{idx}")
                else:
                    failed.append(f"#{idx}(無効)")
            
            # レスポンス生成（簡潔なフォーマット）
            message = ""
            if completed:
                message += f"✅ 完了: {', '.join(completed)}（{len(completed)}件）"
            if failed:
                if message:
                    message += "｜"
                message += f"失敗: {', '.join(failed)}"
            
            # ★ ポストアクション: 完了後に最新リストを表示
            if len(completed) > 0:
                # 最新のTODOリストを取得して追加
                updated_list = await self._get_updated_list(user_id, channel_id)
                if updated_list:
                    message += "\n\n" + updated_list
                else:
                    message += "\n\n🎉 全部片付きました！"
            
            return {
                'success': len(completed) > 0,
                'message': message,
                'completed_count': len(completed),
                'failed_count': len(failed),
                'response_type': 'bulk_complete'
            }
            
        except Exception as e:
            print(f"Error in _handle_bulk_complete: {e}")
            return {'success': False, 'message': f'完了処理エラー: {str(e)}'}
    
    async def _handle_bulk_delete(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """複数TODO削除処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            if not self.last_listed_todos:
                return {
                    'success': False,
                    'message': '❌ 先にTODO一覧を表示してください',
                    'suggestion': '`todo list` でTODO一覧を表示後、番号指定してください',
                    'response_type': 'no_list'
                }
            
            indices = parse_result.target_indices
            if not indices:
                return {
                    'success': False,
                    'message': '❌ 削除する番号を指定してください',
                    'response_type': 'no_indices'
                }
            
            # 削除は常に確認必要
            titles = []
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo_data = self.last_listed_todos[idx-1].to_dict()
                    titles.append(f"{idx}. {todo_data['title']}")
            
            if not titles:
                return {
                    'success': False,
                    'message': '❌ 有効な番号が指定されていません',
                    'response_type': 'invalid_indices'
                }
            
            # 確認プロンプト
            return {
                'success': True,
                'message': f"⚠️ 以下のタスクを削除しますか？（元に戻せません）\n{chr(10).join(titles)}\n\n確認: `はい` / `いいえ`",
                'response_type': 'confirm_delete',
                'pending_action': {
                    'type': 'bulk_delete',
                    'indices': indices
                }
            }
            
        except Exception as e:
            print(f"Error in _handle_bulk_delete: {e}")
            return {'success': False, 'message': f'削除処理エラー: {str(e)}'}
    
    async def execute_pending_delete(self, indices: List[int], user_id: str, channel_id: str = None) -> Dict:
        """削除の実行（確認後）"""
        try:
            deleted = []
            failed = []
            
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo = self.last_listed_todos[idx-1]
                    todo_data = todo.to_dict()
                    todo_id = todo.id
                    
                    try:
                        # 削除実行
                        self.db.collection(self.collection_name).document(todo_id).delete()
                        deleted.append(f"#{idx}")
                        
                        # 監査ログ
                        await self._add_audit_log(todo_id, user_id, 'delete', {
                            'index': idx,
                            'title': todo_data['title']
                        })
                        
                    except Exception as e:
                        failed.append(f"#{idx}")
                else:
                    failed.append(f"#{idx}(無効)")
            
            # レスポンス生成（簡潔なフォーマット）
            message = ""
            if deleted:
                message += f"🗑️ 削除: {', '.join(deleted)}（{len(deleted)}件）"
            if failed:
                if message:
                    message += "｜"
                message += f"失敗: {', '.join(failed)}"
            
            # ★ ポストアクション: 削除後に最新リストを表示
            if len(deleted) > 0 and channel_id:
                # 最新のTODOリストを取得して追加
                updated_list = await self._get_updated_list(user_id, channel_id)
                if updated_list:
                    message += "\n\n" + updated_list
                else:
                    message += "\n\n🎉 全部片付きました！"
            
            return {
                'success': len(deleted) > 0,
                'message': message,
                'deleted_count': len(deleted),
                'failed_count': len(failed),
                'response_type': 'bulk_delete_executed'
            }
            
        except Exception as e:
            print(f"Error in execute_pending_delete: {e}")
            return {'success': False, 'message': f'削除実行エラー: {str(e)}'}
    
    async def _handle_complete(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """単一TODO完了処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            task = parse_result.task
            
            # タスク特定
            todo_id = None
            todo_title = None
            
            if task.get('task_id'):
                # ID指定
                todo_id = str(task['task_id'])
            elif task.get('title_query'):
                # タイトル検索
                results = self.db.collection(self.collection_name).where(
                    'channel_id', '==', channel_id
                ).where('status', '==', 'open').where(
                    'title', '==', task['title_query']
                ).limit(1).get()
                
                if results:
                    todo = results[0]
                    todo_id = todo.id
                    todo_title = todo.to_dict()['title']
            
            if not todo_id:
                return {
                    'success': False,
                    'message': '❌ 該当するTODOが見つかりません',
                    'response_type': 'not_found'
                }
            
            # 完了更新
            self.db.collection(self.collection_name).document(todo_id).update({
                'status': 'done',
                'updated_at': datetime.now(JST),
                'completed_at': datetime.now(JST)
            })
            
            # 監査ログ
            await self._add_audit_log(todo_id, user_id, 'complete', {'method': 'single'})
            
            return {
                'success': True,
                'message': f"✅ 完了: {todo_title or todo_id}",
                'response_type': 'complete'
            }
            
        except Exception as e:
            print(f"Error in _handle_complete: {e}")
            return {'success': False, 'message': f'完了処理エラー: {str(e)}'}
    
    async def _handle_delete(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """単一TODO削除処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            task = parse_result.task
            
            # タスク特定
            todo_id = None
            todo_title = None
            
            if task.get('task_id'):
                # ID指定
                todo_id = str(task['task_id'])
            elif task.get('title_query'):
                # タイトル検索
                results = self.db.collection(self.collection_name).where(
                    'channel_id', '==', channel_id
                ).where('status', '==', 'open').where(
                    'title', '==', task['title_query']
                ).limit(1).get()
                
                if results:
                    todo = results[0]
                    todo_id = todo.id
                    todo_title = todo.to_dict()['title']
            
            if not todo_id:
                return {
                    'success': False,
                    'message': '❌ 該当するTODOが見つかりません',
                    'response_type': 'not_found'
                }
            
            # 確認プロンプト
            return {
                'success': True,
                'message': f"⚠️ 「{todo_title or todo_id}」を削除しますか？\n確認: `はい` / `いいえ`",
                'response_type': 'confirm_delete',
                'pending_action': {
                    'type': 'delete',
                    'todo_id': todo_id,
                    'title': todo_title
                }
            }
            
        except Exception as e:
            print(f"Error in _handle_delete: {e}")
            return {'success': False, 'message': f'削除処理エラー: {str(e)}'}
    
    async def _handle_update(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """TODO更新処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            task = parse_result.task
            updates = task.get('updates', {})
            
            if not updates:
                return {
                    'success': False,
                    'message': '❌ 更新内容が指定されていません',
                    'response_type': 'no_updates'
                }
            
            # タスク特定（実装省略）
            # ...
            
            return {
                'success': True,
                'message': '✅ 更新完了',
                'response_type': 'update'
            }
            
        except Exception as e:
            print(f"Error in _handle_update: {e}")
            return {'success': False, 'message': f'更新エラー: {str(e)}'}
    
    async def _handle_find(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """TODO検索処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            query_text = parse_result.task.get('query', '')
            
            if not query_text:
                return {
                    'success': False,
                    'message': '❌ 検索キーワードを指定してください',
                    'response_type': 'no_query'
                }
            
            # 検索実行（実装省略）
            # ...
            
            return {
                'success': True,
                'message': '🔍 検索結果',
                'response_type': 'find'
            }
            
        except Exception as e:
            print(f"Error in _handle_find: {e}")
            return {'success': False, 'message': f'検索エラー: {str(e)}'}
    
    async def _handle_postpone(self, parse_result: ParseResult, user_id: str, channel_id: str) -> Dict:
        """TODO延期処理"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            # 延期処理（実装省略）
            # ...
            
            return {
                'success': True,
                'message': '📅 延期完了',
                'response_type': 'postpone'
            }
            
        except Exception as e:
            print(f"Error in _handle_postpone: {e}")
            return {'success': False, 'message': f'延期エラー: {str(e)}'}
    
    async def _add_audit_log(self, todo_id: str, actor: str, action: str, details: Dict = None):
        """監査ログ追加"""
        try:
            if not self.db:
                return
            
            log_doc = {
                'todo_id': todo_id,
                'actor': actor,
                'action': action,
                'details': details or {},
                'timestamp': datetime.now(JST)
            }
            
            self.db.collection(self.audit_collection).add(log_doc)
            
        except Exception as e:
            print(f"Error adding audit log: {e}")
    
    async def _get_updated_list(self, user_id: str, channel_id: str) -> str:
        """削除/完了後の最新TODOリストを取得（ポストアクション用）"""
        try:
            if not self.db:
                return ""
            
            # 最新のオープンなTODOを取得
            query = self.db.collection(self.collection_name)
            query = query.where('channel_id', '==', channel_id)
            query = query.where('status', '==', 'open')
            query = query.order_by('priority', direction='DESCENDING')
            query = query.order_by('created_at').limit(20)
            
            todos = query.get()
            todo_list = list(todos)
            
            # リストを更新
            self.last_listed_todos = todo_list
            self.nlu.set_last_list_count(len(todo_list))
            
            if not todo_list:
                return ""  # 空の場合は呼び出し元で "🎉 全部片付きました！" を表示
            
            # フォーマット（リスト表示と同じ）
            message = "📋 **TODOリスト**\n"
            for i, todo in enumerate(todo_list, 1):
                todo_data = todo.to_dict()
                priority_emoji = {
                    'urgent': '🔴',
                    'high': '🟠',
                    'normal': '🟡',
                    'low': '🟢'
                }.get(todo_data.get('priority', 'normal'), '⚪')
                
                message += f"{i}. ⬜ {priority_emoji} {todo_data['title']}"
                
                if todo_data.get('due_at'):
                    due_dt = todo_data['due_at']
                    if isinstance(due_dt, str):
                        due_dt = datetime.fromisoformat(due_dt)
                    message += f" 〆{due_dt.strftime('%m/%d')}"
                
                if todo_data.get('assignees'):
                    message += f" @{','.join(todo_data['assignees'])}"
                
                if todo_data.get('tags'):
                    message += f" #{' #'.join(todo_data['tags'])}"
                
                message += "\n"
            
            return message
            
        except Exception as e:
            print(f"Error getting updated list: {e}")
            return ""
    
    # ===== スマート意図分類器用の追加メソッド =====
    
    async def _handle_add_with_entities(self, entities: Dict, user_id: str, 
                                      channel_id: str, message_id: str) -> Dict:
        """エンティティベースのTODO追加"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            title = entities.get('title', '')
            if not title:
                return {
                    'success': False,
                    'message': 'TODOのタイトルを教えてください',
                    'suggestion': '例: 「レポート作成」明日18時 high #urgent',
                    'response_type': 'missing_title'
                }
            
            # 重複チェック
            dedupe_key = self.generate_dedupe_key(title, user_id, channel_id)
            existing = self.db.collection(self.collection_name).where(
                'dedupe_key', '==', dedupe_key
            ).where('status', '==', 'open').limit(1).get()
            
            if existing:
                return {
                    'success': False,
                    'message': f'❗ 重複検出: 「{title}」は既に存在します',
                    'response_type': 'duplicate'
                }
            
            # TODO作成
            todo_id = str(uuid.uuid4())
            todo_doc = {
                'todo_id': todo_id,
                'user_id': user_id,
                'channel_id': channel_id,
                'title': title,
                'description': entities.get('description'),
                'status': 'open',
                'priority': entities.get('priority', 'normal'),
                'due_at': entities.get('due_time'),
                'assignees': entities.get('assignees', []),
                'tags': entities.get('tags', []),
                'source_msg_id': message_id,
                'created_at': datetime.now(JST),
                'updated_at': datetime.now(JST),
                'dedupe_key': dedupe_key
            }
            
            # Firestoreに保存
            self.db.collection(self.collection_name).document(todo_id).set(todo_doc)
            
            # 監査ログ
            await self._add_audit_log(todo_id, user_id, 'add', {'task': todo_doc})
            
            # レスポンス生成
            response = f"✅ 追加｜『{title}』"
            if entities.get('due_time'):
                due_dt = datetime.fromisoformat(entities['due_time'])
                response += f" 〆{due_dt.strftime('%m/%d %H:%M')}"
            if entities.get('assignees'):
                response += f" ｜担当: {', '.join(entities['assignees'])}"
            if entities.get('tags'):
                response += f" ｜#{' #'.join(entities['tags'])}"
            
            return {
                'success': True,
                'message': response,
                'todo_id': todo_id,
                'response_type': 'add'
            }
            
        except Exception as e:
            print(f"Error in _handle_add_with_entities: {e}")
            return {'success': False, 'message': f'追加エラー: {str(e)}'}
    
    async def _handle_bulk_delete_indices(self, indices: List[int], user_id: str, channel_id: str) -> Dict:
        """番号指定でのTODO削除（スマート分類器用）"""
        try:
            if not self.last_listed_todos:
                return {
                    'success': False,
                    'message': '❌ 先にTODO一覧を表示してください',
                    'suggestion': '`todo list` でTODO一覧を表示後、番号指定してください',
                    'response_type': 'no_list'
                }
            
            if not indices:
                return {
                    'success': False,
                    'message': '❌ 削除する番号を指定してください',
                    'response_type': 'no_indices'
                }
            
            # 確認プロンプト
            titles = []
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo_data = self.last_listed_todos[idx-1].to_dict()
                    titles.append(f"{idx}. {todo_data['title']}")
            
            if not titles:
                return {
                    'success': False,
                    'message': '❌ 有効な番号が指定されていません',
                    'response_type': 'invalid_indices'
                }
            
            # 確認が必要な削除操作
            self.pending_confirmations[f"{user_id}:{channel_id}"] = {
                'type': 'bulk_delete',
                'indices': indices,
                'user_id': user_id,
                'channel_id': channel_id
            }
            
            return {
                'success': True,
                'message': f"⚠️ 以下のタスクを削除しますか？（元に戻せません）\n{chr(10).join(titles)}\n\n確認: `はい` / `いいえ`",
                'response_type': 'confirm_delete'
            }
            
        except Exception as e:
            print(f"Error in _handle_bulk_delete_indices: {e}")
            return {'success': False, 'message': f'削除処理エラー: {str(e)}'}
    
    async def _handle_bulk_complete_indices(self, indices: List[int], user_id: str, channel_id: str) -> Dict:
        """番号指定でのTODO完了（スマート分類器用）"""
        try:
            if not self.last_listed_todos:
                return {
                    'success': False,
                    'message': '❌ 先にTODO一覧を表示してください',
                    'suggestion': '`todo list` でTODO一覧を表示後、番号指定してください',
                    'response_type': 'no_list'
                }
            
            if not indices:
                return {
                    'success': False,
                    'message': '❌ 完了する番号を指定してください',
                    'response_type': 'no_indices'
                }
            
            # 完了処理実行（確認不要）
            completed = []
            failed = []
            
            for idx in indices:
                if 1 <= idx <= len(self.last_listed_todos):
                    todo = self.last_listed_todos[idx-1]
                    todo_data = todo.to_dict()
                    todo_id = todo.id
                    
                    try:
                        # ステータス更新
                        self.db.collection(self.collection_name).document(todo_id).update({
                            'status': 'done',
                            'updated_at': datetime.now(JST),
                            'completed_at': datetime.now(JST)
                        })
                        
                        completed.append(f"#{idx}")
                        
                        # 監査ログ
                        await self._add_audit_log(todo_id, user_id, 'complete', {'index': idx})
                        
                    except Exception as e:
                        failed.append(f"#{idx}")
                else:
                    failed.append(f"#{idx}(無効)")
            
            # レスポンス生成
            message = ""
            if completed:
                message += f"✅ 完了: {', '.join(completed)}（{len(completed)}件）"
            if failed:
                if message:
                    message += "｜"
                message += f"失敗: {', '.join(failed)}"
            
            # ポストアクション
            if len(completed) > 0:
                updated_list = await self._get_updated_list(user_id, channel_id)
                if updated_list:
                    message += "\n\n" + updated_list
                else:
                    message += "\n\n🎉 全部片付きました！"
            
            return {
                'success': len(completed) > 0,
                'message': message,
                'completed_count': len(completed),
                'failed_count': len(failed),
                'response_type': 'bulk_complete'
            }
            
        except Exception as e:
            print(f"Error in _handle_bulk_complete_indices: {e}")
            return {'success': False, 'message': f'完了処理エラー: {str(e)}'}
    
    async def _handle_list_with_filters(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """フィルター付きTODOリスト表示"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            # クエリ構築
            query = self.db.collection(self.collection_name)
            query = query.where('channel_id', '==', channel_id)
            
            # ステータスフィルタ
            status = 'open'  # デフォルトは未完了
            if entities.get('status') == 'done':
                status = 'done'
            query = query.where('status', '==', status)
            
            # タグフィルタ
            if entities.get('tags'):
                for tag in entities['tags']:
                    query = query.where('tags', 'array_contains', tag)
            
            # 優先度フィルタ  
            if entities.get('priority'):
                query = query.where('priority', '==', entities['priority'])
            
            # 並び替えと制限
            query = query.order_by('priority', direction='DESCENDING')
            query = query.order_by('created_at').limit(20)
            
            # 取得
            todos = query.get()
            self.last_listed_todos = list(todos)
            
            # NLUにリスト件数を設定
            self.nlu.set_last_list_count(len(self.last_listed_todos))
            
            if not self.last_listed_todos:
                return {
                    'success': True,
                    'message': '📝 TODOはありません',
                    'response_type': 'list_empty'
                }
            
            # フォーマット
            message = "📋 **TODOリスト**\n"
            for i, todo in enumerate(self.last_listed_todos, 1):
                todo_data = todo.to_dict()
                status_emoji = '✅' if todo_data['status'] == 'done' else '⬜'
                priority_emoji = {
                    'urgent': '🔴',
                    'high': '🟠',
                    'normal': '🟡',
                    'low': '🟢'
                }.get(todo_data.get('priority', 'normal'), '⚪')
                
                message += f"{i}. {status_emoji} {priority_emoji} {todo_data['title']}"
                
                if todo_data.get('due_at'):
                    due_dt = todo_data['due_at']
                    if isinstance(due_dt, str):
                        due_dt = datetime.fromisoformat(due_dt)
                    message += f" 〆{due_dt.strftime('%m/%d')}"
                
                if todo_data.get('assignees'):
                    message += f" @{','.join(todo_data['assignees'])}"
                
                if todo_data.get('tags'):
                    message += f" #{' #'.join(todo_data['tags'])}"
                
                message += "\n"
            
            message += "\n💡 番号指定で操作: `1,3,5削除` `2-4完了` など"
            
            return {
                'success': True,
                'message': message,
                'count': len(self.last_listed_todos),
                'response_type': 'list'
            }
            
        except Exception as e:
            print(f"Error in _handle_list_with_filters: {e}")
            return {'success': False, 'message': f'一覧取得エラー: {str(e)}'}
    
    async def _handle_natural_delete(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """自然言語でのTODO削除"""
        # タイトルベースの削除など、将来実装
        return {
            'success': False,
            'message': '自然言語削除は番号指定をお使いください',
            'suggestion': '例: 1,3,5削除',
            'response_type': 'natural_delete_unsupported'
        }
    
    async def _handle_natural_complete(self, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """自然言語でのTODO完了"""
        # タイトルベースの完了など、将来実装
        return {
            'success': False,
            'message': '自然言語完了は番号指定をお使いください',
            'suggestion': '例: 1,3,5完了',
            'response_type': 'natural_complete_unsupported'
        }
    
    async def _handle_search(self, query: str, entities: Dict, user_id: str, channel_id: str) -> Dict:
        """TODO検索"""
        try:
            if not self.db:
                return {'success': False, 'message': 'データベース接続エラー'}
            
            # タイトルと説明で検索
            todos = self.db.collection(self.collection_name).where(
                'channel_id', '==', channel_id
            ).where('status', '==', 'open').get()
            
            # フィルタリング（Firestoreの制限回避）
            results = []
            for todo in todos:
                data = todo.to_dict()
                if (query.lower() in data['title'].lower() or 
                    (data.get('description') and query.lower() in data['description'].lower())):
                    results.append(todo)
            
            if not results:
                return {
                    'success': True,
                    'message': f'🔍 「{query}」に一致するTODOが見つかりませんでした',
                    'response_type': 'search_empty'
                }
            
            # 結果表示
            message = f"🔍 **検索結果** (「{query}」)\n\n"
            for i, todo in enumerate(results, 1):
                data = todo.to_dict()
                priority_emoji = {
                    'urgent': '🔴', 'high': '🟠', 'normal': '🟡', 'low': '🟢'
                }.get(data.get('priority', 'normal'), '⚪')
                
                message += f"{i}. {priority_emoji} {data['title']}"
                if data.get('due_at'):
                    due_dt = datetime.fromisoformat(data['due_at'])
                    message += f" 〆{due_dt.strftime('%m/%d')}"
                message += "\n"
            
            return {
                'success': True,
                'message': message,
                'count': len(results),
                'response_type': 'search_results'
            }
            
        except Exception as e:
            print(f"Error in _handle_search: {e}")
            return {'success': False, 'message': f'検索エラー: {str(e)}'}
    
    async def get_daily_todos_and_reminders(self, date: datetime.date, channel_id: str) -> str:
        """指定日のTODOとリマインドを取得（毎朝8:00用）"""
        try:
            if not self.db:
                return "データベース接続エラー"
            
            # その日が期限のTODOを取得
            start_dt = datetime.combine(date, datetime.min.time())
            end_dt = datetime.combine(date, datetime.max.time())
            start_dt = JST.localize(start_dt)
            end_dt = JST.localize(end_dt)
            
            # TODO取得
            todos = self.db.collection(self.collection_name).where(
                'channel_id', '==', channel_id
            ).where(
                'status', '==', 'open'
            ).where(
                'due_at', '>=', start_dt.isoformat()
            ).where(
                'due_at', '<=', end_dt.isoformat()
            ).order_by('due_at').get()
            
            # リマインド取得
            reminder_message = await self.reminder_system.get_daily_schedule(date, channel_id)
            
            # 統合メッセージ作成
            message = f"🌅 **本日の予定** ({date.strftime('%m/%d')})\n\n"
            
            # TODOセクション
            if todos:
                message += "📋 **期限のあるTODO:**\n"
                for todo in todos:
                    todo_data = todo.to_dict()
                    priority_emoji = {
                        'urgent': '🔴',
                        'high': '🟠', 
                        'normal': '🟡',
                        'low': '🟢'
                    }.get(todo_data.get('priority', 'normal'), '⚪')
                    
                    due_dt = datetime.fromisoformat(todo_data['due_at'])
                    time_str = due_dt.strftime('%H:%M')
                    
                    message += f"• {priority_emoji} {todo_data['title']} (〆{time_str})"
                    if todo_data.get('assignees'):
                        message += f" @{','.join(todo_data['assignees'])}"
                    message += "\n"
                message += "\n"
            
            # リマインドセクション
            if "予定はありません" not in reminder_message:
                reminder_lines = reminder_message.split('\n')[2:]  # ヘッダーを除去
                if any(line.strip() for line in reminder_lines if '🔔' in line):
                    message += "⏰ **リマインド:**\n"
                    for line in reminder_lines:
                        if '🔔' in line:
                            message += line + "\n"
                    message += "\n"
            
            if not todos and "予定はありません" in reminder_message:
                message += "予定はありません。良い一日を！"
            else:
                message += "今日も一日頑張りましょう！ 💪"
            
            return message
            
        except Exception as e:
            print(f"Error getting daily schedule: {e}")
            return f"予定取得エラー: {str(e)}"
    
    async def get_help(self) -> str:
        """ヘルプメッセージ生成"""
        return """
📚 **TODO & Reminder システム ヘルプ**

**TODOコマンド:**
• `todo add 「タイトル」 [期日] [優先度] [#タグ]` - TODO追加
• `todo list [フィルタ]` - 一覧表示
• `todo done [ID/タイトル]` - 完了
• `todo delete [ID/タイトル]` - 削除

**番号指定操作:**（リスト表示後）
• `1,3,5 完了` - 複数完了
• `2-4 削除` - 範囲削除
• `全部完了` - 全て完了

**リマインド機能:**
• `18:30に@mrcで『在庫チェック』リマインド` - 指定時刻にリマインド
• `明日9:00に会議リマインド` - 宛先未指定時は確認
• `8/15 18:00にみんなで締切のお知らせ` - 日付指定

**自然言語例:**
• 「明日までにレポート提出 #urgent」
• 「1と3消して」
• 「月曜日の朝9時にミーティング通知」

**毎朝8:00:** 自動でその日の予定をお知らせ

**優先度:** urgent(🔴) > high(🟠) > normal(🟡) > low(🟢)
**期日:** 明日、来週月曜、8/20 18:00 など
**メンション:** @everyone、@mrc、@supy
"""

if __name__ == "__main__":
    # テスト用
    import asyncio
    
    async def test():
        todo_system = FirebaseTodoEnhanced()
        
        # テストケース
        test_messages = [
            ("todo add 「テストタスク」 明日18時 high #test", "user123", "ch456", "msg789"),
            ("todo list", "user123", "ch456", "msg790"),
            ("1,2 完了", "user123", "ch456", "msg791"),
        ]
        
        for msg, user, channel, msg_id in test_messages:
            print(f"\n📨 Input: {msg}")
            result = await todo_system.process_message(msg, user, channel, msg_id)
            print(f"Result: {result}")
    
    # asyncio.run(test())