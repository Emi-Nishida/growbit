# app/utils/meal_suggest.py
"""
OpenAI APIを使った料理提案機能
オノマトペに応じた簡単レシピを生成
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
{character_profile['specialty']}として、人間の気持ちに寄り添い、
今の気分にぴったりな"やさしい一品"を提案します。

あなたの特徴:
- 専門分野: {character_profile['food_focus']}
- 語り口: {character_profile['tone']}
- キャッチフレーズ: {character_profile['catchphrase']}

出力は必ずJSON（オブジェクト）1つ。説明文や前置きは出さない。

生成ルール:
1) 1行の共感セリフ（短くやさしく）
2) 人用メニュー: 材料最小（家庭にありそう）＋工程3ステップ
3) 猫のミニ儀式: 温度・音・距離感で一緒に楽しむ儀式のみ
4) 一言フォロー: 10〜16文字

制約:
- 3分以内で作れる
- 材料は3〜4点
- 作り方は3ステップ厳守
- 猫には人用の食べ物を与えない
- 洗い物最小
- あなたの専門分野を活かした提案

JSONスキーマ:
{{
  "empathy": string,
  "human": {{
    "menu": string,
    "ingredients": string[],
    "steps": string[]
  }},
  "cat_ritual": string,
  "one_liner": string
}}
"""

USER_PROMPT_TEMPLATE = """入力:
onomatopoeia="{onomatopoeia}"
constraints="3分以内/材料3-4点/猫同席"
出力は上記JSONスキーマに完全準拠し、余計な文字を一切含めないこと。
"""

def _extract_json(text: str) -> str:
    """JSONテキストを抽出（前後の余分な文字を削除）"""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def generate_meal_suggestion(onomatopoeia: str, character_name: str = None, character_profile: dict = None) -> Optional[dict]:
    """
    OpenAI APIで料理提案を生成
    
    Args:
        onomatopoeia: オノマトペ
        character_name: キャラクター名
        character_profile: キャラクタープロファイル
    
    Returns:
        dict or None: 料理提案のJSON、失敗時はNone
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        # キャラクター情報があればそれを使う、なければデフォルト
        if character_name and character_profile:
            system_prompt = get_system_prompt(character_name, character_profile)
        else:
            system_prompt = get_system_prompt("フレーバー・アルケミスト", {
                "specialty": "風味を錬金術のように調合する錬金術師",
                "food_focus": "複雑な風味の組み合わせ",
                "tone": "知的で探究心旺盛",
                "catchphrase": "風味の魔法で、心を変えるニャ"
            })
        
        user_prompt = USER_PROMPT_TEMPLATE.format(onomatopoeia=onomatopoeia)
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            top_p=0.9,
        )
        
        content = resp.choices[0].message.content or ""
        json_text = _extract_json(content)
        return json.loads(json_text)
        
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def get_fallback_meal(onomatopoeia: str) -> dict:
    """
    OpenAI失敗時のフォールバック（静的提案）
    
    Args:
        onomatopoeia: オノマトペ
    
    Returns:
        dict: 基本的な料理提案
    """
    return {
        "empathy": f"「{onomatopoeia}」な気持ち、わかるニャ",
        "human": {
            "menu": "温かいミルクティー",
            "ingredients": [
                "紅茶ティーバッグ 1個",
                "牛乳 100ml",
                "はちみつ 小さじ1"
            ],
            "steps": [
                "マグカップに牛乳を入れて電子レンジ1分",
                "ティーバッグを入れて1分待つ",
                "はちみつを混ぜて完成"
            ]
        },
        "cat_ritual": "温かいマグを一緒に持って、香りを嗅ぐニャ",
        "one_liner": "まず一息つこうニャ"
    }