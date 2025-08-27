# 권장 명령어

## 프로젝트 실행
```bash
# 의존성 설치
pip install -r requirements_ner.txt

# 웹 인터페이스 시작
python3 ner_web_interface.py

# 브라우저에서 접속
# http://localhost:8080
```

## 개발 도구
```bash
# 테스트 실행
python3 tests/test_overlapping_annotations.py

# 데모 실행
python3 examples/ner_demo.py

# 설치 스크립트 실행
bash install.sh
```

## 일반적인 시스템 명령어 (Linux)
```bash
# 파일 목록
ls -la

# 디렉토리 이동
cd <directory>

# 파일 검색
find . -name "*.py"
grep -r "pattern" .

# Git 작업
git status
git add .
git commit -m "message"
git push
```

## 패키지 관리
```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 업데이트
pip list --outdated
pip install --upgrade <package>
```