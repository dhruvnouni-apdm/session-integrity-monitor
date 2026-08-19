# Session Integrity Monitor

**A product exercise: identifying a non-obvious clinical safety risk in remote physiologic monitoring, and prototyping a fix.**

🔗 **[Live demo](https://dhruvnouni-apdm.github.io/session-integrity-monitor/)** — click "Start session" to watch it run.

---

## The problem

Telehealth programs that combine live video coaching with wearable vital-sign sensors (pulse oximeters, heart-rate monitors, etc.) share a structural weak point: the sensor is most likely to lose signal or produce artifact noise during the exact activity — physical exertion — that also makes a genuine adverse event more likely. When that happens, the person supervising the session has no built-in way to tell "the sensor slipped" apart from "something is actually wrong." At small scale, an attentive, senior clinical staff can use judgment to fill that gap. That assumption gets riskier fast as a program scales to more patients, more staff, and less shared context per session.

**Full problem framing:** [`docs/problem-doc.md`](docs/problem-doc.md)

## Case study: Kivo Health

This project was prompted by [Kivo Health](https://kivohealth.com), a telehealth pulmonary rehab company that ships patients a Bluetooth pulse oximeter paired to a cellular tablet, with therapists monitoring oxygen saturation live during exercise sessions. It's a real, public example of exactly this architecture, used here as the concrete case that motivated the build — not because of any confirmed gap in their product. Everything here is built from public information only (their site, YC launch post, press), not internal data or insider knowledge. The same reasoning applies to any telehealth program with a similar sensor + live-supervision model.

## What's in this repo

| File | What it is |
|---|---|
| `index.html` | Interactive session-monitor dashboard — live session view, alerts, and session audit trail. This is the live demo. |
| `docs/problem-doc.md` | The PM problem framing: why this matters, success metrics, scope, risks. |
| `python/oximeter_sim.py` | Simulates a realistic oximeter data stream (clean signal, motion artifact, connectivity dropout, genuine desaturation). |
| `python/classifier.py` | The core logic — classifies each reading in real time as valid, artifact, gap, or genuine risk. |
| `python/session_monitor.py` | Escalation logic (only real risk reaches an alert) and audit-log generation. |
| `python/demo.py` | Runs the pipeline end to end in a terminal. |
| `python/plot_session.py` | Generates the static chart version of the session trace. |

## What this demonstrates

- **Problem framing from public information** — scoping a real risk without insider access, and being explicit about what's assumption vs. confirmed.
- **Translating a clinical/technical risk into product terms** — success metrics, scope boundaries, and the alert-fatigue tradeoff that makes the naive solution (alarm on everything) worse than no solution.
- **End-to-end build** — the same core logic implemented twice (Python for the reasoning, JavaScript for the interactive demo), plus a designed interface, not just a script.

## Running it yourself

The demo requires nothing installed — open `index.html` in any browser.

To run the Python version:
```bash
cd python
pip install matplotlib
python demo.py
python plot_session.py
```

---

*Built as a self-directed learning project while transitioning from technical PM work into software product management.*
