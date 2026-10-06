# OptionAnalyzer — persistent context for coding agents

## Read this first in every new session

This is the project's durable handoff and instruction file. If its contents are not already in your active context, read it completely **before investigating or changing the project**. After losing context or conversation compaction, return here rather than guessing earlier decisions.

Then:
1. Read `README.md` for setup, workflows and operating limitations.
2. Inspect `git status` and relevant diffs. This working tree contains existing upgrades and user-managed files; do not undo unrelated changes.
3. Read the actual source files relevant to the user's request. This guide is context, not a substitute for verifying current code.
4. Make focused changes and validate them. **Updating this context is a mandatory part of every task that changes project files**, not an optional follow-up. Follow the maintenance rules below before declaring the task complete.

Pi automatically discovers root `AGENTS.md` when started in this directory or a child directory, unless context loading is explicitly disabled (`--no-context-files` / `-nc`) or a same-directory `AGENTS.override.md` takes precedence. `/reload` reloads changed instructions in an existing Pi session. Other coding agents should read this file explicitly if they do not support automatic discovery.

## Mandatory ongoing context maintenance

Treat `AGENTS.md` as living project memory, not a one-time summary.

For **every change task** (features, fixes, UI/style changes, APIs, configuration, dependencies, launchers, tests or documentation):
1. Review the actual changes, including new files, before finishing.
2. Update the affected sections of this guide so a new agent can understand the current behavior, file map, workflows, design decisions and constraints without the previous conversation.
3. Update **Latest completed changes** below with a concise dated entry: what changed, relevant paths, any new decisions/limitations and the validation actually performed. Keep only the five most recent entries; preserve enduring decisions in their relevant sections.
4. Remove or explicitly mark superseded instructions. If the user reverses an earlier decision, the latest accepted behavior must be unambiguous throughout this guide.
5. Update the validation baseline when tests run. Never claim a check passed when it was not run; record unverified/pending work honestly.
6. Include context maintenance in the completion checklist. **Do not mark a change task complete while this file describes outdated behavior.** Even if a change does not alter architecture, record the change briefly in the latest-changes section.

At session startup, compare this guide with relevant source and working-tree diffs. If changes were made outside the agent session, reconcile material differences as part of the task rather than relying on stale notes. Do not overwrite user work or assume every pre-existing diff belongs to the current task.

Keep context focused on the project. Never store credentials, complete conversations, transient logs, changing journal totals, private manual P&L or recommendations presented as live market facts. This is an agent maintenance requirement, **not a background file watcher**; it does not claim to monitor external edits while no agent is running.

## Latest completed changes

- **2026-10-06 — Git publication preparation:** collected the pending source, UI, launcher, dependency, documentation and regression upgrades for `origin/master`. Excluded local `Input/` uploads, `Output/` workbook/results/reports and the machine-specific `.lnk` shortcut from this commit; these remain untouched locally. Validation rerun: all 40 Python tests and 3 Node DOM-contract tests passed; journal JS syntax and `git diff --check` passed. No scan against original workbooks or real-browser check performed.

