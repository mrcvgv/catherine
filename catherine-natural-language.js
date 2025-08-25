#!/usr/bin/env node

/**
 * Catherine 統合自然言語処理システム
 * 重複を排除し、効率的な人間らしい対話を実現
 */

const { google } = require('googleapis');
require('dotenv').config();

const CLIENT_ID = process.env.GOOGLE_OAUTH_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_FULL_REFRESH_TOKEN || process.env.GMAIL_REFRESH_TOKEN;

class CatherineNaturalLanguage {
    constructor() {
        // Google APIクライアント
        this.oauthClient = null;
        this.gmail = null;
        this.tasks = null;
        this.docs = null;
        this.sheets = null;
        this.calendar = null;
        
        // 会話システム
        this.conversationContext = new Map(); // ユーザーごとの文脈
        this.responseVariations = this.initializeResponseVariations();
        this.intentPatterns = this.initializeIntentPatterns();
    }

    // 応答バリエーション初期化
    initializeResponseVariations() {
        return {
            success: [
                'できました！',
                'はい、完了しました！',
                'お疲れさまでした！',
                '無事に完了です！',
                'バッチリです！',
                'やりました！',
                '完璧です！'
            ],
            error: [
                'あれ、うまくいかなかったみたいです...',
                'すみません、エラーが発生しました',
                'ちょっと問題があったようです',
                '申し訳ございません、失敗してしまいました',
                'うーん、何かおかしいですね...'
            ],
            clarification: [
                'どのような作業をお手伝いしましょうか？',
                '何をしたいか教えてください！',
                'どんなことでお困りですか？',
                'お手伝いできることはありますか？'
            ]
        };
    }

    // 意図パターン初期化
    initializeIntentPatterns() {
        return {
            gmail: {
                keywords: [/メール|mail|gmail|受信|inbox|メッセージ/, /新着|最新|届いた|来た|受け取った/, /確認|チェック|見|読|調べ|何通/],
                minMatches: 2,
                confidence: 0.9
            },
            taskCreate: {
                keywords: [/タスク|todo|やること|課題|仕事|作業|宿題/, /作成|作る|追加|登録|入力|記録|書く/, /して|頼む|お願い|やって|できる/],
                minMatches: 2,
                confidence: 0.8
            },
            taskList: {
                keywords: [/タスク|todo|やること|課題|仕事|作業/, /一覧|リスト|確認|見せ|表示|教え|知り|どんな|ある/],
                minMatches: 2,
                confidence: 0.9
            },
            docCreate: {
                keywords: [/ドキュメント|文書|資料|レポート|報告書|議事録|メモ|docs/, /作成|作る|書く|まとめ|準備|用意/, /して|頼む|お願い|やって|できる/],
                minMatches: 2,
                confidence: 0.8
            },
            sheetCreate: {
                keywords: [/スプレッドシート|表|シート|エクセル|計算書|一覧表|sheets/, /作成|作る|準備|用意|まとめ/],
                minMatches: 1,
                confidence: 0.8
            },
            calendarCreate: {
                keywords: [/予定|イベント|会議|ミーティング|打ち合わせ|アポ|スケジュール/, /作成|追加|入れ|登録|設定|予約/, /明日|来週|今度|後で|来月|\d+時/],
                minMatches: 2,
                confidence: 0.7
            },
            calendarList: {
                keywords: [/予定|イベント|会議|スケジュール|カレンダー/, /確認|見せ|教え|一覧|どんな|ある|今後|これから/],
                minMatches: 2,
                confidence: 0.9
            },
            vague: {
                keywords: [/何か|なんか|ちょっと|少し|適当に|よろしく|頼む|お願い|やって|して|手伝/],
                minMatches: 1,
                confidence: 1.0
            }
        };
    }

    async initialize() {
        console.log('🧠 Catherine Natural Language System starting...');
        
        this.oauthClient = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, 'http://localhost:3000/oauth2/callback');
        this.oauthClient.setCredentials({ refresh_token: REFRESH_TOKEN });
        
        // 全APIクライアントを一度に初期化
        [this.gmail, this.tasks, this.docs, this.sheets, this.calendar] = [
            google.gmail({ version: 'v1', auth: this.oauthClient }),
            google.tasks({ version: 'v1', auth: this.oauthClient }),
            google.docs({ version: 'v1', auth: this.oauthClient }),
            google.sheets({ version: 'v4', auth: this.oauthClient }),
            google.calendar({ version: 'v3', auth: this.oauthClient })
        ];
        
