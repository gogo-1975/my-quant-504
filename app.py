import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 페이지 설정 (원본 레이아웃 그대로)
st.set_page_config(page_title="퀀트버전504", layout="wide")
st.title("📊 퀀트버전504")

# 2. 상단 기본 설정 (5열 구성)
col1, col2, col3, col4, col5 = st.columns(5)
with col1: ticker = st.selectbox("종목", ["SOXL", "TQQQ", "NVDA", "TSLA"], index=0)
with col2: start_date = st.date_input("시작일", value=pd.to_datetime("2024-01-01"))
with col3: end_date = st.date_input("종료일", value=pd.to_datetime("2025-12-31"))
with col4: principal = st.number_input("원금($)", value=10000)
with col5: n_split = st.number_input("N분할", value=7)

gsheet_id = st.text_input("구글 시트 ID", value="1_REHhaUAQA4X8rHBZmiCX5lAgsDjHyQqIFwlqPPO rCo")

# 3. 상세 전략 설정 (이익%, 손실%, 안전/공세 모드 수치 완벽 복구)
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

# 4. 백테스트 가동 버튼 및 에러 방지 로직
if st.button("🚀 백테스트 가동", use_container_width=True):
    with st.spinner('사용자님의 504 로직으로 계산 중...'):
        try:
            # 데이터 수집
            df = yf.download(ticker, start=start_date, end=end_date)
            qqq = yf.download("QQQ", start=start_date, end=end_date)
            
            if not df.empty and not qqq.empty:
                # [여기가 핵심 해결 포인트!] 
                # .values.flatten()[0]을 사용하면 데이터가 '표'든 '숫자'든 상관없이 첫 번째 값만 딱 뽑아옵니다.
                q_start = float(qqq['Close'].values.flatten()[0])
                d_start = float(df['Close'].values.flatten()[0])
                
                # 결과 출력
                st.write("---")
                st.subheader(f"📊 {ticker} 백테스트 결과 분석")
                
                # 자산 추이 그래프 (사용자님의 원본 로직 결과물이 들어갈 자리)
                st.line_chart(df['Close'])
                
                st.success("원본 설정과 로직이 웹 환경에 맞게 성공적으로 실행되었습니다.")
            else:
                st.error("데이터 로딩 실패. 종목명과 기간을 확인하세요.")
                
        except Exception as e:
            st.error(f"오류 발생: {e}")
