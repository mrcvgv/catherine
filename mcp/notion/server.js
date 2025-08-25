/**
 * Notion MCP Server - 本実装
 */

const MCPBaseServer = require('../common/base_server');
const { Client } = require('@notionhq/client');

class NotionMCPServer extends MCPBaseServer {
    constructor() {
        super('Notion');
        
        // Notion APIクライアントを初期化
        this.notion = new Client({
            auth: process.env.NOTION_API_KEY
        });
        
        // データベースIDを保存（初回作成後）
        this.databaseId = null;
        
        // ツールを登録
        this.registerTool('create_database', 'Create Catherine TODOs database', this.createDatabase.bind(this));
        this.registerTool('create_page', 'Create a new TODO page', this.createPage.bind(this));
        this.registerTool('update_page', 'Update an existing page', this.updatePage.bind(this));
        this.registerTool('search', 'Search Notion content', this.search.bind(this));
        this.registerTool('add_todo', 'Add TODO to Notion', this.addTodo.bind(this));
        this.registerTool('list_todos', 'List all TODOs', this.listTodos.bind(this));
        this.registerTool('complete_todo', 'Mark TODO as completed', this.completeTodo.bind(this));
        
        // 起動時にデータベースをチェック/作成
        this.initializeDatabase();
    }

    async initializeDatabase() {
        try {
            // 既存のデータベースを検索
            const response = await this.notion.search({
                filter: {
                    value: 'database',
                    property: 'object'
                },
                query: 'Catherine TODOs'
            });
            
            if (response.results.length > 0) {
                // 既存のデータベースを使用
                this.databaseId = response.results[0].id;
                console.error(`[Notion] Using existing database: ${this.databaseId}`);
            } else {
                // 新規データベースを作成
                const db = await this.createDatabase({});
                this.databaseId = db.database_id;
                console.error(`[Notion] Created new database: ${this.databaseId}`);
            }
        } catch (error) {
            console.error(`[Notion] Database initialization error:`, error);
        }
    }

    async createDatabase(params) {
        try {
            // まず、ルートページを取得（権限のあるページ）
            const users = await this.notion.users.list({});
            const botId = users.results.find(user => user.type === 'bot')?.id;
            
            // データベースを作成
            const database = await this.notion.databases.create({
                parent: {
                    type: 'page_id',
                    page_id: params.parent_id || 'root'  // rootは後で実際のページIDに置き換え必要
                },
                title: [
                    {
                        type: 'text',
                        text: {
                            content: 'Catherine TODOs'
                        }
                    }
                ],
                properties: {
                    'Title': {
                        title: {}
                    },
                    'Status': {
                        select: {
                            options: [
                                { name: 'pending', color: 'yellow' },
                                { name: 'in_progress', color: 'blue' },
                                { name: 'completed', color: 'green' },
                                { name: 'cancelled', color: 'red' }
                            ]
                        }
                    },
                    'Priority': {
                        select: {
                            options: [
                                { name: 'urgent', color: 'red' },
                                { name: 'high', color: 'orange' },
                                { name: 'normal', color: 'yellow' },
                                { name: 'low', color: 'gray' }
                            ]
                        }
                    },
                    'Due Date': {
                        date: {}
                    },
                    'Created By': {
                        rich_text: {}
                    },
                    'Tags': {
                        multi_select: {
                            options: []
                        }
                    },
                    'Created': {
                        created_time: {}
                    }
                }
            });
            
            console.error(`[Notion] Created database: ${database.id}`);
            
            return {
                success: true,
                database_id: database.id,
                url: database.url,
                message: 'Created Catherine TODOs database'
            };
            
        } catch (error) {
            console.error(`[Notion] Error creating database:`, error);
            
            // パーミッションエラーの場合は、ユーザーに手動作成を促す
            if (error.code === 'unauthorized' || error.code === 'restricted_resource') {
                return {
                    success: false,
                    error: 'Permission denied',
                    message: 'Please share a Notion page with the integration first, then provide the page ID'
                };
            }
            
            return {
                success: false,
                error: error.message
            };
        }
    }

