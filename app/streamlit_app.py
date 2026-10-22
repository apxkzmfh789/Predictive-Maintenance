"""
설비 예지보전 대시보드 — Streamlit Community Cloud 배포용

배포 시 주의
  - 경로는 __file__ 기준 (실행 위치가 달라도 동작)
  - 학습은 하지 않고 models/ 결과 파일만 읽음 (Community Cloud 메모리 1GB 제한)
  - 서버에 한글 폰트가 없어 matplotlib 대신 Streamlit 내장 차트 사용

기간
  - 2024년 기준: 분석용 고정 데이터 → models/
  - 최근 14일: GitHub Actions가 매일 수집·재학습 → models/recent/
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "data" / "history"
MODELS = ROOT / "models"

# train.py와 같은 기간 기준 (2024년 기준은 history 파일 이름으로 선택)
BASELINE_START = "2024-01-01"
BASELINE_END = "2024-01-14"
RECENT_DAYS = 14

NUM = [
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "vibration_mms",
    "current_a",
    "humidity_pct",
]

st.set_page_config(page_title="설비 예지보전 대시보드", layout="wide")


# ----------------------------------------------------------------------
# 데이터 로드
# ----------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_history(period: str) -> pd.DataFrame:
    files = sorted(HIST.glob("*.csv"))
    if period == "baseline":
        files = [f for f in files if BASELINE_START <= f.stem <= BASELINE_END]
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    for c in NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["ts"]).drop_duplicates(subset=["machine_id", "ts"])
    if period == "recent" and not df.empty:
        df = df[
            df["ts"] > df["ts"].max() - pd.Timedelta(days=RECENT_DAYS)
        ]  # 마지막 시각 기준 최근 14일
    return df


def model_dir(period: str) -> Path:
    return MODELS if period == "baseline" else MODELS / "recent"


@st.cache_data(ttl=600)
def load_metrics(period: str) -> dict:
    p = model_dir(period) / "metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_data(ttl=600)
def load_preds(period: str) -> pd.DataFrame:
    p = model_dir(period) / "test_predictions.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, parse_dates=["ts"])


@st.cache_data(ttl=600)
def load_importance(period: str) -> pd.DataFrame:
    p = model_dir(period) / "feature_importance.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, index_col=0)


def short(d: str) -> str:
    """'2024-01-01' → '24/01/01'"""
    return d[2:10].replace("-", "/")


def span_label(df: pd.DataFrame) -> str:
    if df.empty:
        return "데이터 없음"
    return f"{df['ts'].min():%y/%m/%d}~{df['ts'].max():%y/%m/%d}"


# ----------------------------------------------------------------------
# 상단: 제목, 기간 선택
# ----------------------------------------------------------------------
st.title("설비 예지보전 대시보드")
st.caption(
    "CNC 밀링 3대 · 1분 단위 센서 · 30분 내 고장 예지 "
    "| 데이터는 물리 기반 시뮬레이터에서 생성 (합성 데이터)"
)

base_raw = load_history("baseline")
recent_raw = load_history("recent")
labels = {
    "baseline": f"2024년 기준 ({short(BASELINE_START)}~{short(BASELINE_END)})",
    "recent": f"최근 {RECENT_DAYS}일 ({span_label(recent_raw)})",
}
period = st.radio(
    "기간", ["baseline", "recent"], format_func=labels.get, horizontal=True
)

raw = base_raw if period == "baseline" else recent_raw
met = load_metrics(period)
preds = load_preds(period)

if raw.empty:
    st.error(
        "선택한 기간의 data/history CSV 없음 → "
        "`python src/collector.py --minutes 1440` 먼저 실행"
    )
    st.stop()

# ----------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["운영 현황", "데이터 품질", "모델 성능", "방법·한계"])

with tab1:
    c = st.columns(4)
    c[0].metric("수집 행수", f"{len(raw):,}")
    c[1].metric("설비 수", raw["machine_id"].nunique())
    c[2].metric("수집 기간(일)", (raw["ts"].max() - raw["ts"].min()).days + 1)
    fr = raw["machine_failure"].mean() * 100 if "machine_failure" in raw else np.nan
    c[3].metric("고장 발생률", f"{fr:.2f}%")

    st.markdown("#### 설비별 센서 추이")
    mid = st.selectbox("설비", sorted(raw["machine_id"].unique()))
    sensor = st.selectbox(
        "센서",
        [
            "torque_nm",
            "vibration_mms",
            "process_temp_k",
            "rot_speed_rpm",
            "current_a",
            "tool_wear_min",
        ],
    )
    sub = raw[raw["machine_id"] == mid].sort_values("ts")
    dates = sorted(sub["ts"].dt.date.unique())
    if len(dates) > 1:
        lo, hi = st.select_slider(
            "표시 기간", options=dates, value=(dates[0], dates[-1])
        )
    else:  # 하루치만 있으면 슬라이더 생략
        lo = hi = dates[0]
    m = sub[(sub["ts"].dt.date >= lo) & (sub["ts"].dt.date <= hi)]
    st.line_chart(m.set_index("ts")[[sensor]], height=260)

    st.markdown("#### 설비별 일간 고장 건수")
    if "machine_failure" in raw:
        daily = (
            raw.assign(d=raw["ts"].dt.date)
            .groupby(["d", "machine_id"])["machine_failure"]
            .sum()
            .unstack()
        )
        st.bar_chart(daily, height=260)

with tab2:
    st.markdown("#### 결측률 (원본 수신 기준)")
    num = [c for c in NUM if c in raw.columns]
    miss = (raw[num].isna().mean() * 100).round(2).rename("결측률(%)")
    st.bar_chart(miss, height=240)

    st.markdown("#### 수집 공백 — 통신이 끊긴 구간")
    g = raw.sort_values(["machine_id", "ts"]).copy()
    g["gap_min"] = g.groupby("machine_id")["ts"].diff().dt.total_seconds() / 60
    gaps = g[g["gap_min"] > 2][["machine_id", "ts", "gap_min"]]
    cc = st.columns(3)
    cc[0].metric("2분 넘는 공백", f"{len(gaps):,}회")
    cc[1].metric("최장 공백", f"{gaps['gap_min'].max():.0f}분" if len(gaps) else "-")
    cc[2].metric(
        "총 결손 시간", f"{gaps['gap_min'].sum() / 60:.1f}시간" if len(gaps) else "-"
    )
    st.dataframe(gaps.sort_values("gap_min", ascending=False).head(15), height=260)

    st.markdown("#### 단위 혼재 흔적")
    if "air_temp_k" in raw:
        n_c = int((raw["air_temp_k"] < 200).sum())
        st.write(
            f"공기온도가 200 K 미만인 행: **{n_c:,}건** "
            f"({n_c / len(raw) * 100:.2f}%) → 섭씨로 기록된 구간"
        )
        st.bar_chart(
            pd.cut(raw["air_temp_k"].dropna(), bins=40)
            .value_counts()
            .sort_index()
            .rename("건수")
            .reset_index(drop=True),
            height=200,
        )

with tab3:
    # 두 기간 비교 (선택한 기간과 무관하게 항상 표시)
    st.markdown("#### 2024년 기준 vs 최근 14일")
    mb, mr = load_metrics("baseline"), load_metrics("recent")
    if mb and mr:
        rows = [
            ("학습 기간", "data_start", "data_end"),
            ("PR-AUC", "pr_auc", None),
            ("기준선(양성률)", "positive_rate_test", None),
            ("ROC-AUC", "roc_auc", None),
            ("임계값", "threshold", None),
            ("정밀도", "precision", None),
            ("재현율", "recall", None),
            ("F1", "f1", None),
        ]

        def cell(mm: dict, k1: str, k2: str | None) -> str:
            if k2:  # 기간 칸
                return f"{short(str(mm.get(k1, '?')))}~{short(str(mm.get(k2, '?')))}"
            return str(mm.get(k1, "-"))

        cmp = pd.DataFrame(
            {
                "항목": [r[0] for r in rows],
                "2024년 기준": [cell(mb, r[1], r[2]) for r in rows],
                f"최근 {RECENT_DAYS}일": [cell(mr, r[1], r[2]) for r in rows],
            }
        )
        st.dataframe(cmp, hide_index=True)
    else:
        st.caption("최근 14일 결과 없음 → GitHub Actions 첫 재학습 후 표시")

    st.divider()

    if not met:
        cmd = "python src/train.py" + ("" if period == "baseline" else " --recent 14")
        st.warning(
            f"{model_dir(period).relative_to(ROOT).as_posix()}/metrics.json 없음 → `{cmd}` 실행 필요"
        )
    else:
        st.markdown(
            f"#### 성능 (시간순 split, 학습 기간 "
            f"{short(str(met.get('data_start', '?')))}~{short(str(met.get('data_end', '?')))})"
        )
        c = st.columns(4)
        c[0].metric("PR-AUC", met.get("pr_auc"))
        c[1].metric("ROC-AUC", met.get("roc_auc"))
        c[2].metric("기준선(양성률)", met.get("positive_rate_test"))
        c[3].metric("적용 임계값", met.get("threshold"))
        c = st.columns(3)
        c[0].metric("정밀도", met.get("precision"))
        c[1].metric("재현율", met.get("recall"))
        c[2].metric("F1", met.get("f1"))

        c05 = met.get("cost_at_0.5", 0)
        cth = met.get("cost_at_threshold", 0)
        cut_pct = (1 - cth / c05) * 100 if c05 else 0.0
        st.info(
            f"임계값은 0.5가 아니라 **{met.get('threshold')}**  \n"
            f"고장 놓침(800만원)이 헛점검(30만원)보다 약 27배 비싸다는 가정에서 총비용이 최소인 지점  \n"
            f"임계값 0.5 대비 총비용 **{cut_pct:.1f}% 감소** "
            f"(비용은 1분 단위 행마다 계산한 값이라 금액보다 감소율로 해석)"
        )

        if not preds.empty:
            st.markdown("#### 예측 확률 분포 — 실제 고장 여부별")
            b = np.linspace(0, 1, 26)
            h0 = np.histogram(preds.loc[preds["y"] == 0, "prob"], bins=b)[0]
            h1 = np.histogram(preds.loc[preds["y"] == 1, "prob"], bins=b)[0]
            st.bar_chart(
                pd.DataFrame(
                    {"정상": h0, "30분내 고장": h1}, index=np.round(b[:-1], 2)
                ),
                height=260,
            )

            st.markdown("#### 상위 K건 점검 시 성능")
            yt = preds.sort_values("prob", ascending=False)["y"].values
            ks = [10, 25, 50, 100, 200, 500]
            rows_k = [
                {
                    "상위 K": k,
                    "잡은 고장": int(yt[:k].sum()),
                    "Precision@K": round(yt[:k].mean(), 3),
                    "무작위 기대": round(k * yt.mean(), 1),
                }
                for k in ks
                if k <= len(yt)
            ]
            st.dataframe(pd.DataFrame(rows_k), hide_index=True)

        imp = load_importance(period)
        if not imp.empty:
            st.markdown("#### 변수 중요도 상위 15")
            st.bar_chart(imp.head(15), height=300)

with tab4:
    st.markdown(f"""