- **2026-10-06 — Journal capital KPI cards:** removed the entire “Continue editing the original workbook” panel from `Script/templates/journal.html`; added five responsive rupee cards with fixed ₹300,000 capital, all-row manual Profit/Loss totals, Open-only Standalone Margin usage and the user-requested available formula (capital + profit − used; loss remains separate). `Script/journal_state.py`, `Script/app.py` and `Script/static/js/journal.js` share server-computed totals for initial load/refresh and successful status saves; failed saves leave cards unchanged. Missing/invalid/formula amounts show unavailable totals; no Excel writes or scans. Updated `README.md`, Python regressions and new dependency-free `tests/test_journal_ui.js`. Validation: all 40 Python tests and 3 Node DOM-contract tests passed; JS syntax and `git diff --check` passed. No real-browser visual check performed for these cards.
- **2026-10-06 — Persistent agent context:** added root `AGENTS.md` with the project purpose, boundaries, file/data ownership, architecture, dashboard design, latest manual-status decision, launch/test commands and mandatory per-task context maintenance. `README.md` links the guide and explains automatic loading/maintenance. Validation: Pi's documented context discovery and `/reload` behavior checked; context/README-link and whitespace checks passed; all 36 regression tests passed. This documentation task does not change application behavior.
- **2026-10-06 — Manual journal status control:** replaced Profit/Loss-based status inference with per-row circular on/off controls (on = Open; off = Closed; unsaved entries = Open). `Script/journal_state.py` persists selections separately in `Output/journal_status.json`; `Script/app.py`, `Script/templates/journal.html`, `Script/static/js/journal.js` and CSS implement saving, live badges/counts and safe error handling. Excel stays unchanged. Validation: 36 regression tests plus Chrome refresh/restart, save-failure and mobile checks.
- **2026-10-06 — Journal refresh and status presentation:** added read-only **Refresh Journal** and professional icon badges/totals. The original Profit/Loss-driven condition is superseded by the manual control above; keep the presentation, not the old condition.

## What this project is for

A **local NIFTY options analysis and Sensibull practice-trading app**. It analyzes manually downloaded option-chain CSVs using the user's existing Excel rulebook, ranks Bull Put and Bear Call spreads independently, and appends the top two observations per strategy to an Excel journal.

The user manually places practice trades in Sensibull and manually records actual funds, margin, profit/loss and notes in Excel. The dashboard is a local decision-support and journal-preview tool, **not a real-order execution system**.

The agreed scope is reliable CSV analysis + Sensibull practice + manual Excel journaling. Live chain automation, journal P&L automation, backtesting, Iron Condor/Fly strategies and new ranking models are deferred unless explicitly requested.

## Non-negotiable behavior to preserve

- No real orders, automatic broker execution or invented market data.
- Preserve the existing CSV input, workbook rulebook, LTP pricing assumptions and independent per-strategy ranking. Do not introduce a global score or change strategy gates silently.
- Return **NO TRADE** when no valid setup qualifies; never force a recommendation.
- Preserve the original Excel journal's manual cells, formulas, formatting, extra columns, layout and other sheets. Do not replace the journal or recreate columns the user removed.
- CSV scans must not call the broker or modify `Input/Config.xlsx`.
- Use temporary copies/fixtures for tests. Do not run a scan against the original workbooks just to inspect or validate unrelated code: scanning can append real journal rows and publish reports.
- Keep modifications scoped. Do not delete legacy files, overwrite user data, rebuild packaged EXEs, add dependencies or redesign the architecture without a reason tied to the request.

## User workflow and file ownership

1. The user downloads the expiry **after current and next expiry** (the third available expiry) and places its CSV in `Input/`.
2. Filename: `NIFTY_YYYY-MM-DD_option_chain_YYYY-MM-DD-HH-MM-SS.csv`.
3. The dashboard selects the **exact uploaded expiry**, not a weekday-derived or automatically guessed third expiry. Multiple uploads for one expiry: latest filename timestamp wins. Expired/expiry-day contracts cannot be scanned.
4. Save/close `Input/Config.xlsx`, the original journal and reports in Excel, then run the practice scan.
5. Review top two **per strategy**, verify quotes/contracts/margin in Sensibull, and manually place practice trades.
6. Edit the original `Output/journal_tracker.xlsx`, sheet `Journal`, in Excel for manual bookkeeping. Save it, then click **Refresh Journal** to see changes.
7. Set each trade's Open/Closed state with the dashboard's circular on/off control.

Authoritative files:
- `Input/Config.xlsx`, sheet `CONFIG`: rules and configured market context.
- `Input/*.csv`: uploaded option snapshots.
- `Output/result.json`: saved dashboard scan snapshot, market/source metadata, eligible spreads and processed option chain.
- `Output/strategy_results_<expiry>.xlsx`: full eligible BullPut/BearCall strategy report.
- `Output/journal_tracker.xlsx`: original journal with append-only observations and manual data.
- `Output/journal_status.json`: manually selected Open/Closed states; separate from Excel and ignored by Git. Back up/move it with the workbook.
- `Output/backups/`: pre-append journal backups.
- `Logs/application.log`: rotating structured app log; `Logs/server.log`: browser-launcher output.

