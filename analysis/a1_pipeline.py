"""
A1. 오염 주입 → 정제 → 참값 대조 검증

참값과 오염 주입 기록(masks)으로 정제 결과를 수치로 검증.
"""

from _common import ROOT, rule, save
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulator import simulate_truth, pollute, MACHINES, POLLUTION
from clean import (
    run_pipeline,
    hampel_flag,
    detect_and_fix_temp_unit,
    detect_vibration_unit,
    PHYS_RANGE,
)

pd.set_option("display.width", 160)
DAYS = 14
SEED = 42

rule("A1-1. 참값 생성 — 물리 기반 시뮬레이터")
truth = simulate_truth(n_minutes=1440 * DAYS, start="2024-01-01", seed=SEED)
print("설비 수     :", truth["machine_id"].nunique())
print("기간        :", truth["ts"].min(), "~", truth["ts"].max())
print("행 수       :", f"{len(truth):,}")
print("\n[고장 모드별 건수]")
modes = truth[["twf", "hdf", "pwf", "osf", "rnf", "machine_failure"]].sum()
tbl = pd.DataFrame({"건수": modes, "비율(%)": (modes / len(truth) * 100).round(3)})
print(tbl.to_string())
print(
    f"\n전체 고장률 {truth['machine_failure'].mean() * 100:.3f}% "
    f"/ 정상 {(1 - truth['machine_failure'].mean()) * 100:.3f}%"
)

print("\n[센서 요약]")
cols = [
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "vibration_mms",
    "current_a",
    "power_w",
]
print(
    truth[cols]
    .describe()
    .loc[["mean", "std", "min", "50%", "max"]]
    .round(2)
    .to_string()
)

rule("A1-2. 오염 주입 — 현장에서 받는 데이터로 변환")
obs, masks = pollute(truth, seed=7, return_masks=True)  # masks = 오염 주입 위치 기록
print("참값 행수   :", f"{len(truth):,}")
print("관측 행수   :", f"{len(obs):,}", f"({len(obs) - len(truth):+,})")
print("\n[관측 데이터 첫 3행 (정렬·단위 미정리 상태)]")
print(obs.head(3).to_string())

print("\n[결측률 %]")
sens = [
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "vibration_mms",
    "current_a",
    "humidity_pct",
]
print((obs[sens].isna().mean() * 100).round(2).to_string())

print("\n[단위 혼재 흔적 — 온도가 300 근처와 30 근처로 두 덩어리]")
print(obs["air_temp_k"].describe().round(2).to_string())
print("200 K 미만 비율: %.2f%%" % ((obs["air_temp_k"] < 200).mean() * 100))

print("\n[중복 — (machine_id, ts) 기준]")
d = obs.duplicated(subset=["machine_id", "ts"]).sum()
print(f"중복 행: {d:,}건")

print("\n[오염 주입 기록 (유형별 건수)]")
inj = pd.DataFrame({"건수": masks.sum(), "비율(%)": (masks.mean() * 100).round(3)})
print(inj.to_string())

rule("A1-3. 정제 파이프라인 실행")
clean, log, rep = run_pipeline(obs)

print("\n[단위 보정 건수]", rep["temp_unit"], "| 진동:", rep["vib_unit"])
print("\n[물리범위 위반 → NaN 처리 건수]")
print(pd.Series(rep["range"]).to_string())
print("\n[짧은 결측 보간 건수]")
print(pd.Series(rep["filled"]).to_string())
print("\n[드리프트 추정 기울기 (K/day)]")
print(pd.Series(rep["drift_slopes"]).round(4).to_string())
print(f"참값: CNC-02 {POLLUTION['drift_per_day']} K/day")

rule("A1-4. 참값 대조 — 정제 후 복원 정확도")
# 정제 데이터가 분 단위로 스냅돼 있어 참값도 스냅 후 (machine_id, ts)로 조인
t = truth.copy()
t["ts"] = t["ts"].dt.round("min")
m = clean.merge(
    t[["machine_id", "ts"] + sens],
    on=["machine_id", "ts"],
    how="inner",
    suffixes=("_c", "_t"),
)
print(
    "대조 가능 행:",
    f"{len(m):,} / 참값 {len(truth):,} ({len(m) / len(truth) * 100:.1f}%)",
)
print(
    f"행 자체가 살아있는 비율 : {m['is_gap'].eq(False).mean() * 100:.2f}% "
    f"(나머지는 통신 끊김 구간)"
)

rows = []
for c in sens:
    a, b = m[f"{c}_c"], m[f"{c}_t"]
    ok = a.notna() & b.notna()
    err = (a[ok] - b[ok]).abs()
    rows.append(
        {
            "센서": c,
            "값보유율%": round(ok.mean() * 100, 2),
            "MAE": round(err.mean(), 4),
            "p95_err": round(err.quantile(0.95), 4),
            "max_err": round(err.max(), 3),
            "참값std": round(b.std(), 3),
        }
    )
