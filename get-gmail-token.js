// node >= 18
require('dotenv').config();
const { google } = require('googleapis');
const readline = require('node:readline/promises');
const { stdin: input, stdout: output } = require('node:process');

const cid = process.env.GOOGLE_OAUTH_CLIENT_ID;
const secret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const redirectUri = process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/oauth2/callback';

(async () => {
  const oAuth2 = new google.auth.OAuth2(cid, secret, redirectUri);

  const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/tasks',
  ];

  const url = oAuth2.generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    scope: scopes,
  });

  console.log('\n1) このURLをローカルのブラウザで開いて同意してください:');
  console.log(url);

  const rl = readline.createInterface({ input, output });
  const pasted = await rl.question('\n2) 同意後に表示（接続エラーでもOK）された「アドレスバーのURL」全体をコピペしてください:\n> ');
  rl.close();

  // フルURLでも code だけでもOKにする
  let code = pasted.trim();
  try {
    const u = new URL(code);
    code = u.searchParams.get('code') || code;
  } catch (_) { /* pastedはcodeだけ */ }

  const { tokens } = await oAuth2.getToken(code);
  console.log('\nGMAIL_REFRESH_TOKEN=', tokens.refresh_token, '\n');
  console.log('→ .env の GMAIL_REFRESH_TOKEN に貼り付けてください。');
})();