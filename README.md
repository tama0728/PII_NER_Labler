# KDPII Labeler - NER Annotation Platform

개발자 인수인계 문서

## 프로젝트 개요

KDPII Labeler는 Named Entity Recognition (NER) 어노테이션을 위한 웹 플랫폼입니다. Flask 기반의 백엔드와 JavaScript 프론트엔드로 구성되어 있으며, 팀 협업 기능과 개별 작업 환경을 모두 제공합니다.

## 시스템 아키텍처

```
kdpii_labler/
├── app.py                      # 메인 애플리케이션 엔트리포인트
├── ner_extractor.py           # NER 핵심 로직 모듈
├── backend/                   # 백엔드 레이어
│   ├── models/               # 데이터 모델
│   ├── services/             # 비즈니스 로직
│   ├── repositories/         # 데이터 액세스
│   ├── api.py               # RESTful API 엔드포인트
│   ├── views.py             # 웹 뷰 라우터
│   └── collaboration_api.py  # 협업 기능 API
├── frontend/                 # 프론트엔드
│   ├── templates/           # HTML 템플릿
│   └── static/             # CSS, JS 정적 파일
├── data/                    # 데이터 저장소
├── exports/                 # 내보내기 파일
└── workspace_data/         # 워크스페이스 데이터
```

## 핵심 기능

### 1. NER 어노테이션 시스템
- 텍스트에서 개체명 인식 및 라벨링
- Label Studio 스타일 인터페이스
- 실시간 어노테이션 편집

### 2. 협업 워크스페이스
- 팀 단위 워크스페이스 생성/관리
- 다중 사용자 동시 작업
- 어노테이션 병합 및 충돌 해결

### 3. 데이터 관리
- JSONL 파일 업로드/다운로드
- 다양한 포맷 지원 (Label Studio, CoNLL)
- 배치 처리 및 대용량 파일 처리

## 주요 모듈 및 함수

### app.py
메인 애플리케이션 팩터리

**핵심 함수:**
- `create_app()`: Flask 앱 생성 및 설정
- `ner_create_task()`: NER 태스크 생성
- `ner_add_annotation()`: 어노테이션 추가
- `get_exports()`: 내보내기 파일 목록 조회
- `save_completed_file()`: 완성된 파일 저장

### ner_extractor.py
NER 어노테이션 핵심 로직

**주요 클래스:**
- `NERExtractor`: 메인 NER 처리 클래스
- `NERLabel`: 라벨 정의 데이터클래스
- `NERAnnotation`: 어노테이션 데이터클래스
- `NERTask`: 태스크 데이터클래스

**핵심 함수:**
- `create_task(text)`: 새 어노테이션 태스크 생성
- `add_annotation(task_id, start, end, labels)`: 어노테이션 추가
- `export_task(task_id)`: Label Studio 포맷으로 내보내기
- `export_conll_format(task_id)`: CoNLL 포맷으로 내보내기
- `create_label(value, background, hotkey)`: 새 라벨 생성

### backend/api.py
RESTful API 엔드포인트

**핵심 함수:**
- `get_projects()`: 프로젝트 목록 조회
- `create_project()`: 새 프로젝트 생성
- `create_task()`: 태스크 생성
- `create_annotation()`: 어노테이션 생성
- `export_task()`: 태스크 내보내기
- `get_statistics()`: 통계 정보 조회

### backend/collaboration_api.py
협업 기능 API

**핵심 함수:**
- `create_workspace()`: 워크스페이스 생성
- `join_workspace()`: 워크스페이스 참여
- `merge_annotations()`: 어노테이션 병합
- `export_workspace()`: 워크스페이스 데이터 내보내기
- `upload_file()`: 파일 업로드 처리
- `batch_upload()`: 배치 파일 업로드

### backend/services/
비즈니스 로직 서비스 레이어

**주요 서비스:**
- `CollaborationService`: 협업 워크스페이스 관리
- `TaskService`: 태스크 관리
- `AnnotationService`: 어노테이션 처리
- `LabelService`: 라벨 관리
- `ProjectService`: 프로젝트 관리
- `DataImportService`: 데이터 가져오기

### frontend/static/js/
프론트엔드 JavaScript 모듈

**주요 모듈:**
- `auth.js`: 인증 관리 (`AuthManager` 클래스)
- `project-manager.js`: 프로젝트 관리 UI

## 데이터베이스 모델

### Task
- `id`: 태스크 고유 ID
- `text`: 어노테이션할 텍스트
- `project_id`: 소속 프로젝트 ID
- `status`: 진행 상태

### Annotation
- `id`: 어노테이션 고유 ID  
- `task_id`: 소속 태스크 ID
- `start`: 시작 위치
- `end`: 끝 위치
- `labels`: 적용된 라벨 목록

