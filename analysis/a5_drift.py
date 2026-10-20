"""
A5. 센서 드리프트 — 학습 시점과 운영 시점의 분포 차이

센서 열화·오염·재보정으로 값이 서서히 밀리면 학습 분포와 운영 분포가 달라짐
  (1) 드리프트 탐지
  (2) 드리프트 유무에 따른 모델 성능 비교
  (3) 고정 임계값 경보에 미치는 영향 확인
"""

from _common import ROOT, rule, save
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

import features as F
from simulator import simulate_truth, pollute, POLLUTION
from clean import run_pipeline, estimate_drift, correct_drift

pd.set_option("display.width", 170)
SEED = 42
HORIZON = 30
DAYS = 14


def prep(df, horizon=HORIZON):
    df = F.make_horizon_label(df, horizon=horizon)
    df = F.build(df, windows=(10, 30, 60), shift_one=True)
    feat = [c for c in F.feature_columns(df) if c not in ("y", "machine_failure")]
    d = df.dropna(subset=feat + ["y"]).sort_values("ts").reset_index(drop=True)
    return d, feat


def split_eval(d, feat, frac=0.75, seed=SEED):
    n = len(d)
    cut = int(n * frac)
    X = d[feat].values
    y = d["y"].values.astype(int)
    m = RandomForestClassifier(
        n_estimators=200, random_state=seed, n_jobs=-1, min_samples_leaf=2
    ).fit(X[:cut], y[:cut])
    p = m.predict_proba(X[cut:])[:, 1]
    yt = y[cut:]
    return (
        {
            "ROC-AUC": round(roc_auc_score(yt, p), 4),
            "PR-AUC": round(average_precision_score(yt, p), 4),
            "F1@0.5": round(f1_score(yt, (p >= 0.5).astype(int), zero_division=0), 4),
        },
        m,
        p,
    )


rule("A5-1. 드리프트 규모와 비교용 데이터 준비")
truth = simulate_truth(n_minutes=1440 * DAYS, start="2024-01-01", seed=SEED)
obs = pollute(truth, seed=7)
drift = POLLUTION["drift_per_day"]
std_proc = truth["process_temp_k"].std()
print(f"주입한 드리프트: CNC-02 공정온도 센서 {drift} K/day")
print(f"  → {DAYS}일 누적 {drift * DAYS:.1f} K")
print(f"  참고: 공정온도의 자연 표준편차 {std_proc:.2f} K")
print(f"""
하루 밀림 {drift} K는 자연 표준편차 {std_proc:.2f} K보다 작아 짧은 구간에서는 잡음에 묻힘
  → 긴 구간을 일별로 집계해야 탐지 가능""")

clean_corr, log, rep0 = run_pipeline(
    obs, verbose=False
)  # 파이프라인 1회 실행 (드리프트 보정 포함)

# 보정량을 되돌려 '보정 안 한 버전' 생성 (드리프트 외 조건 동일)
t0 = clean_corr["ts"].min()
days_all = (clean_corr["ts"] - t0).dt.total_seconds() / 86400.0
uncorr = clean_corr.copy()
for mid, s in rep0["drift_applied"].items():
    if s:
        mask = uncorr["machine_id"] == mid
        uncorr.loc[mask, "process_temp_k"] = (
            uncorr.loc[mask, "process_temp_k"] + s * days_all[mask]
        )

rule("A5-2. 탐지 — 일별 집계 + 회귀 기울기 검정")
d = uncorr.dropna(subset=["process_temp_k", "air_temp_k"]).copy()
d["diff"] = d["process_temp_k"] - d["air_temp_k"]
d["day"] = ((d["ts"] - d["ts"].min()).dt.total_seconds() / 86400.0).astype(int)
daily = d.groupby(["machine_id", "day"])["diff"].median().reset_index()
print("[설비별 일별 (공정온도 - 공기온도) 중앙값]")
piv = daily.pivot(index="day", columns="machine_id", values="diff").round(2)
print(piv.to_string())

