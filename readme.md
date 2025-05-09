<div align="center">
  <h1><img src="https://github.com/user-attachments/assets/13a24ec6-d806-49e7-b6a6-e3a6ed71943b" width="20"> Rezoom</h1>
  <p>AI 기반 이력서-채용공고 매칭 및 코칭 서비스</p>
</div>

---


## 프로젝트 개요

저희 프로젝트 **Rezoom**은 지원자의 이력서와 채용공고를 AI가 분석하여  **매칭 점수, 요약, 학습 로드맵, 자기소개서 피드백**을 제공하는  
**AI 기반 양방향 채용 매칭·코칭 플랫폼**입니다.
단순 API 사용이 아닌 직접 학습시킨 LoRA 기반 LLaMA3 모델 사용 

 [프로젝트 설명서 보기 (PDF)](https://drive.google.com/file/d/1nvfbnXT1kPhEXJKAFP8ScFdXQHpMChsF/view?usp=drive_link)
 
 [프로젝트 시연영상 보기 (Youtube)](https://youtu.be/D0xesYMLBeg)
### 주요 기능
- LLM 기반 이력서-채용공고 정밀 분석 및 매칭
- Multi-Agent 기반 피드백 & 로드맵 생성
- 프론트/백 분리 + 완전 MSA 구조 + ECS 자동 배포

---

## 시스템 아키텍처

| 영역             | 기술 구성                                                                                         |
|------------------|--------------------------------------------------------------------------------------------------|
| **Frontend**     | React                                                                                           |
| **Backend**      | Spring Boot (결제, 인증), FastAPI (AI 분석, DB 연동)                                              |
| **AI/LLM 모델**  | `LLaMA3 8B` (Unsloth LoRA fine-tuned) + CrewAI Agent + LangGraph GAN 구조                        |
| **데이터베이스** | PostgreSQL, MongoDB Atlas                                                                         |
| **스토리지**     | Amazon S3                                                                                        |
| **인프라**       | GitHub Actions → Docker → AWS ECR → ECS Fargate / RunPod 추론 서버                                |
| **기타 연동**    | Toss Payments, OpenAI API, Poetry, Wandb                                                         |

<div align="center">
  <h1>
    <img alt="image" src="https://github.com/user-attachments/assets/33d5c051-b1c9-4b0d-b380-ab68aee11e91" width="90%" style="margin: 10px;"/>
    <img src="https://github.com/user-attachments/assets/2c9b4b83-8843-4b61-a47f-76cdbc24d2b9" height="45%" style="margin: 10px;"/>
    <img width="556" alt="image" src="https://github.com/user-attachments/assets/d50d85d4-1973-446b-8354-1b169dd74ec3" style="margin: 10px;"/>
  </h1>
</div>

---

## 모델 상세

- **모델명**: `ninky0/rezoom-llama3.1-8b-4bit-b16-r64`
- **기반**: Meta LLaMA 3.1 8B, 4-bit 양자화, b16 r64 구조
- **파인튜닝**: Unsloth + Alpaca SFT
- **배포 환경**: RunPod 워커 병렬 추론 → FastAPI 호출로 응답
- **구성**: LLaMA3 기반 8B 모델, 4-bit LoRA, b16 r64 구조
- **추론 환경**: RunPod 병렬 워커 배포, FastAPI로 서빙
- **검증 흐름**: LangGraph 기반 GAN 구조 + Agent 기반 피드백 추천

---

## 화면

<div>
  <table>
    <tr>
      <td>
        <img src="https://github.com/user-attachments/assets/9fd6ce1e-8ef1-4d9d-98b1-85a7728aefbc" style="margin: 10px;">
      </td>
      <td>
        <img src="https://github.com/user-attachments/assets/6aa45948-a8d2-4746-bfb6-d8fdb352b1b1" style="margin: 10px;">
      </td>
    </tr>
    <tr>
      <td>
        <img src="https://github.com/user-attachments/assets/76f3040d-2280-4204-967c-7588c0e976bd" style="margin: 10px;">
      </td>
      <td> 
        <img src="https://github.com/user-attachments/assets/df6a2340-931e-440c-829b-34cca4378a03" style="margin: 10px;">
      </td>
    </tr>
  </table>
</div>

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


## 모델 저장소

[Hugging Face - ninky0/rezoom-llama3.1-8b-4bit-b16-r64](https://huggingface.co/ninky0/rezoom-llama3.1-8b-4bit-b16-r64)

---

## 팀원 및 팀 소개
## 🧑‍💻 팀원 및 팀 소개

| 김지환 | 남인경 | 손정원 | 정우찬 | 최정민 |
|:------:|:------:|:------:|:------:|:------:|
| <img src="https://github.com/user-attachments/assets/ccdf5839-bee6-44f1-a1f8-8d4fea6dd70e" width="100"/> | <img src="https://github.com/user-attachments/assets/d27f9342-eca2-4142-9c8f-df89c445e62a" width="100"/> | <img src="https://github.com/user-attachments/assets/148e27b1-22b0-4ad3-911f-186041e10b3c" width="100"/> | <img src="https://github.com/user-attachments/assets/962d7da4-135f-4d2b-9981-e923db94eff0" width="100"/> | <img src="https://github.com/user-attachments/assets/ceb4fff9-1da7-40d7-ac6e-45deffec56de" width="100"/> |
| PM, FE, AI | BE, FE, AI | BE, AI, Infra | BE, AI | FE, BE, AI |
| 전체 일정과 우선순위를 관리<br>프론트엔드 베이스 코드 구성, 리팩토링, 모듈화<br>모델 학습용 데이터셋 설계 · 생성<br>DeepSeek-Qwen-2.5 7B, Phi-4 4B, Llama-3.1 8B 파인튜닝<br>데이터셋, 모델 성능 평가 · 검증을 통해 모델 품질 개선<br><br> | SpringSecurity+JWT 기반 회원 관리 시스템<br>TossPayments 결제창 연동 및 크레딧 서비스<br>모델 학습용 데이터셋 구축 및 검증<br>Llama-3.1 8B 모델 QLoRA 방식 파인튜닝 및 배포<br>CrewAI+LangGraph 기반 자소서 피드백 서비스<br>Swagger를 활용한 API 명세 자동화<br>Intro.js를 활용한 사용자 온보딩 튜토리얼 구성 | Mistral 7B-instruct 파인튜닝<br>인프라 및 프로젝트 파이프라인 설계 및 구축<br>협업, 배포 및 서버 오류 모니터링 시스템 구축<br>ECS 기반 트래픽 로드밸런싱 및 비용 최적화 설계<br>Git Flow 전략 수립과 PR 관리, 메인 브랜치 유지<br>단계별 예외 처리와 보상 트랜잭션 및 롤백 구현<br>UML 및 시스템 아키텍처 설계 | FastAPI AI 서비스 백엔드 초기 설계 및 전담 개발<br>gemma-3.4b 모델 파인튜닝 및 데이터셋 추론<br>CrewAI 기반 에이전트 시스템 초기 기획 및 구축 담당<br>벡터 DB PDF 비정형 텍스트 / 임베딩 저장 파이프라인 설계 및 구축<br><br><br> | Llama-3.1 8B 기반 파인튜닝 및 성능 평가<br>프롬프트 엔지니어링을 통한 데이터 증강을 하여 학습 데이터셋 생성<br>Agent 기능을 LangGraph 기반 worker-evaluator 구조로 개선<br>프론트엔드 초기 설계 및 재정비, 에러 처리 시스템<br>UI/UX 화면설계 및 AX 인터랙션<br><br> |
| [GitHub](https://github.com/doram419) | [GitHub](https://github.com/Ninky0) | [GitHub](https://github.com/Sonyeoul) | [GitHub](https://github.com/hammer8130) | [GitHub](https://github.com/cjmin-n) |


<br/>

<div align="center">
본 프로젝트는 실무형 AI 채용 서비스를 위한  
엔드-투-엔드 아키텍처 구성 및 모델 추론 시스템을 구현하며 개발 역량을 강화하는 데 중점을 두었습니다.
</div>
