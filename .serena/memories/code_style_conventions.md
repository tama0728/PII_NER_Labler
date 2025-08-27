# 코드 스타일 및 관례

## Python 코드 스타일
- **PEP 8** 준수
- **함수명**: snake_case (예: `create_task`, `add_annotation`)
- **클래스명**: PascalCase (예: `NERExtractor`, `NERLabel`) 
- **상수**: UPPER_SNAKE_CASE
- **파일명**: snake_case.py

## 문서화
- **Docstrings**: 모든 공개 함수와 클래스에 docstring 사용
- **타입 힌트**: 주요 함수에서 사용 (완전하지는 않음)
- **주석**: 한국어와 영어 혼용

## 프로젝트 구조 패턴
- `templates/`: Jinja2 HTML 템플릿
- `static/`: CSS, JavaScript, 이미지 등
- `tests/`: 테스트 파일
- `examples/`: 사용 예제
- `docs/`: 문서화

## Flask 패턴
- **Route 구조**: REST API 스타일 (`/api/tasks`, `/api/statistics`)
- **에러 처리**: try-except 블록 사용
- **JSON 응답**: `jsonify()` 사용
- **디버깅**: `debug=True` 모드 활성화

## 데이터 구조
- **클래스 기반**: NERExtractor, NERLabel, NERTask, NERAnnotation
- **JSON 호환**: `to_dict()` 메서드 구현
- **ID 생성**: UUID 사용