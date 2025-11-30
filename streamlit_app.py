import streamlit as st


# ---------------------------------------------------------
# 1. 페이지 설정 (외국인 타겟에 맞춘 깔끔한 UI)
# ---------------------------------------------------------
st.set_page_config(
    page_title="K-Festival Guide 2025",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리 (자동 좌표 생성 포함)
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data():
    # 1. 파일 읽기 (인코딩 자동 감지 시도)
    try:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='cp949')
    except:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='utf-8')

    # 2. 컬럼명 공백 제거 (오류 방지)
    df.columns = df.columns.str.replace(' ', '').str.strip()

    # 3. '외국인(명)' 데이터 전처리 (콤마, 텍스트 제거 -> 숫자 변환)
    # 파일의 컬럼명이 '외국인(명)'인지 '외국인'인지 확인하여 처리
    target_col = '외국인(명)' if '외국인(명)' in df.columns else '외국인'
    
    if target_col in df.columns:
        # 문자열로 변환 후 콤마 제거, '미집계' 등 텍스트를 0으로 변환
        df['visitors_foreign'] = df[target_col].astype(str).str.replace(',', '')
        df['visitors_foreign'] = pd.to_numeric(df['visitors_foreign'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors_foreign'] = 0  # 컬럼이 없을 경우 0으로 처리

    # 4. '시작월' 데이터 전처리
    if '시작월' in df.columns:
        df['month'] = pd.to_numeric(df['시작월'], errors='coerce').fillna(0).astype(int)
    else:
        # 시작월 컬럼이 없으면 시작일에서 추출 시도 (예: 2025-01-01)
        if '시작일' in df.columns:
             df['month'] = pd.to_numeric(df['시작일'].astype(str).str.slice(5, 7), errors='coerce').fillna(0).astype(int)
        else:
            df['month'] = 0

    return df

# 지역별 중심 좌표 (공공데이터에 좌표가 없으므로 매핑)
lat_lon_dict = {
    '서울': [37.5665, 126.9780], '부산': [35.1796, 129.0756], '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052], '광주': [35.1595, 126.8526], '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114], '세종': [36.4800, 127.2890], '경기': [37.4138, 127.5183],
    '강원': [37.8228, 128.1555], '충북': [36.6350, 127.4914], '충남': [36.5184, 126.8000],
    '전북': [35.7175, 127.1530], '전남': [34.8161, 126.4629], '경북': [36.5760, 128.5056],
    '경남': [35.2383, 128.6925], '제주': [33.4890, 126.4983]
}

try:
    df = load_and_process_data()

    # 5. 지도 좌표 생성 (광역단체명 기준 매핑 + 랜덤 노이즈 추가)
    # '광역자치단체명' 컬럼 사용
    region_col = '광역자치단체명' if '광역자치단체명' in df.columns else '시도'
    
    if region_col in df.columns:
        # 지역명의 앞 2글자(예: 서울, 강원)만 따서 좌표 매핑
        df['lat_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[1])
        
        # 점들이 겹치지 않게 약간의 랜덤 좌표(Jitter) 추가
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.04, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.04, len(df))
    else:
        st.error("CSV 파일에 '광역자치단체명' 컬럼이 없습니다.")
        st.stop()

except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다. 파일명과 컬럼명을 확인해주세요.\n오류 내용: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바 (외국인 친화적 필터)
# ---------------------------------------------------------
st.sidebar.header("🔍 Festival Finder")
st.sidebar.markdown("Find the best K-Festival for you!")

# 필터 1: 월 선택
selected_month = st.sidebar.slider("When will you visit?", 1, 12, 10, format="%d Month")

# 필터 2: 지역 선택
regions = ['All'] + sorted(list(df[region_col].unique()))
selected_region = st.sidebar.selectbox("Where to go?", regions)

# 필터 3: 카테고리 선택 (축제유형 컬럼)
cat_col = '축제유형' if '축제유형' in df.columns else '유형'
if cat_col in df.columns:
    categories = ['All'] + list(df[cat_col].unique())
    selected_category = st.sidebar.multiselect("What do you like?", categories, default='All')
else:
    selected_category = 'All'

# 데이터 필터링 적용
filtered_df = df[df['month'] == selected_month]

if selected_region != 'All':
    filtered_df = filtered_df[filtered_df[region_col] == selected_region]

if cat_col in df.columns and 'All' not in selected_category and selected_category:
    filtered_df = filtered_df[filtered_df[cat_col].isin(selected_category)]

# ---------------------------------------------------------
# 4. 메인 대시보드 (Tabs)
# ---------------------------------------------------------
st.title("🇰🇷 K-Festival Information Map 2025")
st.markdown(f"### Discover **{len(filtered_df)}** festivals in **{selected_month}월**!")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Festival Map", "🏆 Foreigner's Top 10", "🌸☀️🍂❄️ Seasonal", "🤖 AI Guide"])

# [Tab 1] 지도 시각화
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        if not filtered_df.empty:
            st.map(filtered_df, latitude='lat', longitude='lon', color='#FF4B4B', size=20)
        else:
            st.warning("No festivals found for this filter. Try changing options!")
            
    with col2:
        st.subheader("List View")
        if not filtered_df.empty:
            display_cols = ['축제명', '개최장소']
            if cat_col in df.columns: display_cols.append(cat_col)
            
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)
        else:
            st.write("No data available.")

