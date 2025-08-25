/**
 * MCP Base Server - 共通ベースクラス
 */

const readline = require('readline');

class MCPBaseServer {
    constructor(serverName) {
        this.serverName = serverName;
        this.tools = new Map();
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });
    }

    /**
     * ツールを登録
     */
    registerTool(name, description, handler) {
        this.tools.set(name, {
            name,
            description,
            handler
        });
    }

    /**
     * サーバーを起動
     */
    start() {
        console.error(`[${this.serverName}] MCP Server starting...`);
        
        // 標準入力からJSON-RPCリクエストを受信
        this.rl.on('line', async (line) => {
            try {
                const request = JSON.parse(line);
                const response = await this.handleRequest(request);
                console.log(JSON.stringify(response));
            } catch (error) {
                console.error(`[${this.serverName}] Error:`, error);
                const errorResponse = {
                    jsonrpc: '2.0',
                    id: null,
                    error: {
                        code: -32700,
                        message: 'Parse error',
                        data: error.message
                    }
                };
                console.log(JSON.stringify(errorResponse));
            }
        });

        // 初期化完了を通知
        console.error(`[${this.serverName}] MCP Server ready`);
    }

    /**
     * リクエストを処理
     */
    async handleRequest(request) {
        const { id, method, params } = request;

        // メソッドを解析
        if (method === 'tools/_list_tools') {
            // ツール一覧を返す
            const toolList = Array.from(this.tools.values()).map(tool => ({
                name: tool.name,
                description: tool.description
            }));
            
            return {
                jsonrpc: '2.0',
                id,
                result: {
                    tools: toolList
                }
            };
        } else if (method.startsWith('tools/')) {
            // ツール実行
            const toolName = method.substring(6);
            const tool = this.tools.get(toolName);
            
            if (!tool) {
                return {
                    jsonrpc: '2.0',
                    id,
                    error: {
                        code: -32601,
                        message: 'Method not found',
                        data: `Unknown tool: ${toolName}`
                    }
                };
            }

            try {
                const result = await tool.handler(params);
                return {
                    jsonrpc: '2.0',
                    id,
                    result
                };
            } catch (error) {
                return {
                    jsonrpc: '2.0',
                    id,
                    error: {
                        code: -32603,
                        message: 'Internal error',
                        data: error.message
                    }
                };
            }
        } else {
            return {
                jsonrpc: '2.0',
                id,
                error: {
                    code: -32601,
                    message: 'Method not found'
                }
            };
        }
    }
}

module.exports = MCPBaseServer;