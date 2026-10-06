# NIFTY Options — Sensibull Practice Scanner

A local CSV-based app for your existing Bull Put / Bear Call spread rulebook. **No real orders are placed.** Manually enter the chosen practice trades in Sensibull and record actual margin/funds/P&L in the original Excel journal.

## Start the app

Python 3.10+:

```powershell
python -m pip install -r requirements.txt
python Script/OptionAnalyzer.py
```

On Windows you can also double-click `Start_OptionAnalyzer.bat`. For a browser window instead:

```powershell
python Script/start_dashboard.py
```

Or run `python Script/app.py` and open http://127.0.0.1:5000/dashboard. Keep the app process running. Use one app instance at a time.

**Old executables in `Script/dist/` still contain the old application.** Run the source launcher above, or rebuild with the commands below.

## Your daily workflow

1. In your data source/Sensibull, choose the expiry **after current and next expiry** (the third available expiry).
2. Download its NIFTY chain and place it in `Input/`. Keep the existing filename format:
   `NIFTY_YYYY-MM-DD_option_chain_YYYY-MM-DD-HH-MM-SS.csv`.
3. Save and close `Input/Config.xlsx`, `Output/journal_tracker.xlsx`, and any strategy report in Excel.
4. Select that exact uploaded expiry and click **Run practice scan**. If several downloads have the same expiry, the latest filename timestamp wins.
5. Review the top 2 **within each strategy**, verify the contracts/quotes/margin in Sensibull, and place a practice trade manually.
6. Open the original `Output/journal_tracker.xlsx` and enter funds, margin, profit, loss and any other manual columns. A downloaded journal copy is a separate file.

The app does **not** determine the third exchange expiry from weekday guesses: your downloaded CSV supplies the chosen contract. Verify its filename expiry against Sensibull. Expired and expiry-day CSVs are not scanned. Option chains are not fetched or uploaded through a new API; the existing Input-folder workflow is preserved.

## Market values and labels

- Default **CSV mode** uses the recorded underlying reconstructed from positive ITM intrinsic values (`strike + call intrinsic`, `strike − put intrinsic`). These values must agree. It does not estimate spot from stale LTPs or modify Config.xlsx.
- Futures reference, when available, is reconstructed from the corresponding CSV intrinsic fields, not separately fetched.
- VIX, trend and CPR width in CSV mode come from Config.xlsx and are clearly labelled **manual/configured**, not live signals.
- CSV time comes from its filename, with unverified timezone. The dashboard always labels these option prices **CSV SNAPSHOT**, not LIVE. Older-date snapshots carry a warning.
- Optional **SmartAPI mode** refreshes only spot/VIX. It cannot make the uploaded chain live or synchronize its timestamps. An API failure aborts that scan and retains prior results.
- **Manual configuration mode** uses SpotPrice/VIX in Config.xlsx; ensure these match your CSV.

## Rules and ranking preserved

Every scan reloads the existing CONFIG sheet. Short options remain OTM and subject to the workbook's delta, OI, volume and spread rules. Spreads use WingWidth/LotSize, followed by MinPOP, MinimumCredit, MinimumROR and MaxCapitalPerTrade.

The existing descending ranking remains separate for Bull Put and Bear Call:

1. POP proxy
2. Credit efficiency
3. Return on risk
4. Safety margin
5. Average leg OI

There is no new weighted score, global rank, market-regime gate, or Iron Condor/Fly implementation. Existing recommendation-star generation is unchanged in the engine, but the UI emphasizes the actual per-strategy ranks.

Corrections:

- MaxSpreadPoints now compares **absolute ask-minus-bid points**, not a percentage; the existing percentage **OR** points allowance is retained.
- Position Greeks use **buy Greek − sell Greek**.
- Missing/invalid prices, crossed quotes, missing essential Greeks/OI/volume, duplicate strikes, and invalid payoffs cannot become eligible opportunities.
- Positive credit must be below spread width and max loss/RoR must be finite.
- All existing **LTP-based** credit/payoff formulas and the **short-delta POP proxy** are retained. Neither is an executable-fill guarantee. Fees/slippage are excluded. Max loss is not actual broker margin.
- Hedge quotes are checked for validity. No new hedge-liquidity cutoffs were silently added; review hedge spread, OI and volume manually in Sensibull. Gamma/other unused CSV fields can still be missing and are displayed as unavailable.

No eligible setups means **NO TRADE** and no new journal rows.

## Journal safety