### 무엇을 한 프로젝트인가
CNC 밀링 설비 3대의 1분 단위 센서 데이터를 수집·정제하고
**"앞으로 {met.get("horizon_min", 30)}분 안에 고장이 발생할지"** 예측

### 데이터
- **합성 데이터**: 물리 기반 시뮬레이터(`src/simulator.py`)가 생성,
  고장 규칙은 UCI AI4I 2020 데이터셋의 정의를 따름
- 시뮬레이터가 현장급 오염을 의도적으로 주입:
  통신 끊김, 센서 튐, 타임스탬프 중복·흔들림, 단위 혼재(K↔℃), 센서 드리프트
- 기간 구성
  - **2024년 기준 ({short(BASELINE_START)}~{short(BASELINE_END)})**: 분석용 고정 데이터,
    누가 다시 실행해도 같은 결과 (재현용)
  - **최근 {RECENT_DAYS}일**: GitHub Actions가 매일 수집해 `data/history/`에 쌓고 재학습

### 이 프로젝트에서 신경 쓴 것
1. **정확도를 쓰지 않음**: 불균형 데이터에서 정확도는 모델을 구분하지 못함,
   PR-AUC와 기준선(양성률) 대비로 판단
2. **시간순 split**: 랜덤 split은 인접 시점 정보가 섞여 PR-AUC가 0.98까지 부풀려짐
   (실측 비교는 저장소의 분석 리포트 참조)
3. **임계값을 0.5로 쓰지 않음**: 고장 놓침과 헛점검의 비용이 달라 총비용 최소점에서 결정
4. **이상치를 함부로 지우지 않음**: 설비 고장은 이상치의 모습으로 나타남

### 한계
- **합성 데이터**: 실제 설비 데이터가 아니라 성능 수치를 현장에 그대로 적용할 수 없음,
  이 프로젝트의 결과물은 파이프라인 설계와 검증 방법
- 비용(고장 800만원 / 헛점검 30만원)은 **가정**: 실제 값은 정비팀 확인 필요,
  비용비가 바뀌면 임계값도 바뀜
- 시뮬레이터의 고장 규칙이 결정론적이라 실제 설비보다 예측이 쉬움
  → 실데이터(AI4I·SECOM) 분석을 함께 수행
- 3대·2주 단위 데이터라 계절성·장기 열화는 반영하지 못함
""")
    if met:
        st.json(met)

st.caption("소스: https://github.com/apxkzmfh789/predictive-maintenance")
