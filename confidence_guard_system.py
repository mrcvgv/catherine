#!/usr/bin/env python3
"""
Confidence Guard System
低確信度ガード：曖昧時は assumptions + 確認 + 二段階実行
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

class ConfidenceLevel(Enum):
    HIGH = "high"      # 90%+ 確信
    MEDIUM = "medium"  # 70-89% 確信  
    LOW = "low"        # 50-69% 確信
    VERY_LOW = "very_low"  # 50%未満

@dataclass
class ConfidenceAssessment:
    level: ConfidenceLevel
    score: float  # 0.0-1.0
    assumptions: List[str]
    ambiguous_points: List[str]
    requires_confirmation: bool
    confirmation_question: Optional[str] = None
    fallback_options: List[str] = None

class ConfidenceGuardSystem:
    def __init__(self):
        # 破壊的操作のパターン
        self.destructive_patterns = [
            r'削除|delete|remove|消去|廃棄',
            r'リセット|reset|初期化|クリア',
            r'取消|cancel|中止|停止',
            r'変更|更新|修正|update.*全て|一括.*変更'
        ]
        
        # 曖昧さを示すワード
        self.ambiguity_indicators = [
            r'多分|たぶん|おそらく|かもしれない',
            r'適当に|よしなに|いい感じに',
            r'それっぽい|なんとなく|だいたい',
            r'よくわからない|曖昧|不明',
            r'どれか|どちらか|何か|いくつか',
        ]
        
        # 確信度を下げる要因
        self.uncertainty_factors = [
            'multiple_matches',      # 複数候補
            'missing_context',       # 文脈不足
            'ambiguous_reference',   # あいまいな参照
            'incomplete_information', # 情報不足
            'conflicting_signals',   # 矛盾した指示
            'new_user_request',      # 新規ユーザー
            'complex_multi_step',    # 複雑な多段階処理
        ]
    
    def assess_confidence(self, user_text: str, context: Dict, 
                         candidates: List[Any] = None) -> ConfidenceAssessment:
        """確信度を評価"""
        try:
            assumptions = []
            ambiguous_points = []
            confidence_score = 1.0
            
            # 1) 曖昧表現の検出
            ambiguity_count = 0
            for pattern in self.ambiguity_indicators:
                if re.search(pattern, user_text, re.IGNORECASE):
                    ambiguity_count += 1
                    ambiguous_points.append(f"曖昧な表現: {pattern}")
            
            confidence_score -= ambiguity_count * 0.1
            
            # 2) 複数候補の処理
            if candidates and len(candidates) > 1:
                confidence_score -= 0.2
                assumptions.append(f"候補が{len(candidates)}件あります。最新または最適なものを選択します。")
                ambiguous_points.append("対象の特定が必要")
            
            # 3) 情報不足の検出
            required_info = self._detect_missing_info(user_text, context)
            if required_info:
                confidence_score -= len(required_info) * 0.15
                ambiguous_points.extend(required_info)
            
            # 4) 破壊的操作の検出
            is_destructive = any(re.search(pattern, user_text, re.IGNORECASE) 
                               for pattern in self.destructive_patterns)
            
            # 5) 確信度レベル判定
            if confidence_score >= 0.9:
                level = ConfidenceLevel.HIGH
            elif confidence_score >= 0.7:
                level = ConfidenceLevel.MEDIUM
            elif confidence_score >= 0.5:
                level = ConfidenceLevel.LOW
            else:
                level = ConfidenceLevel.VERY_LOW
            
            # 6) 確認が必要かどうか判定
            requires_confirmation = (
                level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW] or
                is_destructive or
                len(ambiguous_points) >= 2
            )
            
            # 7) 確認質問の生成
            confirmation_question = None
            if requires_confirmation:
                confirmation_question = self._generate_confirmation_question(
                    user_text, ambiguous_points, is_destructive, candidates
                )
            
            # 8) フォールバック選択肢
            fallback_options = self._generate_fallback_options(user_text, context)
            
            return ConfidenceAssessment(
                level=level,
                score=max(0.0, min(1.0, confidence_score)),
                assumptions=assumptions,
                ambiguous_points=ambiguous_points,
                requires_confirmation=requires_confirmation,
                confirmation_question=confirmation_question,
                fallback_options=fallback_options
            )
            
        except Exception as e:
            print(f"❌ Confidence assessment error: {e}")
            return ConfidenceAssessment(
                level=ConfidenceLevel.VERY_LOW,
                score=0.0,
                assumptions=[],
                ambiguous_points=["評価処理エラー"],
                requires_confirmation=True,
                confirmation_question="処理を続行しますか？"
            )
    
    def _detect_missing_info(self, user_text: str, context: Dict) -> List[str]:
        """不足情報の検出"""
        missing = []
        
        # 日時指定が曖昧
        if any(word in user_text for word in ['いつか', '後で', 'そのうち']):
            missing.append("具体的な日時が未指定")
        
        # 対象が不明確
        if any(word in user_text for word in ['これ', 'それ', 'あれ', '例のやつ']):
            missing.append("対象が不明確")
        
        # 範囲が曖昧
        if any(word in user_text for word in ['全部', '全て', 'みんな', '一括']) and 'の' not in user_text:
            missing.append("対象範囲が曖昧")
        
        return missing
    
    def _generate_confirmation_question(self, user_text: str, 
                                      ambiguous_points: List[str],
                                      is_destructive: bool, 
                                      candidates: List[Any] = None) -> str:
        """確認質問を生成"""
        
        if is_destructive:
            return f"⚠️ 破壊的な操作です。本当に実行しますか？\n"\
                   f"📝 内容: {user_text[:50]}...\n"\
                   f"✅ 実行する場合は「はい、実行」と返答してください。"
        
        if candidates and len(candidates) > 1:
            question = f"対象が複数見つかりました。どれを選びますか？\n"
            for i, candidate in enumerate(candidates[:5], 1):
                title = candidate.get('title', str(candidate))
                question += f"{i}. {title[:30]}\n"
            question += "\n番号で選択してください。例: `1`"
            return question
        
        if ambiguous_points:
            return f"以下の点を確認させてください：\n" + \
                   "\n".join(f"• {point}" for point in ambiguous_points[:3]) + \
                   "\n\n続行しますか？ (はい/いいえ)"
        
        return "続行しますか？ (はい/いいえ)"
    
    def _generate_fallback_options(self, user_text: str, context: Dict) -> List[str]:
        """フォールバック選択肢を生成"""
        options = []
        
        # 部分実行の提案
        if '全て' in user_text or '一括' in user_text:
            options.append("まず1件だけテスト実行")
            options.append("最重要なもののみ実行")
        
        # 段階的実行の提案
        if any(word in user_text for word in ['更新', '変更', '修正']):
            options.append("バックアップを取ってから実行")
            options.append("元に戻せる形で実行")
        
        # 情報収集の提案
        if any(word in user_text for word in ['よくわからない', '適当']):
            options.append("詳細を確認してから実行")
            options.append("類似の過去事例を参考にする")
        
        return options[:3]  # 最大3つ
    
    def format_confidence_response(self, assessment: ConfidenceAssessment, 
                                  base_response: str) -> str:
        """確信度に基づいてレスポンスを調整"""
        
        if not assessment.requires_confirmation:
            return base_response
        
        # 確認が必要な場合のフォーマット
        response = f"🤔 **確認が必要です**\n\n"
        
        if assessment.confirmation_question:
            response += assessment.confirmation_question + "\n\n"
        
        # 想定していることを明示
        if assessment.assumptions:
            response += "📝 **私の理解:**\n"
            for assumption in assessment.assumptions:
                response += f"• {assumption}\n"
            response += "\n"
        
        # 曖昧な点を明示
        if assessment.ambiguous_points:
            response += "❓ **不明確な点:**\n"
            for point in assessment.ambiguous_points:
                response += f"• {point}\n"
            response += "\n"
        
        # フォールバック選択肢
        if assessment.fallback_options:
            response += "💡 **別の選択肢:**\n"
            for i, option in enumerate(assessment.fallback_options, 1):
                response += f"{i}. {option}\n"
            response += "\n"
        
        # 確信度表示
        confidence_emoji = {
            ConfidenceLevel.HIGH: "🟢",
            ConfidenceLevel.MEDIUM: "🟡", 
            ConfidenceLevel.LOW: "🟠",
            ConfidenceLevel.VERY_LOW: "🔴"
        }
        
        response += f"{confidence_emoji[assessment.level]} 確信度: {assessment.score:.0%}\n"
        response += "\n📞 明確な指示をいただければ、すぐに実行します。"
        
        return response
    
    def is_confirmation_response(self, user_text: str) -> tuple[bool, bool]:
        """確認への返答かどうか判定"""
        user_text = user_text.lower().strip()
        
        # 肯定的な返答
        positive_patterns = [
            r'^(はい|yes|y|ok|実行|続行|やって)$',
            r'^はい[、，]?実行$',
            r'^実行して$',
            r'^続けて$'
        ]
        
        # 否定的な返答
        negative_patterns = [
            r'^(いいえ|no|n|やめ|中止|キャンセル)$',
            r'^やめて$',
            r'^中止して$'
        ]
        
        is_positive = any(re.search(pattern, user_text) for pattern in positive_patterns)
        is_negative = any(re.search(pattern, user_text) for pattern in negative_patterns)
        
        return (is_positive or is_negative), is_positive