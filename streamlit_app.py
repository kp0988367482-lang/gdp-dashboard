import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. GWP (지구온난화지수) 테이블 정의 - 배출계수 시나리오 역할
# 단위: CO2eq/단위 가스 (100년 기준)
GWP_SCENARIOS = {
    "IPCC Second Assessment Report (SAR)": { # 1996년 기준
        "CO2": 1,
        "CH4": 21,
        "N2O": 310,
    },
    "IPCC Fourth Assessment Report (AR4)": { # 2007년 기준 (현행 통계에 많이 사용)
        "CO2": 1,
        "CH4": 25,
        "N2O": 298,
    },
    "IPCC Sixth Assessment Report (AR6)": { # 2021년 기준 (최신 GWP)
        "CO2": 1,
        "CH4": 27.9,
        "N2O": 273,
    }
}

# 2. 가상의 원시 배출량 데이터 (Raw Mass in kt)
# 국가별 CO2, CH4, N2O의 원시 질량 (킬로톤) 데이터 가정
# 실제 사용 시 이 데이터를 실제 활동 자료(Activity Data)와 연동해야 함
DUMMY_RAW_DATA = {
    "Country": ["USA", "China", "India", "EU27", "South Korea"],
    "Year": [2023] * 5,
    "Raw_CO2_kt": [5000000, 12000000, 3500000, 4200000, 600000],
    "Raw_CH4_kt": [38095, 71428, 28571, 28000, 5714],
    "Raw_N2O_kt": [806, 1290, 580, 645, 96],
}
df_raw = pd.DataFrame(DUMMY_RAW_DATA)

# --- 설정 및 데이터 계산 ---

st.set_page_config(
    page_title="GWP/EF 시나리오 기반 GHG 배출량 계산기",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 GWP/EF 시나리오 기반 GHG 배출량 계산기")
st.markdown(
    """
    이 대시보드는 사용자가 **지구온난화지수(GWP)** 시나리오를 선택하면, 
    가상의 **원시 배출량(Raw Mass)** 데이터에 선택된 GWP를 적용하여 
    총 온실가스 ($\text{CO}_2\text{eq}$) 배출량을 **동적으로 재계산**하고 시각화합니다.
    """
)
st.divider()

# 3. 배출계수(GWP) 선택 버튼
st.header("1️⃣ 배출계수 (GWP) 시나리오 선택")

selected_scenario_name = st.selectbox(
    "적용할 GWP/EF 시나리오를 선택하세요:",
    list(GWP_SCENARIOS.keys()),
    help="선택된 시나리오의 GWP 값(배출계수)이 아래 계산에 적용됩니다."
)

selected_gwp = GWP_SCENARIOS[selected_scenario_name]

# 선택된 GWP 값을 테이블로 보여주기
st.markdown("##### ➡️ 적용된 GWP 값 (배출계수)")
st.dataframe(pd.DataFrame({
    'Gas': selected_gwp.keys(),
    'GWP Value': selected_gwp.values()
}), hide_index=True)


# 4. 동적 GHG 계산 함수
@st.cache_data(show_spinner=False)
def calculate_ghg_emissions(df_raw, gwp_values):
    """선택된 GWP 값을 적용하여 CO2eq를 계산하고 총합을 구합니다."""
    
    df = df_raw.copy()
    
    # 배출계수 (GWP) 적용
    df['CO2_eq'] = df['Raw_CO2_kt'] * gwp_values["CO2"]
    df['CH4_eq'] = df['Raw_CH4_kt'] * gwp_values["CH4"]
    df['N2O_eq'] = df['Raw_N2O_kt'] * gwp_values["N2O"]
    
    # 총 배출량 (Total_GHG_kt) 계산 및 정렬
    df['Total_GHG_kt'] = df[['CO2_eq', 'CH4_eq', 'N2O_eq']].sum(axis=1)
    df = df.sort_values(by='Total_GHG_kt', ascending=False).reset_index(drop=True)
    
    # 필요한 컬럼만 선택하여 최종 데이터프레임 구성
    df_final = df[['Country', 'Year', 'CO2_eq', 'CH4_eq', 'N2O_eq', 'Total_GHG_kt']].copy()
    
    return df_final

# 선택된 시나리오로 데이터프레임 계산
df_calculated = calculate_ghg_emissions(df_raw, selected_gwp)

st.divider()

# --- 웹사이트 레이아웃 (재계산된 데이터 사용) ---

# 1. 요약 메트릭
st.header("2️⃣ 재계산된 총 배출량 요약")

total_ghg_emissions_mt = df_calculated['Total_GHG_kt'].sum() / 1000 # kt -> Mt
max_emitter = df_calculated.iloc[0]['Country']
max_emission_mt = df_calculated.iloc[0]['Total_GHG_kt'] / 1000 # kt -> Mt

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label=f"전체 국가 총 배출량 ({selected_scenario_name})", 
        value=f"{total_ghg_emissions_mt:,.1f} Mt $\\text{{CO}}_2\\text{{eq}}$",
        help="데이터에 포함된 모든 국가의 총 온실가스 배출량입니다."
    )

