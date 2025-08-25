"""
Notion連携機能 - Catherine用
MCPブリッジ経由でNotionを操作
"""
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class NotionIntegration:
    """Catherine用Notion連携"""
    
    def __init__(self, mcp_bridge):
        self.mcp_bridge = mcp_bridge
        self.server_name = "notion"
    
    async def is_available(self) -> bool:
        """Notion MCPサーバーが利用可能かチェック"""
        return (self.mcp_bridge.initialized and 
                self.server_name in self.mcp_bridge.servers)
    
    async def add_todo_to_notion(self, title: str, description: str = "", 
                                priority: str = "normal", created_by: str = "",
                                due_date: Optional[str] = None, tags: List[str] = None) -> Dict[str, Any]:
        """NotionにTODOを追加"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {
                "title": title,
                "description": description,
                "priority": priority,
                "created_by": created_by
            }
            
            if due_date:
                params["due_date"] = due_date
            
            if tags:
                params["tags"] = tags
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "add_todo", params
            )
            
            if result:
                logger.info(f"Added TODO to Notion: {title}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP"}
                
        except Exception as e:
            logger.error(f"Error adding TODO to Notion: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_notion_todos(self, status: Optional[str] = None, 
                               priority: Optional[str] = None) -> Dict[str, Any]:
        """NotionからTODO一覧を取得"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {}
            if status:
                params["status"] = status
            if priority:
                params["priority"] = priority
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "list_todos", params
            )
            
            if result:
                logger.info(f"Retrieved {result.get('count', 0)} TODOs from Notion")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP"}
                
        except Exception as e:
            logger.error(f"Error listing Notion TODOs: {e}")
            return {"success": False, "error": str(e)}
    
    async def complete_notion_todo(self, todo_id: str) -> Dict[str, Any]:
        """NotionのTODOを完了にマーク"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "complete_todo", {"todo_id": todo_id}
            )
            
            if result:
                logger.info(f"Completed Notion TODO: {todo_id}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP"}
                
        except Exception as e:
            logger.error(f"Error completing Notion TODO: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_notion(self, query: str) -> Dict[str, Any]:
        """Notionを検索"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "search", {"query": query}
            )
            
            if result:
                logger.info(f"Searched Notion for: {query}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP"}
                
        except Exception as e:
            logger.error(f"Error searching Notion: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_notion_page(self, title: str, content: str = "") -> Dict[str, Any]:
        """Notionページを作成"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "create_page", {
                    "title": title,
                    "content": content
                }
            )
            
            if result:
                logger.info(f"Created Notion page: {title}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP"}
                
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return {"success": False, "error": str(e)}
    
    def format_notion_todos(self, todos_data: Dict[str, Any]) -> str:
        """NotionのTODO一覧を読みやすい形式にフォーマット"""
        if not todos_data.get("success") or not todos_data.get("todos"):
            return "NotionからTODOを取得できませんでした。"
        
        todos = todos_data["todos"]
        if not todos:
            return "📝 NotionのTODOリストは空です。"
        
        priority_icons = {
            'urgent': '⚫',   # 激高
            'high': '🔴',     # 高
            'normal': '🟡',   # 普通
            'low': '🟢'       # 低い
        }
        
        status_icons = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        formatted = f"📋 **Notion TODOs** ({len(todos)}件)\n\n"
        
        for i, todo in enumerate(todos, 1):
            priority = todo.get('priority', 'normal')
            status = todo.get('status', 'pending')
            
            priority_icon = priority_icons.get(priority, '🟡')
            status_icon = status_icons.get(status, '⏳')
            
            formatted += f"{priority_icon} {status_icon} **{todo['title']}**\n"
            
            if todo.get('due_date'):
                formatted += f"   📅 期限: {todo['due_date']}\n"
            
            if todo.get('created_by'):
                formatted += f"   👤 作成者: {todo['created_by']}\n"
            
            if todo.get('tags'):
                tags_str = ", ".join(todo['tags'])
                formatted += f"   🏷️ タグ: {tags_str}\n"
            
            if todo.get('url'):
                formatted += f"   🔗 [Notionで開く]({todo['url']})\n"
            
            formatted += "\n"
        
        return formatted
    
    async def create_reminder_record(self, reminder_id: str, message: str, 
                                   calendar_event_id: str, remind_time: str,
                                   mention_target: str, channel_target: str,
                                   status: str, created_by: str) -> Dict[str, Any]:
        """Notion にリマインダーレコードを作成"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {
                "database_name": "Catherine_Reminders",
                "properties": {
                    "reminder_id": reminder_id,
                    "message": message,
                    "calendar_event_id": calendar_event_id,
                    "remind_time": remind_time,
                    "mention_target": mention_target,
                    "channel_target": channel_target,
                    "status": status,
                    "created_by": created_by
                }
            }
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "create_reminder", params
            )
            
            if result:
                logger.info(f"Created reminder record in Notion: {reminder_id}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP for reminder"}
                
        except Exception as e:
            logger.error(f"Error creating reminder record: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_reminder_status(self, reminder_id: str, status: str, 
                                   executed_at: Optional[str] = None) -> Dict[str, Any]:
        """Notion のリマインダーステータスを更新"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {
                "reminder_id": reminder_id,
                "status": status
            }
            
            if executed_at:
                params["executed_at"] = executed_at
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "update_reminder_status", params
            )
            
            if result:
                logger.info(f"Updated reminder status in Notion: {reminder_id} -> {status}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP for status update"}
                
        except Exception as e:
            logger.error(f"Error updating reminder status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_reminder_record(self, reminder_id: str) -> Dict[str, Any]:
        """Notion からリマインダーレコードを取得"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {"reminder_id": reminder_id}
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "get_reminder", params
            )
            
            if result:
                logger.info(f"Retrieved reminder record from Notion: {reminder_id}")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP for reminder get"}
                
        except Exception as e:
            logger.error(f"Error getting reminder record: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_active_reminders(self) -> Dict[str, Any]:
        """Notion からアクティブなリマインダー一覧を取得"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Notion integration not available"}
            
            params = {"status": "scheduled"}
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "list_reminders", params
            )
            
            if result:
                logger.info(f"Retrieved {result.get('count', 0)} active reminders from Notion")
                return result
            else:
                return {"success": False, "error": "Failed to call Notion MCP for reminder list"}
                
        except Exception as e:
            logger.error(f"Error listing active reminders: {e}")
            return {"success": False, "error": str(e)}