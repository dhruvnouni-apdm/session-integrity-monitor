"""
Ties the classifier to escalation behavior and produces the audit trail.

Design intent (from the problem doc):
  - Only GENUINE_DESAT should ever reach the therapist as an actionable alert.
  - MOTION_ARTIFACT and CONNECTIVITY_GAP are logged but NOT alerted on their own
    (that's the alert-fatigue trap) — UNLESS a connectivity gap runs long enough
    that "we simply don't know" becomes its own risk worth flagging.
  - Every second is logged, so after the session there's a complete,
    gap-explained record — the audit trail piece from the problem doc.
"""

import json
from classifier import SignalClassifier

CONNECTIVITY_GAP_ALERT_SECONDS = 15  # if we lose signal this long, flag it too


class SessionMonitor:
    def __init__(self):
        self.classifier = SignalClassifier()
        self.log = []
        self.alerts = []
        self._gap_start = None
        self._active_desat_alert = False  # debounce: one alert per sustained event

    def process(self, stream):
        for sample in stream:
            result = self.classifier.classify(sample)
            self.log.append(result)
            self._handle_escalation(result)
        return self.log, self.alerts

    def _handle_escalation(self, result):
        if result.label == "GENUINE_DESAT":
            if not self._active_desat_alert:
                self.alerts.append({
                    "t": result.t,
                    "type": "CLINICAL_ALERT",
                    "message": f"[t={result.t}s] Sustained desaturation detected. {result.reason}",
                })
                self._active_desat_alert = True
        else:
            self._active_desat_alert = False

        if result.label == "CONNECTIVITY_GAP":
            if self._gap_start is None:
                self._gap_start = result.t
            gap_duration = result.t - self._gap_start
            if gap_duration == CONNECTIVITY_GAP_ALERT_SECONDS:
                self.alerts.append({
                    "t": result.t,
                    "type": "MONITORING_GAP_ALERT",
                    "message": f"[t={result.t}s] No signal for {gap_duration}s+ — "
                               f"monitoring integrity compromised, therapist should "
                               f"verbally check on patient.",
                })
        else:
            self._gap_start = None

    # ---- Metrics matching the problem doc's success metrics ----
    def summary(self):
        total = len(self.log)
        counts = {}
        for r in self.log:
            counts[r.label] = counts.get(r.label, 0) + 1

        unresolved_gap_seconds = counts.get("CONNECTIVITY_GAP", 0)
        clinical_alerts = [a for a in self.alerts if a["type"] == "CLINICAL_ALERT"]
        gap_alerts = [a for a in self.alerts if a["type"] == "MONITORING_GAP_ALERT"]

        return {
            "total_seconds": total,
            "label_breakdown": counts,
            "pct_time_unresolved_gap": round(100 * unresolved_gap_seconds / total, 1),
            "clinical_alerts_raised": len(clinical_alerts),
            "monitoring_gap_alerts_raised": len(gap_alerts),
            "pct_session_valid_signal": round(100 * counts.get("VALID", 0) / total, 1)
                                         + round(100 * counts.get("GENUINE_DESAT", 0) / total, 1),
            "audit_log_complete": True,  # every second has a labeled entry, by construction
        }

    def export_audit_log(self, path):
        payload = [
            {
                "t": r.t,
                "label": r.label,
                "reason": r.reason,
                "spo2": r.raw.get("spo2"),
                "signal_quality": r.raw.get("signal_quality"),
            }
            for r in self.log
        ]
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
