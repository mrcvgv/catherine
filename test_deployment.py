#!/usr/bin/env python3
"""
Catherine Deployment Test Script
Railway環境での動作確認用
"""
import asyncio
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_bridge import MCPBridge
from notion_integration import NotionIntegration
from google_integration import GoogleIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentTester:
    def __init__(self):
        self.mcp_bridge = None
        self.notion = None
        self.google = None
        self.test_results = []
    
    async def setup(self):
        """MCP統合をセットアップ"""
        try:
            logger.info("Setting up MCP Bridge...")
            self.mcp_bridge = MCPBridge()
            await self.mcp_bridge.initialize()
            
            self.notion = NotionIntegration(self.mcp_bridge)
            self.google = GoogleIntegration(self.mcp_bridge)
            
            logger.info("✅ MCP Bridge setup complete")
            return True
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    def add_test_result(self, test_name: str, success: bool, message: str = ""):
        """テスト結果を記録"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")
    
    async def test_environment_variables(self):
        """環境変数のチェック"""
        logger.info("\n=== Testing Environment Variables ===")
        
        required_vars = [
            "DISCORD_BOT_TOKEN",
            "OPENAI_API_KEY", 
            "NOTION_API_KEY",
            "GOOGLE_SERVICE_ACCOUNT_KEY",
            "GOOGLE_CALENDAR_ID",
            "GOOGLE_DRIVE_FOLDER_ID",
            "MCP_SERVERS"
        ]
        
        all_present = True
        for var in required_vars:
            if os.getenv(var):
                self.add_test_result(f"ENV_{var}", True, "Present")
            else:
                self.add_test_result(f"ENV_{var}", False, "Missing")
                all_present = False
        
        return all_present
    
    async def test_mcp_servers(self):
        """MCPサーバーの起動テスト"""
        logger.info("\n=== Testing MCP Servers ===")
        
        # Check if servers are running
        notion_available = await self.notion.is_available()
        google_available = await self.google.is_available()
        
        self.add_test_result("MCP_Notion_Server", notion_available, 
                           "Running" if notion_available else "Not available")
        self.add_test_result("MCP_Google_Server", google_available,
                           "Running" if google_available else "Not available")
        
        return notion_available and google_available
    
    async def test_notion_integration(self):
        """Notion統合のテスト"""
        logger.info("\n=== Testing Notion Integration ===")
        
        try:
            # Test TODO creation
            test_todo = {
                "title": "🧪 Deployment Test TODO",
                "description": "This is a test TODO created during deployment testing",
                "priority": "low"
            }
            
            result = await self.notion.add_todo_to_notion(**test_todo)
            
            if result.get("success"):
                self.add_test_result("Notion_Create_TODO", True, 
                                   f"TODO created with ID: {result.get('page_id', 'unknown')}")
                
                # Test TODO listing
                list_result = await self.notion.list_notion_todos()
                if list_result.get("success"):
                    todo_count = len(list_result.get("todos", []))
                    self.add_test_result("Notion_List_TODOs", True, 
                                       f"Retrieved {todo_count} TODOs")
                    return True
                else:
                    self.add_test_result("Notion_List_TODOs", False, 
                                       list_result.get("error", "Unknown error"))
            else:
                self.add_test_result("Notion_Create_TODO", False, 
                                   result.get("error", "Unknown error"))
        
        except Exception as e:
            self.add_test_result("Notion_Integration", False, str(e))
        
        return False
    
    async def test_google_integration(self):
        """Google統合のテスト"""
        logger.info("\n=== Testing Google Integration ===")
        
        success_count = 0
        
        try:
            # Test calendar events listing
            events_result = await self.google.list_upcoming_events(days_ahead=7, max_results=5)
            if events_result.get("success"):
                event_count = len(events_result.get("events", []))
                self.add_test_result("Google_Calendar_List", True, 
                                   f"Retrieved {event_count} events")
                success_count += 1
            else:
                self.add_test_result("Google_Calendar_List", False,
                                   events_result.get("error", "Unknown error"))
            
            # Test reminder creation (tomorrow 10 AM)
            tomorrow_10am = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            reminder_result = await self.google.set_reminder(
                title="🧪 Deployment Test Reminder",
                remind_time=tomorrow_10am,
                description="Test reminder created during deployment testing"
            )
            
            if reminder_result.get("success"):
                self.add_test_result("Google_Calendar_Reminder", True, "Reminder created")
                success_count += 1
            else:
                self.add_test_result("Google_Calendar_Reminder", False,
                                   reminder_result.get("error", "Unknown error"))
        
        except Exception as e:
            self.add_test_result("Google_Integration", False, str(e))
        
        return success_count >= 1
    
    async def test_integration_workflow(self):
        """統合ワークフローのテスト"""
        logger.info("\n=== Testing Integration Workflow ===")
        
        try:
            # Create TODO with due date (should trigger calendar event)
            due_date = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            # First create in Notion
            notion_result = await self.notion.add_todo_to_notion(
                title="🧪 Integration Test Task",
                description="Task with due date for testing integration workflow",
                priority="normal",
                due_date=due_date.isoformat()
            )
            
            if notion_result.get("success"):
                # Then create calendar event
                calendar_result = await self.google.create_todo_with_calendar(
                    title="🧪 Integration Test Task",
                    description="Task with due date for testing integration workflow", 
                    due_date=due_date,
                    priority="normal"
                )
                
                if calendar_result.get("success"):
                    self.add_test_result("Integration_Workflow", True,
                                       "TODO created in Notion + Calendar event")
                    return True
                else:
                    self.add_test_result("Integration_Workflow", False,
                                       "Notion OK, Calendar failed")
            else:
                self.add_test_result("Integration_Workflow", False,
                                   "Notion creation failed")
        
        except Exception as e:
            self.add_test_result("Integration_Workflow", False, str(e))
        
        return False
    
    async def cleanup(self):
        """テスト後のクリーンアップ"""
        logger.info("\n=== Cleanup ===")
        if self.mcp_bridge and hasattr(self.mcp_bridge, 'cleanup'):
            await self.mcp_bridge.cleanup()
            logger.info("✅ MCP Bridge cleaned up")
    
    def generate_report(self):
        """テストレポートを生成"""
        logger.info("\n" + "="*50)
        logger.info("DEPLOYMENT TEST REPORT")
        logger.info("="*50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        # Save to file
        report_path = Path(__file__).parent / "deployment_test_results.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total_tests,
                    "successful": successful_tests,
                    "failed": total_tests - successful_tests,
                    "success_rate": successful_tests/total_tests*100
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nReport saved to: {report_path}")
        
        return successful_tests >= total_tests * 0.8  # 80% success rate required

async def main():
    """メインテスト実行"""
    logger.info("🚀 Starting Catherine Deployment Tests...")
    
    tester = DeploymentTester()
    
    try:
        # Setup
        if not await tester.setup():
            logger.error("❌ Setup failed. Exiting.")
            return False
        
        # Run tests
        await tester.test_environment_variables()
        await tester.test_mcp_servers()
        await tester.test_notion_integration()
        await tester.test_google_integration()
        await tester.test_integration_workflow()
        
        # Generate report
        success = tester.generate_report()
        
        if success:
            logger.info("\n🎉 DEPLOYMENT TESTS PASSED!")
            logger.info("Catherine is ready for Railway deployment.")
        else:
            logger.error("\n💥 DEPLOYMENT TESTS FAILED!")
            logger.error("Please check the issues above before deploying.")
        
        return success
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())