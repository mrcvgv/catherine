#!/usr/bin/env node

/**
 * Gmail と Google Tasks の OAuth トークン取得スクリプト
 * 
 * 使用方法:
 * 1. Google Cloud Console で OAuth 2.0 クライアントを作成
 * 2. Client ID と Client Secret を .env に設定
 * 3. このスクリプトを実行してトークンを取得
 */

const { google } = require('googleapis');
const express = require('express');
// const open = require('open');
require('dotenv').config();

// 必要なスコープ
const SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/tasks'
];

const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const REDIRECT_URI = process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/oauth2/callback';

if (!CLIENT_ID || !CLIENT_SECRET) {
    console.error('❌ Error: GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set in .env file');
    console.log('\n📋 Required .env variables:');
    console.log('GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com');
    console.log('GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret');
    console.log('GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3000/oauth2/callback');
    process.exit(1);
}

async function getTokens() {
    const oauth2Client = new google.auth.OAuth2(
        CLIENT_ID,
        CLIENT_SECRET,
        REDIRECT_URI
    );

    const authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
        prompt: 'consent'  // 強制的に consent screen を表示
    });

    console.log('🚀 Starting OAuth token acquisition...\n');
    console.log('📋 Configured scopes:');
    SCOPES.forEach(scope => console.log(`  - ${scope}`));
    console.log();

    // Express server for callback
    const app = express();
    const server = app.listen(3000, () => {
        console.log('🌐 Callback server started on http://localhost:3000');
        console.log('📱 Opening browser for authentication...\n');
        
        console.log(`🔗 Please open this URL in your browser:`);
        console.log(`   ${authUrl}`);
    });

    app.get('/oauth2/callback', async (req, res) => {
        const code = req.query.code;
        
        if (!code) {
            res.send('❌ Authorization failed - no code received');
            server.close();
            return;
        }

        try {
            console.log('✅ Authorization code received');
            console.log('🔄 Exchanging code for tokens...');
            
            const { tokens } = await oauth2Client.getToken(code);
            
            console.log('\n🎉 Tokens acquired successfully!\n');
            console.log('📋 Add this to your .env file:');
            console.log('─'.repeat(50));
            console.log(`GMAIL_REFRESH_TOKEN=${tokens.refresh_token}`);
            console.log(`GOOGLE_ACCESS_TOKEN=${tokens.access_token}`);
            console.log('─'.repeat(50));
            
            if (tokens.refresh_token) {
                console.log('\n✅ Refresh token obtained - you can use this for long-term access');
            } else {
                console.log('\n⚠️  No refresh token - you may need to revoke access and try again');
            }

            res.send(`
                <html>
                <head><title>Catherine OAuth Success</title></head>
                <body style="font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #4CAF50;">✅ Authentication Successful!</h1>
                        <p>Catherine now has access to your Gmail and Google Tasks.</p>
                        <p><strong>Refresh Token:</strong></p>
                        <code style="background: #f5f5f5; padding: 10px; display: block; word-break: break-all;">${tokens.refresh_token || 'Not provided'}</code>
                        <p style="margin-top: 20px; color: #666;">You can close this window and return to the terminal.</p>
                    </div>
                </body>
                </html>
            `);
            
            server.close();
            
        } catch (error) {
            console.error('❌ Error exchanging code for tokens:', error.message);
            res.send(`❌ Error: ${error.message}`);
            server.close();
        }
    });

    app.get('/', (req, res) => {
        res.send(`
            <html>
            <head><title>Catherine OAuth Setup</title></head>
            <body style="font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #2196F3;">🤖 Catherine OAuth Setup</h1>
                    <p>Click the link below to authorize Catherine to access your Gmail and Google Tasks:</p>
                    <a href="${authUrl}" style="display: inline-block; background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Authorize Catherine</a>
                    <p style="color: #666; font-size: 14px;">This will grant read access to Gmail and full access to Google Tasks.</p>
                </div>
            </body>
            </html>
        `);
    });

    console.log(`🔗 If browser doesn't open automatically, visit:`);
    console.log(`   ${authUrl}`);
}

// Handle Ctrl+C
process.on('SIGINT', () => {
    console.log('\n\n👋 OAuth setup cancelled');
    process.exit(0);
});

getTokens().catch(console.error);