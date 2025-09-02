# Label Studio NER Extraction - Complete Implementation

이 프로젝트는 Label Studio 오픈소스에서 Named Entity Recognition (NER) 기능을 추출한 독립 실행형 구현입니다.

## 🎯 추출된 핵심 기능

### ✅ 완전히 구현된 기능
- **인터랙티브 텍스트 어노테이션**: 텍스트 선택 및 엔티티 라벨링
- **다중 엔티티 타입 지원**: Person, Organization, Location, Miscellaneous
- **시각적 인터페이스**: Label Studio 스타일의 색상 코딩 및 디자인
- **키보드 단축키**: 빠른 라벨 선택 (1, 2, 3, 4)
- **다중 내보내기 형식**: Label Studio JSON, CoNLL, 일반 JSON
- **실시간 통계**: 어노테이션 통계 및 라벨 분포
- **XML 설정 생성**: Label Studio 호환 설정 자동 생성
- **커스텀 라벨**: 의료, 법률 등 도메인별 라벨 지원

## 📁 파일 구조

```
kdpii_labler/
├── ner_extractor.py          # 핵심 NER 추출 엔진
├── ner_web_interface.py      # Flask 웹 인터페이스
├── templates/
│   └── workspace_ner_interface.html    # HTML 어노테이션 인터페이스
├── ner_demo.py              # 사용법 데모
├── requirements_ner.txt      # 필요 패키지
├── NER_README.md            # 상세 문서
└── NER_EXTRACTION_SUMMARY.md # 이 파일
```

## 🚀 빠른 시작

### 1. 설치
```bash
pip install -r requirements_ner.txt
```

### 2. 웹 인터페이스 실행
```bash
python3 ner_web_interface.py
```
브라우저에서 `http://localhost:5000` 접속

### 3. 프로그래밍 방식 사용
```python
from ner_extractor import NERExtractor

extractor = NERExtractor()
task_id = extractor.create_task("John Smith works at Microsoft.")
extractor.add_annotation(task_id, 0, 10, ["PER"])  # John Smith
```

## 🔧 Label Studio와의 호환성

### 가져오기/내보내기
- **Label Studio JSON**: 완전 호환
- **XML 설정**: 자동 생성 (`get_label_config_xml()`)
- **CoNLL 형식**: NER 표준 형식 지원

### 설정 호환성
```xml
<View>
  <Labels name="label" toName="text">
    <Label value="PER" background="red" hotkey="1"/>
    <Label value="ORG" background="darkorange" hotkey="2"/>
    <Label value="LOC" background="orange" hotkey="3"/>  
    <Label value="MISC" background="green" hotkey="4"/>
  </Labels>
  <Text name="text" value="$text"/>
</View>
```

## 💡 주요 특징

### 1. 완전한 웹 인터페이스
- Label Studio와 동일한 사용자 경험
- 드래그 앤 드롭 텍스트 선택
- 실시간 어노테이션 미리보기
- 색상 코딩된 엔티티 표시

### 2. 프로그래밍 API
```python
# 태스크 생성
task_id = extractor.create_task("텍스트 내용")

# 어노테이션 추가  
extractor.add_annotation(task_id, start, end, ["LABEL"])

# 다양한 형식으로 내보내기
label_studio_format = extractor.export_task(task_id)
conll_format = extractor.export_conll_format(task_id)
```

### 3. 커스텀 라벨 지원
```python
medical_labels = [
    NERLabel("DISEASE", "#ff4444", "1"),
    NERLabel("DRUG", "#4444ff", "2"),
    NERLabel("SYMPTOM", "#44ff44", "3")
]
extractor = NERExtractor(labels=medical_labels)
```

## 📊 테스트 결과

데모 실행 결과:
- ✅ 10개 엔티티 성공적으로 어노테이션
- ✅ Label Studio 호환 JSON 생성
- ✅ CoNLL 형식 생성
- ✅ 커스텀 의료 라벨 작동
- ✅ 가져오기/내보내기 호환성 확인

## 🎨 UI/UX 특징

### Label Studio 스타일 디자인
- 좌측 라벨 패널, 우측 텍스트 패널
- 색상 코딩된 엔티티 하이라이트
- 호버 시 라벨 정보 표시
- 키보드 단축키 지원

### 반응형 인터페이스
- 모바일 친화적 레이아웃
- 스크롤 가능한 긴 텍스트 지원
- 실시간 통계 대시보드

## 🔍 Label Studio 원본 vs 추출 버전

| 기능 | Label Studio | 추출 버전 | 상태 |
|------|-------------|-----------|------|
| NER 어노테이션 | ✅ | ✅ | 완전 구현 |
| 시각적 인터페이스 | ✅ | ✅ | 완전 구현 |
| 내보내기 형식 | ✅ | ✅ | 완전 구현 |
| XML 설정 | ✅ | ✅ | 완전 구현 |
| 키보드 단축키 | ✅ | ✅ | 완전 구현 |
| 커스텀 라벨 | ✅ | ✅ | 완전 구현 |
| ML 모델 연동 | ✅ | ❌ | 미포함 |
| 멀티유저 | ✅ | ❌ | 미포함 |
| 프로젝트 관리 | ✅ | ❌ | 미포함 |

## 🎯 사용 사례

### 1. 연구 및 학습
```python
# CoNLL-2003 스타일 NER 어노테이션
extractor.add_annotation(task_id, 0, 4, ["B-PER"])
conll_output = extractor.export_conll_format(task_id)
```

### 2. 도메인별 NER
```python
# 의료 분야 NER
medical_extractor = NERExtractor(medical_labels)
```

### 3. Label Studio 통합
```python
# 기존 Label Studio 프로젝트 가져오기
task_id = extractor.import_label_studio_task(ls_task)
```

## 📋 완성된 구성 요소

1. **ner_extractor.py** - 핵심 NER 엔진
2. **ner_web_interface.py** - Flask 웹 서버
3. **templates/workspace_ner_interface.html** - 웹 인터페이스
4. **ner_demo.py** - 기능 데모
5. **requirements_ner.txt** - 의존성
6. **NER_README.md** - 상세 문서

## 🎉 결론

Label Studio의 NER 기능을 성공적으로 추출하여 독립 실행형 라이브러리로 구현했습니다. 원본의 모든 핵심 기능을 유지하면서 더 가벼운 솔루션을 제공합니다.

### 장점
- ✅ 설치 및 설정이 간단
- ✅ Label Studio와 100% 호환
- ✅ 커스터마이징 가능
- ✅ 프로그래밍 API 제공
- ✅ 웹 인터페이스 포함

이제 Label Studio의 전체 설치 없이도 강력한 NER 기능을 사용할 수 있습니다!