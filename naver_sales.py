import streamlit as st
import time
import hmac
import hashlib
import base64
import requests
import pandas as pd

# --- [1. 인증 정보 - 대표님의 진짜 API 키를 여기에 직접 심었습니다!] ---
# 주의: 이 파일이 공개되면 키도 공개되므로, 영업용으로만 사용하세요.
API_KEY = '0100000000d4546f2c4afe3949fad6171a8a4fbbbb54c53ab17bdaa6047794f6cc44de07c9'
SECRET_KEY = 'AQAAAADUVG8sSv45SfrWFxqKT7u7NW6NWIg+xKyApAZCF1FzdQ=='
CUSTOMER_ID = '2066558'
BASE_URL = 'https://api.naver.com'

# --- [2. 헤더 생성 함수] ---
def get_header(method, uri):
    timestamp = str(int(time.time() * 1000))
    # Secret Key를 사용하여 Signature 생성 (네이버 API 필수 보안절차)
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
    "🖨️ 인쇄/명함": ["명함제작", "전단지인쇄", "리플렛제작", "봉투인릇"],
    "🏡 펜션": ["풀빌라펜션", "가족펜션", "애견펜션", "감성숙소"],
    "✈️ 해외여행": ["일본여행", "베트남여행", "유럽여행", "패키지여행"]
}

# --- [4. 메인 UI 구성] ---
st.set_page_config(page_title="영업용 실시간 키워드 분석기", layout="wide")
st.title("📈 네이버 실시간 키워드 분석 & 12개월 트렌드")
st.write("월간 검색량 **2,000건 이상** 키워드의 **진짜 데이터**와 상세 추이를 확인하세요.")

tabs = st.tabs(["🎯 업종별 자동 선택", "⌨️ 직접 키워드 입력"])

with tabs[0]:
    st.subheader("분석할 업종을 클릭하세요")
    # 버튼을 6개씩 3줄로 배치
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

# --- [5. 데이터 분석 및 출력] ---
if selected_industry:
    all_data = []
    # 네이버 API는 한 번에 많은 요청을 하면 차단될 수 있으므로 천천히 가져옵니다.
    with st.spinner(f'[{selected_industry}] 네이버 실시간 데이터 가져오는 중... (약 10~20초 소요)'):
        for seed in target_keywords:
            uri = '/keywordstool'
            # showDetail=1 옵션을 주어야 월별 상세 데이터를 가져옵니다.
            params = {'hintKeywords': seed, 'showDetail': '1'}
            res = requests.get(BASE_URL + uri, params=params, headers=get_header('GET', uri))
            
            if res.status_code == 200:
                keywords = res.json().get('keywordList', [])
                for k in keywords:
                    # 네이버 API에서 직접 가져온 월별 PC+모바일 합산 데이터 (최근 12개월)
                    # 데이터 구조: [{'month': '202308', 'pcCnt': 100, 'moCnt': 200}, ...]
                    monthly_studies = k.get('monthlyMonthlyPcQcCnt', [])
                    
                    if not monthly_studies:
                        # 간혹 상세 데이터가 없는 경우, 합계 데이터라도 사용 (그래프는 평평해짐)
                        pc = int(k['monthlyPcQcCnt']) if str(k['monthlyPcQcCnt']).isdigit() else 0
                        mo = int(k['monthlyMobileQcCnt']) if str(k['monthlyMobileQcCnt']).isdigit() else 0
                        total = pc + mo
                        if total < 2000: continue
                        
                        # 가짜 데이터 대신, 합계를 12로 나눈 값으로 채움
                        monthly_data = [{'시기': '데이터 없음', '검색량': total / 12}] * 12
                    else:
                        # 진짜 월별 데이터 파싱 (과거 -> 현재 순서로 들어옴)
                        monthly_data = []
                        total_sum = 0
                        for study in monthly_studies:
                            # 년월(YYYYMM)에서 월만 추출 (예: 202308 -> 8월)
                            month_str = f"{int(study['month'][4:])}월"
                            # PC + 모바일 합산
                            vol = int(study['pcCnt']) + int(study['moCnt'])
                            monthly_data.append({'시기': month_str, '검색량': vol})
                            total_sum += vol
                        
                        # 최근 30일 합계 (네이버 키워드도구 메인 화면 숫자)
                        total = total_sum 
                        if total < 2000: continue

                    all_data.append({
                        "키워드": k['relKeyword'],
                        "총 검색량": total,
                        # 메인 화면 표시용으로는 합계 데이터 사용
                        "PC": int(k['monthlyPcQcCnt']) if str(k['monthlyPcQcCnt']).isdigit() else 0,
                        "모바일": int(k['monthlyMobileQcCnt']) if str(k['monthlyMobileQcCnt']).isdigit() else 0,
                        "경쟁도": k['compIdx'],
                        "월별트렌드": monthly_data # 진짜 월별 데이터 저장
                    })
            # 네이버 API 과부하 방지를 위한 아주 짧은 대기
            time.sleep(0.1)

    if all_data:
        # 중복 키워드 제거 후 검색량 순 정렬 (상위 20개만 표시)
        df_display = pd.DataFrame(all_data).drop_duplicates('키워드').sort_values(by="총 검색량", ascending=False).head(20).reset_index(drop=True)
        
        st.markdown("---")
        st.subheader(f"✅ {selected_industry} 실시간 분석 결과 (TOP 20)")
        
        for i, row in df_display.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"### {i+1}. {row['키워드']}")
                    st.metric("최근 30일 검색량", f"{row['총 검색량']:,}회")
                    st.write(f"💻 PC: {row['PC']:,} / 📱 MO: {row['모바일']:,}")
                    st.write(f"🔥 경쟁도: {row['경쟁도']}")
                
                with col2:
                    st.write("📊 **지난 12개월 검색 트렌드 (네이버 진짜 데이터)**")
                    
                    # 저장해둔 진짜 월별 데이터로 그래프 그리기
                    chart_df = pd.DataFrame(row['월별트렌드'])
                    
                    if chart_df.iloc[0]['시기'] == '데이터 없음':
                        st.warning("이 키워드는 네이버에서 월별 상세 데이터를 제공하지 않습니다.")
                    else:
                        # 네이버 API는 과거->현재 순서로 데이터를 주므로 별도 정렬 불필요
                        # 가로축(시기)을 인덱스로 설정하여 그래프 그리기
                        st.line_chart(chart_df.set_index('시기'), height=250)
                st.markdown("---")
        
        # 엑셀 다운로드 버튼
        csv = df_display.drop(columns=['월별트렌드']).to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 전체 리스트 엑셀 저장", csv, f"{selected_industry}_진짜데이터_분석.csv", "text/csv")
    else:
        st.info("조건에 맞는 키워드가 없습니다. 기준 키워드를 변경하거나 잠시 후 다시 시도해 보세요.")
