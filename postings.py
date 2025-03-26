# mongo.py
from typing import List, Dict, Any
import os
import openai
import certifi
import logging
import asyncio
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from pymongo.errors import OperationFailure
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# MongoDB 연결
ca = certifi.where()
client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=ca)
db = client["Rezoom"]
collection = db["postings"]

# MongoDB 연결 테스트
try:
    client.admin.command('ping')
    logging.info("MongoDB Atlas 연결 성공!")

    doc_count = collection.count_documents({})
    logging.info(f"현재 컬렉션의 문서 수: {doc_count}")

    index_info = collection.index_information()
    logging.info(f"현재 생성된 인덱스 정보:\n{index_info}")

except Exception as e:
    logging.error(f"MongoDB Atlas 연결 실패: {str(e)}")
    raise e

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
EMBEDDING_MODEL = "text-embedding-3-small"

# 임베딩 생성 함수
async def get_embedding_async(text: str) -> List[float]:
    if not text or not text.strip():
        raise ValueError("임베딩 요청 텍스트가 비어있습니다.")

    # openai 라이브러리는 비동기 지원 미흡하므로 쓰레드에서 실행
    return await asyncio.to_thread(_sync_get_embedding, text)

def _sync_get_embedding(text: str) -> List[float]:
    try:
        response = openai.Embedding.create(input=[text.strip()], model=EMBEDDING_MODEL)
        return response["data"][0]["embedding"]
    except Exception as e:
        logging.error(f"[임베딩 오류]: {e}")
        raise


# 문서 저장
def store_job_posting(title: str, description: str, embedding: List[float], url: str = "") -> bool:
    try:
        document = {
            "title": title,
            "description": description,
            "url": url,
            "embedding": embedding,
            "created_at": datetime.now()
        }
        collection.insert_one(document)
        return True
    except Exception as e:
        logging.error(f"문서 저장 오류: {e}")
        return False

# 문서 개수 확인
def get_document_count():
    return collection.count_documents({})

# 벡터 유사도 기반 검색 (기본)
async def search_similar_documents_with_score(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_vector = await get_embedding_async(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_vector,
                "path": "embedding",
                "numCandidates": 100,
                "limit": top_k,
                "similarity": "cosine"
            }
        },
        {
            "$project": {
                "title": 1,
                "description": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(collection.aggregate(pipeline))


# 벡터 인덱스 생성 (1536차원)
def create_vector_index_if_not_exists():
    index_name = "vector_index"
    existing_indexes = collection.list_search_indexes()
    if index_name in [idx["name"] for idx in existing_indexes]:
        logging.info(f"'{index_name}' 인덱스가 이미 존재합니다.")
        return

    index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": 1536,
                    "similarity": "cosine"
                }
            ]
        },
        name=index_name,
        type="vectorSearch"
    )

    try:
        collection.create_search_index(model=index_model)
        logging.info(f"'{index_name}' 인덱스가 생성되었습니다!")
    except OperationFailure as e:
        logging.error(f"벡터 인덱스 생성 실패: {e.details}")

create_vector_index_if_not_exists()
