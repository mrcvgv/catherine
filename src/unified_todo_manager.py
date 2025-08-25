"""
統合TODOマネージャー - 明確な責任分担でサービス統合
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class UnifiedTodoManager:
    """
    統合TODOマネージャー - スマートルーティング
    
    役割分担:
    - Notion: プロジェクト・長期タスク・詳細管理
    - Google Tasks: 日常タスク・短期リマインダー
    - Firebase: フォールバック・チャット履歴
    """
    
    def __init__(self):
        self.notion_integration = None
        self.google_services = None
        self.firebase_todo = None
        self.initialized = False
    
    async def initialize(self):
        """サービスの初期化"""
        try:
            # Notion統合
            try:
                from src.notion_integration import NotionIntegration
                from src.mcp_bridge import mcp_bridge
                
                if await mcp_bridge.is_server_available('notion'):
                    self.notion_integration = NotionIntegration(mcp_bridge)
                    logger.info("✅ Notion integration initialized")
                else:
                    logger.warning("⚠️  Notion MCP server not available")
                    
            except Exception as e:
                logger.warning(f"⚠️  Notion initialization failed: {e}")
                self.notion_integration = None
            
            # Google Services統合
            try:
                from src.google_services_integration import google_services
                
                if google_services.is_configured():
                    self.google_services = google_services
                    logger.info("✅ Google services initialized")
                else:
                    logger.warning("⚠️  Google services not configured")
                    
            except Exception as e:
                logger.warning(f"⚠️  Google services initialization failed: {e}")
                self.google_services = None
            
            # Firebase TODO（フォールバック）
            try:
                from src.todo_manager import todo_manager
                self.firebase_todo = todo_manager
                logger.info("✅ Firebase TODO fallback initialized")
                
            except Exception as e:
                logger.warning(f"⚠️  Firebase TODO initialization failed: {e}")
                self.firebase_todo = None
            
            self.initialized = True
            logger.info("🚀 Unified TODO Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Unified TODO Manager: {e}")
            self.initialized = False
    
    def _classify_todo_intent(self, title: str, description: str = "", due_date: Optional[datetime] = None) -> str:
        """
        TODOの意図を分析してサービスを決定
        
        Returns:
            'notion' | 'google' | 'both'
        """
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # プロジェクト・長期タスク → Notion
        project_keywords = [
            'プロジェクト', 'project', '企画', '計画', '設計', 'design',
            '資料', '報告書', 'レポート', 'report', '分析', 'analysis',
            'プレゼン', 'presentation', '会議資料', '提案書'
        ]
        
        # 日常・短期タスク → Google Tasks
        daily_keywords = [
            '買い物', 'shopping', '買う', '購入', '連絡', 'call', '電話',
            'メール', 'email', '予約', '確認', 'check', '支払い', 'payment',
            '掃除', 'clean', '洗濯', '料理', 'cook'
        ]
        
        # 緊急度チェック
        if due_date:
            days_until = (due_date - datetime.now(pytz.timezone('Asia/Tokyo'))).days
            if days_until <= 1:  # 明日まで
                return 'google'  # 緊急は日常タスクで管理
            elif days_until > 30:  # 1ヶ月以上先
                return 'notion'  # 長期はプロジェクト管理
        
        # キーワードベース判定
        all_text = f"{title_lower} {desc_lower}"
        
        if any(keyword in all_text for keyword in project_keywords):
            return 'notion'
        elif any(keyword in all_text for keyword in daily_keywords):
            return 'google'
        else:
            return 'both'  # 判別不能なら両方に保存
    
    async def create_todo(self, title: str, user_id: str, priority: str = 'normal',
                         due_date: Optional[datetime] = None, description: str = '') -> Dict[str, Any]:
        """スマートルーティングでTODO作成"""
        if not self.initialized:
            await self.initialize()
        
        # 意図分析
        target_service = self._classify_todo_intent(title, description, due_date)
        
        logger.info(f"📋 TODO '{title[:30]}...' → {target_service}")
        
        results = {}
        created_services = []
        
        # Notion作成
        if target_service in ['notion', 'both'] and self.notion_integration:
            try:
                notion_result = await self.notion_integration.add_todo_to_notion(
                    title=title,
                    description=description,
                    priority=priority,
                    created_by=user_id,
                    due_date=due_date.isoformat() if due_date else None,
                    tags=['catherine-bot', 'project']
                )
                results['notion'] = notion_result
                if notion_result.get('success'):
                    created_services.append('📝 Notion')
                    
            except Exception as e:
                logger.error(f"Notion TODO creation failed: {e}")
                results['notion'] = {'success': False, 'error': str(e)}
        
        # Google Tasks作成
        if target_service in ['google', 'both'] and self.google_services:
            try:
                google_result = await self.google_services.create_google_task(
                    title=title,
                    notes=description or f'Created by Catherine for {user_id}',
                    due_date=due_date
                )
                results['google'] = google_result
                if google_result.get('success'):
                    created_services.append('📱 Google Tasks')
                    
            except Exception as e:
                logger.error(f"Google Tasks creation failed: {e}")
                results['google'] = {'success': False, 'error': str(e)}
        
        # フォールバック: Firebase
        if not created_services and self.firebase_todo:
            try:
                firebase_result = await self.firebase_todo.create_todo(
                    user_id=user_id,
                    title=title,
                    priority=priority,
                    due_date=due_date
                )
                results['firebase'] = firebase_result
                if firebase_result.get('success'):
                    created_services.append('🔥 Firebase (フォールバック)')
                    
            except Exception as e:
                logger.error(f"Firebase TODO creation failed: {e}")
                results['firebase'] = {'success': False, 'error': str(e)}
        
        # 結果統合
        if created_services:
            services_str = ' & '.join(created_services)
            return {
                'success': True,
                'title': title,
                'priority': priority,
                'due_date': due_date,
                'target_service': target_service,
                'created_services': created_services,
                'message': f"TODO「{title}」を{services_str}に作成しました",
                'details': results
            }
        else:
            return {
                'success': False,
                'error': '全てのサービスでTODO作成に失敗しました',
                'details': results
            }
    
    async def list_todos(self, user_id: str = None, include_completed: bool = False) -> Dict[str, Any]:
        """統合TODO一覧（全サービスから取得）"""
        if not self.initialized:
            await self.initialize()
        
        all_todos = []
        services_used = []
        
        # Notionから取得
        if self.notion_integration:
            try:
                status = None if include_completed else "pending,in_progress"
                notion_result = await self.notion_integration.list_notion_todos(status=status)
                
                if notion_result.get('success') and notion_result.get('todos'):
                    for todo in notion_result['todos']:
                        todo['source'] = 'notion'
                        todo['service_icon'] = '📝'
                        todo['category'] = 'プロジェクト'
                    all_todos.extend(notion_result['todos'])
                    services_used.append('📝 Notion')
                    
            except Exception as e:
                logger.error(f"Failed to get Notion TODOs: {e}")
        
        # Google Tasksから取得
        if self.google_services:
            try:
                google_result = await self.google_services.list_google_tasks()
                
                if google_result.get('success') and google_result.get('tasks'):
                    for task in google_result['tasks']:
                        todo = {
                            'id': task.get('id'),
                            'title': task.get('title'),
                            'description': task.get('notes', ''),
                            'status': 'completed' if task.get('status') == 'completed' else 'pending',
                            'priority': 'normal',
                            'due_date': task.get('due'),
                            'created_by': user_id or 'google_tasks',
                            'source': 'google_tasks',
                            'service_icon': '📱',
                            'category': '日常タスク'
                        }
                        all_todos.append(todo)
                    services_used.append('📱 Google Tasks')
                    
            except Exception as e:
                logger.error(f"Failed to get Google Tasks: {e}")
        
        # Firebase（フォールバック）から取得
        if self.firebase_todo and not services_used:
            try:
                firebase_todos = await self.firebase_todo.get_todos(
                    user_id=user_id,
                    include_completed=include_completed
                )
                
                if firebase_todos:
                    for todo in firebase_todos:
                        todo['source'] = 'firebase'
                        todo['service_icon'] = '🔥'
                        todo['category'] = 'ローカル'
                    all_todos.extend(firebase_todos)
                    services_used.append('🔥 Firebase')
                    
            except Exception as e:
                logger.error(f"Failed to get Firebase TODOs: {e}")
        
        # 優先度・期限順でソート
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        all_todos.sort(key=lambda x: (
            priority_order.get(x.get('priority', 'normal'), 2),
            x.get('due_date') or '9999-12-31'  # 期限なしは最後
        ))
        
        # 完了済み除外
        if not include_completed:
            all_todos = [todo for todo in all_todos 
                        if todo.get('status') not in ['completed', 'cancelled']]
        
        services_str = ' & '.join(services_used) if services_used else 'サービスなし'
        
        return {
            'success': True,
            'todos': all_todos,
            'count': len(all_todos),
            'services': services_used,
            'message': f"{len(all_todos)}件のTODOを{services_str}から取得しました"
        }
    
    async def complete_todo_by_number(self, todo_number: int, user_id: str) -> Dict[str, Any]:
        """番号指定でTODO完了"""
        todos_result = await self.list_todos(user_id, include_completed=False)
        if not todos_result.get('success') or not todos_result.get('todos'):
            return {'success': False, 'error': 'TODOが見つかりません'}
        
        todos = todos_result['todos']
        if todo_number < 1 or todo_number > len(todos):
            return {'success': False, 'error': f'番号{todo_number}のTODOは存在しません'}
        
        todo = todos[todo_number - 1]
        source = todo.get('source')
        todo_id = todo.get('id')
        title = todo.get('title', 'Unknown TODO')
        
        # サービス別完了処理
        if source == 'notion' and self.notion_integration:
            result = await self.notion_integration.complete_notion_todo(todo_id)
            service_name = '📝 Notion'
        elif source == 'google_tasks' and self.google_services:
            result = await self.google_services.complete_google_task(todo_id)
            service_name = '📱 Google Tasks'
        elif source == 'firebase' and self.firebase_todo:
            result = await self.firebase_todo.complete_todo(todo_id, user_id)
            service_name = '🔥 Firebase'
        else:
            return {'success': False, 'error': f'サポートされていないサービス: {source}'}
        
        if result.get('success'):
            return {
                'success': True,
                'title': title,
                'service': service_name,
                'message': f"TODO「{title}」を{service_name}で完了にマークしました"
            }
        else:
            return {
                'success': False,
                'error': f"{service_name}でのTODO完了に失敗: {result.get('error', 'Unknown error')}"
            }
    
    def format_todo_list(self, todos: List[Dict]) -> str:
        """統合TODO一覧のフォーマット"""
        if not todos:
            return "📝 TODOはありません"
        
        # カテゴリ別にグループ化
        categories = {}
        for todo in todos:
            category = todo.get('category', 'その他')
            if category not in categories:
                categories[category] = []
            categories[category].append(todo)
        
        formatted = f"📋 **統合TODOリスト** ({len(todos)}件)\n\n"
        
        # カテゴリ別表示
        for category, category_todos in categories.items():
            formatted += f"## {category} ({len(category_todos)}件)\n"
            
            for i, todo in enumerate(category_todos, 1):
                priority = todo.get('priority', 'normal')
                service_icon = todo.get('service_icon', '❓')
                
                # 優先度アイコン
                priority_icons = {'urgent': '⚫', 'high': '🔴', 'normal': '🟡', 'low': '🟢'}
                priority_emoji = priority_icons.get(priority, '🟡')
                
                # 全体のインデックス計算
                global_index = todos.index(todo) + 1
                
                formatted += f"{global_index}. {priority_emoji} **{todo['title']}** {service_icon}\n"
                
                if todo.get('due_date'):
                    formatted += f"   📅 期限: {todo['due_date']}\n"
                
                if todo.get('description') and len(todo['description']) > 0:
                    desc = todo['description'][:40]
                    if len(todo['description']) > 40:
                        desc += "..."
                    formatted += f"   📄 {desc}\n"
                
                formatted += "\n"
            
            formatted += "\n"
        
        return formatted.rstrip()

# グローバルインスタンス
unified_todo_manager = UnifiedTodoManager()