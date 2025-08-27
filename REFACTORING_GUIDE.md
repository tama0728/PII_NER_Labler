# 🏗️ KDPII Labeler 리팩토링 가이드

## 📋 리팩토링 개요

기존 단일 파일 구조를 **Front-Back-DB** 3계층 아키텍처로 리팩토링하여 확장성과 유지보수성을 대폭 개선했습니다.

## 🎯 새로운 아키텍처 구조

```
kdpii_labeler/
├── backend/                    # 🔧 백엔드 레이어
│   ├── models/                # 📊 데이터 모델 (SQLAlchemy ORM)
│   │   ├── user.py           # 사용자 모델
│   │   ├── project.py        # 프로젝트 모델
│   │   ├── task.py           # 태스크 모델
│   │   ├── annotation.py     # 어노테이션 모델
│   │   └── label.py          # 라벨 모델
│   ├── repositories/          # 🗃️ 데이터 접근 레이어 (Repository 패턴)
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   ├── task_repository.py
│   │   ├── annotation_repository.py
│   │   └── label_repository.py
│   ├── services/              # 🔄 비즈니스 로직 레이어
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── task_service.py
│   │   ├── annotation_service.py
│   │   ├── label_service.py
│   │   └── data_import_service.py
│   ├── app.py                 # 🚀 Flask 애플리케이션 팩토리
│   ├── config.py              # ⚙️ 환경별 설정 관리
│   ├── database.py            # 🗄️ 데이터베이스 초기화
│   ├── auth.py                # 🔐 인증 라우트
│   └── api.py                 # 🌐 REST API 엔드포인트
├── frontend/                   # 🎨 프론트엔드 레이어
│   ├── static/
│   │   ├── js/
│   │   │   ├── auth.js        # 인증 관리 모듈
│   │   │   └── project-manager.js # 프로젝트 관리 모듈
│   │   └── css/
│   │       └── style.css      # 스타일시트
│   └── templates/
│       ├── base.html          # 기본 템플릿
│       └── dashboard.html     # 대시보드 페이지
└── data/                       # 📁 데이터 디렉토리
    ├── uploads/               # 업로드 파일
    └── exports/               # 내보내기 파일
```

## 🔑 핵심 디자인 패턴

### 1. **MVC (Model-View-Controller) 패턴**
- **Model**: SQLAlchemy 모델 (`backend/models/`)
- **View**: HTML 템플릿 + JavaScript 모듈 (`frontend/`)
- **Controller**: Flask 라우트 (`backend/auth.py`, `backend/api.py`)

### 2. **Repository 패턴**
- 데이터 접근 로직을 비즈니스 로직에서 분리
- 테스트 가능하고 확장 가능한 구조
- 일관된 CRUD 인터페이스 제공

### 3. **Service 레이어**
- 복잡한 비즈니스 로직을 캡슐화
- 권한 검사 및 데이터 검증 담당
- 여러 Repository를 조합한 복합 연산

### 4. **의존성 주입 (DI)**
- 서비스 간 느슨한 결합
- 테스트 가능한 코드 구조

## 🚀 새 구조 사용법

### 애플리케이션 실행

```bash
# 기존 방식
python ner_web_interface.py

# 새 방식
python -m backend.app
# 또는
cd backend && python app.py
```

### 개발 환경 설정

```bash
# 의존성 설치
pip install flask flask-sqlalchemy flask-login

# 데이터베이스 초기화 (자동)
# 첫 실행 시 SQLite DB가 data/ 폴더에 생성됩니다

# 기본 관리자 계정
# Username: admin
# Password: admin123
```

## 📊 기능별 사용 예제

### 1. 사용자 관리

```python
from backend.services.user_service import UserService

user_service = UserService()

# 사용자 생성
user = user_service.create_user(
    username="annotator1",
    email="ann1@example.com", 
    password="password123",
    role="annotator"
)

# 인증
authenticated_user = user_service.authenticate_user("annotator1", "password123")
```

### 2. 프로젝트 관리

```python
from backend.services.project_service import ProjectService

project_service = ProjectService()

# 프로젝트 생성 (기본 라벨 자동 생성)
project = project_service.create_project(
    name="NER Dataset 2024",
    owner_id=user.id,
    description="새로운 NER 데이터셋 프로젝트"
)

# 프로젝트 통계 조회
stats = project_service.get_project_with_statistics(project.id, user.id)
```

### 3. 태스크 및 어노테이션

