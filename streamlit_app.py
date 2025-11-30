import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
    selected_category =
