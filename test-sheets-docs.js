#!/usr/bin/env node

/**
 * Google Sheets と Google Docs のテストスクリプト
 * 既存のOAuth認証を使用してスプレッドシートとドキュメントを操作
 */

const { google } = require('googleapis');
require('dotenv').config();

const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_FULL_REFRESH_TOKEN || process.env.GMAIL_REFRESH_TOKEN;

if (!CLIENT_ID || !CLIENT_SECRET || !REFRESH_TOKEN) {
    console.error('Missing required environment variables');
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

async function testGoogleSheets(auth) {
    console.log('\nTesting Google Sheets...');
    
    try {
        const sheets = google.sheets({ version: 'v4', auth });
        
        // 新しいスプレッドシートを作成
        console.log('Creating new spreadsheet...');
        const createResponse = await sheets.spreadsheets.create({
            resource: {
                properties: {
                    title: `Catherine Test Spreadsheet - ${new Date().toISOString().split('T')[0]}`
                }
            }
        });

        const spreadsheetId = createResponse.data.spreadsheetId;
        const spreadsheetUrl = createResponse.data.spreadsheetUrl;
        
        console.log(`Created spreadsheet: ${createResponse.data.properties.title}`);
        console.log(`Spreadsheet ID: ${spreadsheetId}`);
        console.log(`URL: ${spreadsheetUrl}`);

        // ヘッダー行を追加
        console.log('Adding header data...');
        const headerValues = [
            ['Task', 'Priority', 'Status', 'Created', 'Due Date', 'Assignee', 'Notes']
        ];

        await sheets.spreadsheets.values.update({
            spreadsheetId,
            range: 'A1:G1',
            valueInputOption: 'RAW',
            resource: {
                values: headerValues
            }
        });

        // サンプルデータを追加
        console.log('Adding sample data...');
        const sampleData = [
            ['Review Catherine MCP Integration', 'High', 'In Progress', '2025-08-25', '2025-08-26', 'mrc', 'Check all MCP servers'],
            ['Update Discord Commands', 'Normal', 'Pending', '2025-08-25', '2025-08-27', 'supy', 'Add new slash commands'],
            ['Gmail Integration Testing', 'Low', 'Completed', '2025-08-25', '2025-09-01', 'Catherine Bot', 'OAuth setup complete'],
            ['Google Sheets Integration', 'High', 'In Progress', '2025-08-25', '2025-08-25', 'Catherine Bot', 'Testing spreadsheet operations']
        ];

        await sheets.spreadsheets.values.update({
            spreadsheetId,
            range: 'A2:G5',
            valueInputOption: 'RAW',
            resource: {
                values: sampleData
            }
        });

        // データを読み取り
        console.log('Reading data back...');
        const readResponse = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: 'A1:G5'
        });

        const values = readResponse.data.values;
        if (values && values.length > 0) {
            console.log('Spreadsheet data:');
            values.forEach((row, index) => {
                if (index === 0) {
                    console.log('  Headers:', row.join(' | '));
                    console.log('  ' + '-'.repeat(80));
                } else {
                    console.log(`  ${row[0]} | ${row[1]} | ${row[2]} | Due: ${row[4]}`);
                }
            });
        }

        // セルの書式設定
        console.log('Applying formatting...');
        await sheets.spreadsheets.batchUpdate({
            spreadsheetId,
            resource: {
                requests: [
                    {
                        repeatCell: {
                            range: {
                                startRowIndex: 0,
                                endRowIndex: 1
                            },
                            cell: {
                                userEnteredFormat: {
                                    backgroundColor: { red: 0.2, green: 0.6, blue: 0.9 },
                                    textFormat: { bold: true, foregroundColor: { red: 1, green: 1, blue: 1 } }
                                }
                            },
                            fields: 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }
                ]
            }
        });

        return { spreadsheetId, spreadsheetUrl, success: true };
        
    } catch (error) {
        console.error('Google Sheets Error:', error.message);
        return { success: false, error: error.message };
    }
}

