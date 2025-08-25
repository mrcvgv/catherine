"""
統合外部TODOマネージャー - Notion + Google Tasks
FirebaseとMCPの問題を回避してより安定した外部サービス統合
"""
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class ExternalTodoManager:
    """Notion + Google Tasks統合TODOマネージャー"""
    
    def __init__(self):
        self.notion_integration = None
        self.google_services = None
        self.initialized = False
        
        # 優先度マッピング
        self.priority_mapping = {
            'urgent': {'emoji': '⚫', 'google_priority': '1'},
            'high': {'emoji': '🔴', 'google_priority': '2'}, 
            'normal': {'emoji': '🟡', 'google_priority': '3'},
            'low': {'emoji': '🟢', 'google_priority': '4'}
        }
    
    async def initialize(self):
        """外部サービスの初期化"""
        try:
            # Notion統合の初期化
            try:
                from src.notion_integration import NotionIntegration
                from src.mcp_bridge import mcp_bridge
                
                if await mcp_bridge.is_server_available('notion'):
                    self.notion_integration = NotionIntegration(mcp_bridge)
                    logger.info("Notion integration initialized successfully")
                else:
                    logger.warning("Notion MCP server not available")
                    
            except Exception as e:
                logger.warning(f"Notion integration failed: {e}")
                self.notion_integration = None
            
            # Google Services統合の初期化
            try:
                from src.google_services_integration import google_services
                
                if google_services.is_configured():
                    self.google_services = google_services
                    logger.info("Google services integration initialized successfully")
                else:
                    logger.warning("Google services not configured")
                    
            except Exception as e:
                logger.warning(f"Google services integration failed: {e}")
                self.google_services = None
            
            # 最低一つのサービスが利用可能なら初期化成功
            self.initialized = (self.notion_integration is not None or 
                              self.google_services is not None)
            
            if self.initialized:
                logger.info("External TODO manager initialized successfully")
            else:
                logger.error("No external services available for TODO management")
                
        except Exception as e:
            logger.error(f"Failed to initialize external TODO manager: {e}")
            self.initialized = False
    
    async def create_todo(self, title: str, user_id: str, priority: str = 'normal', 
                         due_date: Optional[datetime] = None, description: str = '') -> Dict[str, Any]:
        """TODOを作成（両方のサービスに並行して作成）"""
        if not self.initialized:
            await self.initialize()
        
        results = {'notion': None, 'google': None}
        created_todos = []
        
        # Notionに作成
        if self.notion_integration:
            try:
                notion_result = await self.notion_integration.add_todo_to_notion(
                    title=title,
                    description=description,
                    priority=priority,
                    created_by=user_id,
                    due_date=due_date.isoformat() if due_date else None,
                    tags=['catherine-bot']
                )
                results['notion'] = notion_result
                if notion_result.get('success'):
                    created_todos.append('Notion')
                    
            except Exception as e:
                logger.error(f"Failed to create Notion TODO: {e}")
                results['notion'] = {'success': False, 'error': str(e)}
        
        # Google Tasksに作成
        if self.google_services:
            try:
                google_result = await self.google_services.create_google_task(
                    title=title,
                    notes=description or f'Created by Catherine for {user_id}',
                    due_date=due_date
                )
                results['google'] = google_result
                if google_result.get('success'):
                    created_todos.append('Google Tasks')
                    
            except Exception as e:
                logger.error(f"Failed to create Google Task: {e}")
                results['google'] = {'success': False, 'error': str(e)}
        
        # 結果の統合
        success_count = len(created_todos)
        if success_count > 0:
            services_str = ' & '.join(created_todos)
            return {
                'success': True,
                'title': title,
                'priority': priority,
                'due_date': due_date,
                'services': created_todos,
                'message': f"TODO「{title}」を{services_str}に作成しました",
                'details': results
            }
        else:
            error_messages = []
            for service, result in results.items():
                if result and not result.get('success'):
                    error_messages.append(f"{service}: {result.get('error', 'Unknown error')}")
            
            return {
                'success': False,
                'error': 'Failed to create TODO in any service',
                'details': results,
                'error_messages': error_messages
            }
    
    async def list_todos(self, user_id: str = None, include_completed: bool = False) -> Dict[str, Any]:
        """TODO一覧を取得（両サービスから統合）"""
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
                    all_todos.extend(notion_result['todos'])
                    services_used.append('Notion')
                    
            except Exception as e:
                logger.error(f"Failed to get Notion TODOs: {e}")
        
        # Google Tasksから取得
        if self.google_services:
            try:
                google_result = await self.google_services.list_google_tasks()
                
                if google_result.get('success') and google_result.get('tasks'):
                    for task in google_result['tasks']:
                        # Google Task形式をTODO形式に変換
                        todo = {
                            'id': task.get('id'),
                            'title': task.get('title'),
                            'description': task.get('notes', ''),
                            'status': 'completed' if task.get('status') == 'completed' else 'pending',
                            'priority': 'normal',  # Google Tasksに優先度概念がない
                            'due_date': task.get('due'),
                            'created_by': user_id or 'google_tasks',
                            'source': 'google_tasks',
                            'service_icon': '📱'
                        }
                        all_todos.append(todo)
                    services_used.append('Google Tasks')
                    
            except Exception as e:
                logger.error(f"Failed to get Google Tasks: {e}")
        
        # 優先度順でソート
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        all_todos.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 2))
        
        # 完了したタスクを除外（必要に応じて）
        if not include_completed:
            all_todos = [todo for todo in all_todos if todo.get('status') not in ['completed', 'cancelled']]
        
        services_str = ' & '.join(services_used) if services_used else 'No services'
        
        return {
            'success': True,
            'todos': all_todos,
            'count': len(all_todos),
            'services': services_used,
            'message': f"{len(all_todos)}件のTODOを{services_str}から取得しました"
        }
    
    async def complete_todo_by_number(self, todo_number: int, user_id: str) -> Dict[str, Any]:
        """番号指定でTODOを完了"""
        # まず一覧を取得
        todos_result = await self.list_todos(user_id, include_completed=False)
        if not todos_result.get('success') or not todos_result.get('todos'):
            return {'success': False, 'error': 'TODOが見つかりません'}
        
        todos = todos_result['todos']
        if todo_number < 1 or todo_number > len(todos):
            return {'success': False, 'error': f'番号{todo_number}のTODOは存在しません'}
        
        todo = todos[todo_number - 1]
        return await self._complete_todo_by_service(todo)
    
    async def _complete_todo_by_service(self, todo: Dict) -> Dict[str, Any]:
        """サービス別のTODO完了処理"""
        source = todo.get('source')
        todo_id = todo.get('id')
        title = todo.get('title', 'Unknown TODO')
        
        if source == 'notion' and self.notion_integration:
            try:
                result = await self.notion_integration.complete_notion_todo(todo_id)
                if result.get('success'):
                    return {
                        'success': True,
                        'title': title,
                        'service': 'Notion',
                        'message': f"TODO「{title}」をNotionで完了にマークしました"
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Notion TODO完了に失敗: {result.get('error', 'Unknown error')}"
                    }
            except Exception as e:
                return {'success': False, 'error': f"Notion TODO完了エラー: {str(e)}"}
        
        elif source == 'google_tasks' and self.google_services:
            try:
                result = await self.google_services.complete_google_task(todo_id)
                if result.get('success'):
                    return {
                        'success': True,
                        'title': title,
                        'service': 'Google Tasks',
                        'message': f"TODO「{title}」をGoogle Tasksで完了にマークしました"
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Google Tasks完了に失敗: {result.get('error', 'Unknown error')}"
                    }
            except Exception as e:
                return {'success': False, 'error': f"Google Tasks完了エラー: {str(e)}"}
        
        else:
            return {'success': False, 'error': f'サポートされていないサービス: {source}'}
    
    async def delete_todos_by_numbers(self, todo_numbers: List[int], user_id: str) -> Dict[str, Any]:
        """複数番号指定でTODOを削除"""
        todos_result = await self.list_todos(user_id, include_completed=True)
        if not todos_result.get('success'):
            return {'success': False, 'error': 'TODOリストの取得に失敗しました'}
        
        todos = todos_result['todos']
        deleted_count = 0
        deleted_titles = []
        failed_numbers = []
        
        for num in sorted(set(todo_numbers), reverse=True):  # 逆順で削除
            if 1 <= num <= len(todos):
                todo = todos[num - 1]
                delete_result = await self._delete_todo_by_service(todo)
                
                if delete_result.get('success'):
                    deleted_count += 1
                    deleted_titles.append(todo.get('title', f'TODO {num}'))
                else:
                    failed_numbers.append(num)
            else:
                failed_numbers.append(num)
        
        return {
            'success': deleted_count > 0,
            'deleted_count': deleted_count,
            'deleted_titles': deleted_titles,
            'failed_numbers': failed_numbers,
            'message': f"{deleted_count}件のTODOを削除しました" if deleted_count > 0 else "TODOの削除に失敗しました"
        }
    
    async def _delete_todo_by_service(self, todo: Dict) -> Dict[str, Any]:
        """サービス別のTODO削除処理"""
        # 注意: 実際の削除は慎重に実装する必要がある
        # 現在はログ出力のみ
        logger.warning(f"TODO deletion requested but not implemented: {todo.get('title')} from {todo.get('source')}")
        return {'success': False, 'error': 'TODO削除機能は安全のため未実装です'}
    
    def format_todo_list(self, todos: List[Dict]) -> str:
        """TODO一覧を読みやすい形式にフォーマット"""
        if not todos:
            return "📝 TODOはありません"
        
        formatted = f"📋 **統合TODOリスト** ({len(todos)}件)\n\n"
        
        for i, todo in enumerate(todos, 1):
            priority = todo.get('priority', 'normal')
            status = todo.get('status', 'pending')
            source = todo.get('source', 'unknown')
            service_icon = todo.get('service_icon', '❓')
            
            priority_emoji = self.priority_mapping.get(priority, {}).get('emoji', '🟡')
            
            # ステータス表示
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄', 
                'completed': '✅',
                'cancelled': '❌'
            }.get(status, '⏳')
            
            formatted += f"{i}. {priority_emoji} {status_emoji} **{todo['title']}** {service_icon}\n"
            
            if todo.get('due_date'):
                formatted += f"   📅 期限: {todo['due_date']}\n"
            
            if todo.get('description'):
                desc = todo['description'][:50]
                if len(todo['description']) > 50:
                    desc += "..."
                formatted += f"   📄 {desc}\n"
            
            formatted += f"   🔗 {source.title()}\n\n"
        
        return formatted.rstrip()

# グローバルインスタンス
external_todo_manager = ExternalTodoManager()