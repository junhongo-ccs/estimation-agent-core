"""
見積金額算出ロジック
"""
import os
import yaml
from pathlib import Path


# 設定ファイルの読み込み
def _load_config():
    """estimate_config.yaml から係数を読み込む"""
    config_path = Path(__file__).parent.parent / "estimate_config.yaml"
    if not config_path.exists():
        # デフォルト値
        return {
            "base_cost_per_screen": 120000,
            "difficulty_multipliers": {"low": 0.8, "medium": 1.0, "high": 1.3},
            "buffer_multiplier": 1.1,
        }
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 係数をロード
_CONFIG = _load_config()
BASE_COST_PER_SCREEN = _CONFIG["base_cost_per_screen"]
DIFFICULTY_MULTIPLIERS = _CONFIG["difficulty_multipliers"]
BUFFER_MULTIPLIER = _CONFIG["buffer_multiplier"]


def calculate_estimate(screen_count: int, complexity: str) -> dict:
    """
    見積金額を算出する

    Args:
        screen_count: 画面数（正の整数）
        complexity: 複雑度（low, medium, high）

    Returns:
        dict: {
            "estimated_amount": int,  # 見積金額（整数・切り捨て）
            "breakdown": {
                "base": int,           # 基本金額
                "difficulty": float,   # 複雑度係数
                "buffer": float        # バッファ係数
            }
        }
    """
    base = screen_count * BASE_COST_PER_SCREEN
    difficulty = DIFFICULTY_MULTIPLIERS.get(complexity, 1.0)
    total = base * difficulty * BUFFER_MULTIPLIER
    
    return {
        "estimated_amount": int(total),
        "breakdown": {
            "base": base,
            "difficulty": difficulty,
            "buffer": BUFFER_MULTIPLIER,
        }
    }