The journal's small circular on/off control sets each trade's status: **on = Open**, **off = Closed**. Profit/Loss values do not affect this selection. Entries without a saved selection default to Open. Changes save immediately to `Output/journal_status.json` and survive refresh/restart without editing Excel. Keep this file alongside the workbook when backing up/moving the app. Save Excel and click **Refresh Journal** to reload workbook changes.

The Excel journal tab has five KPI cards: fixed **₹3,00,000 Capital**, **Total profit**, **Total loss**, **Available capital**, and **Used capital**. Profit/Loss totals sum the saved manual columns across all entries; used capital sums **Standalone Margin for Open trades only** (not Standalone Funds or estimated max loss). Status changes update the cards immediately after saving. Save Excel and use **Refresh Journal** to update manual amounts.

Available capital follows the requested formula: **Capital + Total profit − Used capital**. Loss is displayed separately and is **not deducted** in this formula; this is a manual practice summary, not verified broker funds. Blank amounts count as zero. Missing required columns, formulas or invalid values show **—** for affected totals rather than an invented amount; formulas are not evaluated. Loss amounts are displayed as magnitudes even if entered negatively. Unknown saved status makes used/available capital unavailable. No workbook cells are changed by these calculations.

Only ranks 1 and 2 per strategy are appended (up to 4 rows). Existing cells, manual entries, formulas, formatting, additional columns and other sheets are preserved. An Available Fund column that you removed is not recreated. A new journal gets the original layout and Available Fund formulas.

Identical expiry/strategy/legs/premiums/POP observations are skipped on repeated scans. Rank changes alone do not duplicate a row. Changed premiums/POP create a new practice observation. There is no new scan-date column in the existing journal layout.

Before an append, a backup is saved in `Output/backups/`. Workbook updates and JSON publication use staged files and atomic replacement. If Excel holds a file open, the app tells you to close it and retry. The old dashboard JSON is retained on failure; report/journal files are not a single multi-file database transaction.

## Outputs

- `Output/result.json`: complete saved scan snapshot, metadata, full strategy metrics and processed chain; dashboard source.
- `Output/strategy_results_<expiry>.xlsx`: original BullPut/BearCall report sheets with all eligible spreads.
- `Output/journal_tracker.xlsx`: top-two practice observations plus your manual entries.
- `Output/journal_status.json`: manually selected Open/Closed states; no Excel cells are changed.
- `Logs/application.log`: rotating structured event/error log; `Logs/server.log` records browser-launcher startup output.

Root `dashboard_data.json`, `Output/journal.json`, old components, and the root journal copy are not used. They were left untouched rather than deleting your files.

## Optional SmartAPI credentials

CSV mode requires no credentials. For spot/VIX refresh, copy `.env.example` to `.env` and fill in ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PIN and ANGEL_TOTP_SECRET. Set ANGEL_CLIENT_PUBLIC_IP if required by your account. `.env` is ignored by Git. No secrets are sent to the frontend.

Previously hard-coded credentials were removed from the current source. **Rotate them if they were committed/shared; removing current literals does not remove Git history.** Optional real authentication was not exercised during this upgrade; its failure paths are tested offline.

## Persistent coding-agent context

[`AGENTS.md`](AGENTS.md) is the project's durable context: purpose, architecture, dashboard design, workflows, safety constraints and latest decisions. Pi loads it automatically when started in this folder or below it, unless context discovery is disabled or overridden. Use `/reload` in an existing Pi session after instructions change. Other agents should read it explicitly if they do not auto-load it.

Agents must update the affected context and its latest-changes section **after every project change**, including what was validated, before marking the task complete. At session startup they must reconcile material changes made outside the previous session. This is a maintained agent workflow, not a background watcher of your Excel files.

## Validation

```powershell
python -B -m unittest discover -s tests -v
node --check Script/static/js/journal.js
node --test tests/test_journal_ui.js
```

Tests use a historical CSV fixture in temporary directories, not the original journal or broker. They cover the full CSV→analysis→strategy→ranking→reports→API→HTML workflow, payoff/Greek arithmetic, NO TRADE, repeated scans, manual-entry/formula/sheet preservation, stale/malformed data, optional API failure, file-lock errors, input validation, and journal KPI arithmetic/status changes. Dependency-free Node DOM-contract tests cover immediate KPI updates, unavailable amounts and failed-save rollback; these are not real-browser visual tests.

## Rebuild the desktop executable

```powershell
python -m pip install -r requirements_dev.txt
cd Script
python -m PyInstaller --clean OptionAnalyzer.spec
```

The executable reads `Input/` and writes `Output/` **beside the executable**. Supply the workbook/CSV there, or keep using the source launcher at the project root. The previous packaged executable has not been silently replaced.
