"""
전체 재현 스크립트

    python run_all.py

데이터 다운로드 → DB 재생성 → 모델 학습(2024년 기준) → 분석 a1~a8 순서로 실행
각 단계 출력은 outputs/ 에 저장
센서 수집은 GitHub Actions 담당이라 여기서는 실행하지 않음
"""

import os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

STEPS = [
    ("데이터 다운로드", [sys.executable, "src/download_data.py"], None),
    ("DB 재생성", [sys.executable, "src/build_db.py"], None),
    ("모델 학습", [sys.executable, "src/train.py"], "train_output.txt"),
]
for name in [
    "a1_pipeline",
    "a2_ai4i",
    "a3_leakage",
    "a4_outlier_trap",
    "a5_drift",
    "a6_cost_threshold",
    "a7_secom",
    "a8_quality_metrics",
]:
    STEPS.append(
        (f"분석 {name}", [sys.executable, f"{name}.py"], f"{name[:2]}_output.txt")
    )


def main() -> int:
    fails = []
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
    }  # 자식 출력을 UTF-8로 (Windows cp949 오류 방지)
    for name, cmd, logfile in STEPS:
        cwd = (
            ROOT / "analysis"
            if cmd[1].startswith("a") and cmd[1].endswith(".py")
            else ROOT
        )
        t0 = time.time()
        print(f"\n{'=' * 60}\n▶ {name}\n{'=' * 60}", flush=True)
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        out = r.stdout + r.stderr
        if logfile:
            (OUT / logfile).write_text(out, encoding="utf-8")
        print(out[-1500:] if len(out) > 1500 else out)
        status = "OK" if r.returncode == 0 else f"FAIL({r.returncode})"
        print(f"  → {status}  {time.time() - t0:.1f}s")
        if r.returncode != 0:
            fails.append(name)
    print(f"\n{'=' * 60}")
    print(f"완료 | 실패 {len(fails)}건" + (f": {fails}" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
