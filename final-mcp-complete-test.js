#!/usr/bin/env node
/**
 * Catherine MCP最終統合テスト
 * 全てのMCPサービスが正しく接続され、実際に機能するか検証
 */
const { spawn } = require('child_process');
require('dotenv').config();

// テスト結果を格納
const testResults = {
  google: {},
  notion: {},
  integration: {},
  timestamp: new Date().toISOString()
};

// MCPサーバーと通信する関数
async function callMCPFunction(serverName, cmd, args, toolName, params) {
  return new Promise((resolve, reject) => {
    const server = spawn(cmd, args, {
      stdio: ['pipe', 'pipe', 'inherit'],
      cwd: process.cwd()
    });
    
    let responseReceived = false;
    let output = '';
    
    const timeout = setTimeout(() => {
      if (!responseReceived) {
        server.kill();
        resolve({ success: false, error: 'Timeout (15s)' });
      }
    }, 15000);
    
    server.on('spawn', () => {
      setTimeout(() => {
        const request = {
          jsonrpc: "2.0",
          id: 1,
          method: `tools/${toolName}`,
          params: params
        };
        server.stdin.write(JSON.stringify(request) + '\n');
      }, 2000);
    });
    
    server.stdout.on('data', (data) => {
      output += data.toString();
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
                resolve({ success: false, error: parsed.error.message });
              } else {
                resolve({ success: true, result: parsed.result });
              }
            }
          } catch (e) {
            // Ignore non-JSON
          }
        }
      });
    });
    
    server.on('error', (error) => {
      clearTimeout(timeout);
      resolve({ success: false, error: error.message });
    });
    
    server.on('exit', (code) => {
      if (!responseReceived) {
        clearTimeout(timeout);
        resolve({ success: false, error: `Exit code ${code}` });
      }
    });
  });
}

// 実際のDiscord統合をシミュレート
async function simulateDiscordIntegration() {
  console.log('\n🤖 Discord統合シミュレーション');
  console.log('========================================');
  
  // ユーザーコマンド例
  const userCommand = "明日の会議用にGoogleドキュメント作成して、スプレッドシートで参加者リスト作って、NotionのTODOに高優先度で追加して";
  console.log(`📨 ユーザー: "${userCommand}"`);
  console.log('\n処理中...\n');
  
  const integrationSteps = [];
  
  // 1. Google Docs作成
  console.log('1️⃣ Google Docs作成中...');
  const docsResult = await callMCPFunction(
    'Google', 'node', ['mcp/google/server.js'],
    'create_doc',
    { title: '会議資料 - ' + new Date().toLocaleDateString('ja-JP'), content: '# 会議アジェンダ\n\n## 議題\n1. \n2. \n3. ' }
  );
  integrationSteps.push({ service: 'Google Docs', ...docsResult });
  console.log(docsResult.success ? '✅ Docs作成成功' : `❌ Docs作成失敗: ${docsResult.error}`);
  
  // 2. Google Sheets作成
  console.log('\n2️⃣ Google Sheets作成中...');
  const sheetsResult = await callMCPFunction(
    'Google', 'node', ['mcp/google/server.js'],
    'create_sheet',
    { title: '参加者リスト - ' + new Date().toLocaleDateString('ja-JP') }
  );
  integrationSteps.push({ service: 'Google Sheets', ...sheetsResult });
  console.log(sheetsResult.success ? '✅ Sheets作成成功' : `❌ Sheets作成失敗: ${sheetsResult.error}`);
  
  // 3. Notion TODO追加
  console.log('\n3️⃣ Notion TODO追加中...');
  const notionResult = await callMCPFunction(
    'Notion', 'node', ['mcp/notion/server.js'],
    'add_todo',
    { 
      title: '会議準備完了確認',
      description: '明日の会議用資料とリストの最終確認',
      priority: 'high',
      due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    }
  );
  integrationSteps.push({ service: 'Notion TODO', ...notionResult });
  console.log(notionResult.success ? '✅ TODO追加成功' : `❌ TODO追加失敗: ${notionResult.error}`);
  
  // 結果まとめ
  const successCount = integrationSteps.filter(s => s.success).length;
  const totalCount = integrationSteps.length;
  
  console.log('\n📊 統合処理結果:');
  console.log(`成功: ${successCount}/${totalCount}`);
  
  if (successCount === totalCount) {
    console.log('\n🎉 Catherine応答:');
    console.log('「ふふ、会議の準備は整えてあげたよ」');
    if (docsResult.result?.url) {
      console.log(`📄 [会議資料](${docsResult.result.url})`);
    }
    if (sheetsResult.result?.spreadsheet_url) {
      console.log(`📊 [参加者リスト](${sheetsResult.result.spreadsheet_url})`);
    }
    if (notionResult.result?.url) {
      console.log(`📝 [TODO](${notionResult.result.url})`);
    }
    console.log('「あとは内容をちゃんと作りなさいね」');
  }
  
  return integrationSteps;
}

