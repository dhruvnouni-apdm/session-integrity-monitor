from oximeter_sim import generate_session
from session_monitor import SessionMonitor

def main():
    print("=" * 70)
    print("KIVO SESSION INTEGRITY MONITOR — simulated session")
    print("=" * 70)

    stream = generate_session(total_seconds=600, seed=7)
    monitor = SessionMonitor()
    log, alerts = monitor.process(stream)

    print("\n--- What the therapist actually sees (alerts only) ---")
    if not alerts:
        print("No alerts raised.")
    for a in alerts:
        tag = "🔴 CLINICAL" if a["type"] == "CLINICAL_ALERT" else "🟡 GAP"
        print(f"{tag}  {a['message']}")

    print("\n--- What did NOT alert the therapist (and why that's correct) ---")
    artifact_windows = [r.t for r in log if r.label == "MOTION_ARTIFACT"]
    if artifact_windows:
        print(f"Motion artifact detected at t={artifact_windows[0]}-{artifact_windows[-1]}s "
              f"({len(artifact_windows)} samples) — suppressed as noise, not a clinical event.")

    print("\n--- Session summary metrics (from the problem doc) ---")
    summary = monitor.summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")

    monitor.export_audit_log("audit_log.json")
    print("\nFull second-by-second audit log written to audit_log.json")

if __name__ == "__main__":
    main()