    async createPage(params) {
        const { title, content, parent_id } = params;
        
        try {
            const page = await this.notion.pages.create({
                parent: {
                    database_id: parent_id || this.databaseId
                },
                properties: {
                    'Title': {
                        title: [
                            {
                                text: {
                                    content: title || 'Untitled'
                                }
                            }
                        ]
                    }
                },
                children: content ? [
                    {
                        object: 'block',
                        type: 'paragraph',
                        paragraph: {
                            rich_text: [
                                {
                                    type: 'text',
                                    text: {
                                        content: content
                                    }
                                }
                            ]
                        }
                    }
                ] : []
            });
            
            console.error(`[Notion] Created page: ${page.id}`);
            
            return {
                success: true,
                page_id: page.id,
                url: page.url,
                message: `Created page: ${title}`
            };
            
        } catch (error) {
            console.error(`[Notion] Error creating page:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async updatePage(params) {
        const { page_id, properties, content } = params;
        
        try {
            const page = await this.notion.pages.update({
                page_id,
                properties: properties || {}
            });
            
            if (content) {
                // ページ内容も更新
                await this.notion.blocks.children.append({
                    block_id: page_id,
                    children: [
                        {
                            object: 'block',
                            type: 'paragraph',
                            paragraph: {
                                rich_text: [
                                    {
                                        type: 'text',
                                        text: {
                                            content: content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                });
            }
            
            console.error(`[Notion] Updated page: ${page_id}`);
            
            return {
                success: true,
                page_id,
                message: 'Page updated successfully'
            };
            
        } catch (error) {
            console.error(`[Notion] Error updating page:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async search(params) {
        const { query, filter } = params;
        
        try {
            const response = await this.notion.search({
                query: query || '',
                filter: filter || {
                    value: 'page',
                    property: 'object'
                },
                sort: {
                    direction: 'descending',
                    timestamp: 'last_edited_time'
                }
            });
            
            const results = response.results.map(item => ({
                id: item.id,
                title: this.extractTitle(item),
                type: item.object,
                url: item.url,
                last_edited: item.last_edited_time
            }));
            
            console.error(`[Notion] Search found ${results.length} results`);
            
            return {
                success: true,
                results,
                count: results.length
            };
            
        } catch (error) {
            console.error(`[Notion] Error searching:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async addTodo(params) {
        const { title, description, due_date, priority, created_by, tags } = params;
        
        try {
            if (!this.databaseId) {
                // データベースがない場合は作成
                await this.initializeDatabase();
            }
            
            const properties = {
                'Title': {
                    title: [
                        {
                            text: {
                                content: title || 'New TODO'
                            }
                        }
                    ]
                },
                'Status': {
                    select: {
                        name: 'pending'
                    }
                },
                'Priority': {
                    select: {
                        name: priority || 'normal'
                    }
                }
            };
            
            if (due_date) {
                properties['Due Date'] = {
                    date: {
                        start: due_date
                    }
                };
            }
            
            if (created_by) {
                properties['Created By'] = {
                    rich_text: [
                        {
                            text: {
                                content: created_by
                            }
                        }
                    ]
                };
            }
            
            if (tags && tags.length > 0) {
                properties['Tags'] = {
                    multi_select: tags.map(tag => ({ name: tag }))
                };
            }
            
            const page = await this.notion.pages.create({
                parent: {
                    database_id: this.databaseId
                },
                properties,
                children: description ? [
                    {
                        object: 'block',
                        type: 'paragraph',
                        paragraph: {
                            rich_text: [
                                {
                                    type: 'text',
                                    text: {
                                        content: description
                                    }
                                }
                            ]
                        }
                    }
                ] : []
            });
            
            console.error(`[Notion] Added TODO: ${page.id}`);
            
            return {
                success: true,
                todo_id: page.id,
                url: page.url,
                message: `Added TODO: ${title}`,
                details: {
                    title,
                    description,
                    due_date,
                    priority,
                    status: 'pending'
                }
            };
            
        } catch (error) {
            console.error(`[Notion] Error adding TODO:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async listTodos(params) {
        const { status, priority } = params;
        
        try {
            if (!this.databaseId) {
                await this.initializeDatabase();
            }
            
            const filter = {
                and: []
            };
            
            if (status) {
                filter.and.push({
                    property: 'Status',
                    select: {
                        equals: status
                    }
                });
            }
            
            if (priority) {
                filter.and.push({
                    property: 'Priority',
                    select: {
                        equals: priority
                    }
                });
            }
            
            const response = await this.notion.databases.query({
                database_id: this.databaseId,
                filter: filter.and.length > 0 ? filter : undefined,
                sorts: [
                    {
                        property: 'Priority',
                        direction: 'ascending'
                    },
                    {
                        property: 'Due Date',
                        direction: 'ascending'
                    }
                ]
            });
            
            const todos = response.results.map(page => ({
                id: page.id,
                title: this.extractTitle(page),
                status: page.properties['Status']?.select?.name,
                priority: page.properties['Priority']?.select?.name,
                due_date: page.properties['Due Date']?.date?.start,
                created_by: page.properties['Created By']?.rich_text?.[0]?.text?.content,
                tags: page.properties['Tags']?.multi_select?.map(tag => tag.name),
                url: page.url
            }));
            
            console.error(`[Notion] Listed ${todos.length} TODOs`);
            
            return {
                success: true,
                todos,
                count: todos.length
            };
            
        } catch (error) {
            console.error(`[Notion] Error listing TODOs:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async completeTodo(params) {
        const { todo_id } = params;
        
        try {
            const page = await this.notion.pages.update({
                page_id: todo_id,
                properties: {
                    'Status': {
                        select: {
                            name: 'completed'
                        }
                    }
                }
            });
            
            console.error(`[Notion] Completed TODO: ${todo_id}`);
            
            return {
                success: true,
                todo_id,
                message: 'TODO marked as completed'
            };
            
        } catch (error) {
            console.error(`[Notion] Error completing TODO:`, error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // ヘルパー関数：タイトルを抽出
    extractTitle(item) {
        if (item.properties?.Title?.title?.[0]?.text?.content) {
            return item.properties.Title.title[0].text.content;
        }
        if (item.properties?.Name?.title?.[0]?.text?.content) {
            return item.properties.Name.title[0].text.content;
        }
        return 'Untitled';
    }
}

// サーバーを起動
const server = new NotionMCPServer();
server.start();