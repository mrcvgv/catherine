"""
Discord メンション機能ユーティリティ
@everyone, @ユーザー, @role など適切なDiscord文法でメンション処理
"""
import re
import logging
from typing import Optional, Dict, List, Union
import discord

logger = logging.getLogger(__name__)

class DiscordMentionHandler:
    """Discordメンション処理クラス"""
    
    def __init__(self, client: discord.Client):
        self.client = client
    
    def parse_mention_text(self, text: str, guild: Optional[discord.Guild] = None) -> Dict[str, Union[str, List[str]]]:
        """
        テキストからメンション対象を解析
        
        Args:
            text: 解析するテキスト
            guild: 対象のギルド（サーバー）
            
        Returns:
            {
                'mention_type': 'everyone' | 'user' | 'role' | 'users' | 'mixed',
                'targets': ['user_id', 'role_id', ...] または ['everyone'],
                'mention_string': 実際のDiscord文法メンション文字列,
                'readable_names': 読みやすい名前のリスト
            }
        """
        text_lower = text.lower()
        
        # @everyone または @here
        if '@everyone' in text_lower or 'みんな' in text_lower or '全員' in text_lower or '@here' in text_lower:
            return {
                'mention_type': 'everyone',
                'targets': ['everyone'],
                'mention_string': '@everyone',
                'readable_names': ['everyone']
            }
        
        # ロール指定（role:ロール名）
        if text.startswith('role:'):
            role_name = text[5:]  # "role:"を削除
            if guild:
                role = self._find_role_by_pattern(role_name, guild)
                if role:
                    return {
                        'mention_type': 'role',
                        'targets': [str(role.id)],
                        'mention_string': f'<@&{role.id}>',
                        'readable_names': [role.name]
                    }
            # ロールが見つからない場合は @everyone にフォールバック
            return {
                'mention_type': 'everyone',
                'targets': ['everyone'],
                'mention_string': '@everyone',
                'readable_names': ['everyone']
            }
        
        # 複数のメンション対象を格納
        user_targets = []
        role_targets = []
        readable_names = []
        
        if guild:
            # ユーザー名での検索
            user_patterns = self._extract_user_patterns(text)
            for pattern in user_patterns:
                user = self._find_user_by_pattern(pattern, guild)
                if user:
                    user_targets.append(str(user.id))
                    readable_names.append(user.display_name or user.name)
                    logger.info(f"Found user: {user.name} (ID: {user.id})")
            
            # ロール名での検索
            role_patterns = self._extract_role_patterns(text)
            for pattern in role_patterns:
                role = self._find_role_by_pattern(pattern, guild)
                if role:
                    role_targets.append(str(role.id))
                    readable_names.append(role.name)
                    logger.info(f"Found role: {role.name} (ID: {role.id})")
        
        # 結果を構築
        if user_targets and role_targets:
            mention_type = 'mixed'
            all_targets = user_targets + role_targets
        elif user_targets:
            mention_type = 'users' if len(user_targets) > 1 else 'user'
            all_targets = user_targets
        elif role_targets:
            mention_type = 'role'
            all_targets = role_targets
        else:
            # デフォルトは @everyone
            return {
                'mention_type': 'everyone',
                'targets': ['everyone'],
                'mention_string': '@everyone',
                'readable_names': ['everyone']
            }
        
        mention_string = self._build_mention_string(user_targets, role_targets)
        
        return {
            'mention_type': mention_type,
            'targets': all_targets,
            'mention_string': mention_string,
            'readable_names': readable_names
        }
    
    def _extract_user_patterns(self, text: str) -> List[str]:
        """テキストからユーザー名パターンを抽出"""
        patterns = []
        text_lower = text.lower()
        
        # 明示的な@メンション
        explicit_mentions = re.findall(r'@(\w+)', text)
        patterns.extend(explicit_mentions)
        
        # 特定の名前パターン
        name_patterns = [
            'mrc', 'mrcvgl', 'ko', 'kouhei', 'admin', 'owner',
            'catherine', 'bot', 'assistant'
        ]
        
        for pattern in name_patterns:
            if pattern in text_lower:
                patterns.append(pattern)
        
        # 日本語での指定
        if 'さん' in text_lower:
            # 「〇〇さん」パターンを抽出
            name_san_matches = re.findall(r'(\w+)さん', text)
            patterns.extend(name_san_matches)
        
        return list(set(patterns))  # 重複除去
    
    def _extract_role_patterns(self, text: str) -> List[str]:
        """テキストからロール名パターンを抽出"""
        patterns = []
        text_lower = text.lower()
        
        # 一般的なロール名
        role_patterns = [
            'admin', 'administrator', '管理者', 'mod', 'moderator', 'モデレーター',
            'member', 'メンバー', 'user', 'ユーザー', 'guest', 'ゲスト',
            'staff', 'スタッフ', 'helper', 'ヘルパー', 'vip',
            'developer', '開発者', 'tester', 'テスター'
        ]
        
        for pattern in role_patterns:
            if pattern in text_lower:
                patterns.append(pattern)
        
        return patterns
    
    def _find_user_by_pattern(self, pattern: str, guild: discord.Guild) -> Optional[discord.Member]:
        """パターンでユーザーを検索"""
        pattern_lower = pattern.lower()
        
        # 完全一致を優先
        for member in guild.members:
            if (member.name.lower() == pattern_lower or 
                (member.display_name and member.display_name.lower() == pattern_lower)):
                return member
        
        # 部分一致
        for member in guild.members:
            if (pattern_lower in member.name.lower() or 
                (member.display_name and pattern_lower in member.display_name.lower())):
                return member
        
        return None
    
    def _find_role_by_pattern(self, pattern: str, guild: discord.Guild) -> Optional[discord.Role]:
        """パターンでロールを検索"""
        pattern_lower = pattern.lower()
        
        # 完全一致を優先
        for role in guild.roles:
            if role.name.lower() == pattern_lower:
                return role
        
        # 部分一致
        for role in guild.roles:
            if pattern_lower in role.name.lower():
                return role
        
        return None
    
    def _build_mention_string(self, user_ids: List[str], role_ids: List[str]) -> str:
        """Discord文法のメンション文字列を構築"""
        mentions = []
        
        # ユーザーメンション: <@user_id>
        for user_id in user_ids:
            mentions.append(f'<@{user_id}>')
        
        # ロールメンション: <@&role_id>
        for role_id in role_ids:
            mentions.append(f'<@&{role_id}>')
        
        return ' '.join(mentions)
    
    async def send_mention_message(self, channel: discord.TextChannel, 
                                  message: str, mention_data: Dict) -> bool:
        """メンション付きメッセージを送信"""
        try:
            mention_string = mention_data.get('mention_string', '')
            full_message = f"{mention_string} {message}" if mention_string else message
            
            await channel.send(full_message)
            logger.info(f"Sent mention message to {channel.name}: {mention_data['readable_names']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send mention message: {e}")
            return False
    
    def format_mention_for_response(self, mention_data: Dict) -> str:
        """レスポンス用のメンション文字列をフォーマット"""
        if mention_data['mention_type'] == 'everyone':
            return '@everyone'
        
        readable_names = mention_data.get('readable_names', [])
        if len(readable_names) == 1:
            return f'@{readable_names[0]}'
        elif len(readable_names) > 1:
            return '@' + ', @'.join(readable_names)
        else:
            return '@everyone'

