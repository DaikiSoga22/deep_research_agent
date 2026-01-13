#%%
import os
import time
import requests
import json
import logging
from typing import Any, Callable, cast
from dotenv import load_dotenv

# 環境変数の読み込み（ルートディレクトリの.envを参照）
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

# 設定値の取得（環境変数から）
CU_ENDPOINT = os.getenv("AZURE_CONTENT_UNDERSTANDING_ENDPOINT")
CU_API_KEY = os.getenv("AZURE_CONTENT_UNDERSTANDING_API_KEY")
CU_ANALYZER_ID = os.getenv("AZURE_CONTENT_UNDERSTANDING_ANALYZER_ID")
CU_API_VERSION = "2024-12-01-preview" # ユーザー指定または公式サンプルの推奨に合わせる

class ContentUnderstandingClient:
    def __init__(self, endpoint=None, api_key=None, analyzer_id=None, api_version=None):
        self.endpoint = (endpoint or CU_ENDPOINT).rstrip("/")
        self.api_key = api_key or CU_API_KEY
        self.analyzer_id = analyzer_id or CU_ANALYZER_ID
        self.api_version = api_version or CU_API_VERSION
        
        if not all([self.endpoint, self.api_key, self.analyzer_id]):
            raise ValueError("Environment variables for Content Understanding are not set.")

        self._logger = logging.getLogger(__name__)
        # 必要に応じてログレベル設定
        # logging.basicConfig(level=logging.INFO)

        self._headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "x-ms-useragent": "cu-sample-code-python"
        }

    def analyze_file(self, file_path):
        """
        ローカルファイルをアップロードして解析し、Markdown結果を返します。
        """
        url = f"{self.endpoint}/contentunderstanding/analyzers/{self.analyzer_id}:analyze?api-version={self.api_version}&stringEncoding=utf16"
        
        headers = self._headers.copy()
        headers["Content-Type"] = "application/octet-stream"

        print(f"Uploading file: {file_path}")
        with open(file_path, "rb") as f:
            data = f.read()

        # 1. 解析リクエスト送信
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 202:
            raise Exception(f"Analysis request failed: {response.status_code}, {response.text}")

        operation_location = response.headers.get("Operation-Location")
        if not operation_location:
             raise Exception("Operation-Location header missing in response.")

        print(f"Analysis started. Polling URL: {operation_location}")

        # 2. ポーリング
        return self._poll_result(operation_location)

    def _poll_result(self, operation_location, timeout_seconds=120, polling_interval_seconds=2):
        headers = self._headers.copy()
        start_time = time.time()
        
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Operation timed out after {timeout_seconds:.2f} seconds.")

            response = requests.get(operation_location, headers=headers)
            if response.status_code != 200:
                 raise Exception(f"Polling failed: {response.status_code}, {response.text}")

            result = response.json()
            status = result.get("status", "").lower()
            
            print(f"Status: {status}")

            if status == "succeeded":
                return self._extract_markdown(result)
            elif status == "failed":
                raise RuntimeError(f"Request failed. Reason: {json.dumps(result, ensure_ascii=False)}")
            
            time.sleep(polling_interval_seconds)

    def _extract_markdown(self, result_json):
        """
        解析結果JSONからMarkdownを抽出するヘルパーメソッド。
        """
        try:
            # 汎用的な探索: result -> contents -> markdown または result -> markdown
            analysis_result = result_json.get("result", {})
            
            if "contents" in analysis_result:
                for content in analysis_result["contents"]:
                    if "markdown" in content:
                        return content["markdown"]
            
            if "markdown" in analysis_result:
                return analysis_result["markdown"]
                
             # Analyzer固有のフィールド構造の場合があるため、見つからない場合はJSONダンプを返す（デバッグ用）
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error extracting markdown: {e}")
            return json.dumps(result_json, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        client = ContentUnderstandingClient() # 環境変数からロード
        try:
            md = client.analyze_file(sys.argv[1])
            print("\n--- Extracted Markdown ---\n")
            print(md[:500] + "..." if len(md) > 500 else md)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python content_understanding_client.py <path_to_pdf>")
#%%
