"""
A2. AI4I 2020 (UCI) — 불균형 데이터에서 정확도의 한계

실데이터 10,000행, 고장 339건(3.39%)
"""

from _common import RAW, rule, save
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pd.set_option("display.width", 170)
SEED = 42

rule("A2-1. 로드 & 첫 점검")
df = pd.read_csv(RAW / "ai4i" / "ai4i2020.csv")
print("shape:", df.shape)
print("\n[컬럼]")
print(
    pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "결측": df.isna().sum(),
            "고유값": df.nunique(),
        }
    ).to_string()
)
print("\n중복 행:", df.duplicated().sum(), "| 중복 UDI:", df["UDI"].duplicated().sum())

# 컬럼명 정리 (대괄호·공백 제거)
REN = {
    "Air temperature [K]": "air_temp_k",
    "Process temperature [K]": "process_temp_k",
    "Rotational speed [rpm]": "rot_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
    "Machine failure": "failure",
    "Product ID": "product_id",
    "Type": "type",
}
df = df.rename(columns=REN)
MODES = ["TWF", "HDF", "PWF", "OSF", "RNF"]
NUM = ["air_temp_k", "process_temp_k", "rot_speed_rpm", "torque_nm", "tool_wear_min"]

print("\n[수치형 요약]")
print(df[NUM].describe().loc[["mean", "std", "min", "50%", "max"]].round(2).to_string())
print("\n[품질 등급]")
print(df["type"].value_counts().to_string())

rule("A2-2. 라벨 검산 — 고장 라벨과 세부 모드의 불일치")
anyf = df[MODES].sum(axis=1)
bad1 = ((df["failure"] == 1) & (anyf == 0)).sum()
bad2 = ((df["failure"] == 0) & (anyf > 0)).sum()
print(f"고장=1 인데 세부 모드가 하나도 없음 : {bad1}건")
print(f"세부 모드가 있는데 고장=0          : {bad2}건")
print("\n두 번째 경우의 내역:")
print(df[(df["failure"] == 0) & (anyf > 0)][MODES].sum().to_string())
print("""
RNF(원인불명 고장) 대부분이 Machine failure=0으로 기록됨
  데이터 제공자 정의상 RNF가 최종 고장 라벨에 포함되지 않은 것으로 추정
  → 원본 Machine failure를 그대로 목표변수로 사용하고, 이 특이점은 보고서 한계 항목에 기록""")

print("\n[모드별 건수 / 전체 대비]")
mt = pd.DataFrame({"건수": df[MODES + ["failure"]].sum()})
mt["비율(%)"] = (mt["건수"] / len(df) * 100).round(2)
print(mt.to_string())

rule("A2-3. 불균형 — 정확도가 무의미한 이유")
rate = df["failure"].mean()
print(f"고장률          : {rate * 100:.2f}%  ({df['failure'].sum()}건 / {len(df)}건)")
print(f"정상률          : {(1 - rate) * 100:.2f}%")
print(
    f"\n'무조건 정상' 모델의 정확도 = {(1 - rate) * 100:.2f}% (고장은 한 건도 탐지 못 함)"
)

X = pd.get_dummies(df[NUM + ["type"]], columns=["type"], drop_first=True)
y = df["failure"]
Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.25, random_state=SEED, stratify=y
)
print(f"\ntrain {Xtr.shape} / test {Xte.shape} | test 고장 {yte.sum()}건")

dummy = DummyClassifier(strategy="most_frequent").fit(Xtr, ytr)
dp = dummy.predict(Xte)
print("\n[무조건 정상 모델]")
print(f"  정확도  : {accuracy_score(yte, dp):.4f}")
print(f"  정밀도  : {precision_score(yte, dp, zero_division=0):.4f}")
print(f"  재현율  : {recall_score(yte, dp, zero_division=0):.4f}")
print(f"  F1      : {f1_score(yte, dp, zero_division=0):.4f}")
print("  혼동행렬:")
print(
    pd.DataFrame(
        confusion_matrix(yte, dp),
        index=["실제정상", "실제고장"],
        columns=["예측정상", "예측고장"],
    ).to_string()
)
print(
    f"\n정확도 {accuracy_score(yte, dp):.4f} / 재현율 "
    f"{recall_score(yte, dp, zero_division=0):.4f}"
)

rule("A2-4. 실제 모델 — 로지스틱 vs 랜덤포레스트")
models = {
    "로지스틱": Pipeline(
        [
            ("sc", StandardScaler()),
            ("m", LogisticRegression(max_iter=1000, random_state=SEED)),
        ]
    ),
    "로지스틱+가중": Pipeline(
        [
            ("sc", StandardScaler()),
            (
                "m",
                LogisticRegression(
                    max_iter=1000, class_weight="balanced", random_state=SEED
                ),
            ),
        ]
    ),
    "랜덤포레스트": RandomForestClassifier(
        n_estimators=300, random_state=SEED, n_jobs=-1
    ),
    "랜덤포레스트+가중": RandomForestClassifier(
        n_estimators=300, class_weight="balanced", random_state=SEED, n_jobs=-1
    ),
}
rows, probs = [], {}
for name, mdl in models.items():
    mdl.fit(Xtr, ytr)
    p = mdl.predict_proba(Xte)[:, 1]
    probs[name] = p
    pred = (p >= 0.5).astype(int)
    rows.append(
        {
            "모델": name,
            "정확도": round(accuracy_score(yte, pred), 4),
            "정밀도": round(precision_score(yte, pred, zero_division=0), 4),
            "재현율": round(recall_score(yte, pred, zero_division=0), 4),
            "F1": round(f1_score(yte, pred, zero_division=0), 4),
            "ROC-AUC": round(roc_auc_score(yte, p), 4),
            "PR-AUC": round(average_precision_score(yte, p), 4),
        }
    )
