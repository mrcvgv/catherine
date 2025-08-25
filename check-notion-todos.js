const { Client } = require('@notionhq/client');
require('dotenv').config();

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function checkTaskDatabase() {
  try {
    const databaseId = '1a3c881f-b75c-80f1-80de-c685be42d89b';
    
    console.log('🔍 Taskデータベースの内容を確認中...');
    
    // データベース内の全ページを取得
    const response = await notion.databases.query({
      database_id: databaseId,
      sorts: [
        {
          property: 'タスク名',
          direction: 'descending'
        }
      ]
    });
    
    console.log(`📊 データベース内のページ数: ${response.results.length}`);
    
    if (response.results.length > 0) {
      console.log('\n📝 最新のタスク一覧:');
      response.results.slice(0, 10).forEach((page, i) => {
        const title = page.properties['タスク名']?.title?.[0]?.text?.content || 'タイトルなし';
        const status = page.properties['ステータス']?.status?.name || '状態不明';
        const priority = page.properties['優先度']?.select?.name || '優先度なし';
        const created = new Date(page.created_time).toLocaleString('ja-JP');
        
        console.log(`${i+1}. 📄 ${title}`);
        console.log(`   ├─ ステータス: ${status}`);
        console.log(`   ├─ 優先度: ${priority}`);
        console.log(`   ├─ 作成日時: ${created}`);
        console.log(`   └─ URL: ${page.url}`);
        console.log('');
      });
    } else {
      console.log('⚠️ データベースは空です');
    }
    
    // 直接ブラウザで確認できるURL
    console.log('🌐 ブラウザで確認:');
    console.log(`   データベース: https://notion.so/${databaseId.replace(/-/g, '')}`);
    console.log('   ビュー付き: https://www.notion.so/1a3c881fb75c80f180dec685be42d89b?v=1a3c881fb75c80f1ae3a000c3b65bc93');
    
    // Catherine作成のページのみフィルター
    const catherinePages = response.results.filter(page => {
      const title = page.properties['タスク名']?.title?.[0]?.text?.content || '';
      return title.includes('Catherine') || title.includes('メール') || title.includes('統合') || title.includes('Direct Test');
    });
    
    if (catherinePages.length > 0) {
      console.log(`\n🤖 Catherine作成のタスク (${catherinePages.length}個):`);
      catherinePages.forEach((page, i) => {
        const title = page.properties['タスク名']?.title?.[0]?.text?.content || 'タイトルなし';
        console.log(`${i+1}. ${title}`);
        console.log(`   URL: ${page.url}`);
      });
    }
    
  } catch (error) {
    console.error('❌ エラー:', error.message);
  }
}

checkTaskDatabase();