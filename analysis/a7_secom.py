"""
A7. SECOM (UCI) — 반도체 공정 데이터의 예측 한계와 원인 분석

590개 센서 × 1,567개 웨이퍼 로트, 불량률 약 6.6%
결측 대량, 상수 컬럼 대량, 고차원 저표본, 불균형
성능이 나오지 않는 경우 원인을 규명하는 것을 목표로 함
"""

from _common import RAW, ROOT, rule, save
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pd.set_option("display.width", 170)
SEED = 42


def effect_label(d):
    if d >= 0.8:
        return "큼"
    if d >= 0.5:
        return "중간"
    if d >= 0.2:
        return "작음"
    return "매우 작음"


rule("A7-1. 로드 — 컬럼 이름 없는 센서 행렬")
X = pd.read_csv(RAW / "secom" / "secom.data", sep=" ", header=None)
X.columns = [f"s{i:03d}" for i in range(X.shape[1])]
lab = pd.read_csv(
    RAW / "secom" / "secom_labels.data", sep=" ", header=None, names=["label", "ts"]
)
lab["ts"] = pd.to_datetime(lab["ts"].str.strip('"'), format="%d/%m/%Y %H:%M:%S")
print("센서 행렬:", X.shape, "| 라벨:", lab.shape)
print(
    "기간:",
    lab["ts"].min(),
    "~",
    lab["ts"].max(),
    f"({(lab['ts'].max() - lab['ts'].min()).days}일)",
)
y = (lab["label"] == 1).astype(int)  # 1 = 불량(fail)
print(
    f"\n불량 {int(y.sum())}건 / 정상 {int((1 - y).sum())}건 = 불량률 {y.mean() * 100:.3f}%"
)
print("""
타임스탬프 형식 DD/MM/YYYY → format 명시
  기본 파싱(MM/DD)으로 읽으면 일·월이 뒤바뀌거나 NaT 발생""")

rule("A7-2. 데이터 품질 점검")
miss = X.isna().mean()
nuniq = X.nunique(dropna=True)
print(
    f"전체 결측: {int(X.isna().sum().sum()):,}개 ({X.isna().sum().sum() / X.size * 100:.2f}%)"
)
print("\n[컬럼 결측률 분포]")
print(miss.describe().round(4).to_string())
print("\n[구간별 컬럼 수]")
bins = pd.cut(
    miss,
    [-0.001, 0, 0.05, 0.2, 0.5, 0.9, 1.0],
    labels=["0%", "0~5%", "5~20%", "20~50%", "50~90%", "90~100%"],
)
print(bins.value_counts().sort_index().to_string())
print(f"\n상수 컬럼(고유값 ≤ 1) : {int((nuniq <= 1).sum())}개")
print(
    f"준상수 컬럼(최빈값 99% 이상): "
    f"{int((X.apply(lambda c: c.value_counts(normalize=True, dropna=True).max() if c.notna().any() else 1) > 0.99).sum())}개"
)
print(
    f"\n행 대비 열 비율 : {X.shape[1]}열 / {X.shape[0]}행 = {X.shape[1] / X.shape[0]:.2f}"
)
print(f"불량 1건당 센서 : {X.shape[1] / y.sum():.1f}개")
print(f"""
불량 {int(y.sum())}건 대비 센서 {X.shape[1]}개 → 고차원 저표본
  우연히 불량과 맞아떨어지는 센서가 나오기 쉬워 과적합 위험이 큼 (A7-4에서 확인)""")

rule("A7-3. 정제 — 제거 규칙 적용")
steps = []


def log(name, cols):
    steps.append({"단계": name, "남은 컬럼": len(cols)})
    return cols


cols = log("0. 원본", list(X.columns))
cols = log("1. 상수 컬럼 제거", [c for c in cols if nuniq[c] > 1])
cols = log("2. 결측 50% 초과 제거", [c for c in cols if miss[c] <= 0.5])
# 값이 완전히 같은 센서(중복 컬럼) 제거
sub = X[cols]
dup = sub.T.duplicated()
cols = log("3. 중복 컬럼 제거", [c for c in cols if not dup[c]])
print(pd.DataFrame(steps).to_string(index=False))
print(f"\n590개 → {len(cols)}개 ({len(cols) / 590 * 100:.1f}% 생존)")

