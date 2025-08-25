"""
MCP (Model Context Protocol) ブリッジ
子プロセスとしてMCPサーバーを起動し、通信を管理
"""
import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPServer:
    """MCPサーバーの設定"""
    name: str
    cmd: str
    args: List[str]
    process: Optional[subprocess.Popen] = None
    reader: Optional[asyncio.StreamReader] = None
    writer: Optional[asyncio.StreamWriter] = None

class MCPBridge:
    """MCPサーバーとの通信を管理するブリッジ"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.initialized = False
    
    async def initialize(self) -> bool:
        """環境変数からMCPサーバー設定を読み込み、起動"""
        try:
            # 環境変数から設定を読み込み
            mcp_config = os.getenv('MCP_SERVERS', '[]')
            server_configs = json.loads(mcp_config)
            
            if not server_configs:
                logger.info("No MCP servers configured")
                return False
            
            # 各サーバーを起動
            for config in server_configs:
                server = MCPServer(
                    name=config['name'],
                    cmd=config['cmd'],
                    args=config['args']
                )
                
                success = await self.start_server(server)
                if success:
                    self.servers[server.name] = server
                    logger.info(f"Started MCP server: {server.name}")
                else:
                    logger.error(f"Failed to start MCP server: {server.name}")
            
            self.initialized = True
            logger.info(f"MCP Bridge initialized with {len(self.servers)} servers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Bridge: {e}")
            return False
    
    async def start_server(self, server: MCPServer) -> bool:
        """MCPサーバーを子プロセスとして起動"""
        try:
            # プロセスを起動（STDIOで通信）
            server.process = subprocess.Popen(
                [server.cmd] + server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # バイナリモード
            )
            
            # 非同期ストリームに変換
            loop = asyncio.get_event_loop()
            
            # 初期化確認（ダミー実装では簡略化）
            await asyncio.sleep(0.5)  # サーバー起動待ち
            
            if server.process.poll() is None:
                logger.info(f"MCP server {server.name} started successfully")
                return True
            else:
                logger.error(f"MCP server {server.name} failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting MCP server {server.name}: {e}")
            return False
    
    async def call_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """MCPサーバーのツールを呼び出し"""
        try:
            if server_name not in self.servers:
                logger.error(f"Unknown MCP server: {server_name}")
                return None
            
            server = self.servers[server_name]
            if not server.process or server.process.poll() is not None:
                logger.error(f"MCP server {server_name} is not running")
                return None
            
            # JSON-RPCリクエストを作成
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": f"tools/{tool_name}",
                "params": params
            }
            
            # リクエストを送信（ダミー実装）
            request_json = json.dumps(request) + "\n"
            server.process.stdin.write(request_json.encode())
            server.process.stdin.flush()
            
            # レスポンスを読み取り（ダミー実装）
            # 実際の実装では非同期読み取りが必要
            await asyncio.sleep(0.1)
            
            # ダミーレスポンス
            response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "success": True,
                    "data": f"Called {tool_name} on {server_name}"
                }
            }
            
            return response.get("result")
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return None
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """MCPサーバーの利用可能なツールをリスト"""
        try:
            result = await self.call_tool(server_name, "_list_tools", {})
            if result and "tools" in result:
                return result["tools"]
            
            # ダミー実装のデフォルトツール
            if server_name == "notion":
                return [
                    {"name": "create_page", "description": "Create a new Notion page"},
                    {"name": "update_page", "description": "Update an existing page"},
                    {"name": "search", "description": "Search Notion content"}
                ]
            elif server_name == "google":
                return [
                    {"name": "create_event", "description": "Create calendar event"},
                    {"name": "list_events", "description": "List upcoming events"},
                    {"name": "create_sheet", "description": "Create spreadsheet"}
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing tools for {server_name}: {e}")
            return []
    
    async def shutdown(self):
        """全てのMCPサーバーを停止"""
        for server_name, server in self.servers.items():
            try:
                if server.process and server.process.poll() is None:
                    server.process.terminate()
                    await asyncio.sleep(0.5)
                    if server.process.poll() is None:
                        server.process.kill()
                    logger.info(f"Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping MCP server {server_name}: {e}")
        
        self.servers.clear()
        self.initialized = False
        logger.info("MCP Bridge shutdown complete")

# グローバルインスタンス（main.pyから使用）
mcp_bridge = MCPBridge()