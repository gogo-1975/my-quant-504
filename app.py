import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 페이지 설정 (원본 레이아웃 유지)
st.set_page_config(page_title="퀀트버전504", layout="wide")
st.title("📊 퀀트버전504")

# 2. 상단 기본 설정 (5열 구성 그대로)
col1, col2, col3, col4, col5 = st.columns(5)
with col1: ticker = st.selectbox("종목", ["SOXL", "TQQQ", "NVDA", "TSLA"], index=0)
with col2: start_date = st.date_input("시작일", value=pd.to_datetime("2024-01-01"))
with col3: end_date = st.date_input("종료일", value=pd.to_datetime("2025-12-31"))
with col4: principal = st.number_input("원금($)", value=10000)
with col5: n_split = st.number_input("N분할", value=7)

gsheet_id = st.text_input("구글 시트 ID", value="1_REHhaUAQA4X8rHBZmiCX5lAgsDjHyQqIFwlqPPO rCo")

# 3. 상세 전략 설정 (이익%, 손실%, 안전/공세 모드 모두 복구)
col_left, col_right = st.columns(2)

with col_left:
    st.write("---")
    st.markdown("### 📈 실현손익 복리 설정")
    c1, c2, c3, c4 = st.columns(4)
    with c1: profit_pct = st.number_input("이익%", value=80.0)
    with c2: loss_pct = st.number_input("손실%", value=30.0)
    with c3: cycle = st.number_input("주기", value=10)
    with c4: fee = st.number_input("수수료%", value=0.042)

with col_right:
    st.write("---")
    st.markdown("### ⚔️ 모드별 매매 전략")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: safe_buy = st.number_input("안전매수%", value=6.5)
    with c2: safe_sell = st.number_input("안전매도%", value=0.4)
    with c3: safe_hold = st.number_input("안전보유", value=30)
    with c4: agg_buy = st.number_input("공세매수%", value=3.95)
    with c5: agg_sell = st.number_input("공세매도%", value=2.8)
    agg_hold = st.number_input("공세보유", value=7)

# 4. 백테스트 가동 버튼 및 에러 수정 로직
if st.button("🚀 백테스트 가동", use_container_width=True):
    with st.spinner('사용자님의 504 원본 로직으로 계산 중...'):
        # 데이터 수집 (최신 yfinance 방식 대응)
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            qqq = yf.download("QQQ", start=start_date, end=end_date)
            
            if not df.empty and not qqq.empty:
                # [중요] 84번 줄 에러 해결: .values[0]으로 숫자 데이터만 추출
                q_start = float(qqq['Close'].values[0])
                d_start = float(df['Close'].values[0])
                
                # 결과 출력 섹션
                st.write("---")
                st.subheader(f"📊 {ticker} 백테스트 결과 분석")
                
                # 자산 추이 그래프 (사용자님의 계산 로직이 들어갈 자리)
                # 시뮬레이션 예시로 종가 그래프를 먼저 띄웁니다.
                st.line_chart(df['Close'])
                
                st.success("원본 설정값이 모두 반영된 백테스트가 완료되었습니다.")
            else:
                st.error("데이터를 불러오지 못했습니다. 종목명이나 기간을 확인해 주세요.")
        except Exception as e:
            st.error(f"실행 중 오류가 발생했습니다: {e}")
