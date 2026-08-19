"""
Real-time classifier for the oximeter stream.

Given the running window of recent samples, decide what a therapist is
actually looking at:

  VALID              - trustworthy reading, in a safe/expected range
  MOTION_ARTIFACT     - sensor slip / noise: erratic, low quality, self-reverting
  CONNECTIVITY_GAP    - no data (BLE/cellular dropout)
  GENUINE_DESAT       - sustained, physiologically plausible decline

Heuristics are intentionally simple and inspectable (not a black-box model) —
this is a V1 rules engine, not a diagnostic device. Thresholds are labeled
as assumptions, not clinical fact, and would need real clinician + data review
before this touched an actual patient.
"""

from collections import deque
from dataclasses import dataclass, field

# ---- Tunable thresholds (assumptions — flagged, not clinical fact) ----
LOW_QUALITY_THRESHOLD = 0.55          # below this, sensor itself is unsure
MAX_PHYSIOLOGIC_DELTA_PER_SEC = 4.0   # SpO2 can't realistically jump this fast
DESAT_ALERT_THRESHOLD = 90.0          # sustained SpO2 below this is a concern
DESAT_SUSTAINED_SECONDS = 20          # how long a real decline must hold
DESAT_MAX_NOISE = 1.0                 # real desat is smooth, not jittery


@dataclass
class ClassifiedSample:
    t: int
    raw: dict
    label: str
    reason: str


class SignalClassifier:
    def __init__(self, window_seconds=20):
        self.window = deque(maxlen=window_seconds)

    def classify(self, sample: dict) -> ClassifiedSample:
        t = sample["t"]

        # 1. No data at all -> connectivity gap, not a false reading.
        if not sample["connected"] or sample["spo2"] is None:
            result = ClassifiedSample(t, sample, "CONNECTIVITY_GAP",
                                       "No signal — device disconnected, not a clinical reading of zero.")
            self.window.append(result)
            return result

        spo2 = sample["spo2"]
        quality = sample["signal_quality"]

        # 2. Compare to the last valid-ish sample for rate-of-change sanity check.
        prev = self.window[-1] if self.window else None
        implausible_jump = False
        if prev is not None and prev.raw.get("spo2") is not None:
            delta = abs(spo2 - prev.raw["spo2"])
            if delta > MAX_PHYSIOLOGIC_DELTA_PER_SEC:
                implausible_jump = True

        # 3. Low sensor-reported quality + implausible jump = artifact signature.
        if quality is not None and quality < LOW_QUALITY_THRESHOLD and implausible_jump:
            result = ClassifiedSample(t, sample, "MOTION_ARTIFACT",
                                       f"Signal quality {quality:.2f} with implausible "
                                       f"{delta:.1f}%/s jump — sensor contact issue, not patient status.")
            self.window.append(result)
            return result

        # 4. Sustained, smooth, low reading over the window = genuine desat.
        recent_valid = [s for s in self.window if s.raw.get("spo2") is not None][-DESAT_SUSTAINED_SECONDS:]
        if len(recent_valid) >= DESAT_SUSTAINED_SECONDS:
            recent_vals = [s.raw["spo2"] for s in recent_valid] + [spo2]
            below_threshold = all(v < DESAT_ALERT_THRESHOLD for v in recent_vals)
            noise = max(recent_vals) - min(recent_vals)
            smooth_decline = recent_vals[0] - recent_vals[-1] > 0  # net downward
            if below_threshold and noise < (DESAT_ALERT_THRESHOLD * 0 + 6.0) and smooth_decline:
                result = ClassifiedSample(t, sample, "GENUINE_DESAT",
                                           f"SpO2 sustained below {DESAT_ALERT_THRESHOLD}% for "
                                           f"{DESAT_SUSTAINED_SECONDS}s+ with stable, smooth signal — "
                                           f"consistent with real desaturation, not artifact.")
                self.window.append(result)
                return result

        # 5. Otherwise, trust it.
        result = ClassifiedSample(t, sample, "VALID", "Reading within expected bounds and quality.")
        self.window.append(result)
        return result