The root `journal_tracker.xlsx`, root `dashboard_data.json`, `Output/journal.json` and old template components are **not the active data sources**. Leave them alone unless the user requests cleanup.

## Architecture and code map

Python 3.10+, Flask/Jinja, Waitress, pandas/numpy, openpyxl, vanilla JavaScript/CSS, optional pywebview desktop shell and optional vendored SmartAPI SDK.

Scan pipeline:
`ConfigManager` selects/validates input → `OptionChain` loads/cleans/validates the CSV → `MarketContext` carries the rules → `Analyzer` enriches the chain → `OptionScorer` checks short-side eligibility → `StrategyEngine` builds/ranks spreads → `TradeTracker` writes reports/appends journal → publish `result.json`.

| File | Responsibility |
| --- | --- |
| `Script/config.py` | Portable source/packaged paths, config validation, uploaded expiries, latest snapshot selection. |
| `Script/main.py` | `run_analysis(expiry_date=None, market_source="csv", config_manager=None)`; validation before any optional broker access; in-process `_SCAN_LOCK` and `AnalysisBusy`; orchestration and metadata publication. |
| `Script/option_chain.py` | CSV parsing/normalization, quote validation, intrinsic-based recorded spot/futures reconstruction. |
| `Script/market_context.py`, `Script/analyzer.py` | Rule/market context and chain enrichment. |
| `Script/scorer.py`, `Script/strategies.py` | Existing filters, spread arithmetic and independent strategy ranking. |
| `Script/trade_tracker.py` | `TradeTracker`, full report export, append-only top-two journal export, deduplication and rich result JSON. |
| `Script/app.py` | `create_app(config_manager=None, analysis_runner=None)`, routes, API validation/errors, downloads and template context. |
| `Script/journal_state.py` | Read-only workbook loading, stable journal-entry IDs, atomic persistent manual status selections and journal KPI calculations (`INITIAL_CAPITAL = 300000`). |
| `Script/app_support.py` | Atomic JSON/workbook replacement and controlled structured logging. |
| `Script/data_provider.py`, `Script/nifty_spot.py` | Optional environment-configured spot/VIX refresh, not live option-chain retrieval. |
| `Script/OptionAnalyzer.py` | pywebview desktop launcher with local Waitress server. |
| `Script/start_dashboard.py` | Browser launcher. |
| `Script/templates/`, `Script/static/` | Active dashboard UI. |
| `tests/test_workflow.py`, `tests/fixtures/nifty_snapshot.csv` | Offline regression tests with temporary input/output files, including journal KPI arithmetic/persistence. |
| `tests/test_journal_ui.js` | Dependency-free Node DOM-contract tests for status-driven KPI updates and failure rollback (not real-browser rendering). |

Routes: `/` and `/dashboard`; `/journal`; `/settings`; `POST /run-analysis`; `/api/dashboard`; `/api/health`; `POST /api/journal/status`; `/downloads/journal`; `/downloads/results`.

Non-static responses use `Cache-Control: no-store`. Download routes resolve fixed known output files rather than arbitrary user paths.

## Dashboard design and why it looks this way

A responsive **dark, professional practice terminal**, using local assets without CDN dependencies. Do not replace it with a new frontend framework merely to make a small change.

