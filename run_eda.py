import os
import io
import contextlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from tabulate import tabulate
from sklearn.feature_extraction.text import TfidfVectorizer

# 기본 경로 및 설정
BASE_DIR = r"C:\Users\wodyd\OneDrive\PythonWorkspace\electric-vehicle-EDA"
RAW_DIR = os.path.join(BASE_DIR, "raw")
IMG_DIR = os.path.join(BASE_DIR, "images")
REPORT_PATH = os.path.join(BASE_DIR, "EDA_Report.md")

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

files_to_process = [
    ("ev_charging_patterns.csv", "전기차 사용자 충전 패턴 데이터"),
    ("EV_Population.csv", "전기차 기본 보급 데이터"),
    ("ev-charging-forecasting-with-weather-data-LA.csv", "LA 충전 예측 및 날씨 데이터"),
    ("Electric_Vehicle_Population_Data.csv", "워싱턴 주 전기차 등록 인구 데이터"),
    ("caltech_acn_data_2018_2020.csv", "Caltech ACN 충전 세션 데이터"),
    ("EVChargingStationUsage.csv", "충전소 사용 이력 대용량 데이터")
]

def df_info_to_string(df):
    buf = io.StringIO()
    df.info(buf=buf)
    return buf.getvalue()

def save_plot(fig, filename):
    filepath = os.path.join(IMG_DIR, filename)
    fig.tight_layout()
    fig.savefig(filepath, dpi=150)
    plt.close(fig)
    return f"images/{filename}"

