"""
Simulates a per-second Bluetooth pulse oximeter data stream during a live
pulmonary rehab exercise session.

This is synthetic data built from publicly documented clinical patterns
(exertional dips, motion artifact behavior, BLE dropout), NOT real Kivo data.
The point is to give the classifier realistic failure modes to distinguish.

Each sample: {t, spo2, pulse, signal_quality, connected}
  - spo2: percent, None if disconnected
  - signal_quality: 0-1 confidence score reported by the sensor itself
  - connected: bool, False during a BLE/cellular dropout
"""

import random
import math


def _clean_baseline(t, duration, start_spo2=96.0, exertion_dip=2.5):
    """Normal exercise session: gentle exertion-driven dip and recovery,
    small realistic noise, high signal quality."""
    # exertion ramps up mid-session then eases — a smooth sinusoidal dip
    phase = t / duration * math.pi
    dip = exertion_dip * math.sin(phase)
    spo2 = start_spo2 - dip + random.uniform(-0.3, 0.3)
    spo2 = max(88.0, min(99.0, spo2))
    quality = random.uniform(0.90, 0.99)
    pulse = 78 + 15 * math.sin(phase) + random.uniform(-2, 2)
    return spo2, quality, pulse


def generate_session(total_seconds=600, seed=7):
    """
    Builds one simulated session with a mix of segment types so the
    classifier has real ambiguity to resolve. Segment layout (seconds):
      0-150   clean baseline
      150-165 motion artifact burst (erratic, self-reverting)
      165-300 clean baseline
      300-330 connectivity dropout (BLE/cellular gap)
      330-420 clean baseline
      420-480 genuine desaturation trend (sustained, plausible decline)
      480-540 clean recovery
      540-600 second short motion artifact
    """
    random.seed(seed)
    stream = []
    t = 0
    while t < total_seconds:
        if 150 <= t < 165:
            # Motion artifact: fast, large, physiologically implausible swings
            # that revert quickly — classic sensor-slip signature.
            spo2 = random.choice([random.uniform(65, 78), random.uniform(99, 100)])
            quality = random.uniform(0.15, 0.45)
            pulse = random.uniform(40, 180)
            connected = True

        elif 300 <= t < 330:
            # Connectivity dropout: no data at all, not a fake low reading.
            spo2, quality, pulse = None, None, None
            connected = False

        elif 420 <= t < 480:
            # Genuine desaturation: smooth, sustained, monotonic-ish decline,
            # high signal quality (sensor is working fine — patient isn't).
            progress = (t - 420) / 60.0
            spo2 = 95.0 - (10.0 * progress) + random.uniform(-0.2, 0.2)
            quality = random.uniform(0.90, 0.98)
            pulse = 110 + 20 * progress + random.uniform(-2, 2)
            connected = True

        elif 540 <= t < 552:
            spo2 = random.choice([random.uniform(70, 80), random.uniform(98, 100)])
            quality = random.uniform(0.15, 0.45)
            pulse = random.uniform(45, 175)
            connected = True

        else:
            spo2, quality, pulse = _clean_baseline(t, total_seconds)
            connected = True

        stream.append({
            "t": t,
            "spo2": round(spo2, 1) if spo2 is not None else None,
            "pulse": round(pulse, 1) if pulse is not None else None,
            "signal_quality": round(quality, 2) if quality is not None else None,
            "connected": connected,
        })
        t += 1

    return stream


if __name__ == "__main__":
    session = generate_session()
    print(f"Generated {len(session)} samples")
    for row in session[145:170]:
        print(row)
