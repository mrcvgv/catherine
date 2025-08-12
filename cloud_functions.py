#!/usr/bin/env python3
"""
Cloud Functions for Catherine AI - TypeScript/Node.js Implementation Guide
リマインダー登録・発火・RRULE繰り返し処理
"""

# TypeScript/Node.js Cloud Functions の実装ガイド
CLOUD_FUNCTIONS_TYPESCRIPT = """
// package.json dependencies
{
  "dependencies": {
    "firebase-admin": "^12.0.0",
    "firebase-functions": "^4.5.0",
    "@google-cloud/tasks": "^4.0.0",
    "node-cron": "^3.0.0",
    "rrule": "^2.8.0",
    "axios": "^1.6.0"
  }
}

// src/index.ts
import { onRequest } from "firebase-functions/v2/https";
import { initializeApp } from "firebase-admin/app";
import { getFirestore, FieldValue } from "firebase-admin/firestore";
import { CloudTasksClient } from "@google-cloud/tasks";
import { RRule } from "rrule";
import axios from "axios";

initializeApp();
const db = getFirestore();
const tasksClient = new CloudTasksClient();

// 1. リマインダー登録エンドポイント
export const createReminder = onRequest(async (req, res) => {
  try {
    const { userId, what, runAt, rrule, mention, channelId } = req.body;
    
    // バリデーション
    if (!userId || !what || !runAt || !channelId) {
      return res.status(400).json({ error: "Missing required fields" });
    }
    
    const validMentions = ["@everyone", "@mrc", "@supy"];
    if (!validMentions.includes(mention)) {
      return res.status(400).json({ error: "Invalid mention" });
    }
    
    // Firestore保存
    const reminderData = {
      userId,
      what,
      mention: mention || "@everyone",
      runAt: new Date(runAt),
      rrule: rrule || null,
      channelId,
      status: "scheduled",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp()
    };
    
    const docRef = await db.collection("reminders").add(reminderData);
    
    // Cloud Tasks エンキュー
    const taskName = await enqueueFireTask(docRef.id, runAt);
    await docRef.update({ taskName });
    
    res.json({ 
      success: true, 
      reminderId: docRef.id,
      scheduledAt: runAt,
      taskName 
    });
    
  } catch (error) {
    console.error("createReminder error:", error);
    res.status(500).json({ error: error.message });
  }
});

// 2. リマインダー発火エンドポイント
export const fireReminder = onRequest(async (req, res) => {
  try {
    const { reminderId } = req.body;
    
    if (!reminderId) {
      return res.status(400).json({ error: "reminderId required" });
    }
    
    const reminderRef = db.collection("reminders").doc(reminderId);
    const reminderSnap = await reminderRef.get();
    
    if (!reminderSnap.exists) {
      return res.status(404).json({ error: "Reminder not found" });
    }
    
    const reminder = reminderSnap.data()!;
    
    if (reminder.status !== "scheduled") {
      return res.json({ skipped: true, reason: `Status is ${reminder.status}` });
    }
    
    // 二重防止トランザクション
    await db.runTransaction(async (transaction) => {
      const freshSnap = await transaction.get(reminderRef);
      if (freshSnap.get("status") !== "scheduled") {
        throw new Error("Status changed during transaction");
      }
      
      transaction.update(reminderRef, {
        status: "sending",
        updatedAt: FieldValue.serverTimestamp()
      });
    });
    
    // Discord送信
    const discordMessage = `${reminder.mention} ⏰ リマインド: ${reminder.what}`;
    const discordSuccess = await sendToDiscord(reminder.channelId, discordMessage);
    
    // 結果更新
    const updateData: any = {
      updatedAt: FieldValue.serverTimestamp()
    };
    
    if (discordSuccess) {
      updateData.status = "sent";
    } else {
      updateData.status = "failed";
      // Cloud Tasksが自動再試行するため、ここではログのみ
      console.error(`Discord send failed for reminder ${reminderId}`);
    }
    
    await reminderRef.update(updateData);
    
    // RRULE処理（繰り返し）
    if (reminder.rrule && discordSuccess) {
      await scheduleNextRecurrence(reminderId, reminder);
    }
    
    res.json({
      success: true,
      discordSent: discordSuccess,
      hasRecurrence: !!reminder.rrule
    });
    
  } catch (error) {
    console.error("fireReminder error:", error);
    res.status(500).json({ error: error.message });
  }
});

// 3. リマインダー削除
export const cancelReminder = onRequest(async (req, res) => {
  try {
    const { reminderId } = req.body;
    
    const reminderRef = db.collection("reminders").doc(reminderId);
    const reminderSnap = await reminderRef.get();
    
    if (!reminderSnap.exists) {
      return res.status(404).json({ error: "Reminder not found" });
    }
    
    const reminder = reminderSnap.data()!;
    
    // Cloud Tasks削除
    if (reminder.taskName) {
      try {
        await tasksClient.deleteTask({ name: reminder.taskName });
      } catch (error) {
        console.warn(`Failed to delete task ${reminder.taskName}:`, error);
      }
    }
    
    // ステータス更新
    await reminderRef.update({
      status: "cancelled",
      updatedAt: FieldValue.serverTimestamp()
    });
    
    res.json({ success: true, cancelled: reminderId });
    
  } catch (error) {
    console.error("cancelReminder error:", error);
    res.status(500).json({ error: error.message });
  }
});

// ヘルパー関数：Cloud Tasks エンキュー
async function enqueueFireTask(reminderId: string, runAt: string | Date): Promise<string> {
  const project = process.env.GCLOUD_PROJECT;
  const location = "asia-northeast1"; // Tokyo
  const queue = "catherine-reminders";
  
  const queuePath = tasksClient.queuePath(project!, location, queue);
  
  const task = {
    httpRequest: {
      httpMethod: "POST" as const,
      url: `https://${location}-${project}.cloudfunctions.net/fireReminder`,
      headers: {
        "Content-Type": "application/json"
      },
      body: Buffer.from(JSON.stringify({ reminderId }))
    },
    scheduleTime: {
      seconds: Math.floor(new Date(runAt).getTime() / 1000)
    }
  };
  
  const [response] = await tasksClient.createTask({
    parent: queuePath,
    task
  });
  
  return response.name!;
}

// ヘルパー関数：Discord送信
async function sendToDiscord(channelId: string, message: string): Promise<boolean> {
  try {
    const discordBotToken = process.env.DISCORD_BOT_TOKEN;
    if (!discordBotToken) {
      throw new Error("DISCORD_BOT_TOKEN not configured");
    }
    
    await axios.post(`https://discord.com/api/v10/channels/${channelId}/messages`, {
      content: message
    }, {
      headers: {
        "Authorization": `Bot ${discordBotToken}`,
        "Content-Type": "application/json"
      }
    });
    
    return true;
  } catch (error) {
    console.error("Discord send error:", error);
    return false;
  }
}

// ヘルパー関数：RRULE次回スケジュール
async function scheduleNextRecurrence(reminderId: string, reminder: any): Promise<void> {
  try {
    if (!reminder.rrule) return;
    
    // RRULEパース
    const rrule = RRule.fromString(reminder.rrule);
    const now = new Date();
    const nextOccurrence = rrule.after(now);
    
    if (!nextOccurrence) {
      console.log(`No more occurrences for reminder ${reminderId}`);
      return;
    }
    
    // 新しいリマインダードキュメント作成
    const nextReminderData = {
      ...reminder,
      runAt: nextOccurrence,
      status: "scheduled",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
      parentReminderId: reminderId // 元リマインダーとの関連
    };
    
    delete nextReminderData.taskName; // 新しいタスクIDが割り当てられる
    
    const nextDocRef = await db.collection("reminders").add(nextReminderData);
    
    // 次回のCloud Tasksエンキュー
    const nextTaskName = await enqueueFireTask(nextDocRef.id, nextOccurrence.toISOString());
    await nextDocRef.update({ taskName: nextTaskName });
    
    console.log(`Next recurrence scheduled: ${nextDocRef.id} at ${nextOccurrence}`);
    
  } catch (error) {
    console.error("scheduleNextRecurrence error:", error);
  }
}

// 4. 毎朝8:00定期通知（Pub/Sub トリガー）
export const morningNotification = onRequest(async (req, res) => {
  try {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const todayEnd = new Date(todayStart);
    todayEnd.setDate(todayEnd.getDate() + 1);
    
    // 今日のリマインダー取得
    const remindersSnap = await db.collection("reminders")
      .where("runAt", ">=", todayStart)
      .where("runAt", "<", todayEnd)
      .where("status", "==", "scheduled")
      .get();
    
    // チャンネル別にグループ化
    const channelReminders: { [channelId: string]: any[] } = {};
    
    remindersSnap.forEach(doc => {
      const reminder = doc.data();
      if (!channelReminders[reminder.channelId]) {
        channelReminders[reminder.channelId] = [];
      }
      channelReminders[reminder.channelId].push(reminder);
    });
    
    // 各チャンネルに通知
    let sentCount = 0;
    for (const [channelId, reminders] of Object.entries(channelReminders)) {
      if (reminders.length === 0) continue;
      
      let message = `@everyone\\n\\n🌅 本日の予定 (${now.toLocaleDateString('ja-JP')})\\n\\n`;
      
      reminders.forEach((reminder, i) => {
        const time = new Date(reminder.runAt.toDate()).toLocaleTimeString('ja-JP', { 
          hour: '2-digit', 
          minute: '2-digit' 
        });
        message += `🔔 ${time} - ${reminder.what} (${reminder.mention})\\n`;
      });
      
      message += "\\n今日も一日頑張りましょう！ 💪";
      
      const success = await sendToDiscord(channelId, message);
      if (success) sentCount++;
    }
    
    res.json({ 
      success: true, 
      channelsNotified: sentCount,
      totalReminders: remindersSnap.size 
    });
    
  } catch (error) {
    console.error("morningNotification error:", error);
    res.status(500).json({ error: error.message });
  }
});
"""