- `Script/templates/base.html`: shared sidebar and page shell. Three navigation items: **Strategy scanner**, **Excel journal**, **Existing rules**. Practice-only/no-order messaging stays visible.
- `Script/templates/dashboard.html` + `Script/static/js/dashboard.js`: exact uploaded-expiry/market-reference controls, explicit scan versus Refresh view, source/time/quality notes, market summary cards, top opportunity per strategy, ranked filterable/sortable table, expandable leg details, option chain and optional Greek columns. Default table selection is top two per strategy; this does not alter engine ranking.
- `Script/templates/journal.html` + `Script/static/js/journal.js`: five capital/P&L KPI cards, read-only Excel preview, **Refresh Journal**, Open/Closed totals, per-row circular on/off controls and existing status badges. The entire original-workbook instruction/path panel was removed at the user's request.
- `Script/templates/settings.html`: read-only workbook rules and explanations. Edit rules in Excel; the next scan reloads them.
- `Script/static/css/style.css`: dark theme variables, responsive grids/sidebar, horizontal table scrolling, accessible focus states, badges and circular controls.
- Status badges use local inline SVG icons and text, not color alone: blue clock for **Open**, green check for **Closed**, neutral **Unavailable** if saved status cannot be read.

**Refresh view** reloads the dashboard without scanning. **Refresh Journal** is a GET that reloads saved Excel changes without scanning or writing the workbook. No automatic background journal refresh exists.

## Latest journal status decision — do not revert this

An earlier implementation inferred status from Profit/Loss. The user explicitly replaced that behavior with a manual control:

- Circular control **ON = Open**; **OFF = Closed**.
- Entries without a saved selection default to **Open**.
- Profit, Loss, zeros, formulas, expiry and margin **do not determine status**.
- The radio-like appearance is implemented as a checkbox with `role="switch"`, allowing either direction by clicking again.
- A change saves immediately via `POST /api/journal/status`, updates the badge/icon/counts without a full reload, and survives refresh or app restart.
- Excel cells and scan results are never modified by this control. The status is the user's annotation, not verified broker-position state.
- Persistence schema: `{"schema_version": 1, "statuses": {"<entry-id>": "open|closed"}}` in `Output/journal_status.json`.
- Standard entry IDs derive from expiry, strategy, option type, strikes, premiums and POP plus duplicate occurrence. They exclude rank and manual bookkeeping fields, so normal row reordering, rank edits and P&L edits retain selections. Changing identifying trade values can produce a new identity. Do not casually change this scheme.
- Invalid/stale entry IDs are rejected. Corrupt/unreadable saved state disables controls instead of silently overwriting selections. Failed saves revert the UI and show an error.

## Journal KPI decisions

- Initial capital is fixed at **₹300,000** in `Script/journal_state.py`, separate from workbook rule/config capital and never changed by a scan/status toggle.
- Total profit sums numeric manual **Profit** amounts across all rows, regardless of status. Total loss sums numeric **Loss** magnitudes across all rows (supports negative loss entries).
- Used capital sums manual **Standalone Margin** only for **Open** rows. Never substitute Standalone Funds, estimated MaxLoss or calculated margin. Closed rows release their recorded margin; unsaved statuses default Open as before.
- Available capital is explicitly **initial capital + total profit − used capital**, per user request. **Total loss is displayed separately, not deducted.** This is a practice summary, not a broker funds balance; do not silently replace it with a different accounting formula.
- Blank cells count as zero/unrecorded. Missing needed columns or invalid/nonfinite/formula amounts make affected totals unavailable (—). Profit and margin must be nonnegative numeric Excel amounts. Formulas are not evaluated. Invalid amounts on closed rows do not affect used capital. Unreadable workbook makes derived totals unavailable; unknown statuses make used/available unavailable.
- Server computes the same KPI payload for page load/Refresh Journal and successful `POST /api/journal/status`; JS updates cards after successful save only. Failed saves keep previous cards, restore the control and show an error. Saved Excel amount edits require Refresh Journal; there is no background polling or automated broker P&L.
- Cards are responsive (five desktop columns, three medium, two mobile), use local existing metric styles and rupee labels. Workbook files/cells are unchanged.

## Calculation and journal invariants

