"""
정제 파이프라인 (오염 주입의 역순으로 처리)

1) 타입 강제
2) 타임스탬프 분 단위 정렬 (흔들린 행은 가까운 빈 분으로)
3) 중복 제거 (machine_id, ts 기준)
4) 단위 통일 (온도 ℃→K, 진동 m/s²→mm/s)
5) 물리 범위 밖 값 → NaN (행은 유지)
6) 스파이크 플래그 (Hampel, 삭제하지 않음)
7) 짧은 결측 보간 (연속 5개 이하)
8) 드리프트 보정 (설비 간 비교)
9) 시간축 재색인 (끊김 구간을 NaN 행으로 표시)

단계별 행 수는 StepLog에 기록.
"""

from __future__ import annotations

import bisect

import numpy as np
import pandas as pd

SENSOR_COLS = [
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "vibration_mms",
    "current_a",
    "humidity_pct",
]

# 물리적으로 가능한 범위 (설비 스펙 + 상식)
PHYS_RANGE = {
    "air_temp_k": (270.0, 340.0),  # -3 ~ 67 도
    "process_temp_k": (280.0, 360.0),
    "rot_speed_rpm": (500.0, 4000.0),
    "torque_nm": (1.0, 100.0),
    "tool_wear_min": (0.0, 400.0),
    "vibration_mms": (0.05, 30.0),  # ISO 10816: 11 mm/s 초과면 위험
    "current_a": (0.1, 40.0),
    "humidity_pct": (0.0, 100.0),
}


class StepLog:
    """단계별 행 수와 증감 기록"""

    def __init__(self):
        self.rows = []

    def __call__(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        prev = self.rows[-1][1] if self.rows else len(df)
        self.rows.append((name, len(df), len(df) - prev))
        return df

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows, columns=["단계", "행수", "증감"])


# 1~3. 타입 · 중복 · 타임스탬프


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    for c in SENSOR_COLS + ["machine_failure"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["ts", "machine_id"])


MAX_JITTER_SEC = 90  # 시각 흔들림 허용 범위. 이보다 멀리 떨어진 분에는 배정하지 않음


def _stable_order(df: pd.DataFrame) -> pd.DataFrame:
    """입력 순서와 무관하게 항상 같은 순서로 정렬 (환경이 달라도 결과가 같도록)"""
    keys = ["machine_id", "ts"] + [c for c in SENSOR_COLS if c in df.columns]
    return df.sort_values(keys, kind="mergesort", na_position="last")


