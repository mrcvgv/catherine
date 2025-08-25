// Google Workspace フル機能のためのOAuth認証
// Gmail, Tasks, Sheets, Docs, Drive すべてのスコープを含む

require('dotenv').config();
const { google } = require('googleapis');
const readline = require('node:readline/promises');
const { stdin: input, stdout: output } = require('node:process');

const cid = process.env.GOOGLE_OAUTH_CLIENT_ID;
const secret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const redirectUri = process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/oauth2/callback';

(async () => {
  const oAuth2 = new google.auth.OAuth2(cid, secret, redirectUri);

  // すべてのGoogle サービスのスコープを追加
  const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/spreadsheets',      // Google Sheets
    'https://www.googleapis.com/auth/documents',         // Google Docs  
    'https://www.googleapis.com/auth/drive.file',        // Google Drive (作成したファイルのみ)
    'https://www.googleapis.com/auth/calendar'           // Google Calendar (既存)
  ];

  const url = oAuth2.generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    scope: scopes,
  });

  console.log('\n🚀 Catherine フル機能OAuth認証');
  console.log('=====================================');
  console.log('\n📋 認証するGoogle サービス:');
  console.log('  ✉️  Gmail (読み取り)');
  console.log('  ✅ Google Tasks');
  console.log('  📊 Google Sheets');
  console.log('  📄 Google Docs');
  console.log('  💾 Google Drive');
  console.log('  📅 Google Calendar');
  
  console.log('\n1) このURLをブラウザで開いて同意してください:');
  console.log('─'.repeat(80));
  console.log(url);
  console.log('─'.repeat(80));

  const rl = readline.createInterface({ input, output });
  const pasted = await rl.question('\n2) 同意後のURL（エラーでもOK）をコピペしてください:\n> ');
  rl.close();

  // URLからcodeを抽出
  let code = pasted.trim();
  try {
    const u = new URL(code);
    code = u.searchParams.get('code') || code;
  } catch (_) { /* codeだけの場合 */ }

  const { tokens } = await oAuth2.getToken(code);
  
  console.log('\n🎉 認証成功！以下を.envに貼り付けてください:');
  console.log('─'.repeat(50));
  console.log('GOOGLE_FULL_REFRESH_TOKEN=', tokens.refresh_token);
  console.log('─'.repeat(50));
  
  if (tokens.access_token) {
    console.log('GOOGLE_ACCESS_TOKEN=', tokens.access_token);
  }
  
  console.log('\n💡 これで以下の機能が使用可能になります:');
  console.log('  - Gmail件名取得・メール監視');
  console.log('  - Google Tasks作成・管理');
  console.log('  - スプレッドシート作成・編集');
  console.log('  - Google Docs作成・編集');
  console.log('  - Drive ファイル管理');
  console.log('  - Calendar イベント管理');
})();