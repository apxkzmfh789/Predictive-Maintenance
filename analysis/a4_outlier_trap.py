"""
A4. 센서 오작동 vs 진짜 이상 — 이상치 제거의 위험

설비 고장은 이상치 형태로 나타날 수 있어 무조건 제거하면 고장 신호도 함께 사라짐
AI4I(실데이터)로 삭제 영향을 측정하고, 시뮬레이터(참값 보유)로 오작동과 고장의 구분 가능 여부 확인
"""

from _common import ROOT, RAW, rule, save
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

pd.set_option("display.width", 170)
SEED = 42

rule("A4-1. AI4I에 IQR 이상치 기준 적용")
df = pd.read_csv(RAW / "ai4i" / "ai4i2020.csv").rename(
    columns={
        "Air temperature [K]": "air_temp_k",
        "Process temperature [K]": "process_temp_k",
        "Rotational speed [rpm]": "rot_speed_rpm",
        "Torque [Nm]": "torque_nm",
        "Tool wear [min]": "tool_wear_min",
        "Machine failure": "failure",
        "Type": "type",
    }
)
NUM = ["air_temp_k", "process_temp_k", "rot_speed_rpm", "torque_nm", "tool_wear_min"]
MODES = ["TWF", "HDF", "PWF", "OSF", "RNF"]


def iqr_outlier(s: pd.Series, k: float = 1.5) -> pd.Series:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return ~s.between(q1 - k * iqr, q3 + k * iqr)


flags = pd.DataFrame({c: iqr_outlier(df[c]) for c in NUM})
rows = []
for c in NUM:
    f = flags[c]
    rows.append(
        {
            "센서": c,
            "이상치": int(f.sum()),
            "이상치비율%": round(f.mean() * 100, 2),
            "이상치중 고장%": round(df.loc[f, "failure"].mean() * 100, 2)
            if f.sum()
            else 0.0,
            "정상치중 고장%": round(df.loc[~f, "failure"].mean() * 100, 2),
        }
    )
print(pd.DataFrame(rows).to_string(index=False))
base_rate = df["failure"].mean() * 100
print(f"\n전체 고장률 {base_rate:.2f}%")
print("""
IQR 이상치 행의 고장률이 전체 고장률보다 높으면 이상치가 곧 고장 신호
  → 이상치 삭제 시 학습에 필요한 고장 사례가 함께 사라짐""")

any_out = flags.any(axis=1)
print(
    f"\n한 개 이상 센서에서 이상치인 행 : {any_out.sum():,}건 ({any_out.mean() * 100:.2f}%)"
)
print(f"  그중 고장 행                  : {int(df.loc[any_out, 'failure'].sum())}건")
print(
    f"  전체 고장 {int(df['failure'].sum())}건 중 "
    f"{df.loc[any_out, 'failure'].sum() / df['failure'].sum() * 100:.1f}%가 이상치 행에 포함"
)

print("\n[고장 모드별 — 이상치 삭제 시 함께 사라지는 비율]")
mr = []
for m in MODES:
    sub = df[df[m] == 1]
    mr.append(
        {
            "모드": m,
            "건수": len(sub),
            "이상치로 걸림": int(any_out[sub.index].sum()),
            "삭제될 비율%": round(any_out[sub.index].mean() * 100, 1),
        }
    )
print(pd.DataFrame(mr).to_string(index=False))

rule("A4-2. 이상치 삭제 후 학습 비교 (test는 원본 유지)")
X = pd.get_dummies(df[NUM + ["type"]], columns=["type"], drop_first=True)
X["temp_diff_k"] = df["process_temp_k"] - df["air_temp_k"]
X["power_w"] = df["torque_nm"] * df["rot_speed_rpm"] * 2 * np.pi / 60
X["wear_torque"] = df["tool_wear_min"] * df["torque_nm"]
y = df["failure"]
Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.25, random_state=SEED, stratify=y
)


def fit_eval(Xa, ya, Xb, yb, name):
    m = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)
    m.fit(Xa, ya)
    p = m.predict_proba(Xb)[:, 1]
    pr = (p >= 0.5).astype(int)
    return {
        "처리": name,
        "train행": len(Xa),
        "train고장": int(ya.sum()),
        "정밀도": round(precision_score(yb, pr, zero_division=0), 4),
        "재현율": round(recall_score(yb, pr, zero_division=0), 4),
        "F1": round(f1_score(yb, pr, zero_division=0), 4),
        "PR-AUC": round(average_precision_score(yb, p), 4),
    }, p


res = []
r0, p0 = fit_eval(Xtr, ytr, Xte, yte, "① 아무것도 안 지움")
res.append(r0)

keep = ~any_out.loc[Xtr.index]
r1, p1 = fit_eval(Xtr[keep], ytr[keep], Xte, yte, "② IQR 이상치 행 삭제")
res.append(r1)

# ③ 삭제하지 않고 이상치 여부를 피처로 추가
Xtr2 = Xtr.copy()
Xte2 = Xte.copy()
for c in NUM:
    Xtr2[f"out_{c}"] = flags[c].loc[Xtr.index].astype(int)
    Xte2[f"out_{c}"] = flags[c].loc[Xte.index].astype(int)
r2, p2 = fit_eval(Xtr2, ytr, Xte2, yte, "③ 지우지 않고 플래그로 추가")
res.append(r2)

print(pd.DataFrame(res).to_string(index=False))
print(f"""
② 이상치 삭제: train 고장 {int(ytr.sum())}건 → {r1["train고장"]}건, 재현율 {r0["재현율"]:.4f} → {r1["재현율"]:.4f}
③ 플래그 추가: 재현율 {r2["재현율"]:.4f}, 데이터를 버리지 않고 이상치 여부를 피처로 제공""")

print("\n[② 모델의 혼동행렬]")
print(
    pd.DataFrame(
        confusion_matrix(yte, (p1 >= 0.5).astype(int)),
        index=["실제정상", "실제고장"],
        columns=["예측정상", "예측고장"],
    ).to_string()
)

rule("A4-3. 시뮬레이터 검증 — 오작동과 진짜 이상의 구분 가능 여부")
import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from simulator import simulate_truth, pollute  # noqa: E402
from clean import hampel_flag  # noqa: E402

truth = simulate_truth(n_minutes=1440 * 14, start="2024-01-01", seed=SEED)
obs, masks = pollute(truth, seed=7, return_masks=True)
o = obs.copy()
for c in ["torque_nm", "vibration_mms", "rot_speed_rpm", "process_temp_k"]:
    o[c] = pd.to_numeric(o[c], errors="coerce")
o["ts"] = pd.to_datetime(o["ts"])
o = o.sort_values(["machine_id", "ts"])
masks = masks.loc[o.index]

print("튀는 값의 두 종류")
print(
    f"  (A) 센서 오작동 = 주입한 스파이크 : {int(masks['spike_torque_nm'].sum())}건 (토크 기준)"
)
print(f"  (B) 진짜 설비 이상 = 고장 라벨    : {int(o['machine_failure'].sum())}건")

# 토크 IQR 이상치 판정
out_iqr = iqr_outlier(o["torque_nm"]).fillna(False).astype(bool)
kind = pd.Series(
    np.where(
        masks["spike_torque_nm"],
        "센서오작동",
        np.where(o["machine_failure"] == 1, "진짜고장", "정상"),
    ),
    index=o.index,
    name="실제정체",
)
tab = pd.crosstab(out_iqr.rename("IQR이상치"), kind)
print("\n[토크 IQR 이상치 판정 vs 실제 정체]")
print(tab.to_string())
hit_spike = int(tab.loc[True].get("센서오작동", 0)) if True in tab.index else 0
hit_fail = int(tab.loc[True].get("진짜고장", 0)) if True in tab.index else 0
miss_fail = int(tab.loc[False].get("진짜고장", 0)) if False in tab.index else 0
tot_flag = int(out_iqr.sum())
ai4i_tq = df.loc[flags["torque_nm"], "failure"].mean() * 100
print(f"""
AI4I와 시뮬레이터에서 IQR 결과가 반대
  - AI4I      : 토크 IQR 이상치 중 진짜 고장 {ai4i_tq:.1f}%
  - 시뮬레이터: IQR 이상치 {tot_flag}건 중 센서오작동 {hit_spike}건({hit_spike / tot_flag * 100:.1f}%),
                진짜 고장 {hit_fail}건({hit_fail / tot_flag * 100:.1f}%)
                고장 {miss_fail}건은 IQR 경계 안쪽에 위치 (전체 고장의 {miss_fail / (miss_fail + hit_fail) * 100:.1f}%)

원인: 8~40배로 튀는 센서 오작동이 사분위수를 밀어올려 IQR 경계가 바깥으로 이동
  → 정상보다 약간 높은 진짜 고장의 토크가 경계 안쪽에 남음

IQR 결과는 분포의 꼬리에 무엇이 있느냐에 따라 달라짐
  같은 규칙이 데이터에 따라 고장을 지우기도, 놓치기도 함
  → 이상치 규칙 적용 전 무엇이 걸리는지 확인 필요""")

rule("A4-4. 구분 단서 — 지속시간과 센서 간 정합성")
o2 = o.dropna(subset=["torque_nm", "rot_speed_rpm", "vibration_mms"]).copy()
mk = masks.loc[o2.index]
grp = o2.groupby("machine_id")

# 단서 1: 지속시간 (스파이크는 단발, 실제 이상은 지속된다고 가정)
o2["tq_ham"] = grp["torque_nm"].transform(lambda s: hampel_flag(s, 11, 4.0))
o2["run"] = grp["tq_ham"].transform(
    lambda s: s.groupby((s != s.shift()).cumsum()).transform("size")
)
o2["persist"] = o2["tq_ham"] & (o2["run"] >= 3)

# 단서 2: 물리 정합성 (실제 부하 변화면 전류도 함께 변함)
o2["cur_ham"] = grp["current_a"].transform(
    lambda s: hampel_flag(pd.to_numeric(s, errors="coerce"), 11, 4.0)
)
o2["coherent"] = o2["tq_ham"] & o2["cur_ham"]

check = []
for name, pred in [
    ("Hampel 단독", o2["tq_ham"]),
    ("지속 3분 이상", o2["persist"]),
    ("전류와 동시 이상", o2["coherent"]),
]:
    pred = pred.fillna(False).astype(bool)
    is_spike = mk["spike_torque_nm"].astype(bool)
    is_fail = o2["machine_failure"].astype(bool) & ~is_spike
    check.append(
        {
            "판정 규칙": name,
            "걸린 행": int(pred.sum()),
            "센서오작동 포함": int((pred & is_spike).sum()),
            "진짜고장 포함": int((pred & is_fail).sum()),
            "오작동 비중%": round(
                (pred & is_spike).sum() / max(pred.sum(), 1) * 100, 1
            ),
        }
    )
chk = pd.DataFrame(check)
print(chk.to_string(index=False))
r_ham = chk.iloc[0]
r_per = chk.iloc[1]
r_coh = chk.iloc[2]
print(f"""
규칙별 결과

 · Hampel 단독      : {int(r_ham["걸린 행"])}행 중 센서오작동 비중 {r_ham["오작동 비중%"]}%
                     급변만 보면 오작동이 함께 포함됨

 · 지속 3분 이상     : {int(r_per["걸린 행"])}행
                     시뮬레이터 고장(야간 저부하 PWF 등)은 급변이 아니라 서서히 진입해 Hampel에 잘 걸리지 않음
                     → 지속시간 규칙은 급변 후 지속되는 고장에만 유효

 · 전류와 동시 이상  : {int(r_coh["걸린 행"])}행 중 센서오작동 {int(r_coh["센서오작동 포함"])}건 (비중 {r_coh["오작동 비중%"]}%)
                     Hampel 단독 {r_ham["오작동 비중%"]}% 대비 감소
                     토크만 튀고 전류가 정상이면 물리적으로 불가능 → 센서 문제
                     두 센서가 함께 변하면 실제 부하 변화

단일 센서 이상치 규칙으로는 오작동과 고장 구분 불가
  → 여러 센서의 물리적 정합성으로 판단""")

rule("A4-5. 그림")
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
ax = axes[0]
ok = df[df["failure"] == 0]
ng = df[df["failure"] == 1]
ax.scatter(
    ok["tool_wear_min"], ok["torque_nm"], s=4, alpha=0.25, color="#a0aec0", label="정상"
)
ax.scatter(
    ng["tool_wear_min"],
    ng["torque_nm"],
    s=12,
    alpha=0.85,
    color="#c53030",
    label="고장",
)
q1, q3 = df["torque_nm"].quantile([0.25, 0.75])
iqr = q3 - q1
ax.axhline(q3 + 1.5 * iqr, color="black", ls="--", lw=1)
ax.axhline(q1 - 1.5 * iqr, color="black", ls="--", lw=1, label="IQR 경계")
ax.set_xlabel("공구 마모(분)")
ax.set_ylabel("토크(Nm)")
ax.set_title("AI4I — 토크·공구 마모와 IQR 경계")
ax.legend(fontsize=8)

ax = axes[1]
lbl = ["① 그대로", "② IQR 삭제", "③ 플래그 추가"]
vals = [r["재현율"] for r in res]
b = ax.bar(lbl, vals, color=["#2b6cb0", "#c53030", "#276749"], width=0.6)
ax.bar_label(b, fmt="%.3f", fontsize=10)
ax.set_ylim(0, 1.0)
ax.set_ylabel("재현율")
ax.set_title("이상치 처리 방식별 재현율 (AI4I)")
ax.tick_params(axis="x", labelsize=9)

ax = axes[2]
cm = pd.DataFrame(check).set_index("판정 규칙")[["센서오작동 포함", "진짜고장 포함"]]
cm.index = ["Hampel\n단독", "지속\n3분+", "전류와\n동시"]
cm.plot(kind="bar", ax=ax, color=["#c53030", "#2b6cb0"], rot=0, width=0.7)
ax.set_title("판정 규칙별 탐지 구성 (시뮬레이터)")
ax.set_ylabel("행 수")
ax.tick_params(axis="x", labelsize=9)
ax.legend(fontsize=8)
fig.tight_layout()
save(fig, "outlier_trap")
