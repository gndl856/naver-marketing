import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

# --- [1. 인증 정보] ---
API_KEY = '0100000000d4546f2c4afe3949fad6171a8a4fbbbb54c53ab17bdaa6047794f6cc44de07c9'
SECRET_KEY = 'AQAAAADUVG8sSv45SfrWFxqKT7u7NW6NWIg+xKyApAZCF1FzdQ=='
CUSTOMER_ID = '2066558'
BASE_URL = 'https://api.naver.com'

# --- [2. 헤더 생성 함수] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    signature = base64.b64encode(hmac.new(
        SECRET_KEY.encode(), (timestamp + "." + method + "." + uri).encode(), hashlib.sha256).digest()).decode()
    return {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Timestamp': timestamp,
        'X-API-KEY': API_KEY,
        'X-Customer': str(CUSTOMER_ID),
        'X-Signature': signature
    }

# --- [3. 업종 데이터] ---
INDUSTRY_MAP = {
    "🚚 이사/운송": ["포장이사", "이삿짐센터", "원룸이사", "용달이사"],
    "⚖️ 개인회생/파산": ["개인회생", "개인파산", "회생파산상담", "개인회생비용"],
    "💔 이혼/가사": ["이혼변호사", "상간녀소송", "재산분할", "양육권소송"],
    "🚨 형사/일반": ["형사변호사", "성범죄변호사", "음주운전방어", "무료법률상담"],
    "🦷 치과": ["임플란트", "치아교정", "전체임플란트", "치과추천"],
    "💉 성형/피부": ["성형외과", "피부과", "쌍꺼풀수술", "필러"],
    "👨‍💼 세무/회계": ["세무사", "법인설립", "기장대리", "종합소득세신고"],
    "🚗 렌트/리스": ["장기렌트카", "자동차리스", "신차장기렌트", "렌터카"],
    "🧹 청소/소독": ["입주청소", "에어컨청소", "이사청소", "방역업체"],
    "🏢 인테리어": ["아파트인테리어", "상가인테리어", "리모델링비용", "욕실리모델링"]
}

st.set_page_config(page_title="영업용 키워드 분석기", layout="wide")
st.title("🚀 실시간 업종별 알짜 키워드 분석")

tabs = st.tabs(["🎯 업종별 자동 선택", "⌨️ 직접 키워드 입력"])

with tabs[0]:
    st.subheader("분석할 업종을 클릭하세요")
    cols = st.columns(5)
    selected_industry = None
    for idx, (name, seeds) in enumerate(INDUSTRY_MAP.items()):
        if cols[idx % 5].button(name, use_container_width=True):
            selected_industry = name
            target_keywords = seeds

with tabs[1]:
    st.subheader("키워드 직접 입력")
    custom_input = st.text_input("기준 키워드 (쉼표 구분)", placeholder="예: 무릎보호대, 보호대추천")
    if st.button("분석 시작", use_container_width=True):
        if custom_input:
            selected_industry = "사용자 정의"
            target_keywords = [k.strip() for k in custom_input.split(",")]

if selected_industry:
    all_data = []
    with st.spinner(f'[{selected_industry}] 수집 중...'):
        for seed in target_keywords:
            uri = '/keywordstool'
            params = {'hintKeywords': seed, 'showDetail': '1'}
            res = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
            if res.status_code == 200:
                keywords = res.json().get('keywordList', [])
                for k in keywords:
                    pc = int(k['monthlyPcQcCnt']) if str(k['monthlyPcQcCnt']).isdigit() else 0
                    mo = int(k['monthlyMobileQcCnt']) if str(k['monthlyMobileQcCnt']).isdigit() else 0
                    total = pc + mo
                    if total >= 2000:
                        all_data.append({"키워드": k['relKeyword'], "총 검색량": total, "PC": pc, "모바일": mo, "경쟁도": k['compIdx']})
            time.sleep(0.05)

    if all_data:
        df = pd.DataFrame(all_data).drop_duplicates('키워드').sort_values(by="총 검색량", ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, height=500)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 엑셀 저장", csv, f"분석결과.csv", "text/csv")