- Bull Put and Bear Call ranking is independently descending: **POP proxy → credit efficiency → RoR → safety margin → average leg OI**. Rank 1 in one strategy is not globally ranked against the other.
- Preserve LTP-based credit/payoffs and POP proxy `(1 - abs(short delta)) * 100`. These are estimates, not executable fills or backtested win rates; fees/slippage excluded.
- Position Greeks = **buy minus sell**. `MaxSpreadPoints` compares absolute ask-minus-bid price points, not percent. Keep the existing spread allowance: percent threshold **OR** points threshold.
- Reject invalid/missing essential quotes/Greeks/OI/volume, crossed quotes, duplicate strikes, invalid legs, nonfinite risk and credit that is nonpositive or not below spread width.
- Do not fabricate missing unused Greeks or silently impose new hedge-liquidity thresholds. Hedge liquidity and actual margin are reviewed in Sensibull. Max loss is not broker margin.
- CSV spot/futures references come from consistent intrinsic columns. VIX/trend/CPR are configured context in CSV mode, not live or newly calculated signals. Shared CSV IV and Greeks are imported, not recalculated.
- Optional `live` market reference only refreshes spot/VIX; the option chain remains **CSV SNAPSHOT**. Filename timestamps have unverified timezone. On API failure retain previous results; do not pretend stale data is live.
- Journal append: only rank 1 and 2 per strategy, up to four rows. Identical expiry/strategy/option/strikes/premiums/POP observations are skipped. Rank alone does not duplicate a row; changed premiums/POP create a new observation.
- Back up before appending; stage and atomically replace files. Publish dashboard JSON after successful report/journal writes. There is no all-files transaction or cross-process lock: run one app instance.
- Workbook preview uses `read_only=True, data_only=False`; formulas are displayed as **Excel formula**, not evaluated or replaced.

## Launch, validate and troubleshoot

From the repository root:
```powershell
python -m pip install -r requirements.txt
python Script/OptionAnalyzer.py
# Windows shortcut: Start_OptionAnalyzer.bat
# Browser alternative:
python Script/start_dashboard.py
# Server only: python Script/app.py
# URL: http://127.0.0.1:5000/dashboard
```

Old EXEs under `Script/dist/` are still the old app. Use source launchers unless a rebuild is requested. Packaging instructions are in `README.md`; templates/static assets are bundled by `Script/OptionAnalyzer.spec`. Packaged data paths live beside the executable.

After backend changes, stop/restart the source app; a running Waitress process does not automatically reload Python code. Verify the user is not running an old EXE if new UI features are absent.

Validation:
```powershell
python -B -m unittest discover -s tests -q
git diff --check
node --check Script/static/js/journal.js
node --test tests/test_journal_ui.js
```

At the latest KPI implementation, **40 Python tests and 3 Node DOM-contract tests passed**, with JS syntax and whitespace checks. No real-browser visual test was performed for the KPI cards. Earlier Chrome checks verified manual toggles, live badge/count updates, refresh/restart persistence, failed-save rollback and no mobile page overflow using a temporary workbook copy; these predate the cards. Treat counts and historical validation as a baseline; rerun tests after changes and report the actual current outcome.

`UPGRADE_NOTES.md` records the initial focused upgrade and historical October CSV validation; its original test count predates later journal features. Do not treat those saved example opportunities as current market recommendations.

## Security and remaining boundaries

Optional credentials belong only in environment variables/ignored `.env`: `ANGEL_API_KEY`, `ANGEL_CLIENT_ID`, `ANGEL_PIN`, `ANGEL_TOTP_SECRET`, `ANGEL_CLIENT_PUBLIC_IP`. Never commit/log/expose their values or initiate broker calls during discovery. Earlier hard-coded credentials were removed from current code, but history may retain them; rotation was advised. Real broker authentication was not validated; automated failure-path tests are mocked.

Still deferred: live chain ingestion, automatic third-expiry discovery, automatic funds/margin/P&L, journal date/version columns, cross-process transactions, backtesting and extra strategies. Preserve these boundaries unless the user explicitly changes the scope.
