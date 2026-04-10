import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import koreanize_matplotlib

# 페이지 설정
st.set_page_config(
    page_title="글로벌 전기차(EV) 데이터 대시보드",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw")

# 커스텀 CSS (프리미엄 룩)
st.markdown("""
<style>
    .main {background-color: #F8F9FA;}
    h1, h2, h3 {color: #1a202c;}
    .stMetric .metric-value {color: #2b6cb0;}
    .reportview-container .main .block-container{padding-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# 데이터 로딩 함수
@st.cache_data(show_spinner=False)
def load_data(filename, is_excel=False, nrows=None):
    filepath = os.path.join(RAW_DIR, filename)
    if not os.path.exists(filepath):
        return pd.DataFrame()
    if is_excel:
        return pd.read_excel(filepath, nrows=nrows)
    else:
        return pd.read_csv(filepath, low_memory=False, nrows=nrows)

# 사이드바
st.sidebar.title("⚡ EV Data Dashboard")
st.sidebar.write("7가지 전기차 도메인 데이터 기반 다목적 분석 엔진")

menu = st.sidebar.radio("데이터 분석 메뉴", (
    "Overview (핵심 지표)", 
    "Map (지리 데이터 & 인프라)", 
    "Patterns (충전 사용자 패턴)", 
    "Population (기기 및 브랜드 동향)",
    "Summary Report (EDA)"
))

st.sidebar.markdown("---")
st.sidebar.info("**진단 모델**: Multi-Dataset Association\n\n**적용 패키지**: Streamlit, Pandas, Matplotlib")

# 데이터 사전 로드 (메모리 제어용 제한)
with st.spinner("빅데이터 로딩 최적화 중..."):
    df_patterns = load_data("ev_charging_patterns.csv")
    df_pop = load_data("EV_Population.csv")
    df_station = load_data("EVChargingStationUsage.csv", nrows=100000) # 대용량
    df_caltech = load_data("caltech_acn_data_2018_2020.csv", nrows=50000)
    df_la = load_data("ev-charging-forecasting-with-weather-data-LA.csv")
    df_wa = load_data("Electric_Vehicle_Population_Data.csv", nrows=50000)

if menu == "Overview (핵심 지표)":
    st.title("📊 전기차 분석 통합 대시보드 요약")
    st.markdown("수만 단위를 넘나드는 충전 세션, 딜러망, 보급 데이터를 한 곳에서 모니터링합니다.")
    
    col1, col2, col3 = st.columns(3)
    if not df_patterns.empty:
        col1.metric("분석된 유저 충전 패턴", f"{len(df_patterns):,} 건", "세션 수")
    if not df_pop.empty:
        col2.metric("기본 보급 차량 수", f"{len(df_pop):,} 대", "등록 기준")
    if not df_station.empty:
        col3.metric("분석된 스테이션 로그", f"{len(df_station):,} 건", "10만 건 샘플링")

    st.markdown("---")
    st.subheader("데이터셋 샘플 프리뷰")
    
    dataset_opt = st.selectbox("데이터셋 선택", [
        "User Patterns", "EV Population", "Station Usage", "Caltech ACN", "WA Pop"
    ])
    
    if dataset_opt == "User Patterns" and not df_patterns.empty:
        st.dataframe(df_patterns.head(50), use_container_width=True)
    elif dataset_opt == "EV Population" and not df_pop.empty:
        st.dataframe(df_pop.head(50), use_container_width=True)
    elif dataset_opt == "Station Usage" and not df_station.empty:
        st.dataframe(df_station.head(50), use_container_width=True)
    elif dataset_opt == "Caltech ACN" and not df_caltech.empty:
        st.dataframe(df_caltech.head(50), use_container_width=True)
    elif dataset_opt == "WA Pop" and not df_wa.empty:
        st.dataframe(df_wa.head(50), use_container_width=True)

elif menu == "Map (지리 데이터 & 인프라)":
    st.title("🗺️ 공간 인프라 지도 분석")
    st.markdown("전기차 충전망 거점 분포를 시각화합니다.")
    
    st.subheader("EV 스테이션 위도/경도 매핑 (북미 중심 샘플)")
    if not df_station.empty and 'Latitude' in df_station.columns and 'Longitude' in df_station.columns:
        stat_map = df_station[['Latitude', 'Longitude']].rename(columns={"Latitude": "lat", "Longitude": "lon"}).dropna()
        st.map(stat_map.head(1000)) # 퍼포먼스를 위해 1000개만
    else:
        st.write("충전소 사용 데이터에 유효한 위경도 컬럼이 없습니다.")

elif menu == "Patterns (충전 사용자 패턴)":
    st.title("👥 전기차 유저 충전 행태 다각도 분석")
    
    if df_patterns.empty:
        st.error("충전 패턴 데이터(ev_charging_patterns.csv)가 유효하지 않습니다.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("선호되는 대상 모델 분포 (Top 15)")
            model_counts = df_patterns['Vehicle Model'].value_counts().head(15)
            st.bar_chart(model_counts)
            
        with c2:
            st.subheader("요일별 충전 트래픽 분포")
            day_counts = df_patterns['Day of Week'].value_counts()
            st.bar_chart(day_counts)
            
        st.markdown("---")
        st.subheader("충전 소요 시간과 에너지 요구량 상관관계 (1000개 샘플)")
        
        sample_pat = df_patterns.head(1000)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(sample_pat['Charging Duration (hours)'], sample_pat['Energy Consumed (kWh)'], alpha=0.6, c='teal')
        ax.set_title("Hours vs kWh Consumed")
        ax.set_xlabel("시간 (hr)")
        ax.set_ylabel("소모 Kwh")
        ax.grid(alpha=0.3)
        st.pyplot(fig)

elif menu == "Population (기기 및 브랜드 동향)":
    st.title("📈 시장 성숙도 및 브랜드 점유율 (Population)")
    
    tab1, tab2 = st.tabs(["브랜드 점유율 (Make)", "충전단자 및 전압 환경"])
    
    with tab1:
        if not df_pop.empty and 'Make' in df_pop.columns:
            st.subheader("제조사(Make)별 보급 등록 현황")
            make_dist = df_pop['Make'].value_counts().head(15).sort_values()
            fig, ax = plt.subplots(figsize=(8, 5))
            make_dist.plot(kind='barh', ax=ax, color='salmon')
            ax.set_title("제조사별 전기차 수량")
            st.pyplot(fig)
        else:
            st.write("표시할 수 있는 브랜드 데이터가 없습니다.")
            
    with tab2:
        if not df_station.empty and 'Plug Type' in df_station.columns:
            st.subheader("AC/DC, J1772 등 충전 포트 점유 스펙")
            plug_cnt = df_station['Plug Type'].value_counts()
            st.bar_chart(plug_cnt)
        if not df_caltech.empty and 'kWhDelivered' in df_caltech.columns:
            st.subheader("ACN Caltech - 사이트별 전달 누적 에너지")
            site_energy = df_caltech.groupby('siteID')['kWhDelivered'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(site_energy)

elif menu == "Summary Report (EDA)":
    st.title("📜 Py-EDA 스크립트 실행 백서")
    st.markdown("본 대시보드를 구축하기 전 기반으로 도출된 통합 마크다운 분석 보고서입니다.")
    report_file = os.path.join(BASE_DIR, "EDA_Report.md")
    
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with st.expander("EDA 원문 리포트 열기 (클릭)", expanded=True):
            st.markdown(content)
    else:
        st.warning("`EDA_Report.md` 파일이 아직 생성되지 않았습니다.")
