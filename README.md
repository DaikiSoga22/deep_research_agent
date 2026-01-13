# Azure AI Foundry Deep Research Agent

Azure AI Foundry Agent ServiceとAzure AI Searchを連携したマルチエージェント型Deep Researchシステム。

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
