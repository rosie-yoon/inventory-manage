# 로로샵 재고 대여 관리 시스템 (Streamlit)

빠르고 효율적인 재고 대여 관리 시스템입니다. Google Sheets 연동과 실시간 데이터 분석을 지원합니다.

## 🚀 특징

- ⚡ **빠른 속도**: SQLite 데이터베이스로 즉각적인 응답
- 📊 **실시간 대시보드**: 월별 정산 현황을 한눈에
- 📁 **CSV 업로드**: Google Sheets 데이터를 간편하게 가져오기
- 📈 **시각화**: Plotly 차트로 데이터 분석
- 📱 **반응형**: 모바일, 태블릿, 데스크톱 모두 지원

## 📋 주요 기능

### 1. 대시보드
- 월별 총 정산 금액 (받을 금액/줄 금액)
- 샵별 정산 현황
- 최근 거래 내역 10건

### 2. 거래 내역 관리
- 거래 추가/삭제
- 상품 자동완성 (공급가 자동 입력)
- 월별/샵별/유형별 필터링

### 3. 상품 관리
- CSV 파일 업로드 (Google Sheets)
- 수동 상품 추가
- 전체 삭제 기능

### 4. 월별 통계
- 월별 통계 (빌려준/빌린 총액, 순 정산)
- 샵별 누적 통계 (차트)

## 🛠️ 설치 및 실행

### 로컬 환경

```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

### Streamlit Community Cloud 배포

1. GitHub 저장소 생성 및 코드 푸시
2. https://streamlit.io/cloud 접속
3. "New app" 클릭
4. GitHub 저장소 선택
5. Main file path: `app.py`
6. Deploy 클릭!

## 📁 파일 구조

```
.
├── app.py              # 메인 Streamlit 앱
├── requirements.txt    # Python 패키지 목록
├── README.md          # 프로젝트 설명서
└── lolo_shop.db       # SQLite 데이터베이스 (자동 생성)
```

## 💡 사용 방법

### CSV 업로드로 상품 등록

1. Google Sheets에서 "파일 → 다운로드 → CSV" 선택
2. "상품 관리" 페이지로 이동
3. CSV 파일 업로드
4. 완료!

**필수 열**: 상품명, SKU, 공급가

### 거래 추가

1. "거래 내역" 페이지로 이동
2. 날짜, 거래처, 상품명, 수량, 단가 입력
3. 거래 유형 선택 (빌려줌/빌림)
4. 저장 클릭

## 🎯 거래처 목록

- 원더조이
- 뚜샵
- 코스블라
- 온리
- 여진
- 소연

## 📊 데이터베이스

SQLite를 사용하여 로컬에 데이터를 저장합니다.

### 테이블 구조

**transactions** (거래 내역)
- id, date, shop, product_name, quantity, unit_price, total
- transaction_type (lend/borrow), month, created_at

**products** (상품 정보)
- id, product_name, sku, supply_price, created_at

## 🔒 보안

- 모든 데이터는 로컬 또는 Streamlit Cloud에 안전하게 저장
- GitHub에 민감한 정보 업로드 금지

## 📝 버전 히스토리

### v2.0 (2026-01-11) - Streamlit 버전
- 완전히 새로운 Streamlit 기반 앱
- SQLite 데이터베이스로 빠른 속도
- CSV 업로드 기능
- Plotly 차트 시각화

### v1.0 (2026-01-11) - 초기 버전
- HTML/CSS/JavaScript 기반
- RESTful Table API 사용

## 🤝 기여

문제가 발생하거나 개선 사항이 있으면 이슈를 등록해주세요!

## 📄 라이선스

이 프로젝트는 로로샵의 내부 관리 시스템입니다.

---

**Made with ❤️ by AI Assistant**