def snap_timestamp(df: pd.DataFrame, max_jitter_sec: int = MAX_JITTER_SEC) -> pd.DataFrame:
    """초 단위로 흔들린 ts를 분 격자에 맞춤

    단순 반올림은 30초 넘게 흔들린 행을 이웃 분으로 보내 진짜 행과 겹치게 만듦.
    1) 정각(초=0)으로 들어온 행은 제자리로 확정
    2) 흔들린 행은 max_jitter_sec 안에서 가장 가까운 빈 분에 배정
    3) 값이 완전히 같고 시각 차이가 max_jitter_sec 이내인 행만 재전송으로 보고 같은 분에 묶음
       (3단계에서 하나만 남김). 설비 정지처럼 값이 몇 분간 같은 정상 행은 묶지 않음
    4) 정각 행끼리는 따로 둠. 단, 한 분에 값이 다른 정각 행이 둘 이상 겹치면(±60초 흔들림),
       90초 안에 같은 값의 다른 정각 행이 있는 쪽을 재전송으로 봄
    """
    df = _stable_order(df.copy())
    if df.empty:
        return df
    vals = ["machine_id"] + [c for c in SENSOR_COLS + ["machine_failure"] if c in df.columns]
    key = pd.util.hash_pandas_object(df[vals], index=False).to_numpy()
    ts_ns = df["ts"].to_numpy().astype("datetime64[ns]").astype(np.int64)
    mid = df["machine_id"].to_numpy()
    on_minute = (df["ts"] == df["ts"].dt.floor("min")).to_numpy()
    MIN = 60 * 10**9
    limit = max_jitter_sec * 10**9

    group_minute: dict = {}  # 묶음 id → 배정된 분(ns), 흔들린 묶음은 배정 전 None
    group_of = [None] * len(df)
    by_key: dict = {}  # 값 key → (시각 목록, 묶음 id 목록), 시각순 정렬 유지

    def nearest_group(k, t):
        """같은 값 key 중 t에서 limit 이내인 가장 가까운 묶음"""
        if k not in by_key:
            return None
        times, gids = by_key[k]
        lo = bisect.bisect_left(times, t - limit)
        best = None
        for j in range(lo, len(times)):
            if times[j] > t + limit:
                break
            d = abs(times[j] - t)
            if best is None or d < best[0]:
                best = (d, gids[j])
        return None if best is None else best[1]

    def add_group(k, t, gid, minute):
        group_minute[gid] = minute
        times, gids = by_key.setdefault(k, ([], []))
        j = bisect.bisect_right(times, t)
        times.insert(j, t)
        gids.insert(j, gid)

    anchors = np.flatnonzero(on_minute)
    keys_at: dict = {}
    for i in anchors:
        keys_at.setdefault((mid[i], ts_ns[i]), set()).add(key[i])
    contested = {mk for mk, ks in keys_at.items() if len(ks) > 1}

    # 정각 행: 겹치지 않은 분 먼저 확정
    for i in anchors:
        if (mid[i], ts_ns[i]) in contested:
            continue
        gid = ("a", mid[i], ts_ns[i], key[i])
        if gid not in group_minute:
            add_group(key[i], ts_ns[i], gid, ts_ns[i])
        group_of[i] = gid
    # 겹친 분의 정각 행: 90초 안에 같은 값 정각 행이 있으면 그 재전송으로 봄
    for i in anchors:
        if (mid[i], ts_ns[i]) not in contested:
            continue
        g = nearest_group(key[i], ts_ns[i])
        if g is None:
            g = ("a", mid[i], ts_ns[i], key[i])
            if g not in group_minute:
                add_group(key[i], ts_ns[i], g, ts_ns[i])
        group_of[i] = g

    # 흔들린 행: 90초 안에 같은 값 묶음이 있으면 합류, 없으면 새 묶음
    pending = []
    for i in np.flatnonzero(~on_minute):
        g = nearest_group(key[i], ts_ns[i])
        if g is None:
            g = ("j", i)
            add_group(key[i], ts_ns[i], g, None)
            t = int(ts_ns[i])
            off = min(t % MIN, MIN - t % MIN)  # 가장 가까운 정각까지 거리
            pending.append((off, mid[i], t, g))
        group_of[i] = g

    occupied = {(m, v) for (m, v) in ((g[1], mn) for g, mn in group_minute.items() if g[0] == "a")}
    pending.sort(key=lambda x: (x[0], x[1], x[2]))  # 분에 가까운 행부터 배정
    for _, m, t, g in pending:
        base = t - t % MIN
        cands = [base + s * MIN for s in (-1, 0, 1, 2)]
        cands = sorted((c for c in cands if abs(c - t) <= limit), key=lambda c: (abs(c - t), c))
        chosen = next((c for c in cands if (m, c) not in occupied), None)
        if chosen is None:  # 빈 분이 없으면 반올림 (3단계에서 겹친 행 정리)
            chosen = int(pd.Timestamp(t).round("min").value)
        group_minute[g] = chosen
        occupied.add((m, chosen))

    df["ts"] = pd.to_datetime(np.array([group_minute[g] for g in group_of], dtype=np.int64))
    return df


def drop_dups(df: pd.DataFrame) -> pd.DataFrame:
    """(machine_id, ts) 중복 제거. 값이 다르면 나중에 수집된 것을 유지(재전송을 정정본으로 가정)"""
    return (
        _stable_order(df)
        .sort_values("collected_at", kind="mergesort")
        .drop_duplicates(subset=["machine_id", "ts"], keep="last")
        .sort_values(["machine_id", "ts"], kind="mergesort")
        .reset_index(drop=True)
    )


