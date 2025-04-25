<div align="center">

<h1>Rezoom</h1>
<p>AI 기반 이력서-채용공고 매칭 및 코칭 서비스</p>


</div>

---

## 프로젝트 소개

**Rezoom**은 사용자의 이력서와 채용공고를 AI가 분석하여  
 매칭 점수 ·  요약 ·  학습 로드맵을 제공하는 **AI 기반 채용 매칭·코칭 서비스**입니다.

- 자체 파인튜닝한 LLM과 벡터 검색 시스템을 결합
- Multi-Agent 구조 기반의 AI 분석 & 코칭 흐름 구현
- 완전 모듈화된 MSA 아키텍처 기반 실시간 응답 시스템

---

## 시스템 구성

| 영역             | 기술 구성                                                                                                                                   |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **Frontend**     | React                                                                                                                       |
| **Backend**      | Spring Boot (결제 모듈 연동, S3 연동), FastAPI (AI 분석, 벡터 검색)                                                                 |
| **AI/LLM 모델**  | `LLaMA3 8B` (LoRA fine-tuned via Unsloth), CrewAI 기반 Agent, LangGraph GAN 검증                                                            |
| **데이터베이스** | PostgreSQL, MongoDB Atlas                                                                                                |
| **인프라**       | GitHub Actions → Docker → AWS ECR → ECS Fargate, RunPod 추론 서버                                                                             |
| **기타 연동**    | Toss Payments, Poetry, wandb, OpenAI API                                                                                                      |

---

## 모델 상세

- **모델명**: `ninky0/rezoom-llama3.1-8b-4bit-b16-r64-merged`
- **구성**: LLaMA3 기반 8B 모델, 4-bit LoRA, b16 r64 구조
- **추론 환경**: RunPod 병렬 워커 배포, FastAPI로 서빙
- **검증 흐름**: LangGraph 기반 GAN 구조 + Agent 기반 피드백 추천

---

## 기술 스택

<div align="center">

<img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=React&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=FastAPI&logoColor=white"/>
<img src="https://img.shields.io/badge/SpringBoot-6DB33F?style=flat-square&logo=SpringBoot&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=PostgreSQL&logoColor=white"/>
<img src="https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=MongoDB&logoColor=white"/>
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=Docker&logoColor=white"/>
<img src="https://img.shields.io/badge/AWS_ECS-F8991D?style=flat-square&logo=amazonaws&logoColor=white"/>
<img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white"/>
<img src="https://img.shields.io/badge/TossPayments-0984E3?style=flat-square&logoColor=white"/>
<img src="https://img.shields.io/badge/Poetry-3D3D3D?style=flat-square&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/RunPod-purple?style=flat-square&logo=docker&logoColor=white"/>

</div>

---



- 🤖 모델 저장소: [Hugging Face - ninky0/rezoom](https://huggingface.co/ninky0/rezoom-llama3.1-8b-4bit-b16-r64-merged)


---

<div align="center">

⭐ 본 프로젝트는 실무형 AI 서비스 구축을 위한 종합적인 실험과 개발 경험을 바탕으로 진행되었습니다.

</div>