Xc = X[cols].copy()
print(f"남은 결측: {int(Xc.isna().sum().sum()):,}개 → 중앙값 대체 예정")
print("""
중앙값 대체: 공정 센서는 이상치가 흔하고 분포가 치우쳐 평균보다 안정적
대체는 파이프라인 안에서 train으로만 계산 → 전체 중앙값 사용 시 test 정보 유입 (A3-8과 같은 문제)""")

rule("A7-4. 다중검정 — 센서별 t-검정과 보정")
pvals = {}
for c in cols:
    a = Xc.loc[y == 0, c].dropna()
    b = Xc.loc[y == 1, c].dropna()
    if len(a) > 5 and len(b) > 5 and (a.std() > 0 or b.std() > 0):
        pvals[c] = stats.ttest_ind(a, b, equal_var=False).pvalue
pv = pd.Series(pvals).dropna().sort_values()
n_test = len(pv)
sig05 = int((pv < 0.05).sum())
print(f"검정한 센서 수       : {n_test}개")
print(f"p < 0.05 인 센서     : {sig05}개")
print(f"우연히 기대되는 개수 : {n_test * 0.05:.1f}개  (검정 수 × 0.05)")
print(f"→ 우연 기대치를 뺀 개수 : 약 {sig05 - n_test * 0.05:.0f}개")

# Bonferroni & BH(FDR)
bonf = 0.05 / n_test
n_bonf = int((pv < bonf).sum())
m = n_test
ranked = pv.reset_index(drop=True)
bh_thresh = (np.arange(1, m + 1) / m) * 0.05
below = ranked.values < bh_thresh
n_bh = int(np.max(np.where(below)[0]) + 1) if below.any() else 0
print(f"\nBonferroni 보정 (α={bonf:.2e}) 통과 : {n_bonf}개")
print(f"BH(FDR 5%) 통과                    : {n_bh}개")
print("\n[p값 상위 10개 센서]")
top = pv.head(10)
tt = pd.DataFrame(
    {
        "p값": top.round(6),
        "정상 평균": [round(Xc.loc[y == 0, c].mean(), 3) for c in top.index],
        "불량 평균": [round(Xc.loc[y == 1, c].mean(), 3) for c in top.index],
    }
)
print(tt.to_string())
print(f"""
p<0.05 센서 {sig05}개 중 약 {n_test * 0.05:.0f}개는 {n_test}번 검정에서 우연히 기대되는 수준
  Bonferroni 통과 {n_bonf}개 (가짜를 거의 막지만 진짜 신호도 놓칠 수 있음)
  BH(FDR 5%) 통과 {n_bh}개 (통과 센서 중 가짜 비율을 5% 이하로 제한하는 절충안)""")

rule("A7-5. 모델링 — 시간순 split")
ordr = lab["ts"].argsort().values
Xo = Xc.iloc[ordr].reset_index(drop=True)
yo = y.iloc[ordr].reset_index(drop=True)
ts_o = lab["ts"].iloc[ordr].reset_index(drop=True)
cut = int(len(Xo) * 0.75)
print(
    f"train {cut}건 ({ts_o.iloc[0].date()} ~ {ts_o.iloc[cut - 1].date()}) "
    f"불량 {int(yo[:cut].sum())}건 ({yo[:cut].mean() * 100:.2f}%)"
)
print(
    f"test  {len(Xo) - cut}건 ({ts_o.iloc[cut].date()} ~ {ts_o.iloc[-1].date()}) "
    f"불량 {int(yo[cut:].sum())}건 ({yo[cut:].mean() * 100:.2f}%)"
)


