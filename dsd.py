import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="그래프_최종 대시보드",
    page_icon="📊",
    layout="wide"
)

# =========================
# 사이드바: 파일 업로드/선택
# =========================
st.sidebar.title("📁 데이터 로드")
uploaded = st.sidebar.file_uploader("엑셀 파일 업로드 (.xlsx)", type=["xlsx"])

default_path = "0. 그래프_최종.xlsx"
use_default = st.sidebar.toggle("기본 경로 사용(실행 폴더 내)", value=True)
path_input = None
if not uploaded and not use_default:
    path_input = st.sidebar.text_input("또는 파일 경로 직접 입력", value=default_path)

st.sidebar.markdown("---")
st.sidebar.caption("시트명(한글) 기준: 바차트_히스토그램 · 시계열차트 · 파이차트 · 산점도 · 파레토차트")

# ================
# 데이터 로더
# ================
@st.cache_data(show_spinner=False)
def load_excel(_file_like_or_path: str | io.BytesIO):
    xls = pd.ExcelFile(_file_like_or_path)
    sheets = {name: pd.read_excel(_file_like_or_path, sheet_name=name) for name in xls.sheet_names}
    return sheets

def ensure_loaded():
    if uploaded:
        return load_excel(uploaded)
    else:
        target = default_path if use_default else (path_input or default_path)
        return load_excel(target)

try:
    sheets = ensure_loaded()
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

# 시트 존재 체크
required = ["바차트_히스토그램", "시계열차트", "파이차트", "산점도", "파레토차트"]
missing = [s for s in required if s not in sheets]
if missing:
    st.error(f"아래 시트가 파일에 없습니다: {', '.join(missing)}")
    st.stop()

# ================
# 상단 헤더 / 설명
# ================
st.title("그래프_최종 대시보드")
st.caption("월별 총매출 · 제품별 추세 · 1분기 비중 · 매출 vs 비용 · 파레토")

# ====================================================
# 0) 상단 KPI 카드 (예: 총매출 합계, 최고/최저 월)
# ====================================================
bar_df = sheets["바차트_히스토그램"].copy()
# 날짜형 변환 & 정렬
if not np.issubdtype(bar_df["월"].dtype, np.datetime64):
    bar_df["월"] = pd.to_datetime(bar_df["월"])
bar_df = bar_df.sort_values("월")

total_sales = int(bar_df["총 매출"].sum())
max_row = bar_df.loc[bar_df["총 매출"].idxmax()]
min_row = bar_df.loc[bar_df["총 매출"].idxmin()]

c1, c2, c3 = st.columns(3)
c1.metric("연간 총매출 합계", f"{total_sales:,}")
c2.metric("최고 매출 월", f"{max_row['월'].strftime('%Y-%m')}", f"{int(max_row['총 매출']):,}")
c3.metric("최저 매출 월", f"{min_row['월'].strftime('%Y-%m')}", f"{int(min_row['총 매출']):,}")

st.divider()

# ==========================================
# 1) 월별 총매출 (막대)
# ==========================================
bar_df["월_label"] = bar_df["월"].dt.strftime("%Y-%m")
fig_bar = px.bar(
    bar_df,
    x="월_label", y="총 매출",
    text="총 매출",
    title="월별 총 매출",
)
fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
fig_bar.update_layout(yaxis_title="매출", xaxis_title="월", uniformtext_minsize=8, uniformtext_mode="show")
st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 2) 제품별 월 매출 추세 (멀티 라인)
# ==========================================
ts_df = sheets["시계열차트"].copy()
if not np.issubdtype(ts_df["월"].dtype, np.datetime64):
    ts_df["월"] = pd.to_datetime(ts_df["월"])
ts_df = ts_df.sort_values("월")
ts_df_melt = ts_df.melt(id_vars="월", var_name="제품", value_name="매출")
fig_line = px.line(
    ts_df_melt, x="월", y="매출", color="제품",
    markers=True, title="제품별 월 매출 추세"
)
fig_line.update_layout(yaxis_title="매출", xaxis_title="월")
st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# 3) 1분기 제품별 매출 비중 (도넛)
# ==========================================
pie_df = sheets["파이차트"].copy()
# 열 이름 다듬기
pie_df = pie_df.rename(columns={pie_df.columns[0]: "제품", pie_df.columns[1]: "1분기 매출"})
fig_pie = px.pie(
    pie_df, names="제품", values="1분기 매출",
    hole=0.55, title="1분기 제품별 매출 비중"
)
fig_pie.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# 4) 제품 A 매출 vs 비용 (산점도 + 회귀선)
# ==========================================
sc_df = sheets["산점도"].copy()
x = sc_df["제품 A 매출"].to_numpy()
y = sc_df["비용"].to_numpy()

# 단순회귀 계수
m, b = np.polyfit(x, y, 1)
x_line = np.array([x.min(), x.max()])
y_line = m * x_line + b

fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(
    x=x, y=y, mode="markers", name="관측치",
    marker=dict(size=8, opacity=0.8)
))
fig_scatter.add_trace(go.Scatter(
    x=x_line, y=y_line, mode="lines", name=f"회귀선 y = {m:.2f}x + {b:.1f}"
))
fig_scatter.update_layout(title="제품 A 매출 vs 비용 (상관·회귀)", xaxis_title="제품 A 매출", yaxis_title="비용")
st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# 5) 파레토차트 (부서별 매출 + 누적%)
# ==========================================
pareto_df = sheets["파레토차트"].copy()
pareto_df = pareto_df.sort_values("매출", ascending=False).reset_index(drop=True)
pareto_df["누적매출비율(%)"] = pareto_df["매출"].cumsum() / pareto_df["매출"].sum() * 100

fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
fig_pareto.add_trace(
    go.Bar(x=pareto_df["부서"], y=pareto_df["매출"], name="매출"),
    secondary_y=False
)
fig_pareto.add_trace(
    go.Scatter(x=pareto_df["부서"], y=pareto_df["누적매출비율(%)"], name="누적매출비율(%)", mode="lines+markers"),
    secondary_y=True
)
# 80% 기준선
fig_pareto.add_hline(y=80, line_dash="dash", line_color="green", secondary_y=True)

fig_pareto.update_yaxes(title_text="매출", secondary_y=False)
fig_pareto.update_yaxes(title_text="누적매출비율(%)", range=[0, 100], secondary_y=True)
fig_pareto.update_layout(title="부서별 매출 파레토", legend=dict(orientation="h"))
st.plotly_chart(fig_pareto, use_container_width=True)

# ==========================================
# (선택) 데이터 검증 섹션
# ==========================================
with st.expander("🔍 데이터 검증 & 참고(옵션)"):
    # 월별 총매출 == 제품합 비교
    ts_sum = ts_df.set_index("월").sum(axis=1)
    compare = pd.DataFrame({
        "월": bar_df["월"],
        "총 매출(바차트)": bar_df["총 매출"].values,
        "제품합(시계열 합)": ts_sum.reindex(bar_df["월"]).values
    })
    compare["차이"] = compare["총 매출(바차트)"] - compare["제품합(시계열 합)"]
    st.write("월별 총매출 vs 제품합 비교")
    st.dataframe(compare.set_index("월"))

st.caption("데이터 출처: 업로드한 엑셀 파일(그래프_최종)")
