from typing import List, Dict, Any
import os
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel
from dotenv import load_dotenv
from openai import OpenAI
import certifi
import logging
import asyncio
# 환경설정 및 로깅
load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# MongoDB 연결
ca = certifi.where()
client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=ca)
db = client["Rezoom"]
resumes_collection = db["resumes"]

# OpenAI 설정
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-3-small"

# 동기 임베딩 함수 (내부에서 사용)
def _sync_get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        logging.warning("[임베딩 요청 차단] 빈 텍스트")
        return []
    try:
        response = openai_client.embeddings.create(
            input=[text.strip()],
            model=EMBEDDING_MODEL
        )
        embedding = response.data[0].embedding
        if not embedding or len(embedding) != 1536:
            logging.error(f"[임베딩 오류] 벡터 길이 오류: {len(embedding)}")
            return []
        return embedding
    except Exception as e:
        logging.error(f"[임베딩 생성 실패]: {e}")
        return []

# 비동기 wrapper
async def get_embedding(text: str) -> List[float]:
    if not text or not text.strip():
        logging.warning("[임베딩 요청 차단] 빈 텍스트")
        return []
    return await asyncio.to_thread(_sync_get_embedding, text)

# 사용자 이력서 저장
async def store_resume_from_pdf(resume_text: str) -> str:
    try:
        embedding = await get_embedding(resume_text)
        doc = {
            "original_text": resume_text,
            "structured": {},  # PDF는 정형 데이터 파싱 생략하겠음
            "embedding": embedding,
            "source": "pdf"
        }
        result = resumes_collection.insert_one(doc)
        return str(result.inserted_id)
    except Exception as e:
        logging.error(f"[PDF 이력서 저장 실패]: {e}")
        return ""

# CSV 이력서 처리 == 이건 csv structed 추가하려고
def process_resume_csv(filepath: str) -> int:
    success_count = 0

    try:
        df = pd.read_csv(filepath, encoding='cp949')  # 또는 utf-8 안 돼면 둘 중에 하나
        for _, row in df.iterrows():
            try:
                # 전체 텍스트를 하나의 문자열로
                original_text = " ".join(str(v).strip() for v in row.values if pd.notnull(v))
                name = row.get("name", "").strip()
                skills = row.get("skills", "").strip()
                if not name or not skills:
                    continue

                skills_list = [s.strip() for s in skills.split(",") if s.strip()]
                education = row.get("education", "").strip()
                experience = row.get("experience", "").strip()
                self_intro = row.get("self_intro", "").strip()
                phone = row.get("phone", "").strip()
                email = row.get("email", "").strip()

                embed_input = f"{', '.join(skills_list)} {experience} {self_intro}"
                embedding = asyncio.run(get_embedding(embed_input))
                if not embedding:
                    continue

                document = {
                    "original_text": original_text,
                    "structured": {
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "skills": skills_list,
                        "education": education,
                        "experience": experience,
                        "self_intro": self_intro
                    },
                    "embedding": embedding,
                    "source": "csv"
                }

                resumes_collection.insert_one(document)
                success_count += 1

            except Exception as e:
                logging.error(f"[하이브리드 이력서 저장 실패]: {e}")

    except Exception as e:
        logging.error(f"[CSV 파싱 실패]: {e}")

    logging.info(f"[하이브리드 저장 완료] 유효 이력서 수: {success_count}")
    return success_count

# 유사도 검색
async def search_similar_resumes_with_score(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    query_vector = await get_embedding(query)
    
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
                "structured": "$structured",
                "original_text": "$original_text",   
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(resumes_collection.aggregate(pipeline))


# 벡터 인덱스 생성
def create_resume_vector_index_if_not_exists():
    index_name = "vector_index"
    existing_indexes = resumes_collection.list_search_indexes()
    if index_name in [idx["name"] for idx in existing_indexes]:
        logging.info(f"'{index_name}' resumes 컬렉션의 인덱스 이미 존재")
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
        resumes_collection.create_search_index(model=index_model)
        logging.info(f"[벡터 인덱스 생성 완료] '{index_name}'")
    except OperationFailure as e:
        logging.error(f"[벡터 인덱스 생성 실패]: {e.details}")

# 인덱스 생성 실행
create_resume_vector_index_if_not_exists()
print("\n저장된 이력서 수:", resumes_collection.count_documents({}))
