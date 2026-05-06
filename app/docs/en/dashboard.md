# Dashboard

Overview of every conversion task plus system status.

## Description

The dashboard has four **summary cards** at the top (Total, Running, Completed, Needs attention) plus three tabs underneath: **All Tasks**, **Activity**, and **Engines**.

**All Tasks** holds the queue table covering every module, refreshed live via the `TaskQueue` subscriber.

**Activity** holds a **QtCharts** bar chart with a **Per day**, **Per week**, **Per month**, or **Per year** bucket filter. Capped to the last 24 buckets so long histories stay readable.

**Engines** holds a grid of 11 engine binaries with `installed` (green) or `missing` (red), plus the FFmpeg hardware accel methods detected (`vaapi`, `cuda`, `qsv`, ...).

## How to use

1. Open **Dashboard** from the sidebar (it's the default page on launch).
2. Watch the summary cards for current task counts.
3. Switch to **Activity** and pick a **Bucket** for the chart.
4. Switch to **Engines** to audit what's missing, install with `apt`.
5. Click **Refresh** after installing a new engine to recheck status.

## Tips & Trick

- Click **Info** or double-click a row in **All Tasks** to open the details dialog (input/output thumbnails plus full log).
- The chart auto-refreshes every time a task completes, no manual refresh needed.
- Bucket labels like `2026-W18` follow SQLite `strftime` ISO week format.

## Troubleshooting

**Chart is empty.** No tasks in the database yet. Run one conversion and the dashboard will pick it up.

**Hardware accel says "none detected".** Either `ffmpeg` is missing or your GPU drivers don't expose hardware encoders. Verify with `ffmpeg -hwaccels` in a terminal.
