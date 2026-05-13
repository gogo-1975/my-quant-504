import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import io
import requests
import numpy as np
import plotly.graph_objects as go

# --- [1] 화면 레이아웃 및 스타일 설정 (기존 유지) ---
st.set_page_config(layout="wide", page_title="퀀트버전 506 (최종 수정본)")

st.markdown("""
    <style>
    header { visibility: hidden; }
    .block-container { padding-top: 4rem !important; }
    .main-title { font-size: 1.8rem; font-weight: 800; margin-bottom: 2rem; color: #1E1E1E; line-height: 1.4; }
    div[data-baseweb="input"] { min-height: 30px !important; }
    input { padding: 4px 8px !important; font-size: 0.85rem !important; text-align: right !important; }
    label { font-size: 0.8rem !important; margin-bottom: 1px !important; font-weight: 600; }
    .config-box { background-color: #f8f9fa; padding: 10px 12px; border-radius: 8px; border: 1px solid #dee2e6; margin-bottom: 10px; }
    .box-title { font-weight: bold; font-size: 0.85rem; margin-bottom: 8px; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

def to_num(val, default=0.0):
    try: return float(str(val).replace(',', ''))
    except: return default

# --- [2] 상단 설정 UI (시작일 제한 수정) ---
st.markdown('<div class="main-title">📊 퀀트버전 506 (SOXL 상장일 대응)</div>', unsafe_allow_html=True)

# ⭐ SOXL 상장일인 2010-03-11로 고정
SOXL_BIRTH = datetime.date(2010, 3, 11)
MAX_DATE = datetime.date(2035, 12, 31)

with st.container():
    c1, c2_start, c2_end, c3, c4, c5 = st.columns([0.6, 0.6, 0.6, 0.7, 0.5, 2.0])
    with c1: ticker = st.selectbox("종목", ["SOXL", "TQQQ", "BULZ", "NVDA"])
    # 시작일 선택 범위를 상장일부터 가능하게 수정
    with c2_start: start_d = st.date_input("시작일", value=datetime.date(2024, 9, 1), min_value=SOXL_BIRTH, max_value=MAX_DATE)
    with c2_end: end_d = st.date_input("종료일", value=datetime.date(2025, 12, 31), min_value=SOXL_BIRTH, max_value=MAX_DATE)
    with c3: capital = to_num(st.text_input("원금($)", "10000"))
    with c4: split_n = int(to_num(st.text_input("N분할", "7")))
    with c5: sheet_id = st.text_input("구글 시트 ID", "1_REHhaUAQA4X8rHBZmiCX5lAgsDjHyQqIFwIqPPOrCo")

row2_col1, row2_col2 = st.columns([1.5, 3.5])
with row2_col1:
    st.markdown('<div class="config-box"><div class="box-title">📈 실현손익 복리 설정</div>', unsafe_allow_html=True)
    cp1, cp2, cp3, cp4 = st.columns(4)
    with cp1: p_ratio = to_num(st.text_input("이익%", "60")) / 100
    with cp2: l_ratio = to_num(st.text_input("손실%", "20")) / 100
    with cp3: update_cycle = int(to_num(st.text_input("주기", "10")))
    with cp4: fee_rate = to_num(st.text_input("수수료%", "0.042")) / 100
    st.markdown('</div>', unsafe_allow_html=True)

with row2_col2:
    st.markdown('<div class="config-box"><div class="box-title">⚔️ 모드별 매매 전략</div>', unsafe_allow_html=True)
    s1, s2, s3, a1, a2, a3 = st.columns([1, 1, 1, 1, 1, 1])
    with s1: s_buy_target = to_num(st.text_input("안전매수%", "1.7")) / 100
    with s2: s_sell_target = to_num(st.text_input("안전매도%", "0.4")) / 100
    with s3: s_hold_days = int(to_num(st.text_input("안전보유", "30")))
    with a1: a_buy_target = to_num(st.text_input("공세매수%", "3.95")) / 100
    with a2: a_sell_target = to_num(st.text_input("공세매도%", "2.8")) / 100
    with a3: a_hold_days = int(to_num(st.text_input("공세보유", "7")))
    st.markdown('</div>', unsafe_allow_html=True)

run = st.button("🚀 백테스트 시작", type="primary", use_container_width=True)

# --- [3] 백테스트 엔진 ---
if run:
    with st.spinner('데이터 로드 중...'):
        try:
            t_obj = yf.Ticker(ticker); q_obj = yf.Ticker("QQQ")
            df_price_full = t_obj.history(start=start_d - datetime.timedelta(days=45), end=end_d, auto_adjust=False)
            df_qqq_full = q_obj.history(start=start_d, end=end_d, auto_adjust=False)
            
            price_data = df_price_full['Close'].dropna()
            splits = df_price_full['Stock Splits']
            qqq_data = df_qqq_full['Close'].dropna()
            
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=0"
            mode_df_raw = pd.read_csv(io.StringIO(requests.get(sheet_url).text), header=3)
            mode_df_raw.columns = [str(c).strip() for c in mode_df_raw.columns]
            mode_df_raw['시트날짜'] = pd.to_datetime(mode_df_raw.iloc[:, 1], errors='coerce').dt.date
            valid_mode_df = mode_df_raw.dropna(subset=['시트날짜']).sort_values('시트날짜')

            cash, total_asset = capital, capital
            slots = [None] * split_n
            logs, asset_history, date_history, trade_results, qqq_hold_history = [], [], [], [], []
            
            trading_days = price_data.index.date.tolist()
            start_idx = next(i for i, d in enumerate(trading_days) if d >= start_d)
            qqq_qty = capital / float(qqq_data.iloc[0])
            planned_amt = capital / split_n 
            days_elapsed, accumulated_profit_in_cycle = 0, 0 

            for i in range(start_idx, len(trading_days)):
                curr_date = trading_days[i]
                curr_close = float(price_data.iloc[i])
                prev_close = float(price_data.iloc[i-1])
                
                # 액면분할 보정
                split_ratio = splits.iloc[i]
                if split_ratio != 0:
                    prev_close /= split_ratio
                    for s in range(split_n):
                        if slots[s]:
                            slots[s]['qty'] *= split_ratio
                            slots[s]['buy_price'] /= split_ratio
                            slots[s]['target_p'] /= split_ratio

                # 금요일 선행 모드 결정
                days_until_friday = 4 - curr_date.weekday()
                target_friday = curr_date + datetime.timedelta(days=days_until_friday)
                m_match = valid_mode_df[valid_mode_df['시트날짜'] == target_friday]
                
                if not m_match.empty:
                    mode = str(m_match.iloc[0, 10]).strip()
                else:
                    mode = str(valid_mode_df.iloc[-1, 10]).strip() if not valid_mode_df.empty else "안전"
                
                bp, sp, hd = (a_buy_target, a_sell_target, a_hold_days) if mode == "공세" else (s_buy_target, s_sell_target, s_hold_days)
                
                if days_elapsed > 0 and days_elapsed % update_cycle == 0:
                    planned_amt += (accumulated_profit_in_cycle * (p_ratio if accumulated_profit_in_cycle >= 0 else l_ratio)) / split_n
                    accumulated_profit_in_cycle = 0
                
                daily_realized_profit, daily_fees = 0, 0
                for s in range(split_n):
                    if slots[s] and slots[s]['buy_date'] != curr_date:
                        if curr_close >= slots[s]['target_p'] or curr_date >= slots[s]['expire_d']:
                            val_raw = curr_close * slots[s]['qty']; fee = val_raw * fee_rate
                            pnl = (val_raw - fee) - (slots[s]['buy_price'] * slots[s]['qty'])
                            cash += (val_raw - fee); daily_fees += fee; daily_realized_profit += pnl; accumulated_profit_in_cycle += pnl
                            trade_results.append(1 if pnl > 0 else 0)
                            for log in logs:
                                if log['날짜'] == slots[s]['buy_date'] and log['매수량'] != "-":
                                    log['실제매도일'], log['매도량'], log['실현수익'] = curr_date, slots[s]['qty'], round(pnl, 2)
                            slots[s] = None

                # ⭐ 매수 로직 (예산 반올림 / 수량 내림 적용)
                target_p = prev_close * (1 + bp)
                
                # 수량 계산: 엑셀 INT와 동일하게 소수점 버림(int)
                raw_qty = min(planned_amt, cash) / (target_p * (1 + fee_rate))
                target_qty = int(raw_qty) if raw_qty > 0 else 0
                
                actual_buy_q, planned_sell_p, moc_date = 0, 0, None
                if curr_close <= target_p and target_qty > 0:
                    for s in range(split_n):
                        if slots[s] is None:
                            slots[s] = {'qty': target_qty, 'buy_price': curr_close, 'target_p': curr_close * (1 + sp), 'buy_date': curr_date, 'expire_d': trading_days[min(i + hd, len(trading_days)-1)]}
                            cash -= (curr_close * target_qty * (1 + fee_rate))
                            actual_buy_q, daily_fees, planned_sell_p, moc_date = target_qty, daily_fees + (curr_close * target_qty * fee_rate), slots[s]['target_p'], slots[s]['expire_d']
                            break

                eval_val = sum(s['qty'] * curr_close for s in slots if s)
                total_asset = cash + eval_val
                asset_history.append(total_asset); date_history.append(curr_date)
                
                try: qqq_hold_history.append(qqq_qty * float(qqq_data.loc[pd.Timestamp(curr_date)]))
                except: qqq_hold_history.append(qqq_hold_history[-1] if qqq_hold_history else capital)
                
                logs.append({
                    '날짜': curr_date, '종가': round(curr_close, 2), '모드': mode, '변동률': f"{((curr_close-prev_close)/prev_close*100):+.2f}%",
                    '매수예정액': int(round(planned_amt)), # ⭐ 반올림 유지
                    '매입목표량': target_qty, '매수가': round(target_p, 2), # ⭐ 내림 적용
                    '매수량': actual_buy_q if actual_buy_q > 0 else "-", '매도목표가': round(planned_sell_p, 2) if actual_buy_q > 0 else "-",
                    'MOC매도일': moc_date if actual_buy_q > 0 else "-", '실제매도일': "-", '매도량': "-", '실현수익': 0.0,
                    '당일실현': round(daily_realized_profit, 2), '수수료': round(daily_fees, 2), '예수금': int(round(cash)), '평가금': int(round(eval_val)), '총자산': int(round(total_asset)), '수익률': f"{((total_asset-capital)/capital*100):.2f}%"
                })
                days_elapsed += 1

            # --- [4] 결과 출력 ---
            st.divider()
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("최종 총자산", f"${int(round(total_asset)):,}")
            m2.metric("총 수익률", f"{((total_asset-capital)/capital*100):.2f}%")
            arr_a = np.array(asset_history); peak = np.maximum.accumulate(arr_a)
            m3.metric("MDD", f"{(np.min((arr_a - peak) / peak) * 100):.2f}%" if len(arr_a)>0 else "0%")
            y = (end_d - start_d).days / 365.25
            m4.metric("CAGR", f"{((total_asset / capital) ** (1 / y) - 1) * 100 if y > 0 else 0:.2f}%")
            m5.metric("승률", f"{(sum(trade_results)/len(trade_results)*100 if trade_results else 0):.1f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=date_history, y=asset_history, mode='lines', name='전략 자산총액', line=dict(color='navy', width=1.5)))
            fig.add_trace(go.Scatter(x=date_history, y=qqq_hold_history, mode='lines', name='QQQ 단순보유', line=dict(color='pink', width=1.5)))
            fig.update_layout(title="전략 자산총액 vs QQQ 단순보유", template="plotly_white", height=500, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
            
        except Exception as e:
            st.error(f"백테스트 중 오류 발생: {e}")