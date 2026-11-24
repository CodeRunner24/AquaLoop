"""Synthetic hourly treatment-line monitoring and chronological alarm evaluation."""

from pathlib import Path
import csv
import json
import math
import random

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
HOURS_PER_DAY = 24
FIT_HOURS = 45 * HOURS_PER_DAY
TEST_START = 60 * HOURS_PER_DAY
PERSISTENCE = 2
MIN_PLANNED_FLOW = 0.08
CALIBRATION_QUANTILE = 0.97
NORMAL_WINDOW = {"id": "normal", "name": "Normal işletim", "window_start": 24, "window_end": 72}
# Events and their strengths are authored scenarios, never used to fit or tune either alarm.
FAULTS = (
    (96, 120, 0.25, 18, "Yavaş verim kaybı"),
    (249, 265, 0.38, 1, "Ani debi düşüşü"),
    (420, 450, 0.17, 25, "Hafif, kademeli verim kaybı"),
    (592, 620, 0.30, 20, "Uzun süreli debi düşüşü"),
)


def synthetic_telemetry(records):
    rng = random.Random(2306)
    rows = []
    raw, clean = 4.2, 2.8
    for hour, row in enumerate(records):
        raw = min(12.0, raw + row["greywater_in_m3"])
        forecast = row["forecast_nonpotable_m3"]
        next_forecast = records[min(hour + 1, len(records) - 1)]["forecast_nonpotable_m3"]
        target = max(0.05, 1.12 * forecast + 0.15 * max(0.0, next_forecast - forecast))
        plan = min(2.2, target, raw, 8.0 - clean)
        raw_fill, clean_fill = raw / 12.0, clean / 8.0

        loss = 0.0
        for start, end, maximum, ramp, _ in FAULTS:
            elapsed = hour - TEST_START - start
            if 0 <= elapsed < end - start:
                loss = maximum * min(1.0, (elapsed + 1) / ramp)
                break

        flow_factor = 0.94 + 0.025 * raw_fill - 0.035 * clean_fill
        true_treated = max(0.0, min(plan, plan * flow_factor * (1 + rng.gauss(0, 0.024)) * (1 - loss)))
        power_rate = 0.39 + 0.17 * (1 - raw_fill) + 0.12 * clean_fill
        power = (0.11 + plan * power_rate) * (1 + rng.gauss(0, 0.035)) * (1 + 0.30 * loss)
        power = max(0.0, power) if plan > 0.02 else 0.0
        measured_treated = max(0.0, true_treated + rng.gauss(0, 0.007)) if plan > 0.02 else 0.0
        raw -= true_treated
        clean += true_treated
        reuse = min(row["nonpotable_demand_m3"], clean)
        clean -= reuse

        rows.append({
            "hour": hour - TEST_START,
            "planned_m3": plan,
            "treated_m3": measured_treated,
            "pump_kwh": power,
            "raw_fill": raw_fill,
            "clean_fill": clean_fill,
            "fault": loss > 0.0,
        })
    return rows


def operating_features(row):
    plan = row["planned_m3"]
    return [1, plan, plan * row["raw_fill"], plan * row["clean_fill"]]


def persistent_flags(scores, threshold):
    count = 0
    flagged = []
    for score in scores:
        count = count + 1 if score is not None and score > threshold else 0
        flagged.append(count >= PERSISTENCE)
    return flagged


def build_diagnostics(records):
    rows = synthetic_telemetry(records)
    eligible = [row["planned_m3"] >= MIN_PLANNED_FLOW for row in rows]
    fit_rows = [row for row, active in zip(rows[:FIT_HOURS], eligible[:FIT_HOURS]) if active]
    features = np.array([operating_features(row) for row in fit_rows])
    targets = np.array([[row["treated_m3"], row["pump_kwh"]] for row in fit_rows])
    weights = np.linalg.lstsq(features, targets, rcond=None)[0]
    predictions = np.array([operating_features(row) for row in rows]) @ weights
    observed = np.array([[row["treated_m3"], row["pump_kwh"]] for row in rows])
    deviations = (observed - predictions) * [-1, 1]
    calibration_active = np.array(eligible[FIT_HOURS:TEST_START])
    calibration_deviation = deviations[FIT_HOURS:TEST_START][calibration_active]
    scale = np.maximum(np.std(calibration_deviation, axis=0), [0.007, 0.009])
    anomaly_score = np.max(deviations / scale, axis=1)
    ai_scores = [float(score) if active else None for score, active in zip(anomaly_score, eligible)]
    fixed_scores = [row["pump_kwh"] / max(row["treated_m3"], 0.01) if active else None for row, active in zip(rows, eligible)]

    thresholds = {}
    for name, scores in (("fixed", fixed_scores), ("ai", ai_scores)):
        calibration = [s for s in scores[FIT_HOURS:TEST_START] if s is not None]
        thresholds[name] = float(np.quantile(calibration, CALIBRATION_QUANTILE))
        for row, flag in zip(rows, persistent_flags(scores, thresholds[name])):
            row[name + "_alarm"] = flag

    for row, (flow, power), score in zip(rows, predictions, fixed_scores):
        row["expected_m3"] = max(0.0, float(flow)) if row["planned_m3"] > 0.02 else 0.0
        row["expected_kwh"] = max(0.0, float(power)) if row["planned_m3"] > 0.02 else 0.0
        row["specific_kwh_m3"] = score

    test = rows[TEST_START:]
    events = []
    for i, (start, end, _, _, name) in enumerate(FAULTS, 1):
        event = {"id": f"fault-{i}", "name": name, "start": start, "end": end,
                 "window_start": max(0, start - 12), "window_end": min(len(test), end + 8)}
        for detector in ("fixed", "ai"):
            # A false alarm already active before onset cannot count as detecting the event.
            event[detector + "_delay"] = next((
                j - start for j in range(start, end)
                if test[j][detector + "_alarm"] and (j == 0 or not test[j - 1][detector + "_alarm"])
            ), None)
        events.append(event)

    summary = {"fit_days": 45, "calibration_days": 15, "test_days": 30,
               "test_fault_hours": sum(row["fault"] for row in test),
               "persistence": PERSISTENCE, "thresholds": thresholds, "normal": NORMAL_WINDOW,
               "events": events, "detectors": {}}
    for detector in ("fixed", "ai"):
        delays = [event[detector + "_delay"] for event in events if event[detector + "_delay"] is not None]
        summary["detectors"][detector] = {
            "detected": len(delays), "total_events": len(events),
            "false_alarm_hours": sum(row[detector + "_alarm"] and not row["fault"] for row in test),
            "mean_delay_h": sum(delays) / len(delays) if delays else None,
        }

    for row in test:
        for field, value in row.items():
            if isinstance(value, float) and math.isfinite(value):
                row[field] = round(value, 5)
    return summary, test


def write_diagnostics(summary, rows):
    output = ROOT / "outputs"
    (output / "process_benchmark.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "process_diagnostics.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
