/**
 * Catherine統合システムの完全テスト
 * 1. Google Workspace統合テスト
 * 2. Notion統合テスト  
 * 3. MCP接続テスト
 */

require('dotenv').config();

// Google統合テスト
async function testGoogleIntegration() {
    console.log('\n=== Google Workspace統合テスト ===');
    
    try {
        // 1. Gmail確認テスト
        console.log('1. Gmail API テスト...');
        const { google } = require('googleapis');
        
        const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
        const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
        const REFRESH_TOKEN = process.env.GOOGLE_FULL_REFRESH_TOKEN;
        
        if (!CLIENT_ID || !CLIENT_SECRET || !REFRESH_TOKEN) {
            console.error('❌ Google OAuth設定が不完全です');
            return false;
        }
        
        const oAuth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET);
        oAuth2Client.setCredentials({ refresh_token: REFRESH_TOKEN });
        
        const gmail = google.gmail({ version: 'v1', auth: oAuth2Client });
        
        // Gmail接続テスト
        const messages = await gmail.users.messages.list({
            userId: 'me',
            maxResults: 3,
            q: 'in:inbox'
        });
        
        console.log(`✅ Gmail接続成功 - ${messages.data.messages?.length || 0}通のメールを確認`);
        
        // 2. Google Tasks テスト
        console.log('2. Google Tasks API テスト...');
        const tasks = google.tasks({ version: 'v1', auth: oAuth2Client });
        
        const taskLists = await tasks.tasklists.list();
        const defaultTaskList = taskLists.data.items[0].id;
        
        // テストタスク作成
        const testTask = await tasks.tasks.insert({
            tasklist: defaultTaskList,
            requestBody: {
                title: '🤖 Catherine統合テスト - ' + new Date().toLocaleString('ja-JP'),
                notes: 'Catherineシステム統合テスト用のタスクです',
                due: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
            }
        });
        
        console.log(`✅ Google Tasks接続成功 - タスクID: ${testTask.data.id}`);
        
        // 3. Service Account テスト (Sheets, Docs等)
        console.log('3. Google Service Account API テスト...');
        const serviceKey = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
        
        if (!serviceKey) {
            console.error('❌ GOOGLE_SERVICE_ACCOUNT_KEY が設定されていません');
            return false;
        }
        
        const credentials = JSON.parse(serviceKey);
        const auth = new google.auth.GoogleAuth({
            credentials,
            scopes: [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/documents'
            ]
        });
        
        const authClient = await auth.getClient();
        const sheets = google.sheets({ version: 'v4', auth: authClient });
        
        // テストスプレッドシート作成
        const testSheet = await sheets.spreadsheets.create({
            requestBody: {
                properties: {
                    title: `Catherine統合テスト - ${new Date().toLocaleString('ja-JP')}`
                },
                sheets: [{
                    properties: { title: 'テストデータ' }
                }]
            }
        });
        
        console.log(`✅ Google Sheets接続成功 - スプレッドシートID: ${testSheet.data.spreadsheetId}`);
        
        return true;
        
    } catch (error) {
        console.error('❌ Google統合テスト失敗:', error.message);
        return false;
    }
}

// Notion統合テスト
async function testNotionIntegration() {
    console.log('\n=== Notion統合テスト ===');
    
    try {
        const { Client } = require('@notionhq/client');
        const NOTION_API_KEY = process.env.NOTION_API_KEY;
        
        if (!NOTION_API_KEY) {
            console.error('❌ NOTION_API_KEY が設定されていません');
            return false;
        }
        
        const notion = new Client({ auth: NOTION_API_KEY });
        
        // 1. Notion接続テスト
        console.log('1. Notion API接続テスト...');
        const response = await notion.search({
            filter: { value: 'database', property: 'object' },
            query: 'Catherine'
        });
        
        console.log(`✅ Notion接続成功 - ${response.results.length}個のデータベースを発見`);
        
        // 2. データベース作成/確認テスト
        console.log('2. Catherine TODOsデータベース確認...');
        let database = response.results.find(db => 
            db.title && db.title[0]?.plain_text?.includes('Catherine')
        );
        
        if (!database) {
            console.log('📝 Catherine TODOsデータベースが見つからないため、新規作成が必要です');
            console.log('⚠️  手動でNotionページを作成してから再実行してください');
            return false;
        }
        
        console.log(`✅ Catherine TODOsデータベース確認完了 - ID: ${database.id}`);
        
        // 3. テストページ作成
        console.log('3. テストTODO作成...');
        const testPage = await notion.pages.create({
            parent: { database_id: database.id },
            properties: {
                'Title': {
                    title: [{
                        text: { content: `🤖 統合テスト - ${new Date().toLocaleString('ja-JP')}` }
                    }]
                },
                'Status': {
                    select: { name: 'pending' }
                },
                'Priority': {
                    select: { name: 'normal' }
                }
            }
        });
        
        console.log(`✅ NotionテストTODO作成成功 - ページID: ${testPage.id}`);
        
        return true;
        
    } catch (error) {
        console.error('❌ Notion統合テスト失敗:', error.message);
        return false;
    }
}

// MCP接続テスト
async function testMCPConnection() {
    console.log('\n=== MCP接続テスト ===');
    
    try {
        // MCPサーバー存在確認
        const fs = require('fs');
        const path = require('path');
        
        const notionServerPath = path.join(__dirname, 'mcp', 'notion', 'server.js');
        const googleServerPath = path.join(__dirname, 'mcp', 'google', 'server.js');
        
        if (!fs.existsSync(notionServerPath)) {
            console.error('❌ Notion MCPサーバーファイルが見つかりません:', notionServerPath);
            return false;
        }
        
        if (!fs.existsSync(googleServerPath)) {
            console.error('❌ Google MCPサーバーファイルが見つかりません:', googleServerPath);
            return false;
        }
        
        console.log('✅ MCPサーバーファイル確認完了');
        
        // 環境変数確認
        const mcpServersConfig = process.env.MCP_SERVERS;
        if (!mcpServersConfig) {
            console.error('❌ MCP_SERVERS環境変数が設定されていません');
            return false;
        }
        
        const servers = JSON.parse(mcpServersConfig);
        console.log(`✅ MCP設定確認完了 - ${servers.length}個のサーバーが設定済み`);
        
        return true;
        
    } catch (error) {
        console.error('❌ MCP接続テスト失敗:', error.message);
        return false;
    }
}

// 総合テスト実行
async function runFullTest() {
    console.log('🚀 Catherine統合システム - 完全テスト開始');
    console.log('=' .repeat(50));
    
    const results = [];
    
    // 1. Google Workspace テスト
    results.push(await testGoogleIntegration());
    
    // 2. Notion テスト
    results.push(await testNotionIntegration());
    
    // 3. MCP テスト
    results.push(await testMCPConnection());
    
    // 結果サマリー
    console.log('\n' + '='.repeat(50));
    console.log('📊 テスト結果サマリー');
    console.log('=' .repeat(50));
    
    const successCount = results.filter(r => r).length;
    const totalCount = results.length;
    
    if (successCount === totalCount) {
        console.log('🎉 全ての統合テストが成功しました!');
        console.log('✅ Catherineは完全に機能する状態です');
    } else {
        console.log(`⚠️  ${totalCount - successCount}個のテストが失敗しました`);
        console.log('🔧 修正が必要な統合があります');
    }
    
    console.log(`\n成功: ${successCount}/${totalCount}`);
    
    return successCount === totalCount;
}

// 実行
if (require.main === module) {
    runFullTest().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = { testGoogleIntegration, testNotionIntegration, testMCPConnection };