# 4. 단위 통일


def detect_and_fix_temp_unit(df: pd.DataFrame, cols=("air_temp_k", "process_temp_k")):
    """200 K 미만 온도는 섭씨로 판단해 켈빈으로 변환

    공장 실내가 -73℃ 이하일 수 없다는 물리적 기준 사용
    """
    df = df.copy()
    report = {}
    for c in cols:
        if c not in df.columns:
            continue
        mask = df[c].notna() & (df[c] < 200)
        report[c] = int(mask.sum())
        df.loc[mask, c] = df.loc[mask, c] + 273.15
    return df, report


def detect_vibration_unit(
    df: pd.DataFrame, col="vibration_mms", factor=9.81, ratio=4.0
):
    """설비별 중앙값의 ratio배를 넘는 진동은 m/s²로 판단해 mm/s로 변환.

    통계적 추정이라 온도보다 불확실함. 단위 메타데이터가 있으면 그쪽을 우선
    """
    df = df.copy()
    med = df.groupby("machine_id")[col].transform("median")
    mask = df[col].notna() & (df[col] > med * ratio)
    df.loc[mask, col] = df.loc[mask, col] / factor
    return df, int(mask.sum())


# 5. 물리 범위 검사


def range_check(df: pd.DataFrame, rng: dict | None = None):
    """물리 범위 밖 값을 NaN으로 변경. 같은 시각의 다른 센서값을 살리기 위해 행은 삭제하지 않음"""
    rng = rng or PHYS_RANGE
    df = df.copy()
    report = {}
    for c, (lo, hi) in rng.items():
        if c not in df.columns:
            continue
        bad = df[c].notna() & ~df[c].between(lo, hi)
        report[c] = int(bad.sum())
        df.loc[bad, c] = np.nan
    return df, report


# 6. 스파이크 탐지 (Hampel)


def hampel_flag(s: pd.Series, window: int = 11, n_sigma: float = 5.0) -> pd.Series:
    """이동 중앙값에서 n_sigma x MAD 이상 벗어난 점을 True로 표시

    표준편차 대신 MAD 사용: 스파이크가 표준편차를 부풀려 기준이 무너지는 것을 방지
    """
    med = s.rolling(window, center=True, min_periods=3).median()
    mad = (s - med).abs().rolling(window, center=True, min_periods=3).median()
    sigma = 1.4826 * mad
    sigma = sigma.replace(0, np.nan)
    return ((s - med).abs() > n_sigma * sigma).fillna(False)


def flag_spikes(df: pd.DataFrame, cols=None, window=11, n_sigma=5.0):
    """센서별 스파이크 플래그 컬럼 추가. 고장 신호일 수 있어 값은 삭제하지 않음"""
    cols = cols or SENSOR_COLS
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            continue
        df[f"spike_{c}"] = df.groupby("machine_id")[c].transform(
            lambda s: hampel_flag(s, window, n_sigma)
        )
    spike_cols = [f"spike_{c}" for c in cols if f"spike_{c}" in df.columns]
    df["spike_any"] = df[spike_cols].any(axis=1)
    df["spike_count"] = df[spike_cols].sum(axis=1)
    return df


# 7. 결측 보간


def interpolate_short_gaps(df: pd.DataFrame, cols=None, max_gap: int = 5):
    """연속 max_gap개 이하의 결측만 선형 보간

    긴 끊김을 채우면 없던 데이터를 만들어내므로 그대로 둠
    """
    cols = cols or SENSOR_COLS
    df = df.sort_values(["machine_id", "ts"]).copy()
    filled = {}
    for c in cols:
        if c not in df.columns:
            continue
        before = df[c].isna().sum()
        df[c] = df.groupby("machine_id")[c].transform(
            lambda s: s.interpolate(
                method="linear", limit=max_gap, limit_direction="both"
            )
        )
        filled[c] = int(before - df[c].isna().sum())
    return df, filled