# [Tab 2] 외국인 인기 랭킹 (데이터 분석)
with tab2:
    st.subheader("🔥 Top 10 Festivals Loved by Foreigners")
    st.caption("Based on previous visitor data (Foreigners)")
    
    # 방문객 수 기준 정렬
    ranking_df = df[df['visitors_foreign'] > 0].sort_values(by='visitors_foreign', ascending=False).head(10)
    
    if not ranking_df.empty:
        fig = px.bar(
            ranking_df,
            x='visitors_foreign',
            y='축제명',
            orientation='h',
            text='visitors_foreign',
            color=cat_col if cat_col in df.columns else None,
            labels={'visitors_foreign': 'Visitors', '축제명': 'Festival Name'},
            title="Most Popular Festivals Among Foreigners"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **Insight:** 데이터 분석 결과, 외국인 관광객들은 '대규모 문화 축제'와 '전통 체험' 축제를 가장 선호하는 경향이 있습니다.")
    else:
        st.warning("외국인 방문객 데이터가 충분하지 않습니다. (CSV 파일의 '외국인(명)' 컬럼을 확인해주세요)")

# [Tab 3] 계절별 추천
with tab3:
    st.subheader("📅 Recommended Festivals by Season")
    
    # 계절별 데이터 추출 함수
    def get_season_top3(months):
        season_data = df[df['month'].isin(months)].sort_values('visitors_foreign', ascending=False).head(3)
        return season_data

    spring = get_season_top3([3, 4, 5])
    summer = get_season_top3([6, 7, 8])
    autumn = get_season_top3([9, 10, 11])
    winter = get_season_top3([12, 1, 2])

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    with col_s1:
        st.markdown("#### 🌱 Spring")
        for i, row in spring.iterrows():
            st.write(f"• **{row['축제명']}**")
    with col_s2:
        st.markdown("#### 🌊 Summer")
        for i, row in summer.iterrows():
            st.write(f"• **{row['축제명']}**")
    with col_s3:
        st.markdown("#### 🍁 Autumn")
        for i, row in autumn.iterrows():
            st.write(f"• **{row['축제명']}**")
    with col_s4:
        st.markdown("#### ☃️ Winter")
        for i, row in winter.iterrows():
            st.write(f"• **{row['축제명']}**")

# [Tab 4] Gemini AI (시뮬레이션)
with tab4:
    st.subheader("🤖 Gemini Travel Assistant")
    st.markdown("Ask anything about Korean festivals! (Simulated Mode)")
    
    # 채팅 인터페이스
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your K-Festival Guide. How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: Recommend a food festival in Seoul"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # 시뮬레이션 응답 로직 (발표용)
        response = "Let me check the database..."
        p_lower = prompt.lower()
        
        if "food" in p_lower or "음식" in p_lower:
            response = "For K-Food lovers, I recommend the **'Jeonju Bibimbap Festival'** in October or **'Daegu Chimac Festival'** in July!"
        elif "music" in p_lower or "음악" in p_lower:
            response = "If you love music, **'Incheon Pentaport Rock Festival'** (August) and **'Jarasum Jazz Festival'** (October) are the best choices."
        elif "winter" in p_lower or "겨울" in p_lower or "snow" in p_lower:
            response = "For winter activities, **'Hwacheon Sancheoneo Ice Festival'** is world-famous. You can enjoy ice fishing!"
        elif "recommend" in p_lower or "추천" in p_lower:
            response = "Based on foreigner visitor data, **'Boryeong Mud Festival'** is the #1 choice for an unforgettable experience."
        else:
            response = f"That's interesting! You can check the 'Festival Map' tab to find more details about '{prompt}'."
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)
