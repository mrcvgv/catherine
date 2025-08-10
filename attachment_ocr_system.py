#!/usr/bin/env python3
"""
Attachment OCR to ToDo System
添付→OCR→要約→ToDo化：画像/PDF/文書から自動タスク抽出
"""

import base64
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pytz
from openai import OpenAI
from firebase_config import firebase_manager
import re

JST = pytz.timezone('Asia/Tokyo')

@dataclass
class ExtractedTask:
    title: str
    description: str
    priority: int  # 1-5
    category: str
    estimated_hours: float
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    confidence: float = 0.5
    source_context: str = ""

@dataclass
class DocumentAnalysis:
    document_type: str  # "invoice", "estimate", "meeting_notes", "email", "specification", "other"
    key_information: Dict[str, Any]
    extracted_tasks: List[ExtractedTask]
    summary: str
    next_actions: List[str]
    urgency_level: int  # 1-5
    filing_suggestion: str

class AttachmentOCRSystem:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.db = firebase_manager.get_db()
        
        # サポートする文書タイプ
        self.document_patterns = {
            'invoice': r'(請求書|invoice|bill|payment)',
            'estimate': r'(見積|estimate|quotation|proposal)',
            'meeting_notes': r'(議事録|minutes|meeting|会議|打合せ)',
            'email': r'(from:|to:|subject:|件名|宛先)',
            'specification': r'(仕様書|specification|requirements|要件)',
            'contract': r'(契約|contract|agreement|合意)',
            'report': r'(報告書|report|レポート|analysis)',
            'manual': r'(マニュアル|manual|手順|procedure)'
        }
    
    async def process_attachment(self, user_id: str, attachment_data: bytes, 
                               filename: str, attachment_type: str = "image") -> DocumentAnalysis:
        """添付ファイルを処理してタスクを抽出"""
        try:
            # 1) OCR/テキスト抽出
            extracted_text = await self._extract_text(attachment_data, attachment_type)
            
            if not extracted_text or len(extracted_text) < 10:
                return DocumentAnalysis(
                    document_type="unknown",
                    key_information={},
                    extracted_tasks=[],
                    summary="テキストを抽出できませんでした",
                    next_actions=[],
                    urgency_level=1,
                    filing_suggestion="manual_review"
                )
            
            # 2) 文書タイプ判定
            doc_type = self._classify_document_type(extracted_text, filename)
            
            # 3) AI分析でタスク抽出
            analysis = await self._analyze_document_content(
                extracted_text, doc_type, filename, user_id
            )
            
            return analysis
            
        except Exception as e:
            print(f"❌ Attachment processing error: {e}")
            return self._get_fallback_analysis()
    
    async def _extract_text(self, attachment_data: bytes, 
                           attachment_type: str) -> str:
        """テキスト抽出（OCR/読み取り）"""
        try:
            if attachment_type == "image":
                return await self._extract_text_from_image(attachment_data)
            elif attachment_type == "pdf":
                return await self._extract_text_from_pdf(attachment_data)
            elif attachment_type == "text":
                return attachment_data.decode('utf-8')
            else:
                # その他の形式もGPT-4 Visionで試行
                return await self._extract_text_from_image(attachment_data)
                
        except Exception as e:
            print(f"❌ Text extraction error: {e}")
            return ""
    
    async def _extract_text_from_image(self, image_data: bytes) -> str:
        """画像からOCRでテキスト抽出"""
        try:
            # Base64エンコード
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # GPT-4 Visionでテキスト抽出
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "この画像からすべてのテキストを正確に抽出してください。レイアウトも可能な限り保持してください。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Image OCR error: {e}")
            return ""
    
    async def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """PDFからテキスト抽出"""
        try:
            # 簡易実装：PDF→画像→OCRの流れ
            # 実際の実装では PyPDF2 や pdfplumber を使用
            return "PDF読み取り機能は開発中です"
            
        except Exception as e:
            print(f"❌ PDF extraction error: {e}")
            return ""
    
    def _classify_document_type(self, text: str, filename: str) -> str:
        """文書タイプを分類"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # ファイル名から判定
        for doc_type, pattern in self.document_patterns.items():
            if re.search(pattern, filename_lower):
                return doc_type
        
        # 内容から判定
        for doc_type, pattern in self.document_patterns.items():
            if re.search(pattern, text_lower):
                return doc_type
        
        return "other"
    
    async def _analyze_document_content(self, text: str, doc_type: str, 
                                       filename: str, user_id: str) -> DocumentAnalysis:
        """文書内容をAI分析"""
        try:
            prompt = f"""
