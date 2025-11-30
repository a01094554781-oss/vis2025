import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data():
    # 1. 파일 읽기 (인코딩 자동 감지)
    try:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='cp949')
    except:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='utf-8')

    # 2. 컬럼명 공백 제거
    df.columns = df.columns.str.replace(' ', '').str.strip()

    # 3. '외국인(명)' 데이터 숫자 변환
    target_col = '외국인(명)' if '외국인(명)' in df.columns else '외국인'
    
    if target_col in df.columns:
        df['visitors_foreign'] = df[target_col].astype(str).str.replace(',', '')
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

# 지역별 중심 좌표
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
        df['lat_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[1])
        
        # 랜덤 노이즈 추가 (겹침 방지)
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.04, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.04, len(df))
    else:
        st.error("Error: '광역자치단체명' column not found in CSV.")
        st.stop()

except Exception as e:
    st.error(f"Data Load Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바 (필터)
# ---------------------------------------------------------
st.sidebar.header("🔍 Festival Finder")

# 필터 1: 월
selected_month = st.sidebar.slider("When will you visit?", 1, 12, 10)

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
        st.info("No visitor data