def make(m):
    return Pipeline(
        [("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()), ("m", m)]
    )


cands = {
    "무조건 정상": DummyClassifier(strategy="most_frequent"),
    "로지스틱": make(LogisticRegression(max_iter=2000, random_state=SEED)),
    "로지스틱+가중": make(
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    ),
    "랜덤포레스트": Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            (
                "m",
                RandomForestClassifier(n_estimators=400, random_state=SEED, n_jobs=-1),
            ),
        ]
    ),
    "랜덤포레스트+가중": Pipeline(
        [
            ("imp", SimpleImputer(strategy="median")),
            (
                "m",
                RandomForestClassifier(
                    n_estimators=400,
                    class_weight="balanced_subsample",
                    random_state=SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    ),
}
rows = []
for name, mdl in cands.items():
    mdl.fit(Xo[:cut], yo[:cut])
    if hasattr(mdl, "predict_proba"):
        p = mdl.predict_proba(Xo[cut:])[:, 1]
    else:
        p = mdl.predict(Xo[cut:])
    pred = (p >= 0.5).astype(int)
    yt = yo[cut:]
    rows.append(
        {
            "모델": name,
            "정확도": round((pred == yt).mean(), 4),
            "재현율": round(recall_score(yt, pred, zero_division=0), 4),
            "F1": round(f1_score(yt, pred, zero_division=0), 4),
            "ROC-AUC": round(roc_auc_score(yt, p), 4) if len(set(p)) > 1 else 0.5,
            "PR-AUC": round(average_precision_score(yt, p), 4),
        }
    )
res = pd.DataFrame(rows)
print("\n" + res.to_string(index=False))
base = yo[cut:].mean()
print(f"\nPR-AUC 기준선(= test 불량률) = {base:.4f}")
best = res.loc[res["PR-AUC"].idxmax()]
print(f"""
최고 PR-AUC {best["PR-AUC"]:.4f} (모델: {best["모델"]}), 기준선 {base:.4f} 대비 {best["PR-AUC"] / base:.2f}배
  참고: AI4I는 PR-AUC 약 0.90, 기준선 0.034 대비 약 26배
정확도 범위 {res["정확도"].min():.3f} ~ {res["정확도"].max():.3f} → 불균형 데이터에서 정확도로는 모델 구분 불가""")

rule("A7-6. 원인 분석 — 신호 강도와 공정 변화")
print("""가설 1) 신호 자체가 약하다
가설 2) 표본이 부족하다
가설 3) 시간에 따라 공정이 변한다 (분포 이동)""")

# 가설 1 검증: 효과크기 (Cohen's d)
eff = []
for c in pv.head(20).index:
    a = Xc.loc[y == 0, c].dropna()
    b = Xc.loc[y == 1, c].dropna()
    sp = np.sqrt(
        ((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / max(len(a) + len(b) - 2, 1)
    )
    eff.append(abs(a.mean() - b.mean()) / sp if sp > 0 else 0)
d_med = np.median(eff)
print(
    f"\n[가설1] p값 상위 20개 센서의 Cohen's d 중앙값 = {d_med:.3f} ({effect_label(d_med)})"
)
print("  기준: 0.2 작음 / 0.5 중간 / 0.8 큼")

# 가설 3 검증: 전반부/후반부 불량률과 분포
half = len(yo) // 2
print(
    f"\n[가설3] 전반부 불량률 {yo[:half].mean() * 100:.2f}% / "
    f"후반부 불량률 {yo[half:].mean() * 100:.2f}%"
)
shift = []
for c in pv.head(50).index:
    a = Xo.loc[:half, c].dropna()
    b = Xo.loc[half:, c].dropna()
    if len(a) > 10 and len(b) > 10:
        shift.append(stats.ks_2samp(a, b).pvalue)
shift = np.array(shift)
print(
    f"  상위 50개 센서 중 전/후반 분포가 유의하게 다른 것: "
    f"{int((shift < 0.05).sum())}개 ({(shift < 0.05).mean() * 100:.0f}%)"
)
print("  → 비율이 높으면 앞 시기로 학습한 패턴이 뒤 시기에 맞지 않을 가능성")

# 랜덤 split과 비교 (누수 확인)
Xtr, Xte, ytr, yte = train_test_split(
    Xc, y, test_size=0.25, random_state=SEED, stratify=y
)
mdl = Pipeline(
    [
        ("imp", SimpleImputer(strategy="median")),
        ("m", RandomForestClassifier(n_estimators=400, random_state=SEED, n_jobs=-1)),
    ]
)
mdl.fit(Xtr, ytr)
pr = mdl.predict_proba(Xte)[:, 1]
print(
    f"\n[참고] 랜덤 split PR-AUC {average_precision_score(yte, pr):.4f} "
    f"vs 시간순 split {best['PR-AUC']:.4f}"
)
print(
    "  SECOM은 로트 간격이 수십 분~수 시간이라 행 간 의존성이 A3 시뮬레이터보다 약할 수 있음"
)

rule("A7-7. 학습 곡선 — 가설 2(표본 부족)와 가설 3(공정 변화) 검증")
# 최고 모델과 같은 설정으로 train 크기만 바꿔 test 성능 비교
# 무작위 부분표본: 데이터 양만 변경 (3개 seed 평균)
# 최근 구간만: test와 가까운 시기의 데이터만 사용
best_name = best["모델"]
base_model = cands[best_name]
Xtr_o, ytr_o = Xo[:cut], yo[:cut]
Xte_o, yte_o = Xo[cut:], yo[cut:]


def fit_pr(Xa, ya):
    if ya.sum() == 0:
        return np.nan
    m_ = clone(base_model)
    m_.fit(Xa, ya)
    pp = m_.predict_proba(Xte_o)[:, 1]
    return average_precision_score(yte_o, pp)


fracs = [0.25, 0.5, 0.75, 1.0]
lc = []
for f in fracs:
    n_sub = int(cut * f)
    rand_scores, rand_pos = [], []
    for s in [0, 1, 2]:
        idx = np.sort(np.random.default_rng(SEED + s).choice(cut, n_sub, replace=False))
        rand_scores.append(fit_pr(Xtr_o.iloc[idx], ytr_o.iloc[idx]))
        rand_pos.append(int(ytr_o.iloc[idx].sum()))
    rec_idx = np.arange(cut - n_sub, cut)
    lc.append(
        {
            "train 비율": f"{int(f * 100)}%",
            "train 행": n_sub,
            "무작위 부분 불량(평균)": round(float(np.mean(rand_pos)), 1),
            "무작위 부분 PR-AUC": round(float(np.nanmean(rand_scores)), 4),
            "최근 구간 불량": int(ytr_o.iloc[rec_idx].sum()),
            "최근 구간 PR-AUC": round(
                fit_pr(Xtr_o.iloc[rec_idx], ytr_o.iloc[rec_idx]), 4
            ),
        }
    )
lc_df = pd.DataFrame(lc)
print(f"모델: {best_name} | test 기준선 {base:.4f}")
print(lc_df.to_string(index=False))
r25 = lc_df.iloc[0]["무작위 부분 PR-AUC"]
r100 = lc_df.iloc[-1]["무작위 부분 PR-AUC"]
rec25 = lc_df.iloc[0]["최근 구간 PR-AUC"]
print(f"""
읽는 법
  무작위 부분표본: 시기 구성은 그대로 두고 양만 변경 → 늘수록 PR-AUC가 오르면 표본 부족이 원인 (가설 2)
  최근 구간만 사용: 오래된 데이터를 제외 → 적은 양으로도 전체와 비슷하거나 높으면 공정 변화가 원인 (가설 3)

  무작위 부분표본 PR-AUC 25% → 100%: {r25:.4f} → {r100:.4f} ({r100 - r25:+.4f})
  최근 25%만 사용 PR-AUC {rec25:.4f} vs 전체 사용 {r100:.4f}
  기준선 {base:.4f}""")

rule("A7-8. 순위 지표로 본 성능")
mdl_best = cands[best_name]  # A7-5 PR-AUC 1등 모델
print(f"모델: {best_name}")
p_best = mdl_best.predict_proba(Xo[cut:])[:, 1]
yt = yo[cut:].values
order = np.argsort(-p_best)
rows = []
for k in [10, 20, 30, 50, 100]:
    hit = int(yt[order][:k].sum())
    rows.append(
        {
            "상위 K": k,
            "잡은 불량": hit,
            "Precision@K": round(hit / k, 3),
            "Recall@K": round(hit / max(yt.sum(), 1), 3),
            "무작위 기대": round(k * yt.mean(), 1),
        }
    )
print(pd.DataFrame(rows).to_string(index=False))
lift50 = yt[order][:50].sum() / max(50 * yt.mean(), 1e-9)
lift100 = yt[order][:100].sum() / max(100 * yt.mean(), 1e-9)
print(f"""
상위 50건 검사 → 불량 {int(yt[order][:50].sum())}건, 무작위 기대 {50 * yt.mean():.1f}건 (향상도 {lift50:.2f}배)
상위 100건 검사 → 불량 {int(yt[order][:100].sum())}건, 무작위 기대 {100 * yt.mean():.1f}건 (향상도 {lift100:.2f}배)
  향상도가 1에 가까우면 무작위 검사와 차이 없음""")

rule("A7-9. 요약")
ratio = best["PR-AUC"] / base
verdict = "운영 적용 수준 미달" if ratio < 2 else "추가 검토 필요"
print(f"""
  SECOM 웨이퍼 불량 예측: 시간순 split PR-AUC {best["PR-AUC"]:.3f}, 기준선 {base:.3f} (기준선 대비 {ratio:.2f}배) → {verdict}

  원인 분석
   (1) 신호 강도: 상위 20개 센서 Cohen's d 중앙값 {d_med:.2f} ({effect_label(d_med)})
   (2) 표본: 불량 {int(y.sum())}건, 센서 {X.shape[1]}개 (고차원 저표본)
       학습 곡선 25% → 100%: PR-AUC {r25:.3f} → {r100:.3f}
   (3) 공정 변화: 상위 50개 센서 중 {(shift < 0.05).mean() * 100:.0f}%에서 전/후반 분포 차이
       최근 25%만 사용 PR-AUC {rec25:.3f}

  순위 기반 검사 향상도 {lift50:.2f}배 (상위 50건, {best_name})

  개선에 필요한 것: (a) 불량 표본 확대 (b) 센서 태그 의미 정보(공정 단계) (c) 공정 변경 이력""")

rule("A7-10. 그림")
fig, axes = plt.subplots(1, 4, figsize=(18, 4.2))
axes[0].hist(miss, bins=50, color="#c53030")
axes[0].set_yscale("log")
axes[0].set_xlabel("컬럼 결측률")
axes[0].set_ylabel("컬럼 수 (log)")
axes[0].set_title("SECOM 결측 구조")

axes[1].hist(pv.values, bins=40, color="#2b6cb0", edgecolor="white")
axes[1].axhline(
    n_test / 40 * 1.0, color="gray", ls="--", label="균등분포(=신호 없음) 기대선"
)
axes[1].axvline(0.05, color="crimson", ls="--", label="p=0.05")
axes[1].set_xlabel("p값")
axes[1].set_ylabel("센서 수")
axes[1].set_title(f"센서별 t-검정 p값 분포 (n={n_test})")
axes[1].legend(fontsize=8)

ks_ = np.arange(1, len(yt) + 1)
axes[2].plot(
    ks_,
    np.cumsum(yt[order]) / max(yt.sum(), 1),
    color="#2b6cb0",
    lw=1.8,
    label="모델 순위",
)
axes[2].plot(
    ks_, ks_ * yt.mean() / max(yt.sum(), 1), color="gray", ls="--", label="무작위"
)
axes[2].set_xlabel("검사 건수 K")
axes[2].set_ylabel("잡은 불량 비율")
axes[2].set_title(f"순위 성능 ({best_name})")
axes[2].legend(fontsize=8)

xs = [int(f * 100) for f in fracs]
axes[3].plot(
    xs,
    lc_df["무작위 부분 PR-AUC"],
    marker="o",
    color="#2b6cb0",
    label="무작위 부분표본",
)
axes[3].plot(
    xs, lc_df["최근 구간 PR-AUC"], marker="s", color="#c53030", label="최근 구간만"
)
axes[3].axhline(base, color="gray", ls="--", label=f"기준선 {base:.3f}")
axes[3].set_xlabel("train 사용 비율 (%)")
axes[3].set_ylabel("test PR-AUC")
axes[3].set_title(f"학습 곡선 ({best_name})")
axes[3].legend(fontsize=8)
fig.tight_layout()
save(fig, "secom")

res.to_csv(ROOT / "data" / "secom_result.csv", index=False)
print("저장: data/secom_result.csv")
