# KDPII NER Labeler 테스트 스위트

KDPII NER Labeler 시스템의 종합 테스트 스위트입니다.

## 📁 디렉토리 구조

```
test-suite/
├── config/                    # 테스트 설정 파일
│   ├── pytest.ini           # pytest 설정
│   └── conftest.py          # 공통 픽스처 및 설정
├── requirements/              # 테스트 의존성
│   └── requirements-test.txt # 테스트 패키지 목록
├── scripts/                   # 테스트 실행 스크립트
│   └── run_tests.py         # 메인 테스트 러너
├── test-data/                # 테스트 데이터
│   ├── test_upload_samples.json
│   ├── test_upload_samples.jsonl
│   └── test_upload_samples.txt
└── tests/                    # 테스트 케이스들
    ├── unit/                 # 단위 테스트
    │   ├── test_ner_core.py
    │   └── test_database.py
    ├── integration/          # 통합 테스트
    │   ├── test_flask_api.py
    │   ├── test_backend_services.py
    │   ├── test_integration.py
    │   └── test_overlapping_annotations.py
    ├── frontend/             # 프론트엔드 테스트
    │   └── test_frontend.py
    └── e2e/                  # 엔드투엔드 테스트
        └── test_end_to_end.py
```

## 🚀 테스트 실행 방법

### 환경 설정

```bash
# 테스트 의존성 설치
pip install -r test-suite/requirements/requirements-test.txt
```

### 테스트 실행

```bash
# 모든 테스트 실행
python3 test-suite/scripts/run_tests.py

# 특정 카테고리만 실행
python3 test-suite/scripts/run_tests.py --unit         # 단위 테스트만
python3 test-suite/scripts/run_tests.py --integration  # 통합 테스트만
python3 test-suite/scripts/run_tests.py --frontend     # 프론트엔드 테스트만
python3 test-suite/scripts/run_tests.py --e2e          # 엔드투엔드 테스트만

# 기타 옵션
python3 test-suite/scripts/run_tests.py --quick        # 빠른 테스트만
python3 test-suite/scripts/run_tests.py --coverage     # 커버리지 포함
python3 test-suite/scripts/run_tests.py --performance  # 성능 테스트만
python3 test-suite/scripts/run_tests.py --verbose      # 상세 출력
```

### pytest 직접 사용

```bash
# 설정 파일을 사용한 pytest 직접 실행
python3 -m pytest -c test-suite/config/pytest.ini test-suite/tests/

# 특정 카테고리만
python3 -m pytest -c test-suite/config/pytest.ini test-suite/tests/unit/
python3 -m pytest -c test-suite/config/pytest.ini test-suite/tests/integration/
```

## 📋 테스트 카테고리

### 단위 테스트 (Unit Tests)
- **test_ner_core.py**: NER 엔진 핵심 기능 테스트
- **test_database.py**: 데이터베이스 작업 및 모델 테스트

### 통합 테스트 (Integration Tests)
- **test_flask_api.py**: Flask API 엔드포인트 통합 테스트
- **test_backend_services.py**: 백엔드 서비스 레이어 테스트
- **test_integration.py**: 컴포넌트 간 통합 테스트
- **test_overlapping_annotations.py**: 중첩 주석 기능 테스트

### 프론트엔드 테스트 (Frontend Tests)
- **test_frontend.py**: Playwright를 사용한 UI 자동화 테스트

### 엔드투엔드 테스트 (E2E Tests)
- **test_end_to_end.py**: 전체 워크플로우 및 실제 사용 시나리오 테스트

## 🧪 테스트 커버리지

### 기능별 테스트 범위
- ✅ 문서 CRUD 작업
- ✅ 주석 생성, 수정, 삭제 (중첩 주석 포함)
- ✅ Label Studio 및 CoNLL 형식 내보내기
- ✅ 데이터베이스 스키마 검증
- ✅ Flask API 엔드포인트 (74개 라우트)
- ✅ 프론트엔드 사용자 상호작용
- ✅ 키보드 단축키 기능
- ✅ 다국어 콘텐츠 처리
- ✅ 성능 및 확장성 테스트
- ✅ 오류 복구 시나리오

### 실제 사용 시나리오
- 뉴스 기사 주석 작업 워크플로우
- 과학 문서 처리 및 엔티티 추출
- 다국어 문서 처리 (한국어, 일본어 포함)
- 대량 문서 배치 처리
- 동시 사용자 시나리오

## ⚙️ 설정 및 구성

### pytest.ini
- 테스트 검색 경로 설정
- 마커 정의 (unit, integration, e2e, performance 등)
- 커버리지 리포팅 설정
- 경고 필터링

### conftest.py
- 공통 픽스처 정의
- 앱 인스턴스 생성
- 데이터베이스 설정
- 테스트 데이터 생성
- Mock 객체 설정

## 📊 테스트 결과 및 리포팅

테스트 실행 후 다음 결과물이 생성됩니다:

- **htmlcov/**: HTML 커버리지 리포트
- **test_report.json**: 상세 테스트 실행 결과
- **coverage.xml**: XML 형식 커버리지 데이터

## 🔧 개발 및 확장

### 새 테스트 추가
1. 적절한 카테고리 디렉토리에 테스트 파일 생성
2. `test_*.py` 명명 규칙 따르기  
3. conftest.py의 픽스처 활용
4. 적절한 마커 사용 (`@pytest.mark.unit`, `@pytest.mark.integration` 등)

### 테스트 러너 수정
`test-suite/scripts/run_tests.py`에서 새로운 테스트 카테고리나 실행 옵션 추가 가능

## 🐛 문제 해결

### 일반적인 문제들
1. **ImportError**: `sys.path` 설정이 올바른지 확인
2. **Database errors**: 임시 데이터베이스 생성 권한 확인
3. **Playwright errors**: 브라우저 드라이버 설치 상태 확인

### 디버깅
```bash
# 상세 출력으로 테스트 실행
python3 test-suite/scripts/run_tests.py --verbose

# 특정 테스트 파일만 실행
python3 -m pytest -c test-suite/config/pytest.ini test-suite/tests/unit/test_ner_core.py -v
```

## 📝 참고사항

- 모든 테스트는 프로젝트 루트 디렉토리에서 실행해야 합니다
- 테스트 실행 전 필요한 의존성을 설치했는지 확인하세요
- 시스템 환경에 따라 일부 테스트가 스킵될 수 있습니다
- 성능 테스트는 시스템 리소스에 따라 결과가 달라질 수 있습니다