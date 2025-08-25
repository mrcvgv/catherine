/**
 * Google MCP Server - 本実装
 * Google Calendar, Sheets, Gmail等の実際のAPI操作
 */

const MCPBaseServer = require('../common/base_server');
const { google } = require('googleapis');

class GoogleMCPServer extends MCPBaseServer {
    constructor() {
        super('Google');
        
        // Google API クライアントを初期化
        this.auth = null;
        this.calendar = null;
        this.sheets = null;
        this.gmail = null;
        this.drive = null;
        this.calendarId = process.env.GOOGLE_CALENDAR_ID || 'primary';
        this.driveFolderId = process.env.GOOGLE_DRIVE_FOLDER_ID;
        
        // ツールを登録
        this.registerTool('create_event', 'Create calendar event', this.createEvent.bind(this));
        this.registerTool('list_events', 'List upcoming events', this.listEvents.bind(this));
        this.registerTool('update_event', 'Update calendar event', this.updateEvent.bind(this));
        this.registerTool('delete_event', 'Delete calendar event', this.deleteEvent.bind(this));
        this.registerTool('create_sheet', 'Create spreadsheet', this.createSheet.bind(this));
        this.registerTool('append_sheet', 'Append data to sheet', this.appendSheet.bind(this));
        this.registerTool('send_email', 'Send email via Gmail', this.sendEmail.bind(this));
        this.registerTool('set_reminder', 'Set a calendar reminder', this.setReminder.bind(this));
        this.registerTool('upload_to_drive', 'Upload file to Google Drive', this.uploadToDrive.bind(this));
        this.registerTool('list_drive_files', 'List files in Google Drive folder', this.listDriveFiles.bind(this));
        this.registerTool('download_from_drive', 'Download file from Google Drive', this.downloadFromDrive.bind(this));
        this.registerTool('create_drive_folder', 'Create folder in Google Drive', this.createDriveFolder.bind(this));
        
        // 初期化
        this.initialize();
    }

    async initialize() {
        try {
            // Service Account認証
            const serviceAccountKey = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
            if (!serviceAccountKey) {
                console.error('[Google] GOOGLE_SERVICE_ACCOUNT_KEY not found');
                return;
            }
            
            const credentials = JSON.parse(serviceAccountKey);
            
            this.auth = new google.auth.GoogleAuth({
                credentials,
                scopes: [
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/drive'
                ]
            });
            
            const authClient = await this.auth.getClient();
            
            // Google API クライアント初期化
            this.calendar = google.calendar({ version: 'v3', auth: authClient });
            this.sheets = google.sheets({ version: 'v4', auth: authClient });
            this.gmail = google.gmail({ version: 'v1', auth: authClient });
            this.drive = google.drive({ version: 'v3', auth: authClient });
            
            console.error('[Google] API clients initialized successfully');
            
        } catch (error) {
            console.error('[Google] Initialization error:', error);
        }
    }