以下の文書を分析し、実行可能なタスクを抽出してください：

【ファイル名】{filename}
【文書タイプ】{doc_type}
【内容】
{text[:2000]}

以下のJSON形式で回答してください：
{{
    "document_type": "分類された文書タイプ",
    "summary": "文書の要約（100字以内）",
    "key_information": {{
        "deadline": "期限があれば抽出（YYYY-MM-DD形式）",
        "amount": "金額があれば抽出",
        "contact_person": "連絡先があれば抽出",
        "project_name": "プロジェクト名があれば抽出"
    }},
    "extracted_tasks": [
        {{
            "title": "タスク名（30字以内）",
            "description": "詳細説明（100字以内）",
            "priority": 1-5の優先度,
            "category": "work/personal/communication/finance/other",
            "estimated_hours": 推定作業時間,
            "assignee": "担当者（明記されていれば）",
            "due_date": "期限（YYYY-MM-DD形式、推定可能なら）",
            "confidence": 0.0-1.0の確信度
        }}
    ],
    "next_actions": [
        "すぐに実行すべき行動1",
        "すぐに実行すべき行動2"
    ],
    "urgency_level": 1-5の緊急度,
    "filing_suggestion": "どこに保存すべきかの提案"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # ExtractedTaskオブジェクトに変換
            extracted_tasks = []
            for task_data in result.get('extracted_tasks', []):
                due_date = None
                if task_data.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task_data['due_date']).replace(tzinfo=JST)
                    except:
                        pass
                
                task = ExtractedTask(
                    title=task_data['title'],
                    description=task_data['description'],
                    priority=task_data['priority'],
                    category=task_data['category'],
                    estimated_hours=task_data['estimated_hours'],
                    assignee=task_data.get('assignee'),
                    due_date=due_date,
                    confidence=task_data.get('confidence', 0.5),
                    source_context=f"文書: {filename}"
                )
                extracted_tasks.append(task)
            
            return DocumentAnalysis(
                document_type=result['document_type'],
                key_information=result['key_information'],
                extracted_tasks=extracted_tasks,
                summary=result['summary'],
                next_actions=result['next_actions'],
                urgency_level=result['urgency_level'],
                filing_suggestion=result['filing_suggestion']
            )
            
        except Exception as e:
            print(f"❌ Document analysis error: {e}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> DocumentAnalysis:
        """フォールバック分析結果"""
        return DocumentAnalysis(
            document_type="unknown",
            key_information={},
            extracted_tasks=[],
            summary="文書の自動分析に失敗しました",
            next_actions=["手動で内容を確認"],
            urgency_level=2,
            filing_suggestion="manual_review"
        )
    
    async def create_todos_from_analysis(self, analysis: DocumentAnalysis, 
                                       user_id: str, team_mode: bool = True) -> List[str]:
        """分析結果からToDoを作成"""
        try:
            created_todo_ids = []
            
            for task in analysis.extracted_tasks:
                if task.confidence < 0.3:  # 確信度が低いものはスキップ
                    continue
                
                if team_mode:
                    # チームToDo作成
                    from team_todo_manager import TeamTodoManager
                    team_manager = TeamTodoManager(self.openai_client)
                    
                    todo_data = await team_manager.create_team_todo(
                        creator_id=user_id,
                        title=task.title,
                        description=f"{task.description}\n\n📎 {task.source_context}",
                        assignee=task.assignee or "unassigned",
                        category=task.category,
                        priority=task.priority,
                        due_date=task.due_date,
                        tags=['auto_extracted', analysis.document_type]
                    )
                    
                    if todo_data:
                        created_todo_ids.append(todo_data['todo_id'])
                
                else:
                    # 個人ToDo作成（実装は環境に応じて）
                    pass
            
            return created_todo_ids
            
        except Exception as e:
            print(f"❌ Todo creation from analysis error: {e}")
            return []
    
    def format_analysis_report(self, analysis: DocumentAnalysis, 
                              created_todo_ids: List[str] = None) -> str:
        """分析結果レポートのフォーマット"""
        urgency_emoji = {1: "📝", 2: "📋", 3: "⚡", 4: "🔥", 5: "🚨"}
        
        report = f"📄 **文書分析レポート** {urgency_emoji.get(analysis.urgency_level, '📝')}\n\n"
        
        # 文書タイプと要約
        report += f"**📂 種別**: {analysis.document_type}\n"
        report += f"**📝 要約**: {analysis.summary}\n\n"
        
        # 重要情報
        if analysis.key_information:
            report += f"**🔍 重要情報**:\n"
            for key, value in analysis.key_information.items():
                if value:
                    key_jp = {
                        'deadline': '期限',
                        'amount': '金額',
                        'contact_person': '連絡先',
                        'project_name': 'プロジェクト'
                    }.get(key, key)
                    report += f"• {key_jp}: {value}\n"
            report += "\n"
        
        # 抽出されたタスク
        if analysis.extracted_tasks:
            report += f"**⚡ 抽出されたタスク** ({len(analysis.extracted_tasks)}件):\n"
            for i, task in enumerate(analysis.extracted_tasks, 1):
                confidence_emoji = "🟢" if task.confidence >= 0.8 else "🟡" if task.confidence >= 0.5 else "🟠"
                due_text = f" (期限: {task.due_date.strftime('%m/%d')})" if task.due_date else ""
                report += f"{i}. {confidence_emoji} **{task.title}** ({task.estimated_hours}h){due_text}\n"
                report += f"   📝 {task.description}\n"
            report += "\n"
        
        # 作成されたToDo
        if created_todo_ids:
            report += f"✅ **作成されたToDo**: {len(created_todo_ids)}件\n\n"
        
        # 次のアクション
        if analysis.next_actions:
            report += f"**➡️ 推奨される次のアクション**:\n"
            for action in analysis.next_actions:
                report += f"• {action}\n"
            report += "\n"
        
        # ファイリング提案
        if analysis.filing_suggestion and analysis.filing_suggestion != "manual_review":
            report += f"**📁 保存先提案**: {analysis.filing_suggestion}\n"
        
        return report
    
    async def batch_process_attachments(self, user_id: str, 
                                       attachments: List[Dict]) -> str:
        """複数添付ファイルの一括処理"""
        try:
            all_analyses = []
            all_created_todos = []
            
            for attachment in attachments:
                analysis = await self.process_attachment(
                    user_id,
                    attachment['data'],
                    attachment['filename'],
                    attachment.get('type', 'image')
                )
                all_analyses.append((attachment['filename'], analysis))
                
                # ToDo作成
                created_todos = await self.create_todos_from_analysis(analysis, user_id)
                all_created_todos.extend(created_todos)
            
            # バッチレポート生成
            batch_report = f"📎 **一括文書処理レポート** ({len(attachments)}件)\n\n"
            
            total_tasks = sum(len(analysis.extracted_tasks) for _, analysis in all_analyses)
            batch_report += f"📊 **サマリー**:\n"
            batch_report += f"• 処理ファイル: {len(attachments)}件\n"
            batch_report += f"• 抽出タスク: {total_tasks}件\n"
            batch_report += f"• 作成ToDo: {len(all_created_todos)}件\n\n"
            
            # 各ファイルの概要
            batch_report += f"**📄 処理結果**:\n"
            for filename, analysis in all_analyses:
                urgency_emoji = {1: "📝", 2: "📋", 3: "⚡", 4: "🔥", 5: "🚨"}
                batch_report += f"• {filename} {urgency_emoji.get(analysis.urgency_level, '📝')}: "
                batch_report += f"{len(analysis.extracted_tasks)}件のタスクを抽出\n"
            
            return batch_report
            
        except Exception as e:
            print(f"❌ Batch processing error: {e}")
            return "一括処理中にエラーが発生しました。"