def parse_mention_from_text(text: str, guild: Optional[discord.Guild] = None, 
                           client: Optional[discord.Client] = None) -> Dict:
    """
    テキストからメンション情報を解析する便利関数
    
    Args:
        text: 解析するテキスト
        guild: Discordギルド
        client: Discordクライアント
        
    Returns:
        メンション情報辞書
    """
    if client and guild:
        handler = DiscordMentionHandler(client)
        return handler.parse_mention_text(text, guild)
    else:
        # フォールバック: 簡単な解析
        text_lower = text.lower()
        if '@everyone' in text_lower or 'みんな' in text_lower or '全員' in text_lower:
            return {
                'mention_type': 'everyone',
                'targets': ['everyone'],
                'mention_string': '@everyone',
                'readable_names': ['everyone']
            }
        
        # デフォルト
        return {
            'mention_type': 'everyone',
            'targets': ['everyone'],
            'mention_string': '@everyone',
            'readable_names': ['everyone']
        }

# 後方互換性のための関数
def get_mention_string(mention_target: str, guild: Optional[discord.Guild] = None, 
                      client: Optional[discord.Client] = None) -> str:
    """
    メンション対象文字列から適切なDiscord文法メンションを生成
    
    Args:
        mention_target: メンション対象 ('everyone', 'mrc', など)
        guild: Discordギルド
        client: Discordクライアント
        
    Returns:
        Discord文法メンション文字列
    """
    if mention_target == 'everyone':
        return '@everyone'
    
    if client and guild:
        handler = DiscordMentionHandler(client)
        mention_data = handler.parse_mention_text(f'@{mention_target}', guild)
        return mention_data.get('mention_string', '@everyone')
    
    return f'@{mention_target}'