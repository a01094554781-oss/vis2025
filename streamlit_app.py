import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os  # 경로 설정을 위해 추가

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="K-Festival Guide 2025",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리 (경로 문제 해결 버전)
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data():
    # [핵심 수정] 현재 app.py가 있는 폴더 위치를 기준으로 파일을 찾습니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'festival.csv')  # 바꾼 파일명

    # 파일이 실제로 있는지 확인 (안전장치)
    if not os.path.exists(file_path):
        # festival.csv가 없으면 원래 이름도 한번 찾아봅니다.
        file_path_old = os.path.join(current_dir, '2025년 지역축제.CSV')
        if os.path.exists(file_path_old):
            file_path = file_path_old
        else:
            st.error(f"❌ 파일을 찾을 수 없습니다! 파일명을 'festival.csv'로 변경해서 app.py와 같은 폴더에 넣어주세요.")
            st.stop()

    # 1. 파일 읽기
    try:
        df = pd.read_csv(file_path, encoding='cp949')
    except:
        df = pd.read_csv(file_path, encoding='utf-8')

    # 2. 컬럼명 공백 제거 (오류 방지)
    df.columns = df.columns.str.replace(' ', '').str.strip()

    # 3. '외국인(명)' 데이터 전처리
    # 파일의 컬럼명이 '외국인(명)'인지 '외국인'인지 확인하여 처리
    target_col = '외국인(명)' if '외국인(명)' in df.columns else '외국인'
    
    if target_col in df.columns:
        # 문자열로 변환 후 콤마, 미집계 제거 -> 숫자 변환
        df['visitors_foreign'] = df[target_col].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        df['visitors_foreign'] = pd.to_numeric(df['visitors_foreign'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors_foreign'] = 0

    # 4. '시작월' 데이터 전처리
    if '시작월' in df.columns:
        df['month'] = pd.to_numeric(df['시작월'], errors='coerce').fillna(0).astype(int)
    else:
        # 시작월 컬럼이 없으면 시작일에서 추출
        if '시작일' in df.columns:
             df['month'] = pd.to_numeric(df['시작일'].astype(str).str.slice(5, 7), errors='coerce').fillna(0).astype(int)
        else:
            df['month'] = 0

    return df

# 지역별 중심 좌표 매핑
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

    # 5. 지도 좌표 생성
    region_col = '광역자치단체명' if '광역자치단체명' in df.columns else '시도'
    
    if region_col in df.columns:
        # 지역명 앞 2글자 매핑
        df['lat_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[1])
        
        # 겹침 방지 (Jitter)
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.04, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.04, len(df))
    else:
        st.error("CSV 파일에 지역명 컬럼('광역자치단체명')이 없습니다.")
        st.stop()

except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바 (필터)
# ---------------------------------------------------------
st.sidebar.header("🔍 Festival Finder")

# 필터 1: 월
selected_month = st.sidebar.slider("When will you visit?", 1, 12, 10, format="%d Month")

# 필터 2: 지역
regions = ['All'] + sorted(list(df[region_col].unique()))
selected_region = st.sidebar.selectbox("Where to go?", regions)

# 필터 3: 카테고리
cat_col = '축제유형' if '축제유형' in df.columns else '유형'
if cat_col in df.columns:
    categories = ['All'] + list(df[cat_col].unique())
    selected_category = st.sidebar.multiselect("What do you like?", categories, default='All')
else:
    selected_category = 'All'

# 데이터 필터링
filtered_df = df[df['month'] == selected_month]

if selected_region != 'All':
    filtered_df = filtered_df[filtered_df[region_col] == selected_region]

if cat_col in df.columns and 'All' not in selected_category and selected_category:
    filtered_df = filtered_df[filtered_df[cat_col].isin(selected_category)]

# ---------------------------------------------------------
# 4. 메인 대시보드
# ---------------------------------------------------------
st.title("🇰🇷 K-Festival Information Map 2025")
st.markdown(f"### Discover **{len(filtered_df)}** festivals in **{selected_month}월**!")

tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map", "🏆 Top 10", "🌸 Seasonal", "🤖 AI Guide"])

# [Tab 1] 지도
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        if not filtered_df.empty:
            st.map(filtered_df, latitude='lat', longitude='lon', color='#FF4B4B', size=20)
        else:
            st.warning("No festivals found.")
    with col2:
        st.subheader("List")
        if not filtered_df.empty:
            display_cols = ['축제명', '개최장소']
            if cat_col in df.columns: display_cols.append(cat_col)
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)

# [Tab 2] 랭킹
with tab2:
    st.subheader("🔥 Top 10 Festivals (Foreigners)")
    ranking_df = df[df['visitors_foreign'] > 0].sort_values(by='visitors_foreign', ascending=False).head(10)
    
    if not ranking_df.empty:
        fig = px.bar(
            ranking_df,
            x='visitors_foreign',
            y='축제명',
            orientation='h',
            text='visitors_foreign',
            color=cat_col if cat_col in df.columns else None,
            title="Most Popular Festivals"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No visitor data available.")

# [Tab 3] 계절 추천
with tab3:
    st.subheader("📅 Seasonal Recommendations")
    def get_season_top3(months):
        return df[df['month'].isin(months)].sort_values('visitors_foreign', ascending=False).head(3)

    cols = st.columns(4)
    seasons = {'Spring': [3,4,5], 'Summer': [6,7,8], 'Autumn': [9,10,11], 'Winter': [12,1,2]}
    
    for i, (name, months) in enumerate(seasons.items()):
        with cols[i]:
            st.markdown(f"#### {name}")
            for _, row in get_season_top3(months).iterrows():
                st.write(f"• {row['축제명']}")

# [Tab 4] AI 가이드
with tab4:
    st.subheader("🤖 Gemini Travel Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your K-Festival Guide."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ask me anything!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        response = "Based on the 2025 festival data..."
        if "food" in prompt.lower():
            response = "I recommend the 'Jeonju Bibimbap Festival' in October!"
        else:
            response = f"Check the Map tab for more details about '{prompt}'."
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)
