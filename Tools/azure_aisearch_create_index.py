#%%
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    VectorSearchAlgorithmKind,
    HnswParameters,
)

# 環境変数の読み込み（ルートディレクトリの.envを参照）
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

# 設定値の取得
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")

INDEX_NAME = "vector-sample-index"

def create_index():
    if not all([AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY]):
        print("エラー: 必要な環境変数が設定されていません。.envを確認してください。")
        return

    index_client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT, 
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
    )

    print(f"インデックス '{INDEX_NAME}' の作成を開始します...")
    
    # ベクトル検索の設定
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                    metric="cosine"
                )
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            )
        ]
    )

    # フィールド定義
    fields = [
        SimpleField(name="id", type="Edm.String", key=True, filterable=True),
        SearchableField(name="content", type="Edm.String"),
        # text-embedding-3-large の標準次元数は 3072
        SearchField(
            name="content_vector", 
            type="Collection(Edm.Single)", 
            vector_search_dimensions=3072, 
            vector_search_profile_name="myHnswProfile"
        ),
        SimpleField(name="file_name", type="Edm.String", filterable=True),
        SimpleField(name="file_id", type="Edm.String", filterable=True),
        SimpleField(name="chunk_no", type="Edm.Int32", filterable=True, sortable=True),
    ]

    index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)
    
    try:
        index_client.create_or_update_index(index)
        print(f"インデックス '{INDEX_NAME}' を作成/更新しました。")
    except Exception as e:
        print(f"インデックス作成エラー: {e}")

if __name__ == "__main__":
    create_index()
