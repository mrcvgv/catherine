const { Client } = require('@notionhq/client');
require('dotenv').config();

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function testNotionConnection() {
  try {
    console.log('Testing Notion API connection...');
    console.log('API Key:', process.env.NOTION_API_KEY.substring(0, 20) + '...');
    
    // 1. ユーザー情報確認
    const user = await notion.users.me();
    console.log('✅ API Key Valid');
    console.log('Bot Name:', user.name);
    console.log('Workspace:', user.bot?.workspace_name);
    
    // 2. 全データベース検索
    console.log('\n🔍 Searching for databases...');
    const searchResponse = await notion.search({
      filter: { value: 'database', property: 'object' }
    });
    
    console.log('Total databases found:', searchResponse.results.length);
    
    // 3. Taskデータベースを使用
    const taskDb = searchResponse.results.find(db => {
      const title = db.title?.[0]?.plain_text || '';
      return title === 'Task';
    });
    
    if (taskDb) {
      console.log('✅ Found Task database:');
      console.log('   ID:', taskDb.id);
      console.log('   Title:', taskDb.title?.[0]?.plain_text);
      console.log('   URL:', taskDb.url);
      
      // 4. データベースの詳細確認
      console.log('\n📋 Database Properties:');
      const dbInfo = await notion.databases.retrieve({
        database_id: taskDb.id
      });
      
      Object.keys(dbInfo.properties).forEach(prop => {
        console.log(`   - ${prop}: ${dbInfo.properties[prop].type}`);
      });
      
      // 5. テストTODO作成
      console.log('\n➕ Creating test TODO...');
      const newPage = await notion.pages.create({
        parent: { database_id: taskDb.id },
        properties: {
          'タスク名': {
            title: [{ text: { content: 'Direct Test TODO' } }]
          },
          'ステータス': {
            status: { name: '未着手' }
          },
          '優先度': {
            select: { name: '中' }
          }
        }
      });
      
      console.log('✅ Test TODO created successfully');
      console.log('   Page ID:', newPage.id);
      console.log('   URL:', newPage.url);
      
    } else {
      console.log('❌ Task database not found');
      console.log('\nAll databases:');
      searchResponse.results.forEach((db, i) => {
        const title = db.title?.[0]?.plain_text || 'Untitled';
        console.log(`   ${i+1}. ${title} (ID: ${db.id})`);
      });
    }
    
  } catch (error) {
    console.error('❌ Error:', error.code, error.message);
    
    if (error.code === 'unauthorized') {
      console.log('\n🔧 Fix: API key is invalid or expired');
      console.log('   1. Go to https://www.notion.so/my-integrations');
      console.log('   2. Click Catherine integration');
      console.log('   3. Copy new Internal Integration Token');
      console.log('   4. Update NOTION_API_KEY in .env file');
    }
  }
}

testNotionConnection();