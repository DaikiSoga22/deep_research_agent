# %%
"""
Deep Research 実行スクリプト

Planner → Researcher → Critic のループを実行し、
ユーザーの質問に対して深い調査を行う。

事前に create_agents.py を実行してエージェントを作成しておく必要がある。
"""

import json
import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

import config


# %%
class DeepResearchRunner:
    """
    Deep Researchのマルチエージェントループを実行するクラス。
    """
    
    def __init__(self):
        """
        クライアントと既存エージェントを初期化する。
        """
        # 設定の検証
        if not config.validate_config():
            raise ValueError("設定が不正です。.envファイルを確認してください。")
        
        # エージェントIDの検証
        if not all([config.PLANNER_AGENT_ID, config.RESEARCHER_AGENT_ID, config.CRITIC_AGENT_ID]):
            raise ValueError(
                "エージェントIDが設定されていません。"
                "先に create_agents.py を実行してください。"
            )
        
        # クライアントの初期化
        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=config.AZURE_AI_PROJECT_CONNECTION_STRING,
            credential=credential,
        )
        
        # 既存エージェントの取得
        self.planner = self.client.agents.get_agent(config.PLANNER_AGENT_ID)
        self.researcher = self.client.agents.get_agent(config.RESEARCHER_AGENT_ID)
        self.critic = self.client.agents.get_agent(config.CRITIC_AGENT_ID)
        
        print("エージェントを読み込みました。")
    
    # %%
    def _run_agent(self, agent, message: str) -> str:
        """
        指定されたエージェントでメッセージを処理する。

        Args:
            agent: 実行するエージェント
            message: 送信するメッセージ

        Returns:
            str: エージェントの応答
        """
        # スレッドの作成
        thread = self.client.agents.threads.create()
        
        # メッセージの送信
        self.client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        
        # 実行
        run = self.client.agents.runs.create(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        # 完了まで待機
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = self.client.agents.runs.get(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status != "completed":
            raise RuntimeError(f"エージェント実行に失敗しました: {run.status}")
        
        # 応答の取得（assistantロールの最後のメッセージを取得）
        response_text = self.client.agents.messages.get_last_message_text_by_role(
            thread_id=thread.id,
            role="assistant"
        )
        return response_text.text.value
    
    # %%
    def run(self, question: str) -> str:
        """
        Deep Researchを実行する。

        Args:
            question: ユーザーの質問

        Returns:
            str: 最終レポート
        """
        print("\n" + "=" * 60)
        print("Deep Research を開始します")
        print("=" * 60)
        print(f"\n質問: {question}\n")
        
        iteration = 0
        all_findings = []
        
        while iteration < config.MAX_RESEARCH_ITERATIONS:
            iteration += 1
            print(f"\n--- イテレーション {iteration}/{config.MAX_RESEARCH_ITERATIONS} ---\n")
            
            # Step 1: Planner - 調査計画を立てる
            print("[Planner] 調査計画を作成中...")
            if iteration == 1:
                planner_input = f"以下の質問に回答するための調査計画を立ててください:\n\n{question}"
            else:
                planner_input = (
                    f"以下の質問に回答するための追加調査が必要です:\n\n"
                    f"質問: {question}\n\n"
                    f"これまでの調査結果: {json.dumps(all_findings, ensure_ascii=False)}\n\n"
                    f"不足している情報を補うための追加クエリを生成してください。"
                )
            
            plan_response = self._run_agent(self.planner, planner_input)
            print(f"[Planner] 計画完了")
            
            # Step 2: Researcher - 情報を検索
            print("[Researcher] 情報を検索中...")
            researcher_input = (
                f"以下の調査計画に基づいて情報を検索してください:\n\n{plan_response}"
            )
            research_response = self._run_agent(self.researcher, researcher_input)
            all_findings.append(research_response)
            print(f"[Researcher] 検索完了")
            
            # Step 3: Critic - 情報を評価
            print("[Critic] 情報を評価中...")
            critic_input = (
                f"以下の情報が元の質問に十分に回答できるか評価してください:\n\n"
                f"質問: {question}\n\n"
                f"収集された情報: {json.dumps(all_findings, ensure_ascii=False)}"
            )
            critic_response = self._run_agent(self.critic, critic_input)
            print(f"[Critic] 評価完了")
            
            # 判断を解析
            try:
                # JSONを抽出（マークダウンのコードブロック内にある場合も対応）
                json_match = critic_response
                if "```json" in critic_response:
                    json_match = critic_response.split("```json")[1].split("```")[0]
                elif "```" in critic_response:
                    json_match = critic_response.split("```")[1].split("```")[0]
                
                evaluation = json.loads(json_match)
                
                if evaluation.get("decision") == "COMPLETE":
                    print("\n[Critic] 調査完了と判断しました。")
                    return evaluation.get("final_report", critic_response)
                
            except json.JSONDecodeError:
                # JSONパースに失敗した場合、テキストから判断
                if "COMPLETE" in critic_response.upper():
                    return critic_response
            
            print("\n[Critic] 追加調査が必要と判断しました。")
        
        # 最大イテレーション到達
        print(f"\n最大イテレーション数 ({config.MAX_RESEARCH_ITERATIONS}) に達しました。")
        
        # 最終レポートを生成（評価ではなく直接レポートを要求）
        final_input = (
            f"これまでの調査結果を基に、ユーザーの質問に対する最終レポートを作成してください。\n"
            f"JSONではなく、読みやすいテキスト形式でレポートを作成してください。\n"
            f"情報が不完全な場合でも、収集された情報を最大限活用してレポートを作成してください。\n\n"
            f"## 質問\n{question}\n\n"
            f"## 収集された情報\n{json.dumps(all_findings, ensure_ascii=False, indent=2)}"
        )
        return self._run_agent(self.planner, final_input)  # Plannerを使用して統合


# %%
if __name__ == "__main__":
    print("=" * 60)
    print("Deep Research Agent")
    print("=" * 60)
    
    # ターミナルから質問を入力
    question = input("\n調査したい質問を入力してください:\n> ")
    
    if not question.strip():
        print("質問が入力されていません。終了します。")
        exit(1)
    
    runner = DeepResearchRunner()
    result = runner.run(question)
    
    print("\n" + "=" * 60)
    print("最終レポート")
    print("=" * 60)
    print(result)
