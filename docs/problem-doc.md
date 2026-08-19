# Problem Doc: Physiologic Signal Integrity in Live Remote Rehab Sessions

**Case study used:** Kivo Health (telehealth pulmonary rehab) · **Type:** Outside-in PM exercise based on public info only — not internal data.

**Problem.** Kivo's live sessions rely on a Bluetooth pulse oximeter streamed through a cellular tablet so therapists can watch oxygen saturation while coaching exercise. But COPD patients desaturate specifically *during* exertion, and Bluetooth sensors are prone to motion-artifact dropout during exactly that kind of movement. Today there's no way for the system to tell a therapist *why* a reading looks bad — sensor slipped, connection dropped, or the patient is genuinely desaturating all look the same.

**Why now.** At small scale, an attentive senior therapist can use judgment to fill that gap. That assumption breaks as Kivo scales from 9 to 50 states with a larger, more distributed, more junior therapist pool. The risk isn't a visible bug — it's a scaling assumption that quietly stops holding. It also creates liability exposure (ambiguous monitoring record if an adverse event occurs) and audit exposure (can't prove continuous monitoring for a billed, supervised session).

**Proposed V1.** A signal-integrity layer between the raw oximeter feed and the therapist view:
1. Classify readings in real time — valid / motion artifact / connectivity gap / genuine desat trend
2. Escalate only genuine risk, to avoid alert fatigue from artifact noise
3. Log a timestamped, gap-explained audit trail per session

**Success metrics.** % sessions with unresolved (unexplained) signal gaps · time-to-acknowledgment for real desat events · false-alert rate · % sessions with a complete audit log.

**Honesty check.** This may already be solved internally — I have no visibility into their actual pipeline. The point isn't "found a bug," it's demonstrating how I reason about risk in a clinical product from the outside, backed by a working prototype.

**Next step.** Build the classification logic on simulated oximeter data (clean / artifact / dropout / real desat), then wrap it in a minimal therapist-facing session view.
