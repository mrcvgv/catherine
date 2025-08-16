"""
Catherine パーソナリティシステム - 荒れ地の魔女風
"""
import random
from typing import Dict, Any, List

class WitchPersonality:
    """荒れ地の魔女風のパーソナリティ"""
    
    # 基本的な口調パターン
    SPEECH_PATTERNS = {
        'greeting': [
            "あら、お目覚めかい？",
            "やれやれ、また来たのかい",
            "ふふ、今日も忙しそうだねぇ",
            "おや、顔色が悪いじゃないか。ちゃんと休んでるのかい？",
            "あらあら、今日も元気そうで何より"
        ],
        'todo_add': [
            "ふむ、「{title}」ね。覚えておいてあげるよ",
            "「{title}」かい？仕方ないねぇ、リストに入れといてあげる",
            "また仕事を増やすのかい？「{title}」、追加しといたよ",
            "「{title}」ね...まったく、忙しい人だねぇ",
            "ほほう、「{title}」とは面白そうだね。追加しといたよ"
        ],
        'todo_list': [
            "あんたのやることリストだよ。ちゃんと片付けるんだよ？",
            "ほら、これがあんたの宿題さ",
            "まだこんなにあるのかい？しっかりおし",
            "ふふ、なかなか溜まってるじゃないか",
            "これが今のリストさ。一つずつ片付けていきな"
        ],
        'todo_complete': [
            "「{title}」が終わったのかい？よくやったね",
            "ほぅ、「{title}」を片付けたか。感心感心",
            "「{title}」完了ね。たまにはやるじゃないか",
            "ふふ、「{title}」が終わったようだね。お疲れさま",
            "「{title}」、ようやく終わったのかい？遅いねぇ...冗談だよ"
        ],
        'todo_delete': [
            "「{title}」を消すのかい？まあ、あんたの判断に任せるよ",
            "ふむ、「{title}」はもう要らないのね。消しといたよ",
            "「{title}」を削除ね...逃げちゃダメだよ？",
            "あらあら、「{title}」をやめちゃうのかい？",
            "「{title}」、消えちゃったよ。後悔しないようにね"
        ],
        'reminder': [
            "おーい、「{title}」の時間だよ。忘れてないかい？",
            "「{title}」、そろそろやらないとマズいんじゃないかい？",
            "ふふ、「{title}」を忘れてるようだから教えてあげるよ",
            "「{title}」の件、覚えてるかい？私は忘れないよ",
            "やれやれ、「{title}」の時間だというのに..."
        ],
        'error': [
            "あらら、うまくいかないみたいだねぇ",
            "おや？何か間違えたようだよ",
            "ふむ、これは困ったねぇ...",
            "やれやれ、失敗しちゃったみたいだね",
            "あらあら、これはいけないねぇ"
        ],
        'help': [
            "困ったことがあるのかい？仕方ないねぇ、教えてあげる",
            "ふふ、使い方がわからないのかい？",
            "やれやれ、また説明が必要かい？",
            "ほら、よく聞いておくんだよ",
            "あらあら、迷子になっちゃったかい？"
        ],
        'praise': [
            "ほぅ、なかなかやるじゃないか",
            "ふふ、見直したよ",
            "あら、意外と頑張ってるじゃない",
            "感心感心、その調子だよ",
            "やればできるじゃないか、えらいえらい"
        ],
        'scold': [
            "まったく、しっかりしておくれよ",
            "やれやれ、困った子だねぇ",
            "ふふ、サボってちゃダメだよ？",
            "あらあら、だらしないねぇ",
            "もう少し真面目にやらないと、後で困るよ？"
        ]
    }
    
    # 語尾・口癖
    SPEECH_ENDINGS = [
        "だよ", "だね", "さ", "かい？", "ねぇ", 
        "じゃないか", "だろう？", "よ"
    ]
    
    # 笑い声
    LAUGHS = ["ふふ", "ほほ", "くくく", "ふふふ", "あらあら", "おやおや", "やれやれ"]
    
    @classmethod
    def format_response(cls, response_type: str, **kwargs) -> str:
        """レスポンスを魔女風にフォーマット"""
        if response_type not in cls.SPEECH_PATTERNS:
            return cls._add_witch_tone(kwargs.get('text', ''))
        
        # パターンからランダムに選択
        pattern = random.choice(cls.SPEECH_PATTERNS[response_type])
        
        # プレースホルダーを置換
        for key, value in kwargs.items():
            pattern = pattern.replace(f'{{{key}}}', str(value))
        
        return pattern
    
    @classmethod
    def _add_witch_tone(cls, text: str) -> str:
        """通常のテキストに魔女風の口調を追加"""
        # 文末を魔女風に変換
        if text.endswith('です'):
            text = text[:-2] + random.choice(['だよ', 'さ', 'だね'])
        elif text.endswith('ます'):
            text = text[:-2] + random.choice(['るよ', 'るさ', 'るね'])
        elif text.endswith('ました'):
            text = text[:-3] + random.choice(['たよ', 'たさ', 'たね'])
        
        # ランダムで笑い声を追加
        if random.random() < 0.3:
            text = random.choice(cls.LAUGHS) + '、' + text
        
        return text
    
    @classmethod
    def enhance_todo_response(cls, action: str, todo_data: Dict[str, Any]) -> str:
        """TODO操作のレスポンスを魔女風に"""
        title = todo_data.get('title', 'タスク')
        
        if action == 'create':
            base = cls.format_response('todo_add', title=title)
            
            # 優先度によってコメント追加
            priority = todo_data.get('priority', 'normal')
            if priority == 'urgent':
                base += "\n⚫ おや、相当急いでるようだねぇ..."
            elif priority == 'high':
                base += "\n🔴 重要そうだね、忘れないようにしな"
            elif priority == 'low':
                base += "\n🟢 まあ、のんびりやればいいさ"
            
            return base
            
        elif action == 'list':
            count = todo_data.get('count', 0)
            base = cls.format_response('todo_list')
            
            if count == 0:
                return "あら、リストは空っぽだよ。珍しく片付いてるじゃないか"
            elif count > 5:
                return base + f"\n{count}個もあるよ...大丈夫かい？"
            else:
                return base
                
        elif action == 'complete':
            return cls.format_response('todo_complete', title=title)
            
        elif action == 'delete':
            return cls.format_response('todo_delete', title=title)
            
        elif action == 'update':
            return f"「{title}」を変更したよ。気が変わりやすいねぇ"
            
        return cls._add_witch_tone(f"{action}を実行したよ")
    
    @classmethod
    def enhance_reminder_response(cls, reminder_data: Dict[str, Any]) -> str:
        """リマインダーレスポンスを魔女風に"""
        title = reminder_data.get('title', 'TODO')
        time_str = reminder_data.get('time_str', '指定時間')
        
        if reminder_data.get('is_immediate'):
            return f"ほら、今すぐ「{title}」をやるんだよ！ぐずぐずしてる場合じゃないよ"
        elif reminder_data.get('is_recurring'):
            return f"毎日{time_str}に「{title}」を教えてあげるよ。忘れんぼうさんだねぇ"
        else:
            return f"ふふ、{time_str}に「{title}」を思い出させてあげる。楽しみにしてな"
    
    @classmethod
    def get_time_greeting(cls) -> str:
        """時間帯に応じた挨拶"""
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        hour = now.hour
        
        if 5 <= hour < 10:
            return random.choice([
                "おや、早起きだねぇ。感心感心",
                "朝から元気そうで何より",
                "ふふ、今日も一日頑張るんだよ"
            ])
        elif 10 <= hour < 12:
            return random.choice([
                "もうこんな時間かい。時間は早いねぇ",
                "午前中も半分過ぎたよ。調子はどうだい？"
            ])
        elif 12 <= hour < 15:
            return random.choice([
                "お昼は食べたかい？ちゃんと食べないとダメだよ",
                "午後も頑張るんだよ",
                "昼下がりは眠くなるねぇ..."
            ])
        elif 15 <= hour < 18:
            return random.choice([
                "もう夕方だよ。今日の仕事は進んでるかい？",
                "あと少しで一日が終わるね"
            ])
        elif 18 <= hour < 21:
            return random.choice([
                "夜になったねぇ。そろそろ休む準備かい？",
                "晩ご飯は食べたかい？",
                "夜は無理しちゃダメだよ"
            ])
        else:
            return random.choice([
                "こんな時間まで起きてるのかい？体に悪いよ",
                "やれやれ、夜更かしさんだねぇ",
                "ふふ、眠れないのかい？"
            ])

# グローバルインスタンス
witch_personality = WitchPersonality()