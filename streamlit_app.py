import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------------------------------------
# 1. 페이지 설정 (Foreigner-Friendly UI)
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
def load_data():
    # 1. 파일 읽기 (인코딩 처리)
    try:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='cp949')
    except:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='utf-8')

    # 2. 컬럼명 공백 제거 (오류 방지)
    df.columns = df.columns.str.replace(' ', '').str.strip()

    # 3. '외국인(명)' 데이터 숫자 변환
    # CSV 파일 컬럼명이 '외국인(명)'이라고 가정
    target_col = '외국인(명)' if '외국인(명)' in df.columns else '외국인'
    
    if target_col in df.columns:
        # 콤마, 텍스트(미집계 등) 제거 후 숫자로 변환
        df['foreign_visitors'] = df[target_col].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초행사', '0')
        # 숫자가 아닌 값 강제 0 처리
        df['foreign_visitors'] = pd.to_numeric(df['foreign_visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['foreign_visitors'] = 0

    # 4. '시작월' 데이터 숫자 변환
    if '시작월' in df.columns:
        df['month'] = pd.to_numeric(df['시작월'], errors='coerce').fillna(0).astype(int)
    else:
        df['month'] = 0
        
    return df

# 지역별 중심 좌표 (CSV에 좌표가 없으므로 매핑용)
lat_lon_dict = {
    '서울': [37.5665, 126.9780], '부산': [35.1796, 129.0756], '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052], '광주': [35.1595, 126.8526], '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114], '세종': [36.4800, 127.2890], '경기': [37.4138, 127.5183],
    '강원': [37.8228, 128.1555], '충북': [36.6350, 127.4914], '충남': [36.5184, 126.8000],
    '전북': [35.7175, 127.1530], '전남': [34.8161, 126.4629], '경북': [36.5760, 128.5056],
    '경남': [35.2383, 128.6925], '제주': [33.4890, 126.4983]
}

try:
    df = load_data()

    # 5. 지도 좌표 생성 Logic
    # 광역단체명 컬럼 확인
    region_col = '광역자치단체명' if '광역자치단체명' in df.columns else '시도'
    
    if region_col in df.columns:
        # 지역명 앞 2글자로 좌표 매핑
        df['lat_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[0])
        df['lon_base'] = df[region_col].astype(str).str[:2].map(lambda x: lat_lon_dict.get(x, [36.5, 127.5])[1])
        
        # 지도에서 점이 겹치지 않게 랜덤 노이즈(Jitter) 추가
        df['lat'] = df['lat_base'] + np.random.normal(0, 0.03, len(df))
        df['lon'] = df['lon_base'] + np.random.normal(0, 0.03, len(df))
    else:
        st.error("CSV 파일에 지역명 컬럼이 없습니다.")
        st.stop()

except Exception as e:
    st.error(f"데이터 로드 에러: {e}")
    st.stop()


# ---------------------------------------------------------
# 3. 사이드바 (필터링 옵션)
# ---------------------------------------------------------
st.sidebar.header("🔍 Festival Finder")
st.sidebar.markdown("Filter festivals by your preference!")

# [필터 1] 지역 (Region)
region_list = ['All'] + sorted(df[region_col].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("📍 Region (Where)", region_list)

# [필터 2] 축제 유형 (Category)
type_col = '축제유형' # CSV 헤더 확인 필요
if type_col in df.columns:
    type_list = ['All'] + sorted(df[type_col].dropna().unique().tolist())
    selected_type = st.sidebar.multiselect("🎨 Category (Interest)", type_list, default='All')
else:
    selected_type = 'All'

# [필터 3] 시작월 (Month)
selected_month = st.sidebar.slider("📅 Month (When)", 1, 12, (3, 10)) # 기본값 3월~10월

# ---------------------------------------------------------
# 4. 데이터 필터링 로직
# ---------------------------------------------------------
# 월 필터링 (범위 선택)
filtered_df = df[(df['month'] >= selected_month[0]) & (df['month'] <= selected_month[1])]

# 지역 필터링
if selected_region != 'All':
    filtered_df = filtered_df[filtered_df[region_col] == selected_region]

# 유형 필터링
if type_col in df.columns and 'All' not in selected_type and selected_type:
    filtered_df = filtered_df[filtered_df[type_col].isin(selected_type)]

# ---------------------------------------------------------
# 5. 메인 대시보드 레이아웃
# ---------------------------------------------------------
st.title("🇰🇷 2025 K-Festival Explorer")
st.markdown(f"Finding festivals from **{selected_month[0]}월** to **{selected_month[1]}월**...")

# 상단 요약 지표
col1, col2, col3 = st.columns(3)
col1.metric("Festivals Found", f"{len(filtered_df)} 개")
col2.metric("Selected Region", selected_region)
if not filtered_df.empty:
    top_festival = filtered_df.sort_values(by='foreign_visitors', ascending=False).iloc[0]['축제명']
    col3.metric("Most Popular (Foreigners)", top_festival)

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🗺️ Map View", "📋 List View", "🏆 Foreigner's Pick"])

with tab1:
    st.subheader("Festival Locations")
    if not filtered_df.empty:
        # 지도 시각화
        st.map(filtered_df, latitude='lat', longitude='lon', color='#FF4B4B', size=20)
    else:
        st.warning("No festivals found matching your criteria.")

with tab2:
    st.subheader("Festival Details")
    if not filtered_df.empty:
        # 보여줄 컬럼 선택
        cols_to_show = ['축제명', region_col, '개최장소', 'month', 'foreign_visitors']
        if type_col in df.columns: cols_to_show.append(type_col)
        
        st.dataframe(
            filtered_df[cols_to_show].sort_values('month'),
            hide_index=True,
            use_container_width=True,
            column_config={
                "month": "Month",
                "foreign_visitors": st.column_config.NumberColumn("Foreign Visitors", format="%d 명")
            }
        )
    else:
        st.write("No data.")

with tab3:
    st.subheader("🔥 Top 10 Festivals for Foreigners")
    st.caption("Based on 'Foreign Visitor' data in the dataset")
    
    # 전체 데이터 중 외국인 방문객 상위 10개 추출
    top10 = df.sort_values(by='foreign_visitors', ascending=False).head(10)
    
    # 막대 그래프
    fig = px.bar(
        top10,
        x='foreign_visitors',
        y='축제명',
        orientation='h',
        text='foreign_visitors',
        color=type_col if type_col in df.columns else None,
        title="Most Visited Festivals by Foreigners"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}) # 많은 순서대로 정렬
    st.plotly_chart(fig, use_container_width=True)