comp = pd.DataFrame(rows)
comp["MAE/std"] = (comp["MAE"] / comp["참값std"]).round(4)
print(comp.to_string(index=False))
print("\n기준: MAE/std < 0.05 이면 복원 성공으로 판단")

# 정제 안 했을 때와 비교
raw_obs = obs.copy()
raw_obs["ts"] = pd.to_datetime(raw_obs["ts"]).dt.round("min")
raw_obs = raw_obs.drop_duplicates(subset=["machine_id", "ts"])
m0 = raw_obs.merge(
    t[["machine_id", "ts"] + sens],
    on=["machine_id", "ts"],
    how="inner",
    suffixes=("_c", "_t"),
)
print("\n[정제 전 vs 정제 후 MAE 비교]")
cmp_rows = []
for c in sens:
    ok0 = m0[f"{c}_c"].notna() & m0[f"{c}_t"].notna()
    e0 = (m0.loc[ok0, f"{c}_c"] - m0.loc[ok0, f"{c}_t"]).abs().mean()
    ok1 = m[f"{c}_c"].notna() & m[f"{c}_t"].notna()
    e1 = (m.loc[ok1, f"{c}_c"] - m.loc[ok1, f"{c}_t"]).abs().mean()
    cmp_rows.append(
        {
            "센서": c,
            "정제전MAE": round(e0, 3),
            "정제후MAE": round(e1, 4),
            "개선배수": round(e0 / e1, 1) if e1 > 0 else np.inf,
        }
    )
print(pd.DataFrame(cmp_rows).to_string(index=False))

rule("A1-5. 탐지 규칙 채점 — 오염 주입 기록과 대조")
# masks는 obs와 행 순서가 같으므로, 규칙을 obs에 직접 적용해 masks로 채점
o2 = obs.copy()
for cc in sens:
    o2[cc] = pd.to_numeric(o2[cc], errors="coerce")


def score(pred, gt, name):
    pred = np.asarray(pred, dtype=bool)
    gt = np.asarray(gt, dtype=bool)
    tp = int((pred & gt).sum())
    fp = int((pred & ~gt).sum())
    fn = int((~pred & gt).sum())
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    return {
        "규칙": name,
        "실제": int(gt.sum()),
        "탐지": int(pred.sum()),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "정밀도": round(prec, 3),
        "재현율": round(rec, 3),
    }


res = []
# (1) 온도 단위: "200 K 미만이면 섭씨" — 물리적 근거가 있는 규칙
res.append(score(o2["air_temp_k"] < 200, masks["unit_temp"], "온도단위(air<200K)"))
res.append(score(o2["process_temp_k"] < 200, masks["unit_temp"], "온도단위(proc<200K)"))
# (2) 진동 단위: "설비 중앙값의 4배 초과" — 통계적 기준(근거가 약함)
med = o2.groupby("machine_id")["vibration_mms"].transform("median")
res.append(
    score(o2["vibration_mms"] > med * 4, masks["unit_vib"], "진동단위(중앙값×4)")
)
print(pd.DataFrame(res).to_string(index=False))

print("\n[임계값 민감도 확인]")
sens_rows = []
for th in [150, 180, 200, 250, 273]:
    sens_rows.append(score(o2["air_temp_k"] < th, masks["unit_temp"], f"온도 <{th}K"))
for r in [1.2, 1.5, 2.0, 4.0, 6.0]:
    sens_rows.append(
        score(o2["vibration_mms"] > med * r, masks["unit_vib"], f"진동 ×{r}")
    )
print(pd.DataFrame(sens_rows).to_string(index=False))
print("""
진동 단위 규칙: 임계값 ×1.5~×6 구간에서 결과 동일.
  정상 진동(약 1.75~4.7 mm/s)과 9.81배 값(약 17~46 mm/s) 사이가 비어 있기 때문.
  단, 이 빈 구간은 데이터의 성질이지 물리 법칙이 아님.
  실제 고장으로 진동이 커지면 오판할 수 있어 아래에서 고장을 심어 확인.""")

# 실제 고장을 인위적으로 심고 단위 규칙의 반응 확인
o4 = o2.copy()
fault_idx = o4.index[(o4["machine_id"] == "CNC-03") & o4["vibration_mms"].notna()][:400]
o4.loc[fault_idx, "vibration_mms"] = (
    o4.loc[fault_idx, "vibration_mms"] * 5.0
)  # 베어링 이상
med4 = o4.groupby("machine_id")["vibration_mms"].transform("median")
rule_hit = o4["vibration_mms"] > med4 * 4
n_fault_killed = int(rule_hit.loc[fault_idx].sum())
print(f"  심은 '진짜 베어링 이상' 행    : {len(fault_idx)}건 (진동 5배)")
print(
    f"  단위 규칙이 잡아서 9.81로 나눈 행: {n_fault_killed}건 "
    f"({n_fault_killed / len(fault_idx) * 100:.1f}%)"
)
print(f"  → 단위 규칙에 의해 고장 신호 {n_fault_killed}건이 보정됨(소실)")
print("""
결론: 통계적 단위 판정은 고장이 드문 데이터에서만 유효하며, 실제 고장을 단위 오류로 오판할 수 있음.
  → 단위는 태그 단위표(메타데이터)로 판정하는 것이 원칙. 없으면 보정한 행을 로그로 남김.""")

