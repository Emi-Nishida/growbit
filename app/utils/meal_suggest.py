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

def get_system_prompt(character_name: str, character_profile: dict, situation: str = None, season: str = None) -> str:
    """キャラクターに応じたシステムプロンプトを生成"""
    
    # シーンと季節の情報を追加
    context_info = ""
    if situation:
        context_info += f"\n現在のシーン: {situation}"
    if season:
        context_info += f"\n現在の季節: {season}"
    
    return f"""あなたは「{character_name}」という猫様のキャラクター。
{character_profile['specialty']}として、人間の気持ちに寄り添い、
今の気分にぴったりな"やさしい一品"を提案します。
{context_info}

あなたの特徴:
- 専門分野: {character_profile['food_focus']}
- 語り口: {character_profile['tone']}
- キャッチフレーズ: {character_profile['catchphrase']}

出力は必ずJSON（オブジェクト）1つ。説明文や前置きは出さない。

生成ルール:
1) 1行の共感セリフ（短くやさしく、あなたのキャラクター性を出す）
2) 人用メニュー: 材料最小（家庭にありそう）＋工程3ステップ
   - シーンに合わせる（朝イチなら朝食、会議前なら手が汚れない軽食、など）
   - 季節の食材を活かす（春なら苺、夏なら冷たいもの、秋なら栗、冬なら温かいもの）
3) 猫のミニ儀式: 温度・音・距離感で一緒に楽しむ儀式のみ
4) 一言フォロー: 10〜16文字、**あなたのキャラクター性を活かしたちょっとくすっとする一言**
   - 例: スリーピー・シェフなら「二度寝も仕事ニャ」
   - 例: キャトラリー・バトラーなら「お皿は完璧に洗うニャ」
   - 例: アロマ・キッチェリアンなら「香りで癒されるニャ」

制約:
- 3分以内で作れる
- 材料は3〜4点
- 作り方は3ステップ厳守
- 猫には人用の食べ物を与えない
- 洗い物最小
- あなたの専門分野を活かした提案
- シーンと季節に合った内容
- くすっとする一言を必ず入れる

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
situation="{situation}"
season="{season}"
constraints="3分以内/材料3-4点/猫同席/シーンと季節に合わせる/くすっとする一言"
出力は上記JSONスキーマに完全準拠し、余計な文字を一切含めないこと。
"""

def _extract_json(text: str) -> str:
    """JSONテキストを抽出（前後の余分な文字を削除）"""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def generate_meal_suggestion(
    onomatopoeia: str, 
    character_name: str = None, 
    character_profile: dict = None,
    situation: str = None,
    season: str = None
) -> Optional[dict]:
    """
    OpenAI APIで料理提案を生成
    
    Args:
        onomatopoeia: オノマトペ
        character_name: キャラクター名
        character_profile: キャラクタープロファイル
        situation: シーン（オプション）
        season: 季節（オプション）
    
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
            system_prompt = get_system_prompt(character_name, character_profile, situation, season)
        else:
            system_prompt = get_system_prompt("フレーバー・アルケミスト", {
                "specialty": "風味を錬金術のように調合する錬金術師",
                "food_focus": "複雑な風味の組み合わせ",
                "tone": "知的で探究心旺盛",
                "catchphrase": "風味の魔法で、心を変えるニャ"
            }, situation, season)
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            onomatopoeia=onomatopoeia,
            situation=situation or "その他",
            season=season or "春"
        )
        
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