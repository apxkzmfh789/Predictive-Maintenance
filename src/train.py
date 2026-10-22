"""
학습 스크립트 — 대시보드용 모델 결과 생성

    python src/train.py              # 2024년 기준 기간 → models/
    python src/train.py --recent 14  # 최근 14일 → models/recent/

원칙
  1) 목표변수는 '30분 내 고장' (감지가 아니라 예지)
  2) split은 시간순
  3) 임계값은 0.5가 아니라 비용 최소점
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import features as F  # noqa: E402
from clean import run_pipeline  # noqa: E402

HORIZON = 30
COST_FN = 8_000_000
COST_FP = 300_000
SEED = 42

# 분석용 고정 데이터 기간 (history 파일 이름 기준)
BASELINE_START = "2024-01-01"
BASELINE_END = "2024-01-14"


def history_files() -> list[Path]:
    files = sorted((ROOT / "data" / "history").glob("*.csv"))
    if not files:
        raise SystemExit("data/history/*.csv 없음 → collector.py 먼저 실행")
    return files


def read_files(files: list[Path]) -> pd.DataFrame:
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def load_baseline() -> pd.DataFrame:
    files = [f for f in history_files() if BASELINE_START <= f.stem <= BASELINE_END]
    if not files:
        raise SystemExit(f"기준 기간 파일 없음 ({BASELINE_START} ~ {BASELINE_END})")
    print(f"기간: 2024년 기준 ({BASELINE_START} ~ {BASELINE_END}, 파일 {len(files)}개)")
    return read_files(files)


def load_recent(days: int) -> pd.DataFrame:
    files = history_files()
    raw = read_files(files)
    ts = pd.to_datetime(raw["ts"], errors="coerce")
    end = ts.max()
    raw = raw[ts > end - pd.Timedelta(days=days)]  # 마지막 시각 기준 최근 N일만 사용
    print(f"기간: 최근 {days}일 (~ {end}, 전체 파일 {len(files)}개 중 해당 구간)")
    return raw


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--recent",
        type=int,
        default=None,
        metavar="DAYS",
        help="최근 N일 데이터로 학습 (생략 시 2024년 기준 기간)",
    )
    args = ap.parse_args(argv)

    if args.recent is None:
        raw = load_baseline()
        period = "baseline"
        outdir = ROOT / "models"
    else:
        raw = load_recent(args.recent)
        period = f"recent_{args.recent}d"
        outdir = ROOT / "models" / "recent"
    print(f"원본 {len(raw):,}행")

    clean, log, rep = run_pipeline(raw, verbose=True)
    clean = clean[~clean["is_gap"].astype(bool)].copy()  # 재색인으로 채운 빈 행 제외

    d = F.make_horizon_label(clean, horizon=HORIZON)
    d = F.build(d, windows=(10, 30, 60), shift_one=True)
    feat = [c for c in F.feature_columns(d) if c not in ("y", "machine_failure")]
    d = d.dropna(subset=feat + ["y"]).sort_values("ts").reset_index(drop=True)
    if len(d) < 500 or d["y"].nunique() < 2:
        raise SystemExit(f"학습 데이터 부족 ({len(d)}행) → 수집 기간 확대 필요")

    X = d[feat].values
    y = d["y"].values.astype(int)
    cut = int(len(d) * 0.75)  # 시간순 split (앞 75% 학습, 뒤 25% 평가)
    print(
        f"\ntrain {cut:,} / test {len(d) - cut:,} | "
        f"train 양성률 {y[:cut].mean() * 100:.2f}% / test {y[cut:].mean() * 100:.2f}%"
    )

    mdl = RandomForestClassifier(
        n_estimators=300, random_state=SEED, n_jobs=-1, min_samples_leaf=2
    )
    mdl.fit(X[:cut], y[:cut])
    p = mdl.predict_proba(X[cut:])[:, 1]
    yt = y[cut:]

    # 비용 최소 임계값 (FN × 800만원 + FP × 30만원)
    ths = np.linspace(0.01, 0.99, 197)
    costs = []
    for t in ths:
        tn, fp, fn, tp = confusion_matrix(
            yt, (p >= t).astype(int), labels=[0, 1]
        ).ravel()
        costs.append(fn * COST_FN + fp * COST_FP)
    i = int(np.argmin(costs))
    th = float(ths[i])

    metrics = {
        "period": period,
        "data_start": str(d["ts"].iloc[0]),
        "data_end": str(d["ts"].iloc[-1]),
        "n_rows": int(len(d)),
        "n_features": len(feat),
        "horizon_min": HORIZON,
        "train_end": str(d["ts"].iloc[cut - 1]),
        "test_start": str(d["ts"].iloc[cut]),
        "positive_rate_test": round(float(yt.mean()), 4),
        "roc_auc": round(float(roc_auc_score(yt, p)), 4),
        "pr_auc": round(float(average_precision_score(yt, p)), 4),
        "threshold": round(th, 3),
        "precision": round(
            float(precision_score(yt, (p >= th).astype(int), zero_division=0)), 4
        ),
        "recall": round(
            float(recall_score(yt, (p >= th).astype(int), zero_division=0)), 4
        ),
        "f1": round(float(f1_score(yt, (p >= th).astype(int), zero_division=0)), 4),
        "cost_at_threshold": int(costs[i]),
        "cost_at_0.5": int(costs[int(np.argmin(np.abs(ths - 0.5)))]),
    }
    print("\n[성능]")
    for k, v in metrics.items():
        print(f"  {k:<20} {v}")

    imp = pd.Series(mdl.feature_importances_, index=feat).sort_values(ascending=False)
    print("\n[변수 중요도 상위 10]")
    print(imp.head(10).round(4).to_string())

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2)
    )
    imp.head(30).to_csv(outdir / "feature_importance.csv", header=["importance"])
    pd.DataFrame(
        {
            "ts": d["ts"].iloc[cut:].values,
            "machine_id": d["machine_id"].iloc[cut:].values,
            "y": yt,
            "prob": p,
        }
    ).to_csv(outdir / "test_predictions.csv", index=False)
    rel = outdir.relative_to(ROOT).as_posix()
    print(f"\n저장: {rel}/metrics.json, feature_importance.csv, test_predictions.csv")
    print("모델 파일(.pkl)은 저장하지 않음 → sklearn 버전이 다르면 읽기 실패 위험")
    print("  대시보드는 예측 결과 CSV를 사용, 재현은 이 스크립트 재실행")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
