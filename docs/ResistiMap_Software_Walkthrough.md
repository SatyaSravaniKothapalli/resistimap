# ResistiMap — Software Walkthrough & Node Reference

This document has two parts:

1. **What each node does** — a plain-language reference for every piece of software in the project.
2. **Exact commands, in order** — everything needed to build and run a full simulated scan, from a cold terminal to a finished heatmap.

Everything here runs in **SIMULATE mode** on a laptop (no Pi or real sensors needed). When the Raspberry Pi and real hardware are wired up, only the `SIMULATE` flag inside `resistivity_sensor_node.py` needs to change — nothing else in this document changes.

---

## Part 1 — Node Reference

ResistiMap's software is split into small, independent programs called **nodes**. They don't call each other directly — they send messages back and forth through ROS 2, like separate departments sending memos instead of shouting across an office. This means if one node has a problem, it doesn't crash the whole rover.

| Node | Package | Type | What it does |
|---|---|---|---|
| `motor_driver_node` | `resistimap_hardware` | Topic pub/sub | Listens for a "go to cell (x,y)" command, simulates driving there, then announces "arrived." Will control the real TT motors via the TB6612FNG driver once on the Pi. |
| `probe_actuator_node` | `resistimap_hardware` | Topic pub/sub | Listens for `lower` / `raise` commands, simulates moving the servo, then confirms probe position. Will control the real probe-lowering mechanism on the Pi. |
| `resistivity_sensor_node` | `resistimap_hardware` | Publisher | Generates a simulated resistivity (ρ) reading once per second and publishes it. On the real Pi, this reads the ADS1115 (via the INA333 amplifier) and computes ρ = 2πaR from the actual probe voltage. |
| `grid_coverage_action_server` | `resistimap_hardware` | ROS 2 Action server | The "manager" of a scan. Given a grid size, it drives to each cell in a lawnmower pattern, lowers the probes, waits for a resistivity reading, raises the probes, and reports live progress after every cell. Supports being cancelled mid-scan. |
| `risk_classifier_node` | `resistimap_perception` | Subscriber + Publisher | The deep learning piece. Listens for resistivity readings, runs them through a trained MLP, and publishes a risk label (`very_high` / `high` / `low_moderate` / `low`) with a confidence score. |
| `heatmap_builder_node` | `resistimap_perception` | Subscriber | Listens for risk classifications and prints a live, color-coded grid to the terminal as each cell completes — this is the visual output shown during a demo. |

**Custom message/interface types** (defined in `resistimap_msgs`, used by the nodes above to talk to each other):

| Interface | Carries |
|---|---|
| `Resistivity.msg` | A single ρ reading: header, `rho`, `grid_x`, `grid_y` |
| `RiskClassification.msg` | A classified cell: header, `grid_x`, `grid_y`, `rho`, `label`, `confidence` |
| `ScanGrid.action` | The scan itself: **Goal** = rows/cols/spacing to scan, **Feedback** = live progress per cell, **Result** = final success/message when the whole grid is done |

**Why an Action and not just a function call?** A plain function call can't report progress while it's running, and can't be cancelled partway through. `ScanGrid` needs both — live per-cell feedback for the demo, and the ability to stop the rover mid-scan if something looks wrong physically.

**The DL model, honestly:** `risk_classifier_node` currently loads `model_synthetic.pt` — a placeholder MLP trained on randomly generated numbers labeled with the real Langford & Broomfield thresholds. It exists only to prove the training → save → load → predict pipeline works end-to-end. It is **not** the real result and must be retrained on actual slab readings before being used in the final demo/report.

**Not yet built** (not required for the current scan pipeline to run):
- `imu_node` — would read the MPU6050. Nothing downstream currently consumes IMU data, so this is a later addition, not a blocker.

---

## Part 2 — Full Command Sequence (cold start to finished scan)

### Step 0 — One-time setup (already done, included for completeness)
```bash
# Confirm ROS 2 Jazzy is sourced
printenv ROS_DISTRO
# Should print: jazzy
```

### Step 1 — Open a terminal and rebuild the whole workspace
```bash
cd ~/resistimap_ws
colcon build
source install/setup.bash
```
Expected: `Summary: 3 packages finished` (`resistimap_msgs`, `resistimap_hardware`, `resistimap_perception`).

### Step 2 — Open 7 terminal tabs/windows total
Run one command per terminal, **in this order**. Once a node is running, leave that terminal alone — don't type into it again. Use **Ctrl+C only** to stop a node; never Ctrl+Z (it freezes the node instead of stopping it, which breaks the scan).

**Terminal 1 — Motor driver**
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_hardware motor_driver_node
```

**Terminal 2 — Probe actuator**
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_hardware probe_actuator_node
```

**Terminal 3 — Resistivity sensor**
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_hardware resistivity_sensor_node
```

**Terminal 4 — Risk classifier (DL)**
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_perception risk_classifier_node
```

**Terminal 5 — Heatmap builder (the visual output)**
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_perception heatmap_builder_node
```

**Terminal 6 — Action server** (start this only after Terminals 1–5 are all running)
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 run resistimap_hardware grid_coverage_action_server
```

**Terminal 7 — Trigger the scan** (a single one-shot command, not a long-running node)
```bash
cd ~/resistimap_ws && source install/setup.bash
ros2 action send_goal /scan_grid resistimap_msgs/action/ScanGrid "{grid_rows: 2, grid_cols: 2, cell_spacing_m: 0.05}" --feedback
```

### Step 3 — What you should see
- **Terminal 1/2/3**: log lines for driving to each cell, lowering/raising probes, publishing ρ readings.
- **Terminal 4**: one line per cell — `rho=XX.XX -> label=YYYY (confidence=0.ZZ)`.
- **Terminal 5**: a live, color-coded 2×2 grid that fills in cell by cell.
- **Terminal 6**: a log line per completed cell.
- **Terminal 7**: live `Feedback:` blocks (cells completed, current cell, `last_rho`), ending in `Result: success: true`.

### Step 4 — Shutting everything down
In each terminal (1–6), press **Ctrl+C** once to stop that node cleanly.

---

## Quick "what's real vs. placeholder" summary (useful if asked directly)

| Piece | Status |
|---|---|
| Hardware design (Pi, INA333, ADS1115, MPU6050, motors, LM334) | Fully locked, reviewed |
| ROS 2 messaging backbone (`resistimap_msgs`) | Built and verified |
| Motor / probe / sensor nodes | Built, running in simulate mode (real hardware wiring pending) |
| Grid-scan Action server | Built and tested end-to-end |
| DL classifier | Code complete; model is a **synthetic placeholder**, to be retrained on real slab data |
| Heatmap visualization | Built and tested end-to-end |
| IMU node | Not yet built — not required for current pipeline |
