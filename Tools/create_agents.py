# %%
"""
エージェント作成スクリプト

Azure AI Foundry上に3つのエージェント（Planner, Researcher, Critic）を作成する。

このスクリプトは初回のみ実行する。
"""

import sys
import pathlib

# ルートディレクトリをパスに追加
ROOT_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.identity import DefaultAzureCredential

import config
from agents import PLANNER_INSTRUCTIONS, RESEARCHER_INSTRUCTIONS, CRITIC_INSTRUCTIONS


# %%
def create_agents() -> dict[str, str]:
    """
    3つのエージェントをAzure AI Foundry上に作成する。

    Returns:
        dict[str, str]: 各エージェントのIDを含む辞書
    """
    # 設定の検証
    if not config.validate_config():
        raise ValueError("設定が不正です。.envファイルを確認してください。")
    
    # クライアントの初期化
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=config.AZURE_AI_PROJECT_CONNECTION_STRING,
        credential=credential,
    )
    
    # Azure AI Search ツールの設定
    # 注意: AZURE_AI_SEARCH_CONNECTION_ID は Azure AI Foundry ポータルから取得する必要があります
    search_tool = AzureAISearchTool(
        index_connection_id=config.AZURE_AI_SEARCH_CONNECTION_ID,
        index_name=config.AZURE_AI_SEARCH_INDEX_NAME,
        query_type=AzureAISearchQueryType.SIMPLE,  # シンプルキーワード検索
        top_k=5,
    )
    
    agent_ids = {}
    
    # Planner Agent 作成（検索ツールなし）
    print("Planner Agent を作成中...")
    planner = project_client.agents.create_agent(
        model=config.AZURE_OPENAI_MODEL_DEPLOYMENT,
        name="Deep-Research-Planner",
        instructions=PLANNER_INSTRUCTIONS,
    )
    agent_ids["PLANNER_AGENT_ID"] = planner.id
    print(f"  作成完了: {planner.id}")
    
    # Researcher Agent 作成（検索ツールあり）
    print("Researcher Agent を作成中...")
    researcher = project_client.agents.create_agent(
        model=config.AZURE_OPENAI_MODEL_DEPLOYMENT,
        name="Deep-Research-Researcher",
        instructions=RESEARCHER_INSTRUCTIONS,
        tools=search_tool.definitions,
        tool_resources=search_tool.resources,
    )
    agent_ids["RESEARCHER_AGENT_ID"] = researcher.id
    print(f"  作成完了: {researcher.id}")
    
    # Critic Agent 作成（検索ツールなし）
    print("Critic Agent を作成中...")
    critic = project_client.agents.create_agent(
        model=config.AZURE_OPENAI_MODEL_DEPLOYMENT,
        name="Deep-Research-Critic",
        instructions=CRITIC_INSTRUCTIONS,
    )
    agent_ids["CRITIC_AGENT_ID"] = critic.id
    print(f"  作成完了: {critic.id}")
    
    return agent_ids


# %%
if __name__ == "__main__":
    print("=" * 50)
    print("Deep Research Agent 作成スクリプト")
    print("=" * 50)
    
    try:
        agent_ids = create_agents()
        
        print("\n" + "=" * 50)
        print("すべてのエージェントが正常に作成されました！")
        print("作成されたエージェントID:")
        for name, agent_id in agent_ids.items():
            print(f"  {name}: {agent_id}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        raise
