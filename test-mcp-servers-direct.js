#!/usr/bin/env node
/**
 * 直接MCPサーバーをテストして接続状況を確認
 */
const { spawn } = require('child_process');
require('dotenv').config();

async function testMCPServer(serverName, cmd, args) {
    return new Promise((resolve, reject) => {
        console.log(`\n🧪 Testing ${serverName} MCP Server`);
        console.log(`Command: ${cmd} ${args.join(' ')}`);
        console.log('='.repeat(50));
        
        const server = spawn(cmd, args, {
            stdio: ['pipe', 'pipe', 'inherit'],
            cwd: process.cwd()
        });
        
        let responseReceived = false;
        let output = '';
        
        // タイムアウト設定
        const timeout = setTimeout(() => {
            if (!responseReceived) {
                server.kill();
                resolve({
                    success: false,
                    error: 'Server startup timeout (10s)',
                    output: output.trim()
                });
            }
        }, 10000);
        
        server.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        server.on('spawn', () => {
            console.log(`✅ ${serverName} MCP Server spawned successfully`);
            
            // サーバーが起動してから少し待つ
            setTimeout(() => {
                // ツールリストをリクエスト
                const request = {
                    jsonrpc: "2.0",
                    id: 1,
                    method: "tools/_list_tools",
                    params: {}
                };
                
                console.log('📨 Sending tools list request...');
                server.stdin.write(JSON.stringify(request) + '\n');
                
                // レスポンス待ち
                setTimeout(() => {
                    if (!responseReceived) {
                        server.kill();
                        clearTimeout(timeout);
                        resolve({
                            success: false,
                            error: 'No response to tools list request',
                            output: output.trim()
                        });
                    }
                }, 3000);
                
            }, 2000); // 2秒待ってからリクエスト送信
        });
        
        server.stdout.on('data', (data) => {
            const responses = data.toString().split('\n').filter(line => line.trim());
            
            responses.forEach(response => {
                if (response.trim()) {
                    try {
                        const parsed = JSON.parse(response);
                        if (parsed.jsonrpc && parsed.id === 1) {
                            responseReceived = true;
                            clearTimeout(timeout);
                            server.kill();
                            
                            if (parsed.error) {
                                resolve({
                                    success: false,
                                    error: parsed.error.message,
                                    code: parsed.error.code,
                                    output: output.trim()
                                });
                            } else {
                                resolve({
                                    success: true,
                                    tools: parsed.result?.tools || [],
                                    output: output.trim()
                                });
                            }
                        }
                    } catch (e) {
                        // JSON以外のレスポンス（ログなど）は無視
                    }
                }
            });
        });
        
        server.on('error', (error) => {
            clearTimeout(timeout);
            resolve({
                success: false,
                error: error.message,
                output: output.trim()
            });
        });
        
        server.on('exit', (code) => {
            clearTimeout(timeout);
            if (!responseReceived) {
                resolve({
                    success: false,
                    error: `Server exited with code ${code}`,
                    output: output.trim()
                });
            }
        });
    });
}

async function main() {
    console.log('🔍 Catherine MCP Servers Direct Test');
    console.log('=====================================');
    
    // 環境変数をチェック
    console.log('\n📋 Environment Variables Check:');
    console.log(`NOTION_API_KEY: ${process.env.NOTION_API_KEY ? '✅ Set' : '❌ Not set'}`);
    console.log(`GOOGLE_SERVICE_ACCOUNT_KEY: ${process.env.GOOGLE_SERVICE_ACCOUNT_KEY ? '✅ Set' : '❌ Not set'}`);
    console.log(`GOOGLE_OAUTH_CLIENT_ID: ${process.env.GOOGLE_OAUTH_CLIENT_ID ? '✅ Set' : '❌ Not set'}`);
    console.log(`GMAIL_REFRESH_TOKEN: ${process.env.GMAIL_REFRESH_TOKEN ? '✅ Set' : '❌ Not set'}`);
    
    const testResults = [];
    
    // Google MCPサーバーをテスト
    try {
        const googleResult = await testMCPServer(
            'Google', 
            'node', 
            ['mcp/google/server.js']
        );
        
        if (googleResult.success) {
            console.log(`✅ Google MCP Server: Working`);
            console.log(`📋 Available tools: ${googleResult.tools.length}`);
            googleResult.tools.forEach(tool => {
                console.log(`   - ${tool.name}: ${tool.description}`);
            });
        } else {
            console.log(`❌ Google MCP Server: Failed`);
            console.log(`   Error: ${googleResult.error}`);
        }
        
        testResults.push({ server: 'Google', ...googleResult });
        
    } catch (error) {
        console.log(`❌ Google MCP Server: Exception - ${error.message}`);
        testResults.push({ server: 'Google', success: false, error: error.message });
    }
    
    // Notion MCPサーバーをテスト
    try {
        const notionResult = await testMCPServer(
            'Notion', 
            'node', 
            ['mcp/notion/server.js']
        );
        
        if (notionResult.success) {
            console.log(`✅ Notion MCP Server: Working`);
            console.log(`📋 Available tools: ${notionResult.tools.length}`);
            notionResult.tools.forEach(tool => {
                console.log(`   - ${tool.name}: ${tool.description}`);
            });
        } else {
            console.log(`❌ Notion MCP Server: Failed`);
            console.log(`   Error: ${notionResult.error}`);
        }
        
        testResults.push({ server: 'Notion', ...notionResult });
        
    } catch (error) {
        console.log(`❌ Notion MCP Server: Exception - ${error.message}`);
        testResults.push({ server: 'Notion', success: false, error: error.message });
    }
    
    // 結果サマリー
    console.log('\n📊 Test Summary');
    console.log('================');
    const workingServers = testResults.filter(r => r.success).length;
    const totalServers = testResults.length;
    
    console.log(`Working servers: ${workingServers}/${totalServers}`);
    
    testResults.forEach(result => {
        console.log(`${result.success ? '✅' : '❌'} ${result.server}: ${result.success ? 'OK' : result.error}`);
    });
    
    // 具体的な修正手順
    console.log('\n🔧 Required Fixes');
    console.log('==================');
    
    testResults.forEach(result => {
        if (!result.success) {
            console.log(`\n❌ ${result.server} Server Issues:`);
            console.log(`   Error: ${result.error}`);
            
            if (result.server === 'Google') {
                if (result.error?.includes('GOOGLE_SERVICE_ACCOUNT_KEY not found')) {
                    console.log('   🔧 Fix: GOOGLE_SERVICE_ACCOUNT_KEY environment variable is missing');
                    console.log('   📝 Action: Check .env file for GOOGLE_SERVICE_ACCOUNT_KEY');
                } else if (result.error?.includes('permission')) {
                    console.log('   🔧 Fix: Google Service Account permissions issue');
                    console.log('   📝 Action: Update Google Cloud Console IAM settings');
                }
            }
            
            if (result.server === 'Notion') {
                if (result.error?.includes('unauthorized') || result.error?.includes('API token is invalid')) {
                    console.log('   🔧 Fix: Notion API token is invalid or expired');
                    console.log('   📝 Action: Update NOTION_API_KEY in .env file');
                    console.log('   📝 Check: https://www.notion.so/my-integrations');
                } else if (result.error?.includes('Could not find database')) {
                    console.log('   🔧 Fix: Notion database does not exist');
                    console.log('   📝 Action: Create "Catherine TODOs" database in Notion');
                    console.log('   📝 Action: Share database with the integration');
                }
            }
        }
    });
    
    console.log('\n✨ Test completed!');
}

main().catch(console.error);