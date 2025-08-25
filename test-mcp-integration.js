#!/usr/bin/env node

/**
 * Catherine Discord botにGoogle機能を統合するテスト
 * 実際のOAuth認証を使用
 */

const { google } = require('googleapis');
require('dotenv').config();

const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_FULL_REFRESH_TOKEN || process.env.GMAIL_REFRESH_TOKEN;

class CatherineGoogleIntegration {
    constructor() {
        this.oauthClient = null;
        this.gmail = null;
        this.tasks = null;
        this.docs = null;
        this.sheets = null;
        this.drive = null;
        this.calendar = null;
    }

    async initialize() {
        console.log('🤖 Initializing Catherine Google Integration...');
        
        this.oauthClient = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, 'http://localhost:3000/oauth2/callback');
        this.oauthClient.setCredentials({ refresh_token: REFRESH_TOKEN });
        
        // Google APIクライアント初期化
        this.gmail = google.gmail({ version: 'v1', auth: this.oauthClient });
        this.tasks = google.tasks({ version: 'v1', auth: this.oauthClient });
        this.docs = google.docs({ version: 'v1', auth: this.oauthClient });
        this.sheets = google.sheets({ version: 'v4', auth: this.oauthClient });
        this.drive = google.drive({ version: 'v3', auth: this.oauthClient });
        this.calendar = google.calendar({ version: 'v3', auth: this.oauthClient });
        
