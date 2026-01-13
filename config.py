# %%
"""
設定管理モジュール

環境変数を読み込み、アプリケーション全体で使用する設定を一元管理する。
"""

import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# %%
# Azure AI Foundry 設定
AZURE_AI_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", "")

# Azure AI Search 設定
AZURE_AI_SEARCH_CONNECTION_ID = os.getenv("AZURE_AI_SEARCH_CONNECTION_ID", "")
AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT", "")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY", "")
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_AI_SEARCH_INDEX_NAME", "")

# Azure OpenAI 設定
AZURE_OPENAI_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o")

# エージェントID
PLANNER_AGENT_ID = os.getenv("PLANNER_AGENT_ID", "")
RESEARCHER_AGENT_ID = os.getenv("RESEARCHER_AGENT_ID", "")
CRITIC_AGENT_ID = os.getenv("CRITIC_AGENT_ID", "")

# Deep Research 設定
MAX_RESEARCH_ITERATIONS = int(os.getenv("MAX_RESEARCH_ITERATIONS", "3"))


# %%
def validate_config() -> bool:
    """
    必須の設定が存在するか検証する。

    Returns:
        bool: 設定が有効な場合True
    """
    required = [
        ("AZURE_AI_PROJECT_CONNECTION_STRING", AZURE_AI_PROJECT_CONNECTION_STRING),
        ("AZURE_AI_SEARCH_CONNECTION_ID", AZURE_AI_SEARCH_CONNECTION_ID),
        ("AZURE_AI_SEARCH_INDEX_NAME", AZURE_AI_SEARCH_INDEX_NAME),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing)}")
        return False
    
    return True