with col2:
    st.metric(
        label="최대 배출 국가", 
        value=max_emitter,
        delta=f"{max_emission_mt:,.1f} Mt $\\text{{CO}}_2\\text{{eq}}$"
    )
    
with col3:
    st.metric(
        label="데이터 기준 연도", 
        value=f"{df_calculated['Year'].iloc[0]}"
    )

st.divider()

# 2. 국가별 배출량 막대 차트
st.header("3️⃣ 국가별 총 배출량 비교 (차트)")

fig_bar = px.bar(
    df_calculated, 
    x='Country', 
    y='Total_GHG_kt', 
    title=f'국가별 온실가스 총 배출량 (kt $\\text{{CO}}_2\\text{{eq}}$) - {selected_scenario_name}',
    labels={'Total_GHG_kt': '총 배출량 (kt $\\text{{CO}}_2\\text{{eq}}$)', 'Country': '국가'},
    color='Country',
    template='plotly_white'
)

fig_bar.update_layout(showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# 4. 상세 배출량 (가스별) 파이 차트 및 데이터 테이블
st.header("4️⃣ 상세 데이터 및 가스별 분석")

selected_country = st.selectbox(
    "가스별 배출량을 분석할 국가를 선택하세요:", 
    df_calculated['Country'].unique()
)

country_data = df_calculated[df_calculated['Country'] == selected_country].iloc[0]

# 가스별 데이터 준비
gas_data = country_data[['CO2_eq', 'CH4_eq', 'N2O_eq']]
gas_df = gas_data.reset_index()
gas_df.columns = ['Gas', 'Emissions']

# 파이 차트
fig_pie = px.pie(
    gas_df, 
    values='Emissions', 
    names='Gas', 
    title=f'{selected_country}의 가스별 배출량 비율 ({selected_scenario_name})',
    hole=.3, 
    template='plotly_white'
)
fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))

# 파이 차트와 상세 테이블을 나란히 배치
col_pie, col_table = st.columns([1, 1])

with col_pie:
    st.plotly_chart(fig_pie, use_container_width=True)
    
with col_table:
    st.subheader(f"{selected_country} 상세 데이터 (kt $\\text{{CO}}_2\\text{{eq}}$)")
    
    display_df = pd.DataFrame({
        '구분': ['CO₂', 'CH₄', 'N₂O'],
        '배출량 (kt $\\text{CO}_2\\text{eq}$)': [f"{country_data['CO2_eq']:,.0f}", f"{country_data['CH4_eq']:,.0f}", f"{country_data['N2O_eq']:,.0f}"]
    })
    st.dataframe(display_df, hide_index=True, use_container_width=True)
    
    st.markdown(f"**총 배출량**: $\\text{{ {country_data['Total_GHG_kt']:,.0f} kt }}\\text{{ CO}}_2\\text{{eq}}$")
    st.caption(
        f"계산에 사용된 GWP 값: $\\text{{CO}}_2$={selected_gwp['CO2']}, $\\text{{CH}}_4$={selected_gwp['CH4']}, $\\text{{N}}_2\text{{O}}$={selected_gwp['N2O']}"
    )