        console.log('✅ Catherine is ready for natural conversation!');
        return true;
    }

    // 統一された意図解析
    parseIntent(message, userId = 'user') {
        const msg = message.toLowerCase().trim();
        const patterns = this.intentPatterns;
        
        // 各パターンをチェック
        for (const [intentType, config] of Object.entries(patterns)) {
            if (this.matchesPatterns(msg, config.keywords, config.minMatches)) {
                return this.buildIntent(intentType, message, config.confidence);
            }
        }

        return { type: 'unknown', confidence: 0.0, params: {}, needsConfirmation: true };
    }

    // パターンマッチング（共通化）
    matchesPatterns(message, patterns, minMatches) {
        let matches = 0;
        for (const pattern of patterns) {
            if (pattern.test(message)) matches++;
        }
        return matches >= minMatches;
    }

    // 意図オブジェクト構築
    buildIntent(type, message, confidence) {
        const intent = { type, confidence, params: {}, needsConfirmation: false };

        switch (type) {
            case 'gmail':
                intent.params.count = this.extractNumber(message) || 5;
                break;
            
            case 'taskCreate':
                intent.params.title = this.extractContent(message, ['タスク', 'todo', 'やること', '作成', '作る', '追加', '登録', 'して', 'ください', 'お願い', 'やって']);
                intent.needsConfirmation = !intent.params.title || intent.params.title.length < 3;
                break;
            
            case 'docCreate':
                intent.params.title = this.extractContent(message, ['ドキュメント', '文書', '資料', '作成', '作る', '書く', 'まとめ', 'して', 'ください', 'お願い']);
                intent.needsConfirmation = !intent.params.title || intent.params.title.length < 2;
                break;
            
            case 'sheetCreate':
                intent.params.title = this.extractContent(message, ['スプレッドシート', '表', 'シート', '作成', '作る', '準備', 'して', 'ください']);
                intent.needsConfirmation = !intent.params.title || intent.params.title.length < 2;
                break;
            
            case 'calendarCreate':
                intent.params.title = this.extractContent(message, ['予定', 'イベント', '会議', 'ミーティング', '作成', '追加', '入れ', '明日', '来週']);
                intent.params.time = this.extractTime(message);
                intent.needsConfirmation = !intent.params.title || !intent.params.time.specific;
                break;
            
            case 'calendarList':
                intent.params.days = this.extractNumber(message) || 7;
                break;
            
            case 'vague':
                intent.type = 'clarification_needed';
                intent.needsConfirmation = true;
                intent.params = { originalMessage: message };
                break;
        }

        return intent;
    }

    // 共通のコンテンツ抽出
    extractContent(message, stopWords) {
        let cleaned = message;
        stopWords.forEach(word => {
            cleaned = cleaned.replace(new RegExp(word, 'gi'), ' ');
        });
        return cleaned.replace(/\s+/g, ' ').trim();
    }

    // 数字抽出
    extractNumber(message) {
        const match = message.match(/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    // 時間抽出（統合版）
    extractTime(message) {
        const now = new Date();
        
        // 具体的な時間指定
        const timeMatch = message.match(/(\d{1,2})[:時](\d{0,2})/);
        
        if (message.includes('明日')) {
            const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
            if (timeMatch) {
                tomorrow.setHours(parseInt(timeMatch[1]), parseInt(timeMatch[2] || '0'), 0, 0);
                return { start: tomorrow, end: new Date(tomorrow.getTime() + 60 * 60 * 1000), specific: true };
            }
            tomorrow.setHours(10, 0, 0, 0);
            return { start: tomorrow, end: new Date(tomorrow.getTime() + 60 * 60 * 1000), specific: false };
        }
        
        if (message.includes('来週')) {
            const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
            nextWeek.setHours(10, 0, 0, 0);
            return { start: nextWeek, end: new Date(nextWeek.getTime() + 60 * 60 * 1000), specific: false };
        }

        // デフォルト
        const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
        return { start: oneHourLater, end: new Date(oneHourLater.getTime() + 60 * 60 * 1000), specific: false };
    }

    // 人間らしい応答生成
    getRandomResponse(type) {
        const responses = this.responseVariations[type];
        return responses[Math.floor(Math.random() * responses.length)];
    }

    // 確認メッセージ生成
    generateConfirmation(intent) {
        const confirmOptions = {
            taskCreate: {
                message: intent.params.title ? 
                    `「${intent.params.title}」というタスクを作成してよろしいですか？` :
                    'タスクを作成しますね！どんな内容のタスクですか？',
                options: intent.params.title ? 
                    ['はい', 'いいえ', 'タイトルを変更'] :
                    ['会議の準備', 'レポート作成', '資料まとめ', 'その他（手入力）']
            },
            docCreate: {
                message: intent.params.title ?
                    `「${intent.params.title}」というドキュメントを作成してよろしいですか？` :
                    'ドキュメントを作成しますね！どんなタイトルにしますか？',
                options: intent.params.title ?
                    ['はい', 'いいえ', 'タイトルを変更'] :
                    ['会議資料', 'プロジェクト報告書', 'メモ', 'その他（手入力）']
            },
            sheetCreate: {
                message: intent.params.title ?
                    `「${intent.params.title}」というスプレッドシートを作成してよろしいですか？` :
                    'スプレッドシートを作成しますね！どんな表にしますか？',
                options: intent.params.title ?
                    ['はい', 'いいえ', 'タイトルを変更'] :
                    ['タスク管理表', '売上データ', '進捗管理', 'その他（手入力）']
            },
            calendarCreate: {
                message: (intent.params.time && intent.params.time.specific) ?
                    `「${intent.params.title}」を${intent.params.time.start.toLocaleString()}に作成してよろしいですか？` :
                    `「${intent.params.title}」の予定を作成します。いつにしますか？`,
                options: (intent.params.time && intent.params.time.specific) ?
                    ['はい', 'いいえ', '時間を変更'] :
                    ['今日の午後', '明日の朝', '明日の午後', '具体的な日時を入力']
            },
            clarification_needed: {
                message: this.getRandomResponse('clarification'),
                options: ['メールをチェック', 'タスクを作成', 'ドキュメント作成', 'スプレッドシート作成', '予定を追加', 'その他']
            }
        };

        return confirmOptions[intent.type] || {
            message: 'すみません、よく分からなかったです。何をしたいか教えてください。',
            options: ['メール確認', 'タスク管理', 'ドキュメント作成', '予定管理']
        };
    }

    // メインの処理メソッド
    async processMessage(message, userId = 'user') {
        console.log(`💭 User: "${message}"`);
        
        const intent = this.parseIntent(message, userId);
        console.log(`🎯 Intent: ${intent.type} (confidence: ${intent.confidence})`);
        
        // 確認が必要な場合
        if (intent.needsConfirmation || intent.confidence < 0.6) {
            const confirmation = this.generateConfirmation(intent);
            return {
                success: true,
                message: confirmation.message,
                options: confirmation.options,
                needsUserInput: true,
                pendingIntent: intent
            };
        }

        // 実行
        try {
            const result = await this.executeIntent(intent);
            const humanResponse = `${this.getRandomResponse(result.success ? 'success' : 'error')} ${result.message}`;
            
            return {
                success: result.success,
                message: humanResponse,
                data: result.data
            };

        } catch (error) {
            return {
                success: false,
                message: `${this.getRandomResponse('error')} ${error.message}`
            };
        }
    }

    // 意図実行（統合版）
    async executeIntent(intent) {
        switch (intent.type) {
            case 'gmail':
                return await this.executeGmail(intent.params.count);
            case 'taskCreate':
                return await this.executeTaskCreate(intent.params.title);
            case 'taskList':
                return await this.executeTaskList();
            case 'docCreate':
                return await this.executeDocCreate(intent.params.title);
            case 'sheetCreate':
                return await this.executeSheetCreate(intent.params.title);
            case 'calendarCreate':
                return await this.executeCalendarCreate(intent.params.title, intent.params.time);
            case 'calendarList':
                return await this.executeCalendarList(intent.params.days);
            default:
                return { success: false, message: 'その操作はまだ覚えていないです...' };
        }
    }

    // Gmail実行
    async executeGmail(count) {
        const response = await this.gmail.users.messages.list({ userId: 'me', maxResults: count });
        
        if (!response.data.messages?.length) {
            return { success: true, message: '新しいメールはないみたいですね！' };
        }

        const messages = [];
        for (const message of response.data.messages) {
            const detail = await this.gmail.users.messages.get({ userId: 'me', id: message.id });
            const headers = detail.data.payload.headers;
            const subject = headers.find(h => h.name === 'Subject')?.value || 'No Subject';
            const from = headers.find(h => h.name === 'From')?.value || 'Unknown';
            messages.push(`📧 ${subject}\n   👤 ${from}`);
        }

        return {
            success: true,
            message: `最新のメール${messages.length}件をお持ちしました：\n\n${messages.join('\n\n')}`
        };
    }

    // Task作成実行
    async executeTaskCreate(title) {
        const taskLists = await this.tasks.tasklists.list();
        const defaultTaskList = taskLists.data.items[0];
        await this.tasks.tasks.insert({ tasklist: defaultTaskList.id, resource: { title } });
        
        return { success: true, message: `「${title}」をタスクリストに追加しておきました！` };
    }

    // Task一覧実行
    async executeTaskList() {
        const taskLists = await this.tasks.tasklists.list();
        const defaultTaskList = taskLists.data.items[0];
        const response = await this.tasks.tasks.list({ tasklist: defaultTaskList.id, maxResults: 10 });

        if (!response.data.items?.length) {
            return { success: true, message: 'タスクは全部終わってますね！お疲れさまでした！' };
        }

        const tasks = response.data.items.map(task => {
            const status = task.status === 'completed' ? '✅' : '⭕';
            return `${status} ${task.title}`;
        });

        return { success: true, message: `現在のタスクはこちらです：\n\n${tasks.join('\n')}` };
    }

    // Doc作成実行
    async executeDocCreate(title) {
        const createResponse = await this.docs.documents.create({ resource: { title } });
        const url = `https://docs.google.com/document/d/${createResponse.data.documentId}/edit`;
        
        return {
            success: true,
            message: `「${title}」のドキュメントを作成しました！\n🔗 ${url}\n\n編集画面を開いて作業を始められます！`
        };
    }

    // Sheet作成実行
    async executeSheetCreate(title) {
        const response = await this.sheets.spreadsheets.create({ resource: { properties: { title } } });
        
        return {
            success: true,
            message: `「${title}」のスプレッドシートができました！\n🔗 ${response.data.spreadsheetUrl}\n\nデータ入力の準備は万端です！`
        };
    }

    // Calendar作成実行
    async executeCalendarCreate(title, time) {
        const event = {
            summary: title,
            start: { dateTime: time.start.toISOString(), timeZone: 'Asia/Tokyo' },
            end: { dateTime: time.end.toISOString(), timeZone: 'Asia/Tokyo' },
            reminders: { useDefault: false, overrides: [{ method: 'popup', minutes: 10 }] }
        };

        const response = await this.calendar.events.insert({ calendarId: 'primary', resource: event });
        
        return {
            success: true,
            message: `「${title}」の予定を${time.start.toLocaleString()}に入れておきました！\n📅 ${response.data.htmlLink}\n\n10分前にリマインダーが届きます！`
        };
    }

    // Calendar一覧実行
    async executeCalendarList(days) {
        const timeMin = new Date();
        const timeMax = new Date(Date.now() + days * 24 * 60 * 60 * 1000);

        const response = await this.calendar.events.list({
            calendarId: 'primary',
            timeMin: timeMin.toISOString(),
            timeMax: timeMax.toISOString(),
            maxResults: 10,
            singleEvents: true,
            orderBy: 'startTime',
        });

        if (!response.data.items?.length) {
            return { success: true, message: `今後${days}日間は予定がありません！のんびりできますね！` };
        }

        const events = response.data.items.map(event => {
            const start = new Date(event.start.dateTime || event.start.date);
            const dayName = start.toLocaleDateString('ja-JP', { weekday: 'short' });
            const timeStr = start.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
            return `📅 ${event.summary}\n   📆 ${start.getMonth() + 1}/${start.getDate()}(${dayName}) ${timeStr}`;
        });

        return {
            success: true,
            message: `今後の予定をまとめました：\n\n${events.join('\n\n')}`
        };
    }
}

// テスト実行
async function testUnifiedNL() {
    console.log('🧪 Testing Unified Catherine Natural Language');
    console.log('==========================================');

    const catherine = new CatherineNaturalLanguage();
    await catherine.initialize();

    const testMessages = [
        'メール3通確認して',
        '会議の準備というタスク作って',
        'プロジェクト報告書のドキュメント作成',
        'タスクリスト見せて',
        '明日14時に定例会議の予定',
        '売上管理表のスプレッドシート',
        '今後1週間の予定教えて',
        'よろしく',
        'ちょっと手伝って'
    ];

    for (const message of testMessages) {
        console.log(`\n💬 "${message}"`);
        const result = await catherine.processMessage(message);
        
        console.log(`🤖 ${result.message}`);
        
        if (result.options) {
            console.log(`📝 [${result.options.join(', ')}]`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('\n🎉 Unified Natural Language test completed!');
    console.log('✅ No more code duplication');
    console.log('✅ Efficient pattern matching');
    console.log('✅ Human-like responses');
    console.log('✅ Intelligent confirmations');
}

// エクスポート用
module.exports = { CatherineNaturalLanguage };

if (require.main === module) {
    testUnifiedNL().catch(console.error);
}