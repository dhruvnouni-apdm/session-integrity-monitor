import matplotlib.pyplot as plt
from oximeter_sim import generate_session
from session_monitor import SessionMonitor

COLORS = {
    "VALID": "#2E7D32",
    "MOTION_ARTIFACT": "#F9A825",
    "CONNECTIVITY_GAP": "#9E9E9E",
    "GENUINE_DESAT": "#C62828",
}
LABELS = {
    "VALID": "Valid reading",
    "MOTION_ARTIFACT": "Motion artifact (suppressed)",
    "CONNECTIVITY_GAP": "Connectivity gap (no data)",
    "GENUINE_DESAT": "Genuine desaturation (alerted)",
}

def main():
    stream = generate_session(total_seconds=600, seed=7)
    monitor = SessionMonitor()
    log, alerts = monitor.process(stream)

    fig, ax = plt.subplots(figsize=(13, 5))

    for label in COLORS:
        ts = [r.t for r in log if r.label == label and r.raw.get("spo2") is not None]
        vals = [r.raw["spo2"] for r in log if r.label == label and r.raw.get("spo2") is not None]
        ax.scatter(ts, vals, s=10, c=COLORS[label], label=LABELS[label], zorder=3)

    for a in alerts:
        ax.axvline(a["t"], color="black", linestyle="--", linewidth=1, alpha=0.6)
        ax.annotate(a["type"].replace("_", " ").title(), xy=(a["t"], 100),
                    rotation=90, fontsize=8, va="top", ha="right")

    ax.axhline(90, color="red", linestyle=":", linewidth=1, alpha=0.5)
    ax.text(5, 90.5, "Clinical desat threshold (90%)", fontsize=8, color="red")

    ax.set_xlabel("Session time (seconds)")
    ax.set_ylabel("SpO2 (%)")
    ax.set_title("Kivo Session Integrity Monitor — classified oximeter stream\n"
                  "(simulated session; not real patient data)")
    ax.set_ylim(60, 105)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig("session_trace.png", dpi=150)
    print("Saved session_trace.png")

if __name__ == "__main__":
    main()
