"""
경보 임계값 점검 (설계 문서 9장, D23)

mes-api의 경보 규칙을 예측 파일에 그대로 적용해 임계값별 경보 부담을 계산
- R5 연속 2회, 데이터 간격 2분 초과 시 연속 초기화
- R6 열린 경보가 있으면 새로 만들지 않음
- R7 경보 종료 후 30분 재발생 금지

실행 (저장소 루트에서)
    python mes-api/docs/threshold_check.py models/recent/test_predictions.csv

가정: 경보는 생성 후 30분 안에 처리되어 닫힘
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta

THRESHOLDS = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7]
CONSECUTIVE = 2       # R5
MAX_GAP_MIN = 2       # R5
HANDLE_MIN = 30       # 가정: 경보 처리 시간
COOLDOWN_MIN = 30     # R7


def load(path):
    """설비별 (시각, 확률, 정답) 목록, 시간순"""
    points = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ts = datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S")
            points[r["machine_id"]].append((ts, float(r["prob"]), int(r["y"])))
    for v in points.values():
        v.sort()
    return points


def failure_segments(pts):
    """정답 y=1이 이어지는 구간 (30분 안에 고장이 오는 구간) 목록"""
    segs, cur = [], None
    for ts, _, y in pts:
        if y == 1:
            cur = [ts, ts] if cur is None else [cur[0], ts]
        elif cur:
            segs.append(cur)
            cur = None
    if cur:
        segs.append(cur)
    return segs


def simulate(pts, threshold):
    """경보 생성 시각과 그 순간의 정답 목록"""
    created = []
    run, last = 0, None
    open_until, cooldown_until = None, None
    for ts, prob, y in pts:
        # 처리 시간이 지나면 경보 종료, 그때부터 재발생 금지
        if open_until and ts >= open_until:
            cooldown_until = open_until + timedelta(minutes=COOLDOWN_MIN)
            open_until = None
        if last and (ts - last).total_seconds() / 60 > MAX_GAP_MIN:
            run = 0
        last = ts
        if prob < threshold:
            run = 0
            continue
        run += 1
        if open_until:                                    # R6
            continue
        if run < CONSECUTIVE:                             # R5
            continue
        if cooldown_until and ts < cooldown_until:        # R7
            continue
        open_until = ts + timedelta(minutes=HANDLE_MIN)
        created.append((ts, y))
    return created


def main(path):
    points = load(path)
    all_ts = [ts for v in points.values() for ts, _, _ in v]
    days = (max(all_ts) - min(all_ts)).total_seconds() / 86400
    rows = sum(len(v) for v in points.values())
    print(f"{path}: {rows}행, {days:.2f}일, 설비 {len(points)}대")
    print(f"{'임계값':>6} | {'위험인 분':>7} | {'설비당 하루 경보':>10} | {'진짜 경보':>7} | {'고장 포착':>7}")

    for th in THRESHOLDS:
        above = sum(p >= th for v in points.values() for _, p, _ in v) / rows
        alarms = hits = segs_total = segs_caught = 0
        for pts in points.values():
            created = simulate(pts, th)
            alarms += len(created)
            hits += sum(y for _, y in created)
            segs = failure_segments(pts)
            segs_total += len(segs)
            segs_caught += sum(any(s <= ts <= e for ts, _ in created) for s, e in segs)
        per_day = alarms / len(points) / days
        precision = hits / alarms if alarms else 0
        recall = segs_caught / segs_total if segs_total else 0
        print(f"{th:>6.2f} | {above:>7.1%} | {per_day:>10.1f} | {precision:>7.1%} | {recall:>7.1%}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "models/recent/test_predictions.csv")
