# Azure AI Foundry Deep Research Agent

Azure AI Foundry Agent ServiceとAzure AI Searchを連携したマルチエージェント型Deep Researchシステム。

## 概要

複数のAIエージェントが協調して、ユーザーの質問に対して深い調査を行います。

**動作フロー:**
1. **Planner Agent** - 質問を分析し、検索クエリを生成
2. **Researcher Agent** - Azure AI Searchで情報を検索・収集
3. **Critic Agent** - 情報の十分性を評価し、不足があればPlannerに戻る

このループを最大3回繰り返し、十分な情報が集まったら最終レポートを生成します。

## 前提条件（事前に作成が必要なリソース）

| リソース | 用途 |
|---------|------|
| Azure AI Foundry プロジェクト | エージェントのホスティング |
| Azure AI Search | ベクトル検索インデックス |
| Azure OpenAI (gpt-4o) | エージェントの推論 |
| Azure OpenAI (text-embedding-3-large) | ベクトル埋め込み |
| Azure Content Understanding | ドキュメント解析 |

## セットアップ

### 1. 環境構築

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.sample`をコピーして`.env`を作成し、Azure接続情報を設定。

### 3. インデックス作成とデータ取り込み

```bash
# インデックス作成（初回のみ）
python Tools/azure_aisearch_create_index.py

# Tools/files/ にファイルを配置してデータ取り込み
python Tools/add_vector_index.py
```

**データ取り込みの動作:**
1. `Tools/files/` 内のファイル（PDF, DOCX, PPTX等）を検出
2. Azure Content Understandingでドキュメントを解析しMarkdownに変換
3. ヘッダー単位でチャンク分割
4. Azure OpenAI (text-embedding-3-large) でベクトル化
5. Azure AI Searchインデックスにアップロード

※ 同名ファイルが既にインデックスに存在する場合はスキップ

### 4. エージェント作成

```bash
python Tools/create_agents.py
```

作成されたエージェントIDを`.env`に設定。

## 使用方法

```bash
python run_deep_research.py
```

ターミナルから質問を入力してDeep Researchを実行。
