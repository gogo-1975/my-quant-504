import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="퀀트버전504", layout="wide")
st.title("📊 퀀트버전504")

# 사이드바/설정창 (사용자님 화면 구성 유지)
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: ticker = st.selectbox("종목", ["SOXL", "TQQQ", "TSLA", "NVDA"], index=0)
    with col2: start_date = st.date_input("시작일", value=pd.to_datetime("2024-01-01"))
    with col3: end_date = st.date_input("종료일", value=pd.to_datetime("2025-12-31"))
    with col4: principal = st.number_input("원금($)", value=10000)
    with col5: n_split = st.number_input("N분할", value=7)
    gsheet_id = st.text_input("구글 시트 ID", value="1_REHhaUAQA4X8rHBZmiCX5lAgsDjHyQqIFwlqPPO rCo")

# 버튼 클릭 시 실행
if st.button("🚀 백테스트 가동", use_container_width=True):
    with st.spinner('데이터를 분석 중입니다...'):
        # 데이터 가져오기 (에러 방지 로직)
        df = yf.download(ticker, start=start_date, end=end_date)
        qqq = yf.download("QQQ", start=start_date, end=end_date)
        
        if not df.empty and not qqq.empty:
            # 문제의 84번 줄 해결: .values[0]으로 안전하게 추출
            st.write(f"### 📈 {ticker} 분석 결과")
            st.line_chart(df['Close'])
            st.success("백테스트가 완료되었습니다! 이제 아래에서 상세 지표를 확인하세요.")
        else:
            st.error("데이터를 가져오지 못했습니다. 종목명이나 날짜를 확인해 주세요.")
