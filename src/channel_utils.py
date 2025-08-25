"""
Discord チャンネル制御ユーティリティ
Catherineが特定のチャンネルでのみ動作するように制御
"""

import logging
from typing import Optional, List
from discord import Message as DiscordMessage, TextChannel, DMChannel, Thread
from src.constants import ALLOWED_CHANNEL_NAMES, CATHERINE_CHANNELS, ALLOWED_CHANNEL_IDS, CATHERINE_CHANNEL_IDS

logger = logging.getLogger(__name__)

def is_allowed_channel(message: DiscordMessage) -> bool:
    """
    メッセージが許可されたチャンネルから送信されたかチェック
    チャンネルIDベースでの判定を優先し、名前ベースをフォールバックとする
    
    Args:
        message: Discord メッセージ
        
    Returns:
        bool: 許可されたチャンネルかどうか
    """
    # DMチャンネルは常に許可
    if isinstance(message.channel, DMChannel):
        logger.info("DM channel - always allowed")
        return True
    
    # チャンネルIDによる判定を優先
    channel_id = None
    if hasattr(message.channel, 'id'):
        channel_id = message.channel.id
        if channel_id in ALLOWED_CHANNEL_IDS:
            logger.info(f"Channel ID {channel_id} - allowed (ID-based)")
            return True
    
    # フォールバック：チャンネル名による判定
    channel_name = None
    if isinstance(message.channel, TextChannel):
        channel_name = message.channel.name.lower()
    elif isinstance(message.channel, Thread):
        # スレッドの場合は親チャンネル名を使用
        if message.channel.parent:
            channel_name = message.channel.parent.name.lower()
    
    if channel_name:
        allowed_names = [name.strip().lower() for name in ALLOWED_CHANNEL_NAMES]
        is_allowed_by_name = channel_name in allowed_names
        
        if is_allowed_by_name:
            logger.info(f"Channel '{channel_name}' (ID: {channel_id}) - allowed (name-based fallback)")
            return True
    
    logger.info(f"Channel '{channel_name}' (ID: {channel_id}) - blocked")
    return False

def is_catherine_channel(message: DiscordMessage) -> bool:
    """
    メッセージがCatherine専用チャンネル（全メッセージに応答）から送信されたかチェック
    チャンネルIDベースでの判定を優先し、名前ベースをフォールバックとする
    
    Args:
        message: Discord メッセージ
        
    Returns:
        bool: Catherine専用チャンネルかどうか
    """
    # DMチャンネルはCatherine専用として扱う
    if isinstance(message.channel, DMChannel):
        logger.info("DM channel - treated as Catherine channel")
        return True
    
    # チャンネルIDによる判定を優先
    channel_id = None
    if hasattr(message.channel, 'id'):
        channel_id = message.channel.id
        if channel_id in CATHERINE_CHANNEL_IDS:
            logger.info(f"Channel ID {channel_id} - Catherine channel (ID-based)")
            return True
    
    # フォールバック：チャンネル名による判定
    channel_name = None
    if isinstance(message.channel, TextChannel):
        channel_name = message.channel.name.lower()
    elif isinstance(message.channel, Thread):
        # スレッドの場合は親チャンネル名を使用
        if message.channel.parent:
            channel_name = message.channel.parent.name.lower()
    
    if channel_name:
        catherine_names = [name.strip().lower() for name in CATHERINE_CHANNELS]
        is_catherine_by_name = channel_name in catherine_names
        
        if is_catherine_by_name:
            logger.info(f"Channel '{channel_name}' (ID: {channel_id}) - Catherine channel (name-based fallback)")
            return True
    
    logger.info(f"Channel '{channel_name}' (ID: {channel_id}) - not Catherine channel")
    return False

def should_respond_to_message(message: DiscordMessage) -> bool:
    """
    Catherineがメッセージに応答すべきかどうか判定
    
    Rules:
    - #catherine チャンネル: 全てのメッセージに応答
    - その他の許可チャンネル: @catherine メンションがある時のみ応答
    - DM: 常に応答
    - 許可されていないチャンネル: 応答しない
    
    Args:
        message: Discord メッセージ
        
    Returns:
        bool: 応答すべきかどうか
    """
    # まず許可されたチャンネルかチェック
    if not is_allowed_channel(message):
        logger.info("Non-allowed channel - will not respond")
        return False
    
    # Catherine専用チャンネル（#catherine）なら常に応答
    if is_catherine_channel(message):
        logger.info("Catherine channel - will respond to ALL messages")
        return True
    
    # DM も常に応答
    if isinstance(message.channel, DMChannel):
        logger.info("DM channel - will respond")
        return True
    
    # その他の許可チャンネルでは、@catherine メンションがある場合のみ応答
    content_lower = message.content.lower()
    
    # テキスト内でのCatherine言及
    catherine_text_mentions = ['catherine', 'キャサリン', 'カトリーヌ']
    text_mentioned = any(mention in content_lower for mention in catherine_text_mentions)
    
    # Discord @メンション（Botユーザーへの言及）
    bot_mentioned = False
    if message.mentions:
        # Botがメンションされているかチェック
        for mention in message.mentions:
            if hasattr(mention, 'bot') and mention.bot:
                bot_mentioned = True
                break
            # または特定のBot IDチェック（より厳密）
            if hasattr(mention, 'id'):
                # Catherineの実際のBot IDと比較する場合
                pass
    
    is_mentioned = text_mentioned or bot_mentioned
    
    channel_name = getattr(message.channel, 'name', 'unknown')
    logger.info(f"Channel '{channel_name}' - {'will respond (@mentioned)' if is_mentioned else 'will not respond (no mention)'}")
    
    return is_mentioned

def get_channel_info(message: DiscordMessage) -> dict:
    """
    チャンネル情報を取得（デバッグ用）
    
    Args:
        message: Discord メッセージ
        
    Returns:
        dict: チャンネル情報
    """
    info = {
        "channel_type": type(message.channel).__name__,
        "is_dm": isinstance(message.channel, DMChannel),
        "is_allowed": is_allowed_channel(message),
        "is_catherine": is_catherine_channel(message),
        "should_respond": should_respond_to_message(message)
    }
    
    if hasattr(message.channel, 'name'):
        info["channel_name"] = message.channel.name
    
    if isinstance(message.channel, Thread) and message.channel.parent:
        info["parent_channel"] = message.channel.parent.name
    
    return info