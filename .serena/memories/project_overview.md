# 프로젝트 개요

**프로젝트명**: KDPII Labeler (NER Annotation Tool)
**목적**: Label Studio에서 추출한 독립형 Named Entity Recognition (NER) 어노테이션 도구

## 주요 기능
- 텍스트 스팬 선택을 통한 대화형 어노테이션
- 여러 엔티티 타입 지원 (Person, Organization, Location, Miscellaneous)
- 중첩 및 겹치는 어노테이션 지원
- 키보드 단축키 지원
- Label Studio 호환 import/export
- CoNLL 형식 export
- 실시간 통계 대시보드

## 기술 스택
- **백엔드**: Python 3.7+, Flask 2.3+
- **프론트엔드**: HTML, JavaScript, Label Studio 기반 인터페이스
- **데이터 형식**: JSON, CoNLL-U
- **선택적 의존성**: spaCy, scikit-learn, numpy, pandas

## 주요 구성 요소
- `ner_extractor.py`: 핵심 NER 추출 엔진
- `ner_web_interface.py`: Flask 웹 애플리케이션
- `templates/ner_interface.html`: 웹 인터페이스 템플릿
- `static/`: 정적 웹 자산

## 사용 사례
1. 연구 및 개발용 NER 데이터 생성
2. 도메인 특화 NER 모델 학습 데이터 제작
3. Label Studio 프로젝트와의 통합