### Label
- `id`: 라벨 고유 ID
- `value`: 라벨 텍스트
- `background`: 배경색
- `hotkey`: 단축키

### Project
- `id`: 프로젝트 고유 ID
- `name`: 프로젝트 이름
- `description`: 설명

## API 엔드포인트

### NER API
- `POST /api/ner/tasks`: 새 태스크 생성
- `GET /api/ner/tasks/<task_id>`: 태스크 조회
- `POST /api/ner/tasks/<task_id>/annotations`: 어노테이션 추가
- `GET /api/ner/tasks/<task_id>/export`: Label Studio 포맷 내보내기
- `GET /api/ner/tasks/<task_id>/conll`: CoNLL 포맷 내보내기
- `GET /api/ner/statistics`: 통계 정보
- `GET /api/ner/config`: Label Studio 설정

### 라벨 관리 API
- `GET /api/ner/tags`: 모든 라벨 조회
- `POST /api/ner/tags`: 새 라벨 생성
- `GET /api/ner/tags/<label_id>`: 특정 라벨 조회
- `PUT /api/ner/tags/<label_id>`: 라벨 수정
- `DELETE /api/ner/tags/<label_id>`: 라벨 삭제

### 협업 API
- `GET /collab/workspaces`: 워크스페이스 목록
- `POST /collab/workspaces`: 워크스페이스 생성
- `POST /collab/workspaces/<ws_id>/join`: 워크스페이스 참여
- `POST /collab/workspaces/<ws_id>/tasks`: 태스크 생성
- `POST /collab/workspaces/<ws_id>/merge`: 어노테이션 병합
- `GET /collab/workspaces/<ws_id>/export`: 데이터 내보내기

### 파일 관리 API
- `GET /api/exports`: 내보내기 파일 목록
- `GET /api/exports/<file_id>/download`: 파일 다운로드
- `GET /api/exports/<file_id>/preview`: 파일 미리보기
- `DELETE /api/exports/<file_id>`: 파일 삭제
- `POST /api/save-modified-file`: 수정된 파일 저장
- `POST /api/save-completed-file`: 완성된 파일 저장

## 설정 및 환경변수

### config.py 주요 설정
- `SECRET_KEY`: Flask 보안 키

- `UPLOAD_FOLDER`: 파일 업로드 디렉토리
- `MAX_CONTENT_LENGTH`: 최대 파일 크기 (16MB)

### 환경변수
- `SECRET_KEY`: 프로덕션 보안 키
- `UPLOAD_FOLDER`: 업로드 폴더 경로

## 실행 방법

### 개발 환경
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python app.py

# 또는 포트 지정 실행
python app.py --port 8081
```

### 프로덕션 배포
```bash
# 환경변수 설정
export SECRET_KEY="your-production-secret-key"

# 애플리케이션 실행
gunicorn --reload 'app:create_app()' --bind 0.0.0.0:8080
```

## 파일 구조 상세

### 데이터 디렉토리
- `data/`: SQLite 데이터베이스 및 업로드 파일
- `exports/modified/`: 수정된 파일 저장
- `exports/completed/`: 완성된 어노테이션 파일 저장
- `workspace_data/`: 워크스페이스 메타데이터

### 템플릿
- `dashboard.html`: 메인 대시보드
- `collaborate.html`: 협업 워크스페이스 목록
- `workspace_ner_interface.html`: NER 어노테이션 인터페이스

## 주요 기술 스택

- **백엔드**: Flask, SQLAlchemy, SQLite
- **프론트엔드**: HTML5, JavaScript (ES6+), CSS3
- **데이터 처리**: pandas, numpy
- **NER**: spaCy (확장 가능)

## 개발 시 주의사항

1. **세션 관리**: 워크스페이스 참여 시 세션에 `workspace_id`, `member_name` 저장
2. **파일 업로드**: JSONL 포맷 검증 및 대용량 파일 처리
3. **어노테이션 병합**: 충돌 해결 로직 확인 필요
4. **데이터베이스**: SQLite 사용
5. **보안**: 프로덕션 환경에서 SECRET_KEY 반드시 설정


## 트러블슈팅

### 일반적인 문제
1. **포트 충돌**: `--port` 옵션으로 다른 포트 사용
2. **데이터베이스 락**: SQLite 동시 접근 제한 시 재시도
3. **메모리 부족**: 대용량 파일 처리 시 스트리밍 사용
4. **파일 권한**: exports, data 디렉토리 쓰기 권한 확인

### 로그 확인
```bash
# 애플리케이션 로그 확인
tail -f app.log

# 데이터베이스 상태 확인
sqlite3 data/kdpii_labeler.db ".tables"
```

## 연락처 및 지원

프로젝트 관련 문의사항이나 기술적 이슈가 있을 경우, 코드 내 주석과 이 문서를 참고하여 개발을 진행하시기 바랍니다.