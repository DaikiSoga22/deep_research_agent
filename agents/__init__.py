"""
エージェントモジュール

Deep Researchを実行する3つの専門エージェントを提供する:
- Planner: 調査計画を立てる
- Researcher: 情報を検索・収集する
- Critic: 情報の十分性を評価する
"""

from .planner import PLANNER_INSTRUCTIONS
from .researcher import RESEARCHER_INSTRUCTIONS
from .critic import CRITIC_INSTRUCTIONS

__all__ = [
    "PLANNER_INSTRUCTIONS",
    "RESEARCHER_INSTRUCTIONS", 
    "CRITIC_INSTRUCTIONS",
]
