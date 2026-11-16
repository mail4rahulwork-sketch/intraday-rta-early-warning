"""
Intraday Real-Time Analyst (RTA) Early-Warning Simulator
--------------------------------------------------------
How much service level does early intraday detection save?

A SIMULATED contact-centre day (08:00-22:00, 30-min intervals) with two
real-world disruptions:
  - an unplanned volume spike 11:00-16:00 (e.g. an outage / campaign), +25%
  - unplanned absenteeism: 2 agents short from 10:00

Three scenarios are compared:
  A. No real-time management: the plan is never changed.
  B. Late reaction: the issue is noticed at 13:00 (e.g. by a supervisor).
  C. RTA early warning: rule-based alerts fire when
       - actual volume runs >10% over forecast for 2 consecutive intervals, or
       - staffed agents fall below Erlang C requirement,
     and capacity is added one interval later (cancel offline activities,
     move multi-skilled agents, voluntary OT), capped at +6 agents.

Service level per interval is computed with Erlang C (80/20 target).
All data is synthetic. No company data is used.
Author: Rahul
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent / "outputs"
OUT.mkdir(exist_ok=True)
RNG = np.random.default_rng(7)
AHT, T, SL_TGT, IV = 300, 20, 0.80, 30
MAX_EXTRA = 6


def erlang_c(a, n):
    if n <= a:
        return 1.0
    inv_b = 1.0
    for k in range(1, n + 1):
        inv_b = 1 + inv_b * k / a
    b = 1 / inv_b
    return b / (1 - (a / n) * (1 - b))


def sl(calls, agents):
    a = calls * AHT / (IV * 60)
    if calls == 0:
        return 1.0
    if agents <= a:
        return 0.0
    return 1 - erlang_c(a, agents) * math.exp(-(agents - a) * T / AHT)


def req(calls):
    n = max(1, math.ceil(calls * AHT / (IV * 60)))
    while sl(calls, n) < SL_TGT:
        n += 1
    return n


def build_day():
    slots = pd.date_range("2026-11-16 08:00", "2026-11-16 21:30", freq="30min")
    h = np.asarray(slots.hour + slots.minute / 60, dtype=float)
    fc = np.round(60 * (0.55 + 0.9 * np.exp(-((h - 11.5) ** 2) / 4) + 0.6 * np.exp(-((h - 18.5) ** 2) / 3)))
    actual = np.asarray(fc * RNG.normal(1, 0.04, len(fc)), dtype=float)
    spike = (h >= 11) & (h < 16)
    actual[spike] *= 1.25
    df = pd.DataFrame({"slot": slots.strftime("%H:%M"), "hour": h, "forecast": fc, "actual": np.round(actual)})
    df["planned_agents"] = df.forecast.apply(req)
    absent = np.where(h >= 10, 2, 0)
    df["base_staffed"] = df.planned_agents - absent
    df["required_on_actual"] = df.actual.apply(req)
    return df


def run(df, react_from_idx):
    staffed = df.base_staffed.to_numpy().copy()
    if react_from_idx is not None:
        for i in range(react_from_idx, len(df)):
            gap = df.required_on_actual.iloc[i] - df.base_staffed.iloc[i]
            staffed[i] += int(np.clip(gap, 0, MAX_EXTRA))
    s = [sl(c, a) for c, a in zip(df.actual, staffed)]
    return staffed, np.array(s)


def first_alert(df):
    over = (df.actual > df.forecast * 1.10).to_numpy()
    short = (df.base_staffed < df.required_on_actual).to_numpy()
    for i in range(1, len(df)):
        if (over[i] and over[i - 1]) or short[i]:
            return i
    return None


def daily_sl(df, s):
    return float((s * df.actual).sum() / df.actual.sum())


def main():
    df = build_day()
    alert = first_alert(df)
    late = int(np.where(df.slot == "13:00")[0][0])

    scen = {
        "A. No real-time action": run(df, None),
        "B. Late reaction (13:00)": run(df, late),
        f"C. RTA early warning (alert {df.slot[alert]}, act {df.slot[alert + 1]})": run(df, alert + 1),
    }
    rows = []
    for name, (staffed, s) in scen.items():
        df[name] = s
        rows.append({
            "scenario": name,
            "daily_SL_%": round(100 * daily_sl(df, s), 1),
            "intervals_below_80/20": int((s < SL_TGT).sum()),
            "extra_agent_hours": round((staffed - df.base_staffed).sum() * IV / 60, 1),
        })
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "scenario_results.csv", index=False)
    df.to_csv(OUT / "intraday_day.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 4.6))
    colors = ["#c0392b", "#e07a1f", "#2a9d8f"]
    for (name, _), c in zip(scen.items(), colors):
        ax.plot(df.slot, 100 * df[name], lw=2.2, label=name, color=c)
    ax.axhline(80, ls=":", color="grey")
    ax.text(0, 81.5, "80/20 target", color="grey", fontsize=8)
    ax.axvline(df.slot[alert], color="#2a9d8f", ls="--", lw=1)
    ax.set_xticks(df.slot[::4])
    ax.set_ylim(0, 102)
    ax.set_ylabel("Service level % (Erlang C)")
    ax.set_title("Same disruption, three responses: interval service level")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "intraday_sl_scenarios.png", dpi=150)

    txt = f"""# Results (simulated day)

Disruption: +25% volume 11:00-16:00 and 2 agents absent from 10:00.
First rule-based alert fired at **{df.slot[alert]}**.

{res.to_markdown(index=False)}
"""
    (OUT / "RESULTS.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
