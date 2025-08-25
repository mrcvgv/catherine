#!/usr/bin/env node

/**
 * Gmail件名取得 と Google Tasks追加 のテストスクリプト
 * 
 * 必要な環境変数:
 * - GOOGLE_OAUTH_CLIENT_ID
 * - GOOGLE_OAUTH_CLIENT_SECRET  
 * - GMAIL_REFRESH_TOKEN
 */

const { google } = require('googleapis');
require('dotenv').config();

const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GMAIL_REFRESH_TOKEN;

if (!CLIENT_ID || !CLIENT_SECRET || !REFRESH_TOKEN) {
    console.error('❌ Missing required environment variables:');
    if (!CLIENT_ID) console.error('  - GOOGLE_OAUTH_CLIENT_ID');
    if (!CLIENT_SECRET) console.error('  - GOOGLE_OAUTH_CLIENT_SECRET');
    if (!REFRESH_TOKEN) console.error('  - GMAIL_REFRESH_TOKEN');
    console.log('\n💡 First run get-gmail-tasks-token.js to obtain tokens');
    process.exit(1);
}

async function setupAuth() {
    const oauth2Client = new google.auth.OAuth2(
        CLIENT_ID,
        CLIENT_SECRET,
        process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/oauth2/callback'
    );

    oauth2Client.setCredentials({
        refresh_token: REFRESH_TOKEN
    });

    return oauth2Client;
}

async function testGmailSubjects(auth) {
    console.log('\n📧 Testing Gmail subject retrieval...');
    
    try {
        const gmail = google.gmail({ version: 'v1', auth });
        
        // 最新の5件のメールを取得
        const response = await gmail.users.messages.list({
            userId: 'me',
            maxResults: 5,
            q: 'in:inbox'  // 受信箱のメールのみ
        });

        const messages = response.data.messages;
        
        if (!messages || messages.length === 0) {
            console.log('📭 No messages found in inbox');
            return;
        }

        console.log(`✅ Found ${messages.length} recent emails:`);
        console.log('─'.repeat(80));

        for (const message of messages) {
            try {
                const emailData = await gmail.users.messages.get({
                    userId: 'me',
                    id: message.id,
                    format: 'metadata',
                    metadataHeaders: ['From', 'Subject', 'Date']
                });

                const headers = emailData.data.payload.headers;
                const subject = headers.find(h => h.name === 'Subject')?.value || '(No Subject)';
                const from = headers.find(h => h.name === 'From')?.value || '(Unknown Sender)';
                const date = headers.find(h => h.name === 'Date')?.value || '(Unknown Date)';

                console.log(`📨 From: ${from}`);
                console.log(`📋 Subject: ${subject}`);
                console.log(`📅 Date: ${date}`);
                console.log('─'.repeat(40));
                
            } catch (error) {
                console.error(`❌ Error getting message ${message.id}:`, error.message);
            }
        }

    } catch (error) {
        console.error('❌ Gmail API Error:', error.message);
        if (error.code === 401) {
            console.log('💡 Authorization expired. Try running get-gmail-tasks-token.js again');
        }
    }
}

async function testGoogleTasks(auth) {
    console.log('\n✅ Testing Google Tasks creation...');
    
    try {
        const tasks = google.tasks({ version: 'v1', auth });
        
        // タスクリスト一覧を取得
        console.log('📋 Getting task lists...');
        const taskLists = await tasks.tasklists.list();
        
        if (!taskLists.data.items || taskLists.data.items.length === 0) {
            console.log('📝 No task lists found. Creating default list...');
            
            const newList = await tasks.tasklists.insert({
                requestBody: {
                    title: 'Catherine Tasks'
                }
            });
            
            console.log(`✅ Created task list: ${newList.data.title} (${newList.data.id})`);
            taskLists.data.items = [newList.data];
        }

        const taskListId = taskLists.data.items[0].id;
        const taskListTitle = taskLists.data.items[0].title;
        
        console.log(`📁 Using task list: "${taskListTitle}" (${taskListId})`);
        
        // テストタスクを作成
        const testTasks = [
            {
                title: '🤖 Catherine Test Task 1',
                notes: 'This is a test task created by Catherine bot\n\nCreated at: ' + new Date().toISOString(),
                due: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 明日
            },
            {
                title: '📋 Catherine TODO Integration Test',
                notes: 'Testing integration between Catherine and Google Tasks\n\nFeatures:\n- Discord bot integration\n- Natural language processing\n- Automatic task creation',
                due: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 来週
            }
        ];

        console.log('➕ Creating test tasks...');
        
        for (const taskData of testTasks) {
            try {
                const newTask = await tasks.tasks.insert({
                    tasklist: taskListId,
                    requestBody: taskData
                });
                
                console.log(`✅ Created task: "${newTask.data.title}"`);
                console.log(`   📝 Notes: ${taskData.notes.split('\n')[0]}`);
                console.log(`   📅 Due: ${taskData.due}`);
                console.log(`   🔗 Task ID: ${newTask.data.id}`);
                console.log();
                
            } catch (error) {
                console.error(`❌ Failed to create task "${taskData.title}":`, error.message);
            }
        }

        // 既存のタスク一覧を表示
        console.log('📋 Current tasks in list:');
        const existingTasks = await tasks.tasks.list({
            tasklist: taskListId,
            maxResults: 10
        });

        if (existingTasks.data.items && existingTasks.data.items.length > 0) {
            existingTasks.data.items.forEach((task, index) => {
                const status = task.status === 'completed' ? '✅' : '⏳';
                const due = task.due ? `Due: ${new Date(task.due).toLocaleDateString()}` : 'No due date';
                console.log(`${status} ${index + 1}. ${task.title} (${due})`);
            });
        } else {
            console.log('📭 No tasks found in the list');
        }

    } catch (error) {
        console.error('❌ Tasks API Error:', error.message);
        if (error.code === 401) {
            console.log('💡 Authorization expired. Try running get-gmail-tasks-token.js again');
        }
    }
}

async function main() {
    console.log('🚀 Starting Gmail and Google Tasks integration test...\n');
    console.log('🔧 Configuration:');
    console.log(`   Client ID: ${CLIENT_ID?.substring(0, 20)}...`);
    console.log(`   Has Refresh Token: ${REFRESH_TOKEN ? 'Yes' : 'No'}`);
    
    try {
        const auth = await setupAuth();
        
        // Test both APIs
        await testGmailSubjects(auth);
        await testGoogleTasks(auth);
        
        console.log('\n🎉 Integration test completed successfully!');
        console.log('\n💡 Next steps:');
        console.log('   1. Integrate these functions into Catherine bot');
        console.log('   2. Add Gmail monitoring for new emails');
        console.log('   3. Connect Catherine TODO system with Google Tasks');
        console.log('   4. Enable voice commands for task management');
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
        console.log('\n🔧 Troubleshooting:');
        console.log('   1. Check that all environment variables are set');
        console.log('   2. Verify OAuth tokens are valid');
        console.log('   3. Ensure Google APIs are enabled in your project');
        console.log('   4. Try running get-gmail-tasks-token.js again');
    }
}

// Handle Ctrl+C
process.on('SIGINT', () => {
    console.log('\n\n👋 Test cancelled');
    process.exit(0);
});

main().catch(console.error);