print("\n[스파이크 탐지 — 물리범위 검사 + Hampel 필터]")
sp = []
o3, _ = detect_and_fix_temp_unit(o2)
o3, _ = detect_vibration_unit(o3)
o3 = o3.copy()
o3["ts_dt"] = pd.to_datetime(o3["ts"])
order = o3.sort_values(["machine_id", "ts_dt"]).index
for c in sens:
    lo, hi = PHYS_RANGE[c]
    out_of_range = o3[c].notna() & ~o3[c].between(lo, hi)
    s = o3.loc[order, c]
    ham = hampel_flag(s, 11, 5.0).reindex(o3.index).fillna(False)
    sp.append(score(out_of_range, masks[f"spike_{c}"], f"{c} 범위검사"))
    sp.append(score(out_of_range | ham, masks[f"spike_{c}"], f"{c} 범위+Hampel"))
print(pd.DataFrame(sp).to_string(index=False))
print("\n재현율 < 100%: 0으로 튄 스파이크 중 일부는 물리범위 안이라 구분 불가")
print(
    "정밀도 낮음: Hampel은 설비의 실제 급변도 함께 탐지 (오작동 vs 실제 이상 구분 문제)"
)

rule("A1-6. 그림 저장")
fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
one = truth[truth["machine_id"] == "CNC-01"].head(1440 * 2)
axes[0].plot(one["ts"], one["tool_wear_min"], lw=0.8, color="#2b6cb0")
axes[0].set_ylabel("공구 마모(분)")
axes[0].set_title("CNC-01 이틀치 참값 — 마모 누적과 교체, 그리고 고장 시점")
axes[1].plot(one["ts"], one["torque_nm"], lw=0.6, color="#276749")
axes[1].set_ylabel("토크(Nm)")
axes[2].plot(one["ts"], one["vibration_mms"], lw=0.6, color="#975a16")
axes[2].set_ylabel("진동(mm/s)")
f = one[one["machine_failure"] == 1]
for ax in axes:
    for x in f["ts"]:
        ax.axvline(x, color="crimson", alpha=0.25, lw=0.8)
axes[2].set_xlabel("시각")
fig.tight_layout()
save(fig, "sim_truth")

fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
obs_num = pd.to_numeric(obs["air_temp_k"], errors="coerce")
n_hi = int((obs_num > 350).sum())
axes[0].hist(obs_num.dropna(), bins=np.linspace(-20, 350, 120), color="#c53030")
axes[0].set_xlim(-20, 350)  # 스파이크를 축에서 제외해야 두 분포가 보임
axes[0].set_title(
    f"관측: 공기온도 (단위 혼재)\n※ 350K 초과 스파이크 {n_hi}건은 축에서 제외",
    fontsize=10,
)
axes[0].set_xlabel("air_temp_k")
axes[0].annotate(
    "섭씨(℃)로\n들어온 구간",
    xy=(26, 2800),
    xytext=(0.22, 0.42),
    textcoords="axes fraction",
    fontsize=9,
    ha="center",
    arrowprops=dict(arrowstyle="->", lw=1),
)
axes[0].annotate(
    "정상(켈빈)",
    xy=(299, 12000),
    xytext=(0.55, 0.72),
    textcoords="axes fraction",
    fontsize=9,
    ha="center",
    arrowprops=dict(arrowstyle="->", lw=1),
)
axes[1].hist(clean["air_temp_k"].dropna(), bins=80, color="#2b6cb0")
axes[1].set_title("정제 후: 공기온도")
axes[1].set_xlabel("air_temp_k")
dd = rep["drift_daily"]
for mid, g in dd.groupby("machine_id"):
    axes[2].plot(g["d"], g["resid"], marker="o", ms=3, label=mid)
axes[2].axhline(0, color="gray", lw=0.8)
axes[2].set_title("드리프트: 일별 잔차(설비-라인중앙값)")
axes[2].set_xlabel("경과 일")
axes[2].set_ylabel("잔차(K)")
axes[2].legend(fontsize=8)
fig.tight_layout()
save(fig, "clean_effect")

rule("A1-7. 정제 결과 저장")
out = ROOT / "data" / "clean_sim.parquet"
try:
    clean.to_parquet(out, index=False)
    print("saved:", out.name)
except Exception as e:
    out = ROOT / "data" / "clean_sim.csv"
    clean.to_csv(out, index=False)
    print(f"parquet 불가({type(e).__name__}) → CSV로 저장:", out.name)
truth.to_csv(ROOT / "data" / "truth_sim.csv", index=False)
print("saved: truth_sim.csv")
print("\n행수 회계:")
print(
    f"  참값 {len(truth):,} → 관측 {len(obs):,} → 중복제거 {log.frame().iloc[3]['행수']:,}"
    f" → 재색인 {len(clean):,}"
)
