#!/usr/bin/env node
/**
 * 実際のMCP機能をテスト - Google・Notionの実際の操作を確認
 */
const { spawn } = require('child_process');
require('dotenv').config();

async function testMCPFunction(serverName, cmd, args, toolName, params) {
    return new Promise((resolve, reject) => {
        console.log(`\n🧪 Testing ${serverName} - ${toolName}`);
        console.log(`Parameters: ${JSON.stringify(params)}`);
        console.log('-'.repeat(40));
        
        const server = spawn(cmd, args, {
            stdio: ['pipe', 'pipe', 'inherit'],
            cwd: process.cwd()
        });
        
        let responseReceived = false;
        let output = '';
        
        const timeout = setTimeout(() => {
            if (!responseReceived) {
                server.kill();
                resolve({
                    success: false,
                    error: 'Function test timeout (15s)',
                    output: output.trim()
                });
            }
        }, 15000);
        
        server.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        server.on('spawn', () => {
            console.log(`✅ ${serverName} Server spawned`);
            
            setTimeout(() => {
                const request = {
                    jsonrpc: "2.0",
                    id: 1,
                    method: `tools/${toolName}`,
                    params: params
                };
                
                console.log('📨 Sending function request...');
                server.stdin.write(JSON.stringify(request) + '\n');
                
                setTimeout(() => {
                    if (!responseReceived) {
                        server.kill();
                        clearTimeout(timeout);
                        resolve({
                            success: false,
                            error: 'No response to function request',
                            output: output.trim()
                        });
                    }
                }, 8000);
                
            }, 2000);
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
                                    result: parsed.result,
                                    output: output.trim()
                                });
                            }
                        }
                    } catch (e) {
                        // JSON以外の応答は無視
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
    console.log('🔍 Catherine MCP 実機能テスト');
    console.log('============================');
    
    const results = [];
    
    // Google MCP 実機能テスト
    console.log('\n📧 Google Gmail機能テスト');
    try {
        const gmailResult = await testMCPFunction(
            'Google', 'node', ['mcp/google/server.js'],
            'get_gmail_subjects',
            { max_results: 3 }
        );
        
        console.log(gmailResult.success ? '✅ Gmail機能: 動作' : `❌ Gmail機能: ${gmailResult.error}`);
        if (gmailResult.success && gmailResult.result) {
            console.log(`   📨 メール件数: ${gmailResult.result.count || 0}`);
            if (gmailResult.result.messages) {
                gmailResult.result.messages.slice(0, 2).forEach((msg, i) => {
                    console.log(`   ${i+1}. ${msg.subject} (from: ${msg.from})`);
                });
            }
        }
        results.push({ service: 'Google Gmail', ...gmailResult });
    } catch (error) {
        console.log(`❌ Gmail機能: Exception - ${error.message}`);
        results.push({ service: 'Google Gmail', success: false, error: error.message });
    }
    
    console.log('\n📋 Google Tasks機能テスト');
    try {
        const tasksResult = await testMCPFunction(
            'Google', 'node', ['mcp/google/server.js'],
            'create_task',
            { title: 'MCP Test Task', notes: 'Testing MCP integration' }
        );
        
        console.log(tasksResult.success ? '✅ Tasks機能: 動作' : `❌ Tasks機能: ${tasksResult.error}`);
        if (tasksResult.success && tasksResult.result) {
            console.log(`   📋 作成されたタスク: ${tasksResult.result.title}`);
            console.log(`   🆔 タスクID: ${tasksResult.result.task_id}`);
        }
        results.push({ service: 'Google Tasks', ...tasksResult });
    } catch (error) {
        console.log(`❌ Tasks機能: Exception - ${error.message}`);
        results.push({ service: 'Google Tasks', success: false, error: error.message });
    }
    
    console.log('\n📊 Google Sheets機能テスト');
    try {
        const sheetsResult = await testMCPFunction(
            'Google', 'node', ['mcp/google/server.js'],
            'create_sheet',
            { title: 'MCP Test Spreadsheet' }
        );
        
        console.log(sheetsResult.success ? '✅ Sheets機能: 動作' : `❌ Sheets機能: ${sheetsResult.error}`);
        if (sheetsResult.success && sheetsResult.result) {
            console.log(`   📊 作成されたシート: ${sheetsResult.result.message}`);
            console.log(`   🔗 URL: ${sheetsResult.result.spreadsheet_url}`);
        }
        results.push({ service: 'Google Sheets', ...sheetsResult });
    } catch (error) {
        console.log(`❌ Sheets機能: Exception - ${error.message}`);
        results.push({ service: 'Google Sheets', success: false, error: error.message });
    }
    
    // Notion MCP 実機能テスト
    console.log('\n📝 Notion TODO機能テスト');
    try {
        const notionResult = await testMCPFunction(
            'Notion', 'node', ['mcp/notion/server.js'],
            'add_todo',
            { 
                title: 'MCP Test TODO',
                description: 'Testing Notion MCP integration',
                priority: 'normal'
            }
        );
        
        console.log(notionResult.success ? '✅ Notion TODO機能: 動作' : `❌ Notion TODO機能: ${notionResult.error}`);
        if (notionResult.success && notionResult.result) {
            console.log(`   📝 作成されたTODO: ${notionResult.result.details?.title}`);
            console.log(`   🔗 URL: ${notionResult.result.url}`);
        }
        results.push({ service: 'Notion TODO', ...notionResult });
    } catch (error) {
        console.log(`❌ Notion TODO機能: Exception - ${error.message}`);
        results.push({ service: 'Notion TODO', success: false, error: error.message });
    }
    
    console.log('\n🔍 Notion検索機能テスト');
    try {
        const searchResult = await testMCPFunction(
            'Notion', 'node', ['mcp/notion/server.js'],
            'search',
            { query: 'TODO' }
        );
        
        console.log(searchResult.success ? '✅ Notion検索機能: 動作' : `❌ Notion検索機能: ${searchResult.error}`);
        if (searchResult.success && searchResult.result) {
            console.log(`   🔍 検索結果: ${searchResult.result.count || 0}件`);
            if (searchResult.result.results) {
                searchResult.result.results.slice(0, 2).forEach((item, i) => {
                    console.log(`   ${i+1}. ${item.title} (${item.type})`);
                });
            }
        }
        results.push({ service: 'Notion Search', ...searchResult });
    } catch (error) {
        console.log(`❌ Notion検索機能: Exception - ${error.message}`);
        results.push({ service: 'Notion Search', success: false, error: error.message });
    }
    
    // 結果集計
    console.log('\n📊 実機能テスト結果まとめ');
    console.log('================================');
    
    const workingFunctions = results.filter(r => r.success).length;
    const totalFunctions = results.length;
    
    console.log(`動作機能: ${workingFunctions}/${totalFunctions}`);
    console.log('\n詳細:');
    
    results.forEach(result => {
        const status = result.success ? '✅ 動作' : '❌ エラー';
        const detail = result.success ? 'OK' : result.error;
        console.log(`${status} ${result.service}: ${detail}`);
    });
    
    // 具体的な問題と解決策
    console.log('\n🔧 発見された問題と解決策');
    console.log('============================');
    
    const failedResults = results.filter(r => !r.success);
    
    if (failedResults.length === 0) {
        console.log('🎉 全ての機能が正常に動作しています！');
    } else {
        failedResults.forEach(result => {
            console.log(`\n❌ ${result.service}:`);
            console.log(`   エラー: ${result.error}`);
            
            // Google関連のエラー分析
            if (result.service.includes('Google')) {
                if (result.error?.includes('permission') || result.error?.includes('unauthorized')) {
                    console.log('   🔧 修正方法: Google API権限を確認');
                    console.log('   📝 実行: Google Cloud Console > IAM で権限を追加');
                } else if (result.error?.includes('invalid_grant')) {
                    console.log('   🔧 修正方法: OAuth認証を更新');
                    console.log('   📝 実行: node get-full-google-token.js');
                }
            }
            
            // Notion関連のエラー分析
            if (result.service.includes('Notion')) {
                if (result.error?.includes('unauthorized') || result.error?.includes('invalid')) {
                    console.log('   🔧 修正方法: Notion API権限を確認');
                    console.log('   📝 実行: Notion統合設定でAPIキーを更新');
                } else if (result.error?.includes('database')) {
                    console.log('   🔧 修正方法: Notionデータベースを作成');
                    console.log('   📝 実行: Notion.soで"Catherine TODOs"データベースを作成');
                }
            }
        });
    }
    
    console.log('\n✨ 実機能テスト完了!');
    console.log(`最終判定: ${workingFunctions === totalFunctions ? '🎉 完全動作' : '⚠️ 部分動作'}`);
}

main().catch(console.error);