print("\n[선형회귀 기울기 검정]")
rows = []
for mid, g in daily.groupby("machine_id"):
    lr = stats.linregress(g["day"], g["diff"])
    rows.append(
        {
            "설비": mid,
            "기울기(K/day)": round(lr.slope, 4),
            "표준오차": round(lr.stderr, 4),
            "t": round(lr.slope / lr.stderr, 2),
            "p값": f"{lr.pvalue:.2e}",
            "R²": round(lr.rvalue**2, 3),
        }
    )
print(pd.DataFrame(rows).to_string(index=False))
est = rep0["drift_slopes"]["CNC-02"]
print(f"""
기울기가 유의하게 0이 아닌 설비만 드리프트 의심
  한 대만 변하면 센서 문제, 전 설비가 함께 변하면 공정 변화로 판단

라인 중앙값 기준 잔차 기울기 추정값 (CNC-02): {est:.4f} K/day
  참값 {drift} K/day 대비 오차 {abs(est - drift) / drift * 100:.1f}%""")

print("\n[분포 이동 검정 — 전반부 7일 vs 후반부 7일, KS 검정]")
ks_rows = []
for mid, g in uncorr.groupby("machine_id"):
    g = g.dropna(subset=["process_temp_k"])
    half = g["ts"].min() + pd.Timedelta(days=DAYS // 2)
    a = g.loc[g["ts"] < half, "process_temp_k"]
    b = g.loc[g["ts"] >= half, "process_temp_k"]
    ks = stats.ks_2samp(a, b)
    ks_rows.append(
        {
            "설비": mid,
            "전반부 평균": round(a.mean(), 2),
            "후반부 평균": round(b.mean(), 2),
            "차이": round(b.mean() - a.mean(), 2),
            "KS통계량": round(ks.statistic, 4),
            "p값": f"{ks.pvalue:.2e}",
        }
    )
print(pd.DataFrame(ks_rows).to_string(index=False))
print("""
표본이 크면 KS 검정은 작은 차이도 p값을 매우 작게 만듦
  → p값보다 평균 차이(효과 크기)로 실질적 이동 여부 판단""")

rule("A5-3. 드리프트가 모델 성능에 미치는 영향")
d_un, feat = prep(uncorr)
d_co, feat2 = prep(clean_corr)
r_un, _, _ = split_eval(d_un, feat)
r_co, _, _ = split_eval(d_co, feat2)
print(
    pd.DataFrame(
        [dict(데이터="드리프트 방치", **r_un), dict(데이터="드리프트 보정", **r_co)]
    ).to_string(index=False)
)

# 드리프트가 있는 CNC-02만 별도 평가
print("\n[CNC-02 단독]")
sub_un = d_un[d_un["machine_id"] == "CNC-02"].reset_index(drop=True)
sub_co = d_co[d_co["machine_id"] == "CNC-02"].reset_index(drop=True)
r2_un, _, _ = split_eval(sub_un, feat)
r2_co, _, _ = split_eval(sub_co, feat2)
print(
    pd.DataFrame(
        [dict(데이터="드리프트 방치", **r2_un), dict(데이터="드리프트 보정", **r2_co)]
    ).to_string(index=False)
)
gain = (r2_co["PR-AUC"] - r2_un["PR-AUC"]) / max(r2_un["PR-AUC"], 1e-9) * 100
print(f"""
보정 전 → 후 PR-AUC
  전체    {r_un["PR-AUC"]:.4f} → {r_co["PR-AUC"]:.4f}
  CNC-02  {r2_un["PR-AUC"]:.4f} → {r2_co["PR-AUC"]:.4f} ({gain:+.1f}%)

해석
  1) 트리 모델은 시간에 따라 단조 증가하는 편향을 다른 피처와 조합해 흡수 가능
  2) 보정은 추정 기울기({est:.4f})를 빼는 작업이라 추정 오차만큼 새 잡음이 추가됨
  차이가 작으면 seed에 따라 부호가 바뀔 수 있어 보정 효과를 단정하기 어려움

드리프트 보정의 주된 목적은 모델보다 고정 임계값 경보 규칙 보호 (A5-4)""")

rule("A5-4. 고정 임계값 경보와 드리프트")
th = 315.0
al = []
for name, frame in [("보정 안 함", uncorr), ("보정 함", clean_corr)]:
    g = frame.dropna(subset=["process_temp_k"]).copy()
    g["week"] = np.where(
        (g["ts"] - g["ts"].min()).dt.days < DAYS // 2, "1주차", "2주차"
    )
    for mid in ["CNC-01", "CNC-02", "CNC-03"]:
        s = g[g["machine_id"] == mid]
        r = s.groupby("week")["process_temp_k"].apply(lambda x: (x > th).mean() * 100)
        al.append(
            {
                "데이터": name,
                "설비": mid,
                "1주차 경보율%": round(r.get("1주차", np.nan), 2),
                "2주차 경보율%": round(r.get("2주차", np.nan), 2),
            }
        )
alarm = pd.DataFrame(al)
print(f"[공정온도 {th} K 초과 경보 발생률]")
print(alarm.to_string(index=False))
c2u = alarm[(alarm["데이터"] == "보정 안 함") & (alarm["설비"] == "CNC-02")].iloc[0]
c2c = alarm[(alarm["데이터"] == "보정 함") & (alarm["설비"] == "CNC-02")].iloc[0]
print(f"""
CNC-02 경보율 (1주차 → 2주차)
  보정 안 함: {c2u["1주차 경보율%"]}% → {c2u["2주차 경보율%"]}%
  보정 함   : {c2c["1주차 경보율%"]}% → {c2c["2주차 경보율%"]}%

설비 상태와 무관하게 센서 밀림만으로 발생하는 경보 = 가짜 경보
  가짜 경보가 반복되면 경보 무시로 이어져 실제 고장 대응이 늦어질 위험""")

rule("A5-5. 그림")
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
for mid, g in daily.groupby("machine_id"):
    axes[0].plot(g["day"], g["diff"], marker="o", ms=4, label=mid)
    lr = stats.linregress(g["day"], g["diff"])
    axes[0].plot(g["day"], lr.intercept + lr.slope * g["day"], ls="--", lw=1, alpha=0.7)
axes[0].set_xlabel("경과 일")
axes[0].set_ylabel("공정온도 - 공기온도 (K)")
axes[0].set_title("설비별 일별 중앙값과 회귀선")
axes[0].legend(fontsize=8)

for mid, color in [("CNC-02", "#c53030"), ("CNC-01", "#2b6cb0")]:
    g = uncorr[uncorr["machine_id"] == mid].dropna(subset=["process_temp_k"])
    half = g["ts"].min() + pd.Timedelta(days=DAYS // 2)
    axes[1].hist(
        g.loc[g["ts"] < half, "process_temp_k"],
        bins=60,
        alpha=0.5,
        density=True,
        color=color,
        label=f"{mid} 1주차",
    )
    axes[1].hist(
        g.loc[g["ts"] >= half, "process_temp_k"],
        bins=60,
        alpha=0.5,
        density=True,
        histtype="step",
        lw=1.8,
        color=color,
        label=f"{mid} 2주차",
    )
axes[1].set_title("분포 이동 (보정 전)")
axes[1].set_xlabel("공정온도 (K)")
axes[1].legend(fontsize=7)

pv = alarm[alarm["데이터"] == "보정 안 함"].set_index("설비")[
    ["1주차 경보율%", "2주차 경보율%"]
]
pv.plot(kind="bar", ax=axes[2], rot=0, color=["#a0aec0", "#c53030"])
axes[2].set_title(f"고정 임계값({th}K) 경보율 — 보정 전")
axes[2].set_ylabel("%")
axes[2].legend(fontsize=8)
fig.tight_layout()
save(fig, "drift")
