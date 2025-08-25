"""
Google連携機能 - Catherine用
MCPブリッジ経由でGoogle Calendar, Sheets等を操作
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz

logger = logging.getLogger(__name__)

class GoogleIntegration:
    """Catherine用Google連携"""
    
    def __init__(self, mcp_bridge):
        self.mcp_bridge = mcp_bridge
        self.server_name = "google"
    
    async def is_available(self) -> bool:
        """Google MCPサーバーが利用可能かチェック"""
        return (self.mcp_bridge.initialized and 
                self.server_name in self.mcp_bridge.servers)
    
    async def create_calendar_event(self, title: str, start_time: datetime, 
                                   end_time: Optional[datetime] = None,
                                   description: str = "", location: str = "",
                                   reminder_minutes: int = 10) -> Dict[str, Any]:
        """カレンダーイベントを作成"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Google integration not available"}
            
            # 終了時間が指定されていない場合、1時間後に設定
            if not end_time:
                end_time = start_time + timedelta(hours=1)
            
            params = {
                "title": title,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "description": description,
                "location": location,
                "reminder_minutes": reminder_minutes
            }
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "create_event", params
            )
            
            if result:
                logger.info(f"Created calendar event: {title}")
                return result
            else:
                return {"success": False, "error": "Failed to call Google MCP"}
                
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"success": False, "error": str(e)}
    
    async def set_reminder(self, title: str, remind_time: datetime, 
                          description: str = "", reminder_minutes: int = 10) -> Dict[str, Any]:
        """リマインダーを設定（カレンダーイベントとして）"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Google integration not available"}
            
            params = {
                "title": title,
                "time": remind_time.isoformat(),
                "description": description,
                "reminder_minutes": reminder_minutes
            }
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "set_reminder", params
            )
            
            if result:
                logger.info(f"Set reminder: {title}")
                return result
            else:
                return {"success": False, "error": "Failed to call Google MCP"}
                
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_upcoming_events(self, days_ahead: int = 7, 
                                  max_results: int = 10) -> Dict[str, Any]:
        """今後の予定を取得"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Google integration not available"}
            
            params = {
                "max_results": max_results,
                "days_ahead": days_ahead
            }
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "list_events", params
            )
            
            if result:
                logger.info(f"Retrieved {result.get('count', 0)} calendar events")
                return result
            else:
                return {"success": False, "error": "Failed to call Google MCP"}
                
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_todo_with_calendar(self, title: str, description: str = "",
                                       due_date: Optional[datetime] = None,
                                       priority: str = "normal") -> Dict[str, Any]:
        """TODOをNotionに作成し、期限があればカレンダーイベントも作成"""
        try:
            results = {"notion": None, "calendar": None}
            
            # Notionへの保存は呼び出し元で処理済み
            
            # 期限があればカレンダーイベントも作成
            if due_date:
                calendar_title = f"📋 TODO期限: {title}"
                calendar_result = await self.create_calendar_event(
                    title=calendar_title,
                    start_time=due_date,
                    end_time=due_date + timedelta(hours=1),
                    description=f"TODO: {description}\n優先度: {priority}",
                    reminder_minutes=30  # 30分前にリマインダー
                )
                results["calendar"] = calendar_result
            
            return {
                "success": True,
                "results": results,
                "message": "TODO created with calendar integration"
            }
            
        except Exception as e:
            logger.error(f"Error creating TODO with calendar: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_email_notification(self, to: str, subject: str, 
                                     body: str) -> Dict[str, Any]:
        """メール通知を送信"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Google integration not available"}
            
            params = {
                "to": to,
                "subject": subject,
                "body": body
            }
            
            result = await self.mcp_bridge.call_tool(
                self.server_name, "send_email", params
            )
            
            if result:
                logger.info(f"Sent email notification to: {to}")
                return result
            else:
                return {"success": False, "error": "Failed to call Google MCP"}
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_task_sheet(self, title: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """タスクリストのスプレッドシートを作成"""
        try:
            if not await self.is_available():
                return {"success": False, "error": "Google integration not available"}
            
            # スプレッドシートを作成
            sheet_result = await self.mcp_bridge.call_tool(
                self.server_name, "create_sheet", {"title": title}
            )
            
            if not sheet_result.get("success"):
                return sheet_result
            
            # ヘッダー行を追加
            headers = ["タスク", "優先度", "期限", "ステータス", "作成者"]
            values = [headers]
            
            # タスクデータを追加
            for task in tasks:
                row = [
                    task.get("title", ""),
                    task.get("priority", "normal"),
                    task.get("due_date", ""),
                    task.get("status", "pending"),
                    task.get("created_by", "")
                ]
                values.append(row)
            
            # データを追加
            append_result = await self.mcp_bridge.call_tool(
                self.server_name, "append_sheet", {
                    "spreadsheet_id": sheet_result["spreadsheet_id"],
                    "values": values
                }
            )
            
            if append_result.get("success"):
                logger.info(f"Created task sheet: {title}")
                return {
                    "success": True,
                    "spreadsheet_id": sheet_result["spreadsheet_id"],
                    "spreadsheet_url": sheet_result["spreadsheet_url"],
                    "message": f"Created task sheet: {title}"
                }
            else:
                return append_result
                
        except Exception as e:
            logger.error(f"Error creating task sheet: {e}")
            return {"success": False, "error": str(e)}
    
    def format_calendar_events(self, events_data: Dict[str, Any]) -> str:
        """カレンダーイベントを読みやすい形式にフォーマット"""
        if not events_data.get("success") or not events_data.get("events"):
            return "カレンダーからイベントを取得できませんでした。"
        
        events = events_data["events"]
        if not events:
            return "📅 今後の予定はありません。"
        
        formatted = f"📅 **今後の予定** ({len(events)}件)\n\n"
        
        for event in events:
            # 時刻をJSTに変換
            try:
                start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                start_jst = start_time.astimezone(pytz.timezone('Asia/Tokyo'))
                start_str = start_jst.strftime('%m/%d %H:%M')
            except:
                start_str = event.get('start', '')
            
            formatted += f"🕒 **{start_str}** - {event['title']}\n"
            
            if event.get('location'):
                formatted += f"   📍 {event['location']}\n"
            
            if event.get('description'):
                description = event['description'][:100]  # 最初の100文字
                if len(event['description']) > 100:
                    description += "..."
                formatted += f"   📝 {description}\n"
            
            if event.get('html_link'):
                formatted += f"   🔗 [Googleカレンダーで開く]({event['html_link']})\n"
            
            formatted += "\n"
        
        return formatted
    
    def parse_time_from_text(self, text: str) -> Optional[datetime]:
        """テキストから時刻を解析"""
        import re
        
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        
        # 「明日の10時」「明日10時」
        tomorrow_match = re.search(r'明日.*?(\d{1,2})時', text)
        if tomorrow_match:
            hour = int(tomorrow_match.group(1))
            return now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # 「今日の15時」「今日15時」
        today_match = re.search(r'今日.*?(\d{1,2})時', text)
        if today_match:
            hour = int(today_match.group(1))
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # 「10分後」「30分後」
        minutes_match = re.search(r'(\d+)分後', text)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            return now + timedelta(minutes=minutes)
        
        # 「1時間後」「2時間後」
        hours_match = re.search(r'(\d+)時間後', text)
        if hours_match:
            hours = int(hours_match.group(1))
            return now + timedelta(hours=hours)
        
        return None