# 8. 드리프트 보정


def estimate_drift(df: pd.DataFrame, col="process_temp_k", ref="air_temp_k"):
    """설비별 (col - ref) 일별 중앙값을 라인 전체 중앙값과 비교해 하루당 밀림(기울기) 추정

    전 설비가 같이 변하면 공정 변화, 한 대만 변하면 센서 드리프트로 판단
    """
    d = df.dropna(subset=[col, ref]).copy()
    d["diff"] = d[col] - d[ref]
    d["day"] = (d["ts"] - d["ts"].min()).dt.total_seconds() / 86400.0
    daily = (
        d.groupby(["machine_id", d["day"].astype(int)])["diff"]
        .median()
        .rename("v")
        .reset_index()
        .rename(columns={"day": "d"})
    )
    fleet = daily.groupby("d")["v"].median().rename("fleet")
    daily = daily.join(fleet, on="d")
    daily["resid"] = daily["v"] - daily["fleet"]

    out = {}
    for m, g in daily.groupby("machine_id"):
        if len(g) < 3:
            out[m] = 0.0
            continue
        slope = np.polyfit(g["d"], g["resid"], 1)[0]
        out[m] = float(slope)
    return out, daily


def correct_drift(
    df: pd.DataFrame, slopes: dict, col="process_temp_k", min_slope: float = 0.05
):
    """기울기가 min_slope 이상인 설비만 경과 일수만큼 보정"""
    df = df.copy()
    t0 = df["ts"].min()
    days = (df["ts"] - t0).dt.total_seconds() / 86400.0
    applied = {}
    for m, s in slopes.items():
        if abs(s) < min_slope:
            applied[m] = 0.0
            continue
        mask = df["machine_id"] == m
        df.loc[mask, col] = df.loc[mask, col] - s * days[mask]
        applied[m] = s
    return df, applied


# 9. 시간축 재색인


def reindex_time(df: pd.DataFrame, freq: str = "min") -> pd.DataFrame:
    """설비별로 분 단위 전체 시간축을 만들어 빠진 분을 NaN 행으로 추가. is_gap 컬럼으로 표시"""
    parts = []
    for m, g in df.groupby("machine_id"):
        g = g.set_index("ts").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq=freq)
        g2 = g.reindex(full)
        g2["is_gap"] = g2["machine_id"].isna()
        g2["machine_id"] = m
        g2["type"] = g["type"].iloc[0] if "type" in g.columns else None
        g2.index.name = "ts"
        parts.append(g2.reset_index())
    return pd.concat(parts, ignore_index=True).sort_values(["ts", "machine_id"])


# 전체 파이프라인


def run_pipeline(raw: pd.DataFrame, verbose: bool = True):
    log = StepLog()
    rep = {}

    df = log("0. 원본 수신", raw.copy())
    df = log("1. 타입 강제", coerce_types(df))
    df = log("2. 타임스탬프 스냅", snap_timestamp(df))
    df = log("3. 중복 제거", drop_dups(df))

    df, rep["temp_unit"] = detect_and_fix_temp_unit(df)
    df = log("4a. 온도 단위 통일", df)
    df, rep["vib_unit"] = detect_vibration_unit(df)
    df = log("4b. 진동 단위 통일", df)

    df, rep["range"] = range_check(df)
    df = log("5. 물리범위 → NaN", df)

    df = flag_spikes(df)
    df = log("6. 스파이크 플래그", df)

    df, rep["filled"] = interpolate_short_gaps(df)
    df = log("7. 짧은 결측 보간", df)

    slopes, rep["drift_daily"] = estimate_drift(df)
    rep["drift_slopes"] = slopes
    df, rep["drift_applied"] = correct_drift(df, slopes)
    df = log("8. 드리프트 보정", df)

    df = reindex_time(df)
    df = log("9. 시간축 재색인", df)

    if verbose:
        print(log.frame().to_string(index=False))
    return df, log, rep
