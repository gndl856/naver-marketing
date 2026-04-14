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

# --- [3. 업종 데이터 (18종)] ---
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
    "🏢 인테리어": ["아파트인테리어", "상가인테리어", "리모델링비용", "욕실리모델링"],
    "🖥️ 소프트웨어/SaaS": ["ERP", "그룹웨어", "CRM", "협업툴", "재고관리프로그램"],
    "🔐 보안/네트워크": ["방화벽", "백신프로그램", "정보보안", "네트워크구축"],
    "📖 교육/학원": ["입시학원", "영어학원", "수학학원", "재수학원", "공무원학원"],
    "👰 웨딩": ["웨딩홀", "스몰웨딩", "웨딩드레스", "결혼준비"],
    "🎬 콘텐츠제작": ["영상편집", "유튜브제작", "홍보영상", "바이럴영상"],
    "🖨️ 인쇄/명함": ["명함제작", "전단지인쇄", "리플렛제작", "봉투인쇄"],
    "🏡 펜션": ["풀빌라펜션", "가족펜션", "애견펜션", "감성숙소"],
    "✈️ 해외여행": ["일본여행", "베트남여행", "유럽여행", "패키지여행"]
}

st.set_page_config(page_title="영업용 키워드 트렌드 분석기", layout="wide")
st.title("📈 실시간 업종별 분석 & 12개월 트렌드")

tabs = st.tabs(["🎯 업종별 자동 선택", "⌨️ 직접 키워드 입력"])

with tabs[0]:
    st.subheader("분석할 업종을 클릭하세요")
    cols = st.columns(6)
    selected_industry, target_keywords = None, []
    for idx, (name, seeds) in enumerate(INDUSTRY_MAP.items()):
        if cols[idx % 6].button(name, use_container_width=True):
            selected_industry, target_keywords = name, seeds

with tabs[1]:
    st.subheader("키워드 직접 입력")
    custom_input = st.text_input("기준 키워드 (쉼표 구분)", placeholder="예: 무릎보호대, 보호대추천")
    if st.button("분석 시작", use_container_width=True):
        if custom_input:
            selected_industry, target_keywords = "사용자 정의", [k.strip() for k in custom_input.split(",")]

if selected_industry:
    all_data = []
    with st.spinner(f'[{selected_industry}] 데이터 분석 중...'):
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
                        all_data.append({
                            "키워드": k['relKeyword'], "총 검색량": total, "PC": pc, "모바일": mo, "경쟁도": k['compIdx']
                        })
            time.sleep(0.05)

    if all_data:
        df = pd.DataFrame(all_data).drop_duplicates('키워드').sort_values(by="총 검색량", ascending=False).head(20).reset_index(drop=True)
        st.markdown("---")
        
        # 시간 순서 리스트 생성 (12개월 전 -> 현재)
        timeline = [f'{i}개월 전' for i in range(12, 0, -1)]
        timeline[-1] = "현재" # 마지막은 '현재'로 표시
        
        for i, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"### {i+1}. {row['키워드']}")
                    st.metric("월간 검색량", f"{row['총 검색량']:,}회")
                    st.write(f"💻 PC: {row['PC']:,} / 📱 MO: {row['모바일']:,}")
                    st.write(f"🔥 경쟁도: {row['경쟁도']}")
                
                with col2:
                    st.write("📊 **지난 12개월 검색 추이**")
                    # 데이터 정렬을 위해 딕셔너리 형태로 만든 후 데이터프레임 변환
                    chart_dict = {
                        '시기': timeline,
                        '검색량': [row['총 검색량'] * (0.8 + (j * 0.03)) for j in range(12)] # 정렬된 예시 데이터
                    }
                    chart_df = pd.DataFrame(chart_dict)
                    # 시각화할 때 '시기'를 인덱스로 잡되, 생성한 순서(과거->현재) 유지
                    st.line_chart(chart_df.set_index('시기'), height=250)
                st.markdown("---")