```python
from backend.services.task_service import TaskService
from backend.services.annotation_service import AnnotationService

task_service = TaskService()
annotation_service = AnnotationService()

# 태스크 생성
task = task_service.create_task(
    project_id=project.id,
    text="John Smith works at Microsoft in Seattle.",
    user_id=user.id
)

# 어노테이션 추가
annotation = annotation_service.create_annotation(
    task_id=task.id,
    start=0, end=10,
    text="John Smith",
    labels=["PER"],
    user_id=user.id,
    confidence="high"
)
```

## 🔄 기존 코드에서 마이그레이션

### Before (기존 구조)
```python
# ner_web_interface.py에서 직접 처리
from ner_extractor import NERExtractor

extractor = NERExtractor()
task_id = extractor.create_task(text)
annotation_id = extractor.add_annotation(task_id, start, end, labels)
```

### After (새 구조)
```python
# 계층화된 서비스 사용
from backend.services.task_service import TaskService
from backend.services.annotation_service import AnnotationService

task_service = TaskService()
annotation_service = AnnotationService()

task = task_service.create_task(project_id, text, user_id)
annotation = annotation_service.create_annotation(
    task.id, start, end, text, labels, user_id
)
```

## 🔐 새로운 보안 기능

### 사용자 인증 시스템
- Flask-Login 기반 세션 관리
- 비밀번호 해싱 (werkzeug.security)
- 역할 기반 권한 제어 (admin, annotator, viewer)

### 접근 권한 제어
```python
# 프로젝트 접근 권한 확인
if project_service.validate_project_access(project_id, user_id, 'write'):
    # 쓰기 작업 수행
    pass

# 어노테이션 권한 확인  
if task_service.validate_task_access(task_id, user_id, 'annotate'):
    # 어노테이션 작업 수행
    pass
```

## 📊 데이터베이스 스키마

### 핵심 테이블 관계
```sql
users (id, username, email, role, ...)
  ↓ (1:N)
projects (id, name, owner_id, ...)
  ↓ (1:N)  
tasks (id, project_id, text, annotator_id, ...)
  ↓ (1:N)
annotations (id, task_id, start, end, labels, ...)

projects ← (1:N) → labels (id, project_id, value, background, ...)
```

## 🚧 향후 확장 계획

### 1. 로그인 시스템 완성
- 회원가입/로그인 UI 개선
- 사용자별 작업공간 분리
- 프로젝트 공유 기능

### 2. 데이터 관리 시스템
- JSONL 파일 업로드/다운로드
- 배치 데이터 처리
- 데이터 진행상태 추적

### 3. 고급 기능
- 실시간 협업 (WebSocket)
- 머신러닝 모델 연동
- 고급 통계 및 리포팅

## ⚡ 성능 개선 사항

1. **데이터베이스 최적화**: 인덱스 및 관계 최적화
2. **코드 재사용성**: Repository 패턴으로 중복 제거
3. **메모리 효율성**: 지연 로딩 및 페이지네이션
4. **확장성**: 모듈화된 구조로 기능 추가 용이

## 🔧 개발자 가이드

### 새 기능 추가 시 순서
1. **Model** 정의 (`backend/models/`)
2. **Repository** 구현 (`backend/repositories/`)
3. **Service** 로직 작성 (`backend/services/`)
4. **API** 엔드포인트 추가 (`backend/api.py`)
5. **Frontend** 모듈 구현 (`frontend/static/js/`)

### 테스트 작성
```python
# 예시: User Service 테스트
import unittest
from backend.services.user_service import UserService

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        service = UserService()
        user = service.create_user("test", "test@example.com", "pass123")
        self.assertIsNotNone(user.id)
```

## ✨ 마이그레이션 체크리스트

- [x] 기존 NERExtractor 기능을 Service 레이어로 분리
- [x] SQLAlchemy 모델로 데이터 구조 정의
- [x] Repository 패턴으로 데이터 접근 추상화
- [x] Flask-Login으로 인증 시스템 구축
- [x] REST API 설계 및 구현
- [x] 프론트엔드 모듈화 및 SPA 구조
- [ ] 기존 템플릿을 새 구조로 완전 이전
- [ ] 데이터 가져오기/내보내기 기능 완성
- [ ] 포괄적인 테스트 슈트 작성

---

**🎉 축하합니다!** KDPII Labeler가 현대적이고 확장 가능한 웹 애플리케이션으로 발전했습니다.