    async createEvent(params) {
        try {
            if (!this.calendar) {
                await this.initialize();
            }
            
            const { title, start_time, end_time, description, attendees, location, reminder_minutes } = params;
            
            // 開始・終了時間の処理
            const start = new Date(start_time);
            const end = end_time ? new Date(end_time) : new Date(start.getTime() + 60 * 60 * 1000); // デフォルト1時間
            
            const event = {
                summary: title || 'Catherine Event',
                description: description || '',
                location: location || '',
                start: {
                    dateTime: start.toISOString(),
                    timeZone: 'Asia/Tokyo',
                },
                end: {
                    dateTime: end.toISOString(),
                    timeZone: 'Asia/Tokyo',
                },
                attendees: attendees ? attendees.map(email => ({ email })) : [],
                reminders: {
                    useDefault: false,
                    overrides: [
                        { method: 'popup', minutes: reminder_minutes || 10 },
                    ],
                },
            };
            
            const response = await this.calendar.events.insert({
                calendarId: this.calendarId,
                resource: event,
            });
            
            console.error(`[Google] Created event: ${response.data.id}`);
            
            return {
                success: true,
                event_id: response.data.id,
                html_link: response.data.htmlLink,
                message: `Created event: ${title}`,
                details: {
                    title: response.data.summary,
                    start: response.data.start.dateTime,
                    end: response.data.end.dateTime,
                    location: response.data.location,
                    description: response.data.description
                }
            };
            
        } catch (error) {
            console.error('[Google] Error creating event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async listEvents(params) {
        try {
            if (!this.calendar) {
                await this.initialize();
            }
            
            const { max_results = 10, time_min, time_max, days_ahead = 7 } = params;
            
            // デフォルト：今から7日間のイベント
            const timeMin = time_min ? new Date(time_min) : new Date();
            const timeMax = time_max ? new Date(time_max) : new Date(Date.now() + days_ahead * 24 * 60 * 60 * 1000);
            
            const response = await this.calendar.events.list({
                calendarId: this.calendarId,
                timeMin: timeMin.toISOString(),
                timeMax: timeMax.toISOString(),
                maxResults: max_results,
                singleEvents: true,
                orderBy: 'startTime',
            });
            
            const events = response.data.items.map(event => ({
                id: event.id,
                title: event.summary,
                start: event.start.dateTime || event.start.date,
                end: event.end.dateTime || event.end.date,
                description: event.description || '',
                location: event.location || '',
                html_link: event.htmlLink,
                status: event.status
            }));
            
            console.error(`[Google] Listed ${events.length} events`);
            
            return {
                success: true,
                events,
                count: events.length
            };
            
        } catch (error) {
            console.error('[Google] Error listing events:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async updateEvent(params) {
        try {
            if (!this.calendar) {
                await this.initialize();
            }
            
            const { event_id, title, start_time, end_time, description, location } = params;
            
            const updateData = {};
            if (title) updateData.summary = title;
            if (description) updateData.description = description;
            if (location) updateData.location = location;
            
            if (start_time) {
                updateData.start = {
                    dateTime: new Date(start_time).toISOString(),
                    timeZone: 'Asia/Tokyo'
                };
            }
            
            if (end_time) {
                updateData.end = {
                    dateTime: new Date(end_time).toISOString(),
                    timeZone: 'Asia/Tokyo'
                };
            }
            
            const response = await this.calendar.events.patch({
                calendarId: this.calendarId,
                eventId: event_id,
                resource: updateData,
            });
            
            console.error(`[Google] Updated event: ${event_id}`);
            
            return {
                success: true,
                event_id: response.data.id,
                message: 'Event updated successfully',
                html_link: response.data.htmlLink
            };
            
        } catch (error) {
            console.error('[Google] Error updating event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async deleteEvent(params) {
        try {
            if (!this.calendar) {
                await this.initialize();
            }
            
            const { event_id } = params;
            
            await this.calendar.events.delete({
                calendarId: this.calendarId,
                eventId: event_id,
            });
            
            console.error(`[Google] Deleted event: ${event_id}`);
            
            return {
                success: true,
                event_id,
                message: 'Event deleted successfully'
            };
            
        } catch (error) {
            console.error('[Google] Error deleting event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async setReminder(params) {
        try {
            const { title, time, recurring = false, reminder_minutes = 10, description } = params;
            
            // リマインダーをカレンダーイベントとして作成
            const reminderTime = new Date(time);
            const endTime = new Date(reminderTime.getTime() + 5 * 60 * 1000); // 5分間のイベント
            
            const eventResult = await this.createEvent({
                title: `🔔 ${title}`,
                start_time: reminderTime.toISOString(),
                end_time: endTime.toISOString(),
                description: description || 'Catherine reminder',
                reminder_minutes
            });
            
            if (eventResult.success) {
                console.error(`[Google] Set reminder: ${title}`);
                
                return {
                    success: true,
                    reminder_id: eventResult.event_id,
                    html_link: eventResult.html_link,
                    message: `Set reminder: ${title}`,
                    details: {
                        title,
                        time: reminderTime.toISOString(),
                        recurring,
                        reminder_minutes
                    }
                };
            } else {
                return eventResult;
            }
            
        } catch (error) {
            console.error('[Google] Error setting reminder:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async createSheet(params) {
        try {
            if (!this.sheets) {
                await this.initialize();
            }
            
            const { title, sheets_data } = params;
            
            const resource = {
                properties: {
                    title: title || 'Catherine Sheet'
                }
            };
            
            if (sheets_data) {
                resource.sheets = sheets_data;
            }
            
            const response = await this.sheets.spreadsheets.create({
                resource,
                fields: 'spreadsheetId,spreadsheetUrl'
            });
            
            console.error(`[Google] Created spreadsheet: ${response.data.spreadsheetId}`);
            
            return {
                success: true,
                spreadsheet_id: response.data.spreadsheetId,
                spreadsheet_url: response.data.spreadsheetUrl,
                message: `Created spreadsheet: ${title}`
            };
            
        } catch (error) {
            console.error('[Google] Error creating spreadsheet:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async appendSheet(params) {
        try {
            if (!this.sheets) {
                await this.initialize();
            }
            
            const { spreadsheet_id, range = 'Sheet1!A1', values, value_input_option = 'RAW' } = params;
            
            const response = await this.sheets.spreadsheets.values.append({
                spreadsheetId: spreadsheet_id,
                range,
                valueInputOption: value_input_option,
                resource: {
                    values: Array.isArray(values[0]) ? values : [values]
                }
            });
            
            console.error(`[Google] Appended to sheet: ${spreadsheet_id}`);
            
            return {
                success: true,
                updated_cells: response.data.updates.updatedCells,
                updated_range: response.data.updates.updatedRange,
                message: 'Data appended successfully'
            };
            
        } catch (error) {
            console.error('[Google] Error appending to sheet:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async sendEmail(params) {
        try {
            if (!this.gmail) {
                await this.initialize();
            }
            
            const { to, subject, body, from = 'catherine@catherine-470022.iam.gserviceaccount.com' } = params;
            
            // メール本文を作成（RFC2822形式）
            const message = [
                'Content-Type: text/plain; charset="UTF-8"',
                'MIME-Version: 1.0',
                `To: ${to}`,
                `From: ${from}`,
                `Subject: ${subject}`,
                '',
                body
            ].join('\n');
            
            // Base64エンコード
            const encodedMessage = Buffer.from(message)
                .toString('base64')
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=+$/, '');
            
            const response = await this.gmail.users.messages.send({
                userId: 'me',
                resource: {
                    raw: encodedMessage
                }
            });
            
            console.error(`[Google] Sent email: ${response.data.id}`);
            
            return {
                success: true,
                message_id: response.data.id,
                message: `Email sent to ${to}`
            };
            
        } catch (error) {
            console.error('[Google] Error sending email:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async uploadToDrive(params) {
        try {
            if (!this.drive) {
                await this.initialize();
            }
            
            const { fileName, fileContent, mimeType = 'text/plain', folderId } = params;
            
            const fileMetadata = {
                name: fileName,
                parents: [folderId || this.driveFolderId]
            };
            
            const media = {
                mimeType,
                body: Buffer.from(fileContent, 'utf-8')
            };
            
            const response = await this.drive.files.create({
                resource: fileMetadata,
                media: media,
                fields: 'id, name, webViewLink, webContentLink'
            });
            
            console.error(`[Google] Uploaded file to Drive: ${response.data.id}`);
            
            return {
                success: true,
                file_id: response.data.id,
                file_name: response.data.name,
                web_view_link: response.data.webViewLink,
                download_link: response.data.webContentLink,
                message: `Uploaded ${fileName} to Google Drive`
            };
            
        } catch (error) {
            console.error('[Google] Error uploading to Drive:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async listDriveFiles(params) {
        try {
            if (!this.drive) {
                await this.initialize();
            }
            
            const { folderId, pageSize = 20, searchQuery } = params;
            const targetFolderId = folderId || this.driveFolderId;
            
            let query = `'${targetFolderId}' in parents and trashed = false`;
            if (searchQuery) {
                query += ` and name contains '${searchQuery}'`;
            }
            
            const response = await this.drive.files.list({
                q: query,
                pageSize,
                fields: 'files(id, name, mimeType, size, modifiedTime, webViewLink, webContentLink)',
                orderBy: 'modifiedTime desc'
            });
            
            const files = response.data.files.map(file => ({
                id: file.id,
                name: file.name,
                mime_type: file.mimeType,
                size: file.size,
                modified_time: file.modifiedTime,
                web_view_link: file.webViewLink,
                download_link: file.webContentLink
            }));
            
            console.error(`[Google] Listed ${files.length} files from Drive`);
            
            return {
                success: true,
                files,
                count: files.length,
                folder_id: targetFolderId
            };
            
        } catch (error) {
            console.error('[Google] Error listing Drive files:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async downloadFromDrive(params) {
        try {
            if (!this.drive) {
                await this.initialize();
            }
            
            const { fileId } = params;
            
            // ファイルメタデータを取得
            const metaResponse = await this.drive.files.get({
                fileId,
                fields: 'id, name, mimeType'
            });
            
            // ファイル内容を取得
            const response = await this.drive.files.get({
                fileId,
                alt: 'media'
            }, {
                responseType: 'stream'
            });
            
            // ストリームを文字列に変換
            let fileContent = '';
            response.data.on('data', chunk => {
                fileContent += chunk;
            });
            
            await new Promise((resolve, reject) => {
                response.data.on('end', resolve);
                response.data.on('error', reject);
            });
            
            console.error(`[Google] Downloaded file from Drive: ${fileId}`);
            
            return {
                success: true,
                file_id: fileId,
                file_name: metaResponse.data.name,
                mime_type: metaResponse.data.mimeType,
                content: fileContent,
                message: `Downloaded ${metaResponse.data.name} from Google Drive`
            };
            
        } catch (error) {
            console.error('[Google] Error downloading from Drive:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async createDriveFolder(params) {
        try {
            if (!this.drive) {
                await this.initialize();
            }
            
            const { folderName, parentFolderId } = params;
            
            const fileMetadata = {
                name: folderName,
                mimeType: 'application/vnd.google-apps.folder',
                parents: [parentFolderId || this.driveFolderId]
            };
            
            const response = await this.drive.files.create({
                resource: fileMetadata,
                fields: 'id, name, webViewLink'
            });
            
            console.error(`[Google] Created folder in Drive: ${response.data.id}`);
            
            return {
                success: true,
                folder_id: response.data.id,
                folder_name: response.data.name,
                web_view_link: response.data.webViewLink,
                message: `Created folder ${folderName} in Google Drive`
            };
            
        } catch (error) {
            console.error('[Google] Error creating Drive folder:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// サーバーを起動
const server = new GoogleMCPServer();
server.start();