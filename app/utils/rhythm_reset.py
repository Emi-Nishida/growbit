# app/utils/rhythm_reset.py
"""
リズム・リセット機能
オノマトペに応じた呼吸法・リラックス法を提案
"""
import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_system_prompt(character_name: str, character_profile: dict) -> str:
    """キャラクターに応じたシステムプロンプトを生成"""
    return f"""あなたは「{character_name}」という猫様のキャラクター。
{character_profile['specialty']}として、人間の気持ちに寄り添い、短時間でできるリラックス法を提案します。

あなたの特徴:
- 専門分野: {character_profile['rhythm_focus']}
- 語り口: {character_profile['tone']}
- キャッチフレーズ: {character_profile['catchphrase']}

出力は必ずJSON（オブジェクト）1つ。説明文や前置きは出さない。

生成ルール:
1) タイトル（絵文字1つ+短い名前、例: 🌬️ クールダウン）
2) 一言（短くやさしく、10〜20文字）
3) やり方: 3ステップ厳守、各ステップは20文字以内
4) 猫のミニ儀式: 温度・音・距離感で一緒に楽しむ儀式（15〜30文字）
5) 一言フォロー: 10〜16文字

内容の方針:
- あなたの専門分野を活かした提案
- オフィスや自宅で気軽にできる
- 道具不要

JSONスキーマ:
{{
  "title": string,
  "one_liner": string,
  "steps": string[],
  "cat_ritual": string,
  "one_liner_after": string
}}

制約:
- JSON以外は出さない
- 3ステップ厳守、簡潔に
- あなたのキャラクター性を活かす
"""

USER_PROMPT_TEMPLATE = """入力:
onomatopoeia="{onomatopoeia}"
constraints="3ステップ/各20文字以内/道具不要"
出力は上記JSONスキーマに完全準拠し、余計な文字を一切含めないこと。
"""

def _extract_json(text: str) -> str:
    """JSONテキストを抽出（前後の余分な文字を削除）"""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def generate_rhythm_reset(onomatopoeia: str, character_name: str, character_profile: dict) -> Optional[dict]:
    """
    OpenAI APIでリズム・リセットを生成
    
    Args:
        onomatopoeia: オノマトペ
        character_name: キャラクター名
        character_profile: キャラクタープロファイル
    
    Returns:
        dict or None: リセット提案のJSON、失敗時はNone
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        system_prompt = get_system_prompt(character_name, character_profile)
        user_prompt = USER_PROMPT_TEMPLATE.format(onomatopoeia=onomatopoeia)
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            top_p=0.9,
        )
        
        content = resp.choices[0].message.content or ""
        json_text = _extract_json(content)
        return json.loads(json_text)
        
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def get_rhythm_reset(onomatopoeia: str, character_name: str = None, character_profile: dict = None, use_ai: bool = True) -> dict:
    """
    オノマトペに応じたリズム・リセット提案を返す
    
    Args:
        onomatopoeia: オノマトペ
        character_name: キャラクター名
        character_profile: キャラクタープロファイル
        use_ai: OpenAI生成を使うか（デフォルトTrue）
    
    Returns:
        dict: リセット提案
    """
    
    # AI生成を試みる
    if use_ai and character_name and character_profile:
        result = generate_rhythm_reset(onomatopoeia, character_name, character_profile)
        if result:
            return result
    
    # フォールバック（静的データ）
    FALLBACK = {
        "title": "🫧 リズム・リセット",
        "one_liner": "深呼吸から始めよう",
        "steps": [
            "4秒吸う",
            "6秒吐く",
            "8回繰り返す"
        ],
        "cat_ritual": "一緒に深呼吸して、ゆったり過ごすニャ",
        "one_liner_after": "おつかれさま"
    }
    
    return FALLBACK