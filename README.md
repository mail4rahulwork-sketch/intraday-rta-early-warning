# Intraday RTA Early-Warning Simulator

**How much service level does catching a problem early actually save?**
This project simulates one contact-centre day with a volume spike and unplanned absenteeism, then compares three ways a real-time / intraday team could respond.

> **Data note:** all data is **simulated**. No company or customer data is used.

```mermaid
---
config:
  xyChart:
    width: 900
    height: 380
---
xychart-beta
    title "Interval service level %: A no action (line 1), B late 13:00 (line 2), C RTA early warning (line 3)"
    x-axis ["08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00","20:30","21:00","21:30"]
    y-axis "SL %" 0 --> 100
    line [84,88,88,84,69,74,0,0,0,0,0,0,0,8,0,0,69,66,71,73,74,52,69,61,56,41,59,54]
    line [84,88,88,84,69,74,0,0,0,0,85,84,86,82,86,84,84,82,84,85,85,82,82,87,86,82,90,88]
    line [84,88,88,84,69,84,83,76,86,87,85,84,86,82,86,84,84,82,84,85,85,82,82,87,86,82,90,88]
```

## The scenario

- 08:00–22:00, 30-minute intervals, AHT 300 s, target **80/20**
- **+25% unplanned volume** from 11:00 to 16:00 (think outage or campaign)
- **2 agents absent** from 10:00

| Response | What happens |
|---|---|
| A. No real-time action | The plan never changes |
| B. Late reaction | Someone notices at 13:00 and adds capacity |
| C. RTA early warning | Rule-based alerts: volume **>10% over forecast for 2 consecutive intervals**, or **staffed < Erlang C requirement**. Capacity is added one interval later (cancel offline activities, move multi-skilled agents, voluntary OT), capped at +6 agents |

## Key findings (simulated day)

| Scenario | Daily SL | Intervals below 80/20 | Extra agent-hours |
|---|---:|---:|---:|
| A. No real-time action | **37.3%** | 24 of 28 | 0 |
| B. Late reaction (13:00) | **62.4%** | 6 | 21.5 |
| C. RTA early warning (alert 10:00) | **83.7%** | 2 | 33.5 |

- The alert fired at **10:00**, as soon as staffing dropped below requirement and an hour before the volume spike.
- Reacting **3 hours earlier** turned a missed day (62%) into a met day (84%).
- When staffing falls below the traffic load, Erlang C shows the queue becomes unstable and **service level collapses to near 0**, not "a bit lower". That is why the first hour of a disruption matters most.
- Early action used ~12 more agent-hours than the late reaction. The real decision is whether that cost is worth +21 points of SL, which is the conversation an RTA has with operations.

## Run it

```bash
pip install -r requirements.txt
python rta_early_warning.py
```

## Skills shown

Real-time monitoring · Intraday management · Erlang C · Alert rule design · Scenario analysis · Python

---
Built by **Rahul**, Control Tower – WFM Analyst. [LinkedIn](https://www.linkedin.com/in/rahul-219543159/)