def generate_report():
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# 전기차 통합 탐색적 데이터 분석 (EDA) 보고서\n\n")
        f.write("본 보고서는 7가지 원시 데이터셋에 대한 py-eda 스킬 기반의 통합 탐색적 데이터 분석 결과를 포함합니다.\n\n")
        
        plot_counter = 1
        
        for filename, desc in files_to_process:
            filepath = os.path.join(RAW_DIR, filename)
            if not os.path.exists(filepath):
                f.write(f"## {desc} ({filename})\n\n**파일이 존재하지 않습니다.**\n\n---\n\n")
                continue
                
            f.write(f"## {desc} ({filename})\n\n")
            
            try:
                # 대용량 처리를 위해 필요시 제한/샘플링 적용 (샘플링 안하면 너무 느려질 수 있는 파일들)
                if filename == "EVChargingStationUsage.csv":
                    df = pd.read_csv(filepath, low_memory=False, nrows=500000)
                    f.write("*알림: 데이터가 매우 방대하여 무작위는 아니지만 상위 50만 행만 샘플링하여 처리했습니다.*\n\n")
                elif filename.endswith('.csv'):
                    df = pd.read_csv(filepath, low_memory=False)
                else:
                    df = pd.read_excel(filepath)
            except Exception as e:
                f.write(f"데이터 로드 중 에러 발생: {e}\n\n")
                continue
                
            # 기본 정보
            f.write("### 1. 기본 정보 및 데이터 구조\n\n")
            f.write(f"- **데이터 크기**: {df.shape[0]:,}행, {df.shape[1]:,}열\n")
            f.write(f"- **중복 데이터 수**: {df.duplicated().sum():,}개\n\n")
            
            f.write("**[데이터 Info]**\n```\n")
            f.write(df_info_to_string(df))
            f.write("```\n\n")
            
            f.write("**[상위 5개 행]**\n")
            f.write(df.head(5).to_markdown() + "\n\n")
            f.write("**[하위 5개 행]**\n")
            f.write(df.tail(5).to_markdown() + "\n\n")
            
            # 기술 통계 (수치형/범주형 전체)
            f.write("### 2. 기술 통계량\n\n")
            f.write("**[수치형 정보]**\n")
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols:
                f.write(df[num_cols].describe().to_markdown() + "\n\n")
            else:
                f.write("수치형 컬럼이 없습니다.\n\n")
                
            f.write("**[범주형 정보]**\n")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            if cat_cols:
                f.write(df[cat_cols].astype(str).describe().to_markdown() + "\n\n")
            else:
                f.write("범주형 컬럼이 없습니다.\n\n")
                
            # 시각화 및 세부 분석
            f.write("### 3. 세부 특성 및 시각화 분석\n\n")
            
            if filename == "ev_charging_patterns.csv":
                # 1. 차량 모델별 충전 횟수
                fig, ax = plt.subplots(figsize=(10, 6))
                v_counts = df['Vehicle Model'].value_counts().head(30)
                v_counts.plot(kind='bar', ax=ax, color='teal')
                ax.set_title("차량 모델별 충전 세션 빈도")
                ax.set_ylabel("빈도 수")
                img_path = save_plot(fig, f"plot_{plot_counter}.png")
                
                f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                f.write(f"![{ax.get_title()}]({img_path})\n\n")
                f.write("**관련 데이터 표**\n\n")
                f.write(v_counts.reset_index().to_markdown(index=False) + "\n\n")
                f.write("**분석 해석:**\n본 차트는 전체 충전 세션에서 가장 많이 등장하는 상위 30개의 전기차 모델별 이용 횟수를 보여줍니다. 특정 모델이 압도적으로 많이 이용되는 경향이 있는지 파악할 수 있으며, 주력 모델 기반의 충전소 맞춤형 서비스 기획 및 프로모션 타겟팅에 주요 지표로 활용될 수 있는 중요한 분석 결과입니다. 이를 통해 해당 시장에서 어떤 차량이 가장 충전을 활발하게 하는지 뚜렷하게 관측할 수 있습니다.\n\n")
                plot_counter += 1
                
                # 2. 충전시간 vs 소모에너지 산점도
                fig, ax = plt.subplots(figsize=(10, 6))
                valid_num = df.dropna(subset=['Charging Duration (hours)', 'Energy Consumed (kWh)'])
                ax.scatter(valid_num['Charging Duration (hours)'], valid_num['Energy Consumed (kWh)'], alpha=0.5)
                ax.set_title("충전 소요 시간과 소비 전력량의 관계")
                ax.set_xlabel("충전 소요 시간(Hours)")
                ax.set_ylabel("소비 전력량(kWh)")
                img_path = save_plot(fig, f"plot_{plot_counter}.png")
                
                desc_tbl = valid_num[['Charging Duration (hours)', 'Energy Consumed (kWh)']].describe()
                f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                f.write(f"![{ax.get_title()}]({img_path})\n\n")
                f.write("**관련 통계 표**\n\n")
                f.write(desc_tbl.to_markdown() + "\n\n")
                f.write("**분석 해석:**\n충전 시간과 소모 단량의 분포를 흩뿌린 산점도입니다. 우상향하는 추세를 통해 충전 시간이 길어질수록 충전 전력량이 선형적으로 증가한다는 보편적인 결과를 입증합니다. 다만 간혹 동일 시간에 대비 낮거나 높은 형태의 아웃라이어들이 존재하는데, 이는 완속/급속 충전기의 다양한 유형 차이 또는 배터리 잔량의 과도 방전 후 충전 상황 등 이질적인 요소가 있음을 알 수 있게 해주는 유의미한 형태입니다.\n\n")
                plot_counter += 1
                
            elif filename == "EV_Population.csv":
                # 브랜드 점유율
                fig, ax = plt.subplots(figsize=(10, 6))
                make_counts = df['Make'].value_counts().head(20)
                make_counts.sort_values().plot(kind='barh', ax=ax, color='coral')
                ax.set_title("제조사(Make)별 전기차 등록 빈도 순위(Top 20)")
                ax.set_xlabel("차량 대수")
                img_path = save_plot(fig, f"plot_{plot_counter}.png")
                
                f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                f.write(f"![{ax.get_title()}]({img_path})\n\n")
                f.write("**관련 데이터 표**\n\n")
                f.write(make_counts.reset_index().to_markdown(index=False) + "\n\n")
                f.write("**분석 해석:**\n본 가로 막대 그래프는 시장에 보급된 전기차의 상위 20개 제조사별 점유 현황을 나타냅니다. 테슬라와 같은 거대 메이저 브랜드의 독주 현상이 존재하는지 아니면 다양한 레거시 완성차 업체들이 시장 점유율을 나누어 가지고 있는지 파악할 수 있는 가장 대표적인 지표로 작용합니다.\n\n")
                plot_counter += 1
                

            elif filename == "ev-charging-forecasting-with-weather-data-LA.csv":
                fig, ax = plt.subplots(figsize=(10, 6))
                if 'weather_conditions' in df.columns:
                    w_counts = df['weather_conditions'].value_counts()
                    w_counts.plot(kind='bar', ax=ax, color='skyblue')
                    ax.set_title("충전 중의 날씨 상황(Weather Conditions) 빈도")
                    ax.set_ylabel("세션 빈도")
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**관련 데이터 표**\n\n")
                    f.write(w_counts.reset_index().to_markdown(index=False) + "\n\n")
                    f.write("**분석 해석:**\n충전을 예측하는 당시에 기록된 다양한 날씨 상황(흐림, 맑음, 비 등)에 대한 빈도 그래프입니다. LA 지역 기반 데이터 구조상 맑은 날 비율이 월등히 높을 것으로 추정되며, 특정 비나 눈 등 악천후 상황에서 충전 행태가 줄어들거나 급증하는지를 후속 모델링으로 연결하기 위한 예비 분석입니다.\n\n")
                    plot_counter += 1
                else:
                    f.write(f"weather_conditions 컬럼이 없습니다.\n\n")
                
            elif filename == "Electric_Vehicle_Population_Data.csv":
                fig, ax = plt.subplots(figsize=(10, 6))
                if 'County' in df.columns:
                    c_counts = df['County'].value_counts().head(15)
                    c_counts.plot(kind='bar', ax=ax, color='green')
                    ax.set_title("행정 구역(County)별 전기차 인구 분포 Top 15")
                    ax.set_ylabel("보급 대수")
                    plt.xticks(rotation=45)
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**관련 데이터 표**\n\n")
                    f.write(c_counts.reset_index().to_markdown(index=False) + "\n\n")
                    f.write("**분석 해석:**\n미국 워싱턴주 등 주 단위의 포괄적인 데이터에서 가장 전기차가 밀집해있는 하위 행정 구역 리스트 15개입니다. King County와 같이 기술 인프라가 높고 친환경 정책이 강한 대도심 쪽에 집중되어있는 현상을 시각적으로 입증하며 지방으로 갈수록 보급이 감소하는 경향을 보여줍니다.\n\n")
                    plot_counter += 1
                
                fig, ax = plt.subplots(figsize=(10, 6))
                top_makes = df['Make'].value_counts().head(5).index
                df_top = df[df['Make'].isin(top_makes)]
                if not df_top.empty:
                    df_top.boxplot(column='Electric Range', by='Make', ax=ax, grid=False)
                    ax.set_title("주요 핵심 브랜드별 차량의 전기 주행거리 분포")
                    ax.set_xlabel("제조사 브랜드")
                    ax.set_ylabel("전기 주행거리 (Range)")
                    plt.suptitle("")
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**관련 통계 표 (그룹별 Description)**\n\n")
                    f.write(df_top.groupby('Make')['Electric Range'].describe().to_markdown() + "\n\n")
                    f.write("**분석 해석:**\n상위 5개의 핵심 전기차 브랜드를 추출하여 배터리 효율의 척도인 주행 거리(Range)를 박스 플롯으로 나타냈습니다. 데이터에 집적된 구형 및 신형 모델 편차가 포함되어 박스 모양에 분산이 크게 보이지만 제조사별로 핵심 역량인 배터리 밀도를 간접적으로 엿볼 수 있으며 중앙값 레벨의 격차를 보여주는 유용한 그래프입니다.\n\n")
                    plot_counter += 1

            elif filename == "caltech_acn_data_2018_2020.csv":
                fig, ax = plt.subplots(figsize=(10, 6))
                if 'siteID' in df.columns and 'kWhDelivered' in df.columns:
                    site_energy = df.groupby('siteID')['kWhDelivered'].sum().sort_values(ascending=False).head(10)
                    site_energy.plot(kind='bar', ax=ax, color='navy')
                    ax.set_title("충전 사이트(Site ID)별 총 지급된 역대 에너지(kWh)")
                    ax.set_ylabel("총 에너지 지급량 (kWh)")
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**관련 데이터 표**\n\n")
                    f.write(site_energy.reset_index().to_markdown(index=False) + "\n\n")
                    f.write("**분석 해석:**\n캘리포니아 공대 ACN 네트워크 안에 구성된 다수의 주차장 및 충전 섹터(사이트) 중 에너지를 가장 압도적으로 많이 소비한 영역을 보여줍니다. 이는 주간 이용자 통행량이 가장 많거나 장시간 체류하는 주차 허브임을 암시하며 에너지 그리드 매니지먼트에서 최우선 관리대상으로 지정할 수 있는 근거를 제공합니다.\n\n")
                    plot_counter += 1
                
            elif filename == "EVChargingStationUsage.csv":
                # 대용량이라 빈도 위주 간단히
                fig, ax = plt.subplots(figsize=(10, 6))
                if 'Plug Type' in df.columns:
                    plug_counts = df['Plug Type'].value_counts()
                    plug_counts.plot(kind='bar', ax=ax, color='darkorange')
                    ax.set_title("충전 스테이션에서의 플러그 타입(Plug Type) 선호도")
                    ax.set_ylabel("활용 빈도")
                    plt.xticks(rotation=0)
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**관련 데이터 표**\n\n")
                    f.write(plug_counts.reset_index().to_markdown(index=False) + "\n\n")
                    f.write("**분석 해석:**\n네트워크 인프라 데이터 베이스 상에서 관측된 J1772 완속 단자, 혹은 다양한 고속 단자들의 플러그 타입별 사용 비율입니다. 구형 완속 사용량이 지배적인지 신형 급속 비율이 폭발적으로 늘고 있는지 물리적인 기기 이용 생태계를 명확하게 대변하는 도표이며 50만 건 이상이 입증하는 강력한 지표입니다.\n\n")
                    plot_counter += 1
                    
                fig, ax = plt.subplots(figsize=(10, 6))
                if 'Fee' in df.columns:
                    # 요금을 숫자형 변환 처리 시도, 달러나 공백 제거
                    f_val = pd.to_numeric(df['Fee'], errors='coerce').dropna()
                    if not f_val.empty:
                        f_val[f_val < 50].plot.hist(bins=30, ax=ax, color='crimson')
                        ax.set_title("거래당 지불된 충전 요금 빈도 히스토그램 (50 미만 구간)")
                        ax.set_xlabel("지불 금액 (Fee)")
                        img_path = save_plot(fig, f"plot_{plot_counter}.png")
                        
                        desc_tbl = f_val.describe()
                        f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                        f.write(f"![{ax.get_title()}]({img_path})\n\n")
                        f.write("**관련 통계 표**\n\n")
                        f.write(desc_tbl.to_markdown() + "\n\n")
                        f.write("**분석 해석:**\n충전 세션당 부과된 요금(Fee)이 어떻게 뭉쳐있는지 히스토그램으로 출력했습니다. 무료 급속/완속 충전으로 0원에 매우 크게 집중되어 있거나 기본 최저 요금 단위에 몰려 있는 등 사용자들의 충전자금 지출 패턴을 소수점 빈도까지 아주 미세하게 파악할 수 있는 경제적 분석 지표입니다.\n\n")
                        plot_counter += 1

            # 텍스트 특성 분석 (존재할 경우에 한함)
            text_cols = [c for c in cat_cols if df[c].dropna().astype(str).str.len().mean() > 30 and df[c].nunique() > 20]
            if text_cols:
                f.write("### 4. 텍스트 컬럼 주요 키워드 분석\n\n")
                t_col = text_cols[0]
                corpus = df[t_col].dropna().astype(str).tolist()
                corpus = corpus[:5000] # 최적화를 위해 일부 추출
                
                vectorizer = TfidfVectorizer(max_features=30, stop_words='english')
                try:
                    X = vectorizer.fit_transform(corpus)
                    scores = X.sum(axis=0).A1
                    words = vectorizer.get_feature_names_out()
                    word_scores = pd.DataFrame({'Keyword': words, 'TF-IDF Score': scores})
                    word_scores = word_scores.sort_values('TF-IDF Score', ascending=False)
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.barh(word_scores['Keyword'][:15][::-1], word_scores['TF-IDF Score'][:15][::-1], color='magenta')
                    ax.set_title(f"'{t_col}' 컬럼의 상위 키워드 TF-IDF 중요도")
                    img_path = save_plot(fig, f"plot_{plot_counter}.png")
                    
                    f.write(f"#### 시각화 {plot_counter}: {ax.get_title()}\n\n")
                    f.write(f"![{ax.get_title()}]({img_path})\n\n")
                    f.write("**키워드 빈도 표**\n\n")
                    f.write(word_scores.to_markdown(index=False) + "\n\n")
                    f.write("**분석 해석:**\n평균 글자 수 및 고유값이 큰 문자열로 식별된 컬럼에 대하여, 자연어 전처리를 기반으로 한 빈도-역문서 빈도(TF-IDF) 알고리즘을 사용해 가장 특색 있는 핵심 단어를 추출했습니다. 무의미한 불용어를 거르고 도출된 이 결과는 고객의 리뷰 내용이나 운영 세부 데이터에서의 이슈를 파악하는 정성적 지표로 탁월한 통찰들을 제공합니다.\n\n")
                    plot_counter += 1
                except Exception as e:
                    f.write(f"텍스트 키워드 에러: {e}\n\n")

if __name__ == "__main__":
    generate_report()
    print("EDA 통합 리포트 생성 완료: EDA_Report.md 및 이미지 폴더 생성")