async function testGoogleDocs(auth) {
    console.log('\nTesting Google Docs...');
    
    try {
        const docs = google.docs({ version: 'v1', auth });
        
        // 新しいドキュメントを作成
        console.log('Creating new document...');
        const createResponse = await docs.documents.create({
            resource: {
                title: `Catherine Bot Report - ${new Date().toISOString().split('T')[0]}`
            }
        });

        const documentId = createResponse.data.documentId;
        const title = createResponse.data.title;
        
        console.log(`Created document: ${title}`);
        console.log(`Document ID: ${documentId}`);
        console.log(`URL: https://docs.google.com/document/d/${documentId}/edit`);

        // ドキュメントにコンテンツを追加
        console.log('Adding content to document...');
        const content = [
            'Catherine Bot Integration Report',
            '',
            'Generated on: ' + new Date().toLocaleString(),
            '',
            '## Current Status',
            '',
            '✅ Gmail API Integration: Complete',
            '✅ Google Tasks Integration: Complete', 
            '✅ Google Calendar Integration: Complete',
            '✅ Google Drive Integration: Complete',
            '🔄 Google Sheets Integration: Testing',
            '🔄 Google Docs Integration: Testing',
            '',
            '## Recent Tasks',
            '',
            '1. Review MCP Integration - High Priority',
            '2. Update Discord Commands - Normal Priority',
            '3. Gmail Integration Testing - Completed',
            '4. Google Sheets Testing - In Progress',
            '',
            '## Next Steps',
            '',
            '- Integrate all Google services with Discord bot',
            '- Add natural language processing for commands',
            '- Implement automated reporting features',
            '- Set up monitoring and notifications',
            '',
            '## Technical Notes',
            '',
            'OAuth 2.0 authentication is working properly for all Google APIs.',
            'Service Account authentication is available for server-to-server operations.',
            'MCP (Model Context Protocol) integration provides seamless access to all services.',
            '',
            '---',
            '',
            'This report was automatically generated by Catherine Bot.',
            'For questions, contact the development team.'
        ];

        // テキストを挿入
        await docs.documents.batchUpdate({
            documentId,
            resource: {
                requests: content.map((line, index) => ({
                    insertText: {
                        location: { index: index === 0 ? 1 : undefined },
                        text: line + '\n'
                    }
                }))
            }
        });

        // ドキュメントの内容を読み取り
        console.log('Reading document content...');
        const readResponse = await docs.documents.get({
            documentId
        });

        const docContent = readResponse.data.body.content;
        console.log('Document created successfully with content:');
        console.log(`  Title: ${readResponse.data.title}`);
        console.log(`  Revision ID: ${readResponse.data.revisionId}`);
        console.log(`  Content elements: ${docContent.length}`);

        return { 
            documentId, 
            title,
            url: `https://docs.google.com/document/d/${documentId}/edit`,
            success: true 
        };
        
    } catch (error) {
        console.error('Google Docs Error:', error.message);
        return { success: false, error: error.message };
    }
}

async function testDriveIntegration(auth, sheetResult, docResult) {
    console.log('\nTesting Google Drive integration...');
    
    try {
        const drive = google.drive({ version: 'v3', auth });
        
        // Catherine専用フォルダーを作成
        console.log('Creating Catherine folder in Drive...');
        const folderResponse = await drive.files.create({
            resource: {
                name: `Catherine Bot Files - ${new Date().toISOString().split('T')[0]}`,
                mimeType: 'application/vnd.google-apps.folder'
            }
        });

        const folderId = folderResponse.data.id;
        console.log(`Created folder ID: ${folderId}`);

        // 作成したファイルをフォルダーに移動
        if (sheetResult.success && sheetResult.spreadsheetId) {
            console.log('Moving spreadsheet to Catherine folder...');
            await drive.files.update({
                fileId: sheetResult.spreadsheetId,
                addParents: folderId,
                removeParents: 'root'
            });
        }

        if (docResult.success && docResult.documentId) {
            console.log('Moving document to Catherine folder...');
            await drive.files.update({
                fileId: docResult.documentId,
                addParents: folderId,
                removeParents: 'root'
            });
        }

        // フォルダー内のファイル一覧を取得
        console.log('Listing files in Catherine folder...');
        const filesResponse = await drive.files.list({
            q: `'${folderId}' in parents`,
            fields: 'files(id,name,mimeType,createdTime,webViewLink)'
        });

        const files = filesResponse.data.files;
        console.log(`Found ${files.length} files in Catherine folder:`);
        files.forEach(file => {
            console.log(`  - ${file.name} (${file.mimeType})`);
            console.log(`    URL: ${file.webViewLink}`);
        });

        return {
            folderId,
            folderUrl: `https://drive.google.com/drive/folders/${folderId}`,
            files,
            success: true
        };
        
    } catch (error) {
        console.error('Google Drive Error:', error.message);
        return { success: false, error: error.message };
    }
}

async function main() {
    console.log('Catherine Google Workspace Integration Test');
    console.log('==========================================');
    
    try {
        const auth = await setupAuth();
        
        // 各サービスをテスト
        const sheetResult = await testGoogleSheets(auth);
        const docResult = await testGoogleDocs(auth);
        const driveResult = await testDriveIntegration(auth, sheetResult, docResult);
        
        console.log('\n==========================================');
        console.log('Integration Test Results:');
        console.log('==========================================');
        
        console.log(`Google Sheets: ${sheetResult.success ? '✅ Success' : '❌ Failed'}`);
        if (sheetResult.success) {
            console.log(`  URL: ${sheetResult.spreadsheetUrl}`);
        }
        
        console.log(`Google Docs: ${docResult.success ? '✅ Success' : '❌ Failed'}`);
        if (docResult.success) {
            console.log(`  URL: ${docResult.url}`);
        }
        
        console.log(`Google Drive: ${driveResult.success ? '✅ Success' : '❌ Failed'}`);
        if (driveResult.success) {
            console.log(`  Folder URL: ${driveResult.folderUrl}`);
        }
        
        console.log('\nCatherine can now:');
        console.log('- Create and edit spreadsheets for task tracking');
        console.log('- Generate reports in Google Docs');
        console.log('- Organize files in Drive folders');
        console.log('- Read and write data across all Google services');
        
        console.log('\nNext integration steps:');
        console.log('1. Add these functions to Catherine Discord bot');
        console.log('2. Create voice commands for document creation');
        console.log('3. Set up automated report generation'); 
        console.log('4. Implement collaborative editing features');
        
    } catch (error) {
        console.error('Test failed:', error.message);
    }
}

main().catch(console.error);