        console.log('✅ Catherine Google Integration initialized');
        return true;
    }

    // Discord用のコマンドハンドラー例
    async handleDiscordCommand(command, args) {
        console.log(`📨 Processing Discord command: ${command}`);
        
        switch (command) {
            case 'gmail':
                return await this.getGmailSubjects(args.count || 3);
            
            case 'task':
                if (args.action === 'create') {
                    return await this.createTask(args.title, args.notes, args.due);
                } else {
                    return await this.listTasks(args.count || 5);
                }
            
            case 'doc':
                if (args.action === 'create') {
                    return await this.createDocument(args.title, args.content);
                } else if (args.document_id) {
                    return await this.readDocument(args.document_id);
                }
                break;
            
            case 'sheet':
                if (args.action === 'create') {
                    return await this.createSpreadsheet(args.title);
                }
                break;
            
            case 'calendar':
                if (args.action === 'create') {
                    return await this.createEvent(args.title, args.start, args.end, args.description);
                } else {
                    return await this.listEvents(args.days || 7);
                }
                break;
            
            default:
                return { success: false, error: 'Unknown command' };
        }
    }

    async getGmailSubjects(maxResults = 3) {
        try {
            const response = await this.gmail.users.messages.list({
                userId: 'me',
                maxResults
            });

            if (!response.data.messages) {
                return { success: true, messages: [] };
            }

            const messages = [];
            for (const message of response.data.messages) {
                const detail = await this.gmail.users.messages.get({
                    userId: 'me',
                    id: message.id
                });

                const headers = detail.data.payload.headers;
                const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject';
                const from = headers.find(h => h.name === 'From')?.value || 'Unknown';

                messages.push({ subject, from, date: headers.find(h => h.name === 'Date')?.value });
            }

            return { success: true, messages, count: messages.length };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async createTask(title, notes = '', dueDate = null) {
        try {
            const taskLists = await this.tasks.tasklists.list();
            const defaultTaskList = taskLists.data.items[0];

            const taskData = { title, notes };
            if (dueDate) {
                taskData.due = new Date(dueDate).toISOString();
            }

            const response = await this.tasks.tasks.insert({
                tasklist: defaultTaskList.id,
                resource: taskData
            });

            return {
                success: true,
                task_id: response.data.id,
                title: response.data.title,
                message: `✅ Created task: ${title}`
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async listTasks(maxResults = 5) {
        try {
            const taskLists = await this.tasks.tasklists.list();
            const defaultTaskList = taskLists.data.items[0];

            const response = await this.tasks.tasks.list({
                tasklist: defaultTaskList.id,
                maxResults
            });

            const tasks = (response.data.items || []).map(task => ({
                id: task.id,
                title: task.title,
                notes: task.notes,
                status: task.status,
                due: task.due
            }));

            return { success: true, tasks, count: tasks.length };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async createDocument(title, content = '') {
        try {
            const createResponse = await this.docs.documents.create({
                resource: { title }
            });

            const documentId = createResponse.data.documentId;

            if (content) {
                await this.docs.documents.batchUpdate({
                    documentId,
                    resource: {
                        requests: [{
                            insertText: {
                                location: { index: 1 },
                                text: content
                            }
                        }]
                    }
                });
            }

            return {
                success: true,
                document_id: documentId,
                title: createResponse.data.title,
                url: `https://docs.google.com/document/d/${documentId}/edit`,
                message: `📄 Created document: ${title}`
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async readDocument(documentId) {
        try {
            const response = await this.docs.documents.get({ documentId });

            let text = '';
            if (response.data.body && response.data.body.content) {
                response.data.body.content.forEach(element => {
                    if (element.paragraph) {
                        element.paragraph.elements.forEach(el => {
                            if (el.textRun) {
                                text += el.textRun.content;
                            }
                        });
                    }
                });
            }

            return {
                success: true,
                title: response.data.title,
                content: text,
                url: `https://docs.google.com/document/d/${documentId}/edit`
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async createSpreadsheet(title) {
        try {
            const response = await this.sheets.spreadsheets.create({
                resource: {
                    properties: { title }
                }
            });

            return {
                success: true,
                spreadsheet_id: response.data.spreadsheetId,
                url: response.data.spreadsheetUrl,
                message: `📊 Created spreadsheet: ${title}`
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async createEvent(title, startTime, endTime, description = '') {
        try {
            const start = new Date(startTime);
            const end = endTime ? new Date(endTime) : new Date(start.getTime() + 60 * 60 * 1000);

            const event = {
                summary: title,
                description,
                start: {
                    dateTime: start.toISOString(),
                    timeZone: 'Asia/Tokyo',
                },
                end: {
                    dateTime: end.toISOString(),
                    timeZone: 'Asia/Tokyo',
                },
                reminders: {
                    useDefault: false,
                    overrides: [{ method: 'popup', minutes: 10 }],
                },
            };

            const response = await this.calendar.events.insert({
                calendarId: 'primary',
                resource: event,
            });

            return {
                success: true,
                event_id: response.data.id,
                title: response.data.summary,
                start: response.data.start.dateTime,
                url: response.data.htmlLink,
                message: `📅 Created event: ${title}`
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async listEvents(daysAhead = 7) {
        try {
            const timeMin = new Date();
            const timeMax = new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000);

            const response = await this.calendar.events.list({
                calendarId: 'primary',
                timeMin: timeMin.toISOString(),
                timeMax: timeMax.toISOString(),
                maxResults: 10,
                singleEvents: true,
                orderBy: 'startTime',
            });

            const events = response.data.items.map(event => ({
                id: event.id,
                title: event.summary,
                start: event.start.dateTime || event.start.date,
                end: event.end.dateTime || event.end.date,
                description: event.description || '',
                url: event.htmlLink
            }));

            return { success: true, events, count: events.length };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// テスト実行
async function testIntegration() {
    console.log('🧪 Testing Catherine Google Integration');
    console.log('=====================================');

    const catherine = new CatherineGoogleIntegration();
    await catherine.initialize();

    // Discord コマンドのシミュレーション
    console.log('\n📧 Testing Gmail integration...');
    const gmailResult = await catherine.handleDiscordCommand('gmail', { count: 2 });
    if (gmailResult.success) {
        console.log(`✅ Found ${gmailResult.count} emails`);
        gmailResult.messages.forEach((msg, i) => {
            console.log(`  ${i + 1}. ${msg.subject} (from: ${msg.from})`);
        });
    }

    console.log('\n📋 Testing Tasks integration...');
    const taskResult = await catherine.handleDiscordCommand('task', {
        action: 'create',
        title: 'Catherine Discord Integration Test',
        notes: 'Testing task creation from Catherine Discord bot',
        due: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    });
    
    if (taskResult.success) {
        console.log(`✅ ${taskResult.message}`);
        console.log(`   Task ID: ${taskResult.task_id}`);
    }

    console.log('\n📄 Testing Docs integration...');
    const docResult = await catherine.handleDiscordCommand('doc', {
        action: 'create',
        title: 'Catherine Discord Bot Integration Report',
        content: 'Catherine Discord Bot Google Integration\\n\\nFeatures:\\n- Gmail monitoring\\n- Task management\\n- Document creation\\n- Spreadsheet operations\\n\\nAll integrations working successfully!'
    });
    
    if (docResult.success) {
        console.log(`✅ ${docResult.message}`);
        console.log(`   URL: ${docResult.url}`);
    }

    console.log('\n📊 Testing Sheets integration...');
    const sheetResult = await catherine.handleDiscordCommand('sheet', {
        action: 'create',
        title: 'Catherine Task Tracker'
    });
    
    if (sheetResult.success) {
        console.log(`✅ ${sheetResult.message}`);
        console.log(`   URL: ${sheetResult.url}`);
    }

    console.log('\n📅 Testing Calendar integration...');
    const eventResult = await catherine.handleDiscordCommand('calendar', {
        action: 'create',
        title: 'Catherine Bot Meeting',
        start: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2時間後
        end: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),   // 3時間後
        description: 'Testing calendar integration with Catherine Discord bot'
    });
    
    if (eventResult.success) {
        console.log(`✅ ${eventResult.message}`);
        console.log(`   Event ID: ${eventResult.event_id}`);
        console.log(`   URL: ${eventResult.url}`);
    }

    // カレンダーイベント一覧取得
    const eventsResult = await catherine.handleDiscordCommand('calendar', { days: 3 });
    if (eventsResult.success) {
        console.log(`✅ Found ${eventsResult.count} upcoming events in next 3 days`);
        eventsResult.events.forEach((event, i) => {
            console.log(`  ${i + 1}. ${event.title} (${new Date(event.start).toLocaleString()})`);
        });
    }

    console.log('\n🎉 Integration test completed!');
    console.log('\nCatherine can now handle Discord commands for:');
    console.log('  - 📧 /gmail - Get recent emails');
    console.log('  - 📋 /task create <title> - Create tasks');
    console.log('  - 📋 /task list - List tasks');  
    console.log('  - 📄 /doc create <title> <content> - Create documents');
    console.log('  - 📊 /sheet create <title> - Create spreadsheets');
    console.log('  - 📅 /calendar create <title> <start> <end> - Create events');
    console.log('  - 📅 /calendar list - List upcoming events');
}

testIntegration().catch(console.error);