// メイン実行
async function main() {
  console.log('🔍 Catherine MCP 最終統合確認テスト');
  console.log('=====================================');
  console.log('実行時刻:', new Date().toLocaleString('ja-JP'));
  
  // 1. Google サービステスト
  console.log('\n📧 Google サービステスト');
  console.log('------------------------');
  
  // Gmail
  console.log('Testing Gmail...');
  testResults.google.gmail = await callMCPFunction(
    'Google', 'node', ['mcp/google/server.js'],
    'get_gmail_subjects',
    { max_results: 1 }
  );
  console.log(`Gmail: ${testResults.google.gmail.success ? '✅' : '❌'}`);
  
  // Tasks
  console.log('Testing Tasks...');
  testResults.google.tasks = await callMCPFunction(
    'Google', 'node', ['mcp/google/server.js'],
    'list_tasks',
    { max_results: 1 }
  );
  console.log(`Tasks: ${testResults.google.tasks.success ? '✅' : '❌'}`);
  
  // Sheets
  console.log('Testing Sheets...');
  testResults.google.sheets = await callMCPFunction(
    'Google', 'node', ['mcp/google/server.js'],
    'create_sheet',
    { title: 'MCP Final Test - ' + Date.now() }
  );
  console.log(`Sheets: ${testResults.google.sheets.success ? '✅' : '❌'}`);
  
  // 2. Notion サービステスト
  console.log('\n📝 Notion サービステスト');
  console.log('------------------------');
  
  // TODO追加
  console.log('Testing TODO creation...');
  testResults.notion.todo = await callMCPFunction(
    'Notion', 'node', ['mcp/notion/server.js'],
    'add_todo',
    { title: 'Final Test - ' + Date.now(), priority: 'normal' }
  );
  console.log(`TODO作成: ${testResults.notion.todo.success ? '✅' : '❌'}`);
  
  // リスト取得
  console.log('Testing TODO list...');
  testResults.notion.list = await callMCPFunction(
    'Notion', 'node', ['mcp/notion/server.js'],
    'list_todos',
    { status: '未着手' }
  );
  console.log(`TODOリスト: ${testResults.notion.list.success ? '✅' : '❌'}`);
  
  // 3. 統合シミュレーション
  testResults.integration = await simulateDiscordIntegration();
  
  // 4. 最終レポート
  console.log('\n' + '='.repeat(50));
  console.log('📊 最終MCP接続状況レポート');
  console.log('='.repeat(50));
  
  // Google集計
  const googleServices = Object.keys(testResults.google);
  const googleWorking = googleServices.filter(s => testResults.google[s].success).length;
  console.log(`\n✅ Google MCP: ${googleWorking}/${googleServices.length} サービス動作`);
  googleServices.forEach(service => {
    const status = testResults.google[service].success ? '✅' : '❌';
    console.log(`   ${status} ${service}`);
  });
  
  // Notion集計
  const notionServices = Object.keys(testResults.notion);
  const notionWorking = notionServices.filter(s => testResults.notion[s].success).length;
  console.log(`\n✅ Notion MCP: ${notionWorking}/${notionServices.length} サービス動作`);
  notionServices.forEach(service => {
    const status = testResults.notion[service].success ? '✅' : '❌';
    console.log(`   ${status} ${service}`);
  });
  
  // 統合集計
  const integrationWorking = testResults.integration.filter(s => s.success).length;
  console.log(`\n✅ 統合処理: ${integrationWorking}/${testResults.integration.length} ステップ成功`);
  
  // 総合判定
  const totalServices = googleServices.length + notionServices.length;
  const totalWorking = googleWorking + notionWorking;
  const percentage = Math.round((totalWorking / totalServices) * 100);
  
  console.log('\n' + '='.repeat(50));
  console.log('🎯 総合判定');
  console.log('='.repeat(50));
  console.log(`MCPサービス動作率: ${percentage}%`);
  console.log(`統合処理成功率: ${Math.round((integrationWorking / testResults.integration.length) * 100)}%`);
  
  if (percentage === 100 && integrationWorking === testResults.integration.length) {
    console.log('\n🎉 結論: Catherine MCP統合は完全に動作しています！');
    console.log('全てのサービスが正常に接続され、実用可能な状態です。');
  } else if (percentage >= 80) {
    console.log('\n✅ 結論: Catherine MCP統合はほぼ完全に動作しています。');
    console.log('主要機能は全て利用可能です。');
  } else {
    console.log('\n⚠️ 結論: 一部のMCPサービスに問題があります。');
    console.log('設定の見直しが必要です。');
  }
  
  // 結果をファイルに保存
  const fs = require('fs');
  fs.writeFileSync(
    'mcp-final-test-results.json',
    JSON.stringify(testResults, null, 2)
  );
  console.log('\n📄 詳細な結果は mcp-final-test-results.json に保存されました。');
}

// 実行
main().catch(console.error);