base = pd.DataFrame(rows)
base.loc[len(base)] = {
    "모델": "무조건정상",
    "정확도": round(accuracy_score(yte, dp), 4),
    "정밀도": 0.0,
    "재현율": 0.0,
    "F1": 0.0,
    "ROC-AUC": 0.5,
    "PR-AUC": round(yte.mean(), 4),
}
print(base.to_string(index=False))
print(f"""
읽는 기준
  - 정확도는 모델 간 차이가 작아 성능 구분에 부적합
  - PR-AUC 기준선 = 고장률 {yte.mean():.4f}, 기준선 대비 배수로 성능 판단
  - ROC-AUC는 불균형 데이터에서 낙관적으로 나옴 → PR-AUC 우선""")

print("\n[랜덤포레스트 상세 리포트]")
best = "랜덤포레스트"
pred = (probs[best] >= 0.5).astype(int)
print(classification_report(yte, pred, target_names=["정상", "고장"], digits=4))
print("혼동행렬:")
print(
    pd.DataFrame(
        confusion_matrix(yte, pred),
        index=["실제정상", "실제고장"],
        columns=["예측정상", "예측고장"],
    ).to_string()
)

rule("A2-5. ROC와 PR 곡선 — 같은 모델, 다른 인상")
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
for name in ["로지스틱", "랜덤포레스트"]:
    fpr, tpr, _ = roc_curve(yte, probs[name])
    axes[0].plot(
        fpr, tpr, lw=1.6, label=f"{name} (AUC={roc_auc_score(yte, probs[name]):.3f})"
    )
    pr, rc, _ = precision_recall_curve(yte, probs[name])
    axes[1].plot(
        rc,
        pr,
        lw=1.6,
        label=f"{name} (AP={average_precision_score(yte, probs[name]):.3f})",
    )
axes[0].plot([0, 1], [0, 1], "k--", lw=0.8, label="무작위")
axes[0].set_xlabel("거짓양성률 FPR")
axes[0].set_ylabel("재현율 TPR")
axes[0].set_title("ROC 곡선")
axes[0].legend(fontsize=8)
axes[1].axhline(
    yte.mean(), color="k", ls="--", lw=0.8, label=f"기준선 = 고장률 {yte.mean():.3f}"
)
axes[1].set_xlabel("재현율")
axes[1].set_ylabel("정밀도")
axes[1].set_title("PR 곡선 (기준선 = 고장률)")
axes[1].legend(fontsize=8)
fig.tight_layout()
save(fig, "ai4i_roc_pr")

rule("A2-6. 고장 모드별 재현율")
rf = models["랜덤포레스트"]
te = df.loc[Xte.index].copy()
te["prob"] = probs["랜덤포레스트"]
te["pred"] = (te["prob"] >= 0.5).astype(int)
mm = []
for md in MODES:
    sub = te[te[md] == 1]
    if len(sub) == 0:
        continue
    mm.append(
        {
            "모드": md,
            "test 건수": len(sub),
            "잡아낸 건수": int(sub["pred"].sum()),
            "재현율": round(sub["pred"].mean(), 3),
            "평균확률": round(sub["prob"].mean(), 3),
        }
    )
print(pd.DataFrame(mm).to_string(index=False))
print("""
RNF(원인불명)는 무작위 발생이라 센서 신호가 없음 → 모델 한계가 아니라 원리적으로 예측 불가""")

print("\n[변수 중요도 — 랜덤포레스트]")
imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
print(imp.round(4).to_string())

rule("A2-7. 파생변수 추가 — 고장 정의식 기반")
X2 = X.copy()
X2["temp_diff_k"] = df["process_temp_k"] - df["air_temp_k"]
X2["power_w"] = df["torque_nm"] * df["rot_speed_rpm"] * 2 * np.pi / 60
X2["wear_torque"] = df["tool_wear_min"] * df["torque_nm"]
X2tr, X2te = X2.loc[Xtr.index], X2.loc[Xte.index]
rf2 = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1).fit(
    X2tr, ytr
)
p2 = rf2.predict_proba(X2te)[:, 1]
print(
    f"파생변수 없음 : PR-AUC {average_precision_score(yte, probs['랜덤포레스트']):.4f} | "
    f"F1 {f1_score(yte, (probs['랜덤포레스트'] >= 0.5).astype(int)):.4f}"
)
print(
    f"파생변수 3개  : PR-AUC {average_precision_score(yte, p2):.4f} | "
    f"F1 {f1_score(yte, (p2 >= 0.5).astype(int)):.4f}"
)
imp2 = pd.Series(rf2.feature_importances_, index=X2.columns).sort_values(
    ascending=False
)
print("\n[중요도 상위 6개]")
print(imp2.head(6).round(4).to_string())
print("""
temp_diff(HDF), power(PWF), wear×torque(OSF)는 AI4I 고장 정의식에 해당
  → 모델 변경 없이 고장 정의를 변수로 반영해 성능 향상""")

np.save(RAW.parent / "ai4i_probs.npy", probs["랜덤포레스트"])
te[["UDI", "prob", "pred", "failure"] + MODES].to_csv(
    RAW.parent / "ai4i_test_pred.csv", index=False
)
print("\n저장: data/ai4i_test_pred.csv")
