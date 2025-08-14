import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="그래프_최종 대시보드", page_icon="📊", layout="wide")

# =========================================
# 내장 데이터 (파일 업로드 없이 사용)
# =========================================
DATA = {
    "bar": {
        "labels": ["2023-01","2023-02","2023-03","2023-04","2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"],
        "values": [885,918,887,1148,1436,1131,1217,1094,1188,1079,1343,1641],
    },
    "ts": {
        "labels": ["2023-01","2023-02","2023-03","2023-04","2023-05","2023-06","2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"],
        "series": {
            "제품 A 매출":[272,147,217,292,423,351,295,459,109,311,377,342],
            "제품 B 매출":[86,137,120,266,138,190,108,243,280,89,137,224],
            "제품 C 매출":[158,407,235,95,403,142,335,185,313,267,405,408],
            "제품 D 매출":[222,97,167,242,373,301,245,59,261,327,292,342],
            "제품 E 매출":[147,130,148,253,99,147,234,148,225,85,132,325],
        },
    },
    "pie": {
        "labels": ["제품 A","제품 B","제품 C","제품 D","제품 E"],
        "values": [3595,2018,3353,2928,2073],
    },
    "scatter": {
        "x": [272,147,217,292,423,351,295,459,109,311,377,342],
        "y": [149,227,293,335,197,197,338,315,235,177,82,81],
    },
    "pareto": {
        "labels": ["기획부","마케팅부","영업부","인사부","개발부"],
        "sales": [954,923,559,477,209],
        "cum": [30.56,60.12,78.03,93.31,100.00],
    },
}

# =========================================
# 헤더 / KPI
# =========================================
st.title("그래프_최종 대시보드")
st.caption("월별 총매출 · 제품별 추세 · 1분기 비중 · 매출 vs 비용 · 파레토")

# KPI 카드 (연간 합계, 최고/최저 월)
bar_df = pd.DataFrame({"월": DATA["bar"]["labels"], "총 매출": DATA["bar"]["values"]})
total_sales = int(bar_df["총 매출"].sum())
max_row = bar_df.iloc[bar_df["총 매출"].idxmax()]
min_row = bar_df.iloc[bar_df["총 매출"].idxmin()]

c1, c2, c3 = st.columns(3)
c1.metric("연간 총매출 합계", f"{total_sales:,}")
c2.metric("최고 매출 월", max_row["월"], f"{int(max_row['총 매출']):,}")
c3.metric("최저 매출 월", min_row["월"], f"{int(min_row['총 매출']):,}")

st.divider()

# =========================================
# 1) 월별 총매출 (막대)
# =========================================
fig_bar = px.bar(
    bar_df, x="월", y="총 매출", text="총 매출", title="월별 총 매출"
)
fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
fig_bar.update_layout(yaxis_title="매출", xaxis_title="월", uniformtext_minsize=8, uniformtext_mode="show")
st.plotly_chart(fig_bar, use_container_width=True)

# =========================================
# 2) 제품별 월 매출 추세 (멀티 라인)
# =========================================
ts_labels = DATA["ts"]["labels"]
ts_records = []
for name, arr in DATA["ts"]["series"].items():
    ts_records.extend([{"월": ts_labels[i], "제품": name, "매출": arr[i]} for i in range(len(ts_labels))])
ts_df = pd.DataFrame(ts_records)

fig_line = px.line(
    ts_df, x="월", y="매출", color="제품", markers=True, title="제품별 월 매출 추세"
)
fig_line.update_layout(yaxis_title="매출", xaxis_title="월", legend=dict(orientation="h"))
st.plotly_chart(fig_line, use_container_width=True)

# =========================================
# 3) 1분기 제품별 매출 비중 (도넛)
# =========================================
pie_df = pd.DataFrame({"제품": DATA["pie"]["labels"], "1분기 매출": DATA["pie"]["values"]})
fig_pie = px.pie(
    pie_df, names="제품", values="1분기 매출", hole=0.55, title="1분기 제품별 매출 비중"
)
fig_pie.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_pie, use_container_width=True)

# =========================================
# 4) 제품 A 매출 vs 비용 (산점도 + 회귀선)
# =========================================
x = np.array(DATA["scatter"]["x"])
y = np.array(DATA["scatter"]["y"])
m, b = np.polyfit(x, y, 1)
x_line = np.array([x.min(), x.max()])
y_line = m * x_line + b

fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(x=x, y=y, mode="markers", name="관측치", marker=dict(size=8, opacity=0.85)))
fig_scatter.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", name=f"회귀선 y = {m:.2f}x + {b:.1f}"))
fig_scatter.update_layout(title="제품 A 매출 vs 비용 (상관·회귀)", xaxis_title="제품 A 매출", yaxis_title="비용")
st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================
# 5) 파레토 (부서별 매출 + 누적%)
# =========================================
pareto_df = pd.DataFrame({
    "부서": DATA["pareto"]["labels"],
    "매출": DATA["pareto"]["sales"],
    "누적매출비율(%)": DATA["pareto"]["cum"],
})

fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
fig_pareto.add_trace(go.Bar(x=pareto_df["부서"], y=pareto_df["매출"], name="매출"), secondary_y=False)
fig_pareto.add_trace(go.Scatter(x=pareto_df["부서"], y=pareto_df["누적매출비율(%)"], mode="lines+markers", name="누적매출비율(%)"), secondary_y=True)
fig_pareto.add_hline(y=80, line_dash="dash", line_color="green", secondary_y=True)
fig_pareto.update_yaxes(title_text="매출", secondary_y=False)
fig_pareto.update_yaxes(title_text="누적매출비율(%)", range=[0,100], secondary_y=True)
fig_pareto.update_layout(title="부서별 매출 파레토", legend=dict(orientation="h"))
st.plotly_chart(fig_pareto, use_container_width=True)

# =========================================
# (옵션) 검증 섹션: 시계열 합 == 총매출 비교
# =========================================
with st.expander("🔍 데이터 검증 (옵션)"):
    # 시계열 합 만들기
    ts_wide = pd.DataFrame({"월": ts_labels})
    for name, arr in DATA["ts"]["series"].items():
        ts_wide[name] = arr
    ts_wide["제품합"] = ts_wide.drop(columns=["월"]).sum(axis=1)

    compare = pd.merge(
        bar_df.rename(columns={"총 매출": "총매출(바차트)"}),
        ts_wide[["월","제품합"]],
        on="월",
        how="left"
    )
    compare["차이"] = compare["총매출(바차트)"] - compare["제품합"]
    st.dataframe(compare.set_index("월"))
    st.caption("검증: 월별 총매출 = Σ(제품 월매출) 인지 확인")
