import base64
import os
import glob
from dotenv import load_dotenv

# ... (existing imports)

def main():
    # ... (existing code)

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        # Azure Searchのキーとして使用するためにBase64エンコード（URLセーフ）
        doc_id = base64.urlsafe_b64encode(file_name.encode("utf-8")).decode("utf-8")
        
        print(f"\nProcessing: {file_name}")
from openai import AzureOpenAI
import re
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from content_understanding_client import ContentUnderstandingClient

# 環境変数の読み込み（ルートディレクトリの.envを参照）
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

# 設定値の取得
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

INDEX_NAME = "vector-sample-index"
PDF_DIR = "files" # PDFファイルが置いてあるディレクトリ

def chunk_markdown_by_headers(markdown_text):
    """
    Markdownテキストをヘッダー(#)単位で分割します。
    """
    chunks = []
    lines = markdown_text.split('\n')
    current_chunk = []
    
    for line in lines:
        # ヘッダー行の検出 (行頭の # + スペース)
        if re.match(r'^#+\s', line):
            if current_chunk:
                chunks.append('\n'.join(current_chunk).strip())
            current_chunk = [line]
        else:
            current_chunk.append(line)
            
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
        
    return [c for c in chunks if c] # 空のチャンクを除外

def main():
    if not all([AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY]):
        print("エラー: 必要な環境変数が設定されていません。.envを確認してください。")
        print(f"Missing (example): { [k for k, v in {'AZURE_SEARCH_ENDPOINT': AZURE_SEARCH_ENDPOINT, 'AZURE_SEARCH_API_KEY': AZURE_SEARCH_API_KEY, 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT': AZURE_OPENAI_EMBEDDING_DEPLOYMENT, 'AZURE_OPENAI_ENDPOINT': AZURE_OPENAI_ENDPOINT, 'AZURE_OPENAI_API_KEY': AZURE_OPENAI_API_KEY}.items() if not v] }")
        return


    # クライアントの初期化
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )

    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
    )
    
    try:
        cu_client = ContentUnderstandingClient(api_version="2025-05-01-preview")
    except ValueError as e:
        print(f"Content Understanding初期化エラー: {e}")
        return


    # 1. ファイルの探索と解析
    # Content Understandingがサポートする拡張子（例）
    SUPPORTED_EXTENSIONS = ['*.pdf', '*.png', '*.jpg', '*.jpeg', '*.tiff', '*.docx', '*.xlsx', '*.pptx', '*.html']
    target_files = []
    for ext in SUPPORTED_EXTENSIONS:
        target_files.extend(glob.glob(os.path.join(PDF_DIR, ext)))
    
    if not target_files:
        print(f"警告: '{PDF_DIR}' ディレクトリに対象ファイルが見つかりません。")
        # ダミーデータなどもここには含めず終了
        return

    documents = []
    
    print(f"{len(target_files)} 件のファイルを処理します...")
    
    for file_path in target_files:
        file_name = os.path.basename(file_path)
        # Azure Searchのキーとして使用するためにBase64エンコード（URLセーフ）
        doc_id = base64.urlsafe_b64encode(file_name.encode("utf-8")).decode("utf-8")
        
        # 既にインデックスに存在するか確認
        try:
            results = search_client.search(search_text="*", filter=f"file_name eq '{file_name}'", top=1)
            if any(results):
                print(f"スキップ: {file_name} (既にインデックスに存在します)")
                continue
        except Exception as e:
            print(f"検索エラー (スキップ確認中): {e}")

        print(f"\nProcessing: {file_name}")
        try:
            # Content Understandingで解析
            markdown_content = cu_client.analyze_file(file_path)
            
            # 解析結果が空でないか確認
            if not markdown_content:
                print(f"スキップ: 解析結果が空でした ({file_name})")
                continue

            # 2. Markdownをチャンク分割
            chunks = chunk_markdown_by_headers(markdown_content)
            print(f"  - {len(chunks)} チャンクに分割されました")

            for i, chunk_content in enumerate(chunks):
                 # ドキュメントオブジェクト作成
                chunk_doc = {
                    "id": f"{doc_id}_{i}",
                    "content": chunk_content,
                    "file_name": file_name,
                    "file_id": doc_id,
                    "chunk_no": i
                }
                documents.append(chunk_doc)
            
        except Exception as e:
            print(f"解析エラー ({file_name}): {e}")

    if not documents:
        print("登録対象のドキュメントがありません。")
        return

    # 3. ベクトル化
    print(f"\n{len(documents)} 件のチャンクのベクトル化を開始します...")
    for doc in documents:
        try:
            # Embeddingモデルのトークン制限（8191トークンなど）に注意が必要
            # 長い場合は切り詰めるかチャンク分割が必要
            # ここでは簡易的に先頭文字で制限
            content_to_embed = doc["content"][:8000] 
            
            response = openai_client.embeddings.create(
                input=content_to_embed,
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            embedding = response.data[0].embedding
            doc["content_vector"] = embedding
            # print(f"ドキュメント ID: {doc['id']} のベクトル化完了")
            
        except Exception as e:
            print(f"ベクトル化エラー (ID: {doc['id']}): {e}")

    # 4. ドキュメントのアップロード
    # 4. ドキュメントのアップロード
    # search_client is already initialized

    try:
        # ベクトル化に失敗して content_vector がないドキュメントを除外
        valid_docs = [d for d in documents if "content_vector" in d]
        if valid_docs:
            result = search_client.upload_documents(documents=valid_docs)
            print(f"\nドキュメントアップロード結果: {len(result)} 件成功")
        else:
            print("アップロード可能なドキュメントがありません。")
            
    except Exception as e:
        print(f"アップロードエラー: {e}")

if __name__ == "__main__":
    main()