# Python側のCloud Functions連携クライアント
import requests
import json
from typing import Dict, Any, Optional

class CloudFunctionsClient:
    """Cloud Functions連携クライアント"""
    
    def __init__(self, functions_base_url: str):
        self.base_url = functions_base_url.rstrip('/')
        
    async def create_reminder(self, user_id: str, what: str, run_at: str,
                             channel_id: str, mention: str = "@everyone", 
                             rrule: Optional[str] = None) -> Dict[str, Any]:
        """リマインダー作成"""
        try:
            payload = {
                'userId': user_id,
                'what': what,
                'runAt': run_at,  # ISO8601形式
                'channelId': channel_id,
                'mention': mention,
                'rrule': rrule
            }
            
            response = requests.post(
                f"{self.base_url}/createReminder",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """リマインダー削除"""
        try:
            payload = {'reminderId': reminder_id}
            
            response = requests.post(
                f"{self.base_url}/cancelReminder",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Cancel request failed: {str(e)}"
            }

# 使用例とテスト
if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta
    
    async def test_cloud_functions():
        """Cloud Functions連携テスト"""
        
        # テスト用のURL（実際のデプロイ後に変更）
        functions_url = "https://asia-northeast1-catherine-9e862.cloudfunctions.net"
        client = CloudFunctionsClient(functions_url)
        
        # リマインダー作成テスト
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        result = await client.create_reminder(
            user_id="test_user_123",
            what="Cloud Functions連携テスト",
            run_at=tomorrow.isoformat(),
            channel_id="test_channel_456",
            mention="@everyone"
        )
        
        print(f"Reminder creation: {result}")
        
        if result['success']:
            reminder_id = result['data']['reminderId']
            print(f"Created reminder: {reminder_id}")
            
            # 削除テスト
            cancel_result = await client.cancel_reminder(reminder_id)
            print(f"Reminder cancellation: {cancel_result}")
    
    print("🚀 Cloud Functions Implementation Guide")
    print("📝 TypeScript/Node.js functions prepared")
    print("🔗 Python client ready for integration")
    print("\n📋 Deployment Commands:")
    print("  firebase init functions")  
    print("  firebase deploy --only functions")
    print("\n⚡ Cloud Tasks Queue Creation:")
    print("  gcloud tasks queues create catherine-reminders \\")
    print("    --location=asia-northeast1")
    
    # テスト実行（実際のCloudFunctions URLが必要）
    try:
        # asyncio.run(test_cloud_functions())
        print("\n✅ Cloud Functions client ready (test skipped - no deployed functions)")
    except Exception as e:
        print(f"Test skipped: {e}")