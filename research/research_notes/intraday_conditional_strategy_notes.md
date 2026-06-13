# Research Workflow — Intraday Conditional Strategy on SPY / QQQ

> **STATUS: ACTIVE — this is the current Strategy #1.** The diversified-trend strategy
> (`research/diversified_trend_strategy_notes.md`) is parked pending a multi-symbol /
> portfolio backtester, so this intraday strategy is the first one being taken to paper.

Research plan for an intraday strategy that uses the first hour of US equity trading as a
signal and expresses the resulting trade in the remainder of the session. Follows the same
step structure as `research/diversified_trend_strategy_notes.md`.

---

## Status

**Step 1 — Framing.** Nothing has been backtested yet. No data has been pulled.

---

## Strategy Summary

One sentence: **after the first 60 minutes of the regular session, take a position in SPY or
QQQ for the remainder of the day, where the direction and sizing are conditioned on what
happened in that first hour.**

The first hour is used purely as a signal — no trades are placed before 10:30 ET. The trade
is held into the close (or exited on a time/level rule, TBD) and the position is always flat
overnight. One symbol per instance per the strategy framework in `STRATEGY.md`.

---

## Hypothesis

**H1 (primary).** The first-hour return `r_1h = (close_10:30 − open_9:30) / open_9:30` is
predictive of the rest-of-day return `r_rod = (close_15:55 − close_10:30) / close_10:30`,
with a relationship that flips sign depending on the *magnitude* of `r_1h` normalized by
recent realized volatility.

**Economic rationale.** Two distinct microstructure regimes drive the open:
- **Small first-hour moves** (`|r_1h|` below ~0.5σ of trailing intraday ATR): the open is
  digesting overnight noise. Mean reversion to the open / VWAP is the dominant flow as
  liquidity normalizes through the day. Expression: **fade the first-hour move.**
- **Large first-hour moves** (`|r_1h|` above ~1.5σ): the open is repricing real information
  (overnight news, macro, earnings spillover). Trend continuation as additional information
  is absorbed and slower participants enter. Expression: **continue with the first-hour
  direction.**
- The middle bucket is the danger zone — neither effect dominates and it should likely be
  no-trade. Confirming or rejecting this is part of Step 3.

**What I expect to find if this works.** Modest edge, gross Sharpe in the 0.8–1.5 range on
IS, dropping meaningfully on OOS and cost-stress. Worse on SPY than QQQ (QQQ has more
post-open dispersion historically). Strongly regime-dependent — should look very different
in 2020, 2022, vs 2017 or 2024.

**What would falsify the hypothesis.** No conditional separation between regimes in EDA
(Step 3) — i.e., if `r_rod | r_1h` looks unconditionally random across all `|r_1h|`
buckets, there is nothing to trade and we stop at Step 3.

---

## Kill Criteria (committed before any backtest)

These are committed now, before looking at IS data. Any one of them triggers a stop.

| Criterion | Threshold | Where evaluated |
|---|---|---|
| Net Sharpe (IS, costs included) | < 1.0 | Step 4 |
| Max drawdown (IS) | > 15% of starting equity | Step 4 |
| Profit factor (IS) | < 1.3 | Step 4 |
| Parameter sensitivity — best vs median Sharpe | best > 2× median | Step 5 (overfit signal) |
| Cost-stressed (2× costs + 2× slippage) Sharpe | < 0.5 | Step 6 |
| OOS Sharpe vs IS Sharpe | OOS < 50% of IS | Step 7 |
| OOS max drawdown | > 20% | Step 7 |
| Paper-trade tracking error vs backtest | > 50bps/trade unexplained | Step 8 |

**The 15% IS drawdown threshold is tight on purpose.** At $25–50k starting capital with a
$25k PDT floor, a 15% drawdown from $35k puts equity at $29.75k — uncomfortable but not
fatal. A 20% drawdown puts $35k at $28k — too close. Drawdown control is a hard constraint
here, not a soft preference.

---

## Open Decisions

Tracked here until resolved. Each should be closed before the step that depends on it.

- [ ] **Intraday data source.** IBKR `reqHistoricalData` will not give us multi-year 1-min
      bars (30-day limit). Candidates: Polygon.io (~$30/mo for stocks starter), FirstRate
      Data (one-time purchase), Algoseek (more expensive, higher quality). Decision needed
      before Step 2. Whatever is chosen needs a loader into the `market_data_bars` table.
- [ ] **Bar size.** 1-min vs 5-min vs 15-min for the underlying analysis. 5-min is likely
      enough for an open→close strategy and is much cheaper to store and process. Decide
      before Step 2.
- [ ] **First-hour window length.** Hypothesis says 60 minutes. Worth checking 30 and 90 in
      Step 3 EDA before locking in. Lock before Step 4.
- [ ] **IS / OOS split.** Default proposal: IS = 2015-01-01 through 2021-12-31 (7 years,
      includes 2018 vol, COVID), OOS = 2022-01-01 through 2024-12-31 (3 years, includes
      2022 bear, 2023 recovery, 2024 low-vol). Confirm before Step 2 — and **commit to no
      iteration on OOS**, period.
- [ ] **Position sizing rule.** Two natural choices: (a) fixed dollar notional sized to
      target X% daily vol contribution, (b) Kelly-fractional from IS edge estimate. (a) is
      simpler and more defensible for a first pass. Decide before Step 4.
- [ ] **Exit rule.** Hold to 15:55 close, or earlier exit on profit/stop/VWAP cross? Adds
      parameters → adds overfit risk. Default: time-only exit at 15:55. Revisit only if
      Step 4 shows large tail losses.
- [ ] **Cost model.** Need a concrete spread + slippage assumption for SPY/QQQ at 10:30
      entry and 15:55 exit. SPY at midday is essentially zero spread for our size; the
      slippage will be commission and fee dominated. Lock before Step 4. See cross-ref to
      `BACKTESTING.md` cost section.
- [ ] **PDT mitigation.** With one round-trip per day this is a guaranteed PDT pattern day
      trade. Equity must stay above $25k at all times. Either (a) start with $30k+ buffer
      and a hard 12% strategy-level drawdown cutoff, or (b) restrict to ≤3 day trades per
      5-day rolling window (kills the strategy on most days). Decide before Step 8.

---

## Workflow

### Step 1 — Framing

**Objective.** State the hypothesis, the economic rationale, expected return profile, and
the conditions under which the work stops. (This document.)

**Done when.** Hypothesis, kill criteria, and open decisions list are written down and
have not changed for 24 hours of reflection. Resist the urge to start pulling data before
this step is locked.

**Anti-pattern to avoid.** Generalizing the hypothesis when EDA disappoints. If H1 fails
in Step 3, the project stops. It does not pivot to "well, maybe overnight gap predicts
intraday range instead" — that's a different strategy and deserves its own workflow doc.

---

### Step 2 — Universe and Data

**Universe.** SPY and QQQ. No other symbols. No futures. Two separate strategy instances
(per `STRATEGY.md` one-instance-one-symbol rule).

**Data needed.**
- Intraday bars (size TBD, see Open Decisions) for SPY and QQQ, spanning the full IS+OOS
  window.
- Daily bars for both symbols (already accessible via IBKR for trailing ATR / realized vol
  features).
- Overnight close-to-open returns (derivable from daily bars).

**Storage.** Goes into the existing `market_data_bars` table per `DATA_MODEL.md`. The
table already has `(symbol, bar_size, datetime)` as the unique key, which supports
multiple bar sizes side by side.

**Quality checks before any analysis.**
- No gaps within RTH on non-holiday trading days.
- Half-day session handling (1pm closes on day before holidays) — drop or label.
- DST transitions handled correctly (the table stores ISO bar_datetime, so should be safe
  if the loader normalizes correctly).
- Spot-check 5-10 random days against a known reference (Yahoo or TradingView chart).

**Done when.** All data is in `market_data_bars`, quality checks pass, and IS/OOS split is
locked in writing in this doc.

---

### Step 3 — Signal Exploration (Notebook)

**Where.** A notebook in `research/`, **not** the strategy module yet. No backtester
called here. Pure EDA.

**EDA outputs required (all on IS data only):**

1. **Intraday vol profile.** Average realized vol per 5-min bucket across the trading day,
   for SPY and QQQ separately, by year. Confirms the U-shape and quantifies how the open
   compares to midday.

2. **First-hour return distribution.** Histogram and time-series of `r_1h`, by symbol, by
   year. Annualized vol of first-hour returns. Compare to overnight return distribution.

3. **The conditional cross-tab — the key test of H1.** For each symbol:
   - Bucket days by `|r_1h|` normalized by trailing 20-day intraday ATR — say into
     quintiles or sextiles.
   - For each bucket, compute the average and median `r_rod`, signed against `r_1h`
     (i.e., is rest-of-day in the same direction or opposite).
   - Look for monotonic structure: small `|r_1h|` → fade dominates (negative average
     signed `r_rod`); large `|r_1h|` → continuation dominates (positive average signed
     `r_rod`).
   - Compute t-stats per bucket. Be honest about multiple testing — six buckets × two
     symbols means some will look "significant" by chance.

4. **Overnight gap conditioning.** Same cross-tab but additionally conditioned on
   overnight gap sign and size. The most common version of this trade conflates
   first-hour move with overnight gap — separate them before assuming the signal is
   really the first-hour move.

5. **Regime dependence.** Repeat the conditional cross-tab year by year. If the
   relationship inverts or vanishes in any major year (2018, 2020, 2022 are the obvious
   ones), that's a serious red flag — note it now, before backtesting compounds it.

6. **Window-length robustness.** Repeat the primary cross-tab for 30-min and 90-min
   first-hour windows. If 60 is special but 30 and 90 don't show the pattern, the 60-min
   result is suspect.

**Decision point.** After EDA, before any backtesting:
- If the conditional structure in (3) is visible in **both** symbols and **most** years,
  proceed to Step 4 with the parameters that EDA suggests (NOT the parameters that
  optimize EDA — pick reasonable round numbers in the same neighborhood).
- If the structure is visible in only one symbol or only some years, **document it
  honestly here** and either narrow scope (e.g., proceed with QQQ only) or stop.
- If no structure is visible, stop. Do not search further until something works.

**Done when.** The decision above is written down in this doc with the supporting plots
saved alongside the notebook.

---

### Step 4 — In-Sample Backtest

**Objective.** A single backtest run on IS data using the parameters chosen at the end of
Step 3, evaluated against the kill criteria.

**Strategy implementation.** As a `BaseStrategy` subclass in `strategy/` per the framework
in `STRATEGY.md`. `on_bar` handles 5-min bars. The strategy maintains:
- A `RollingWindow` of the day's bars to compute `r_1h` at 10:30
- A trailing realized-vol estimate for the `|r_1h|` normalization
- A flag for whether the day's signal has already been generated (one trade per day)
- A flag for exit time (15:55)

It emits at most one `OrderRequest` to enter and one to exit per day.

**Run via.** `backtesting/runner.py::run_backtest(BacktestConfig(...))` per
`BACKTESTING.md`. Use `fill="next_open"` (the default; lookahead-safe).

**Cost assumptions for this step.** IBKR tiered pricing: $0.0035/share, $0.35 minimum.
Slippage: 0.5 bps per side on SPY/QQQ at 10:30 entry; 0.5 bps per side at 15:55 exit. These
are realistic-but-not-conservative; the conservative version comes in Step 6.

**Outputs.** Equity curve, trade log, metrics table (per `BACKTESTING.md` — Sharpe,
max DD, win rate, total trades, total commission). Compare every metric to kill criteria.

**Done when.** Either a kill criterion triggers (stop, document, move on to a different
project) or all kill criteria are passed and we proceed to Step 5.

**Anti-pattern to avoid.** Tweaking parameters after seeing IS results and re-running.
That's the start of overfitting. If the chosen parameters fail, the answer is "this
hypothesis didn't survive contact with the data" — not "try a different window length."

---

### Step 5 — Parameter Sensitivity

**Objective.** Confirm the IS result is not perched on a parameter spike.

**Method.** Sweep each parameter independently across a reasonable neighborhood while
holding the others at the Step 4 value:
- First-hour window: 30, 45, 60, 75, 90 minutes
- Vol-normalization lookback: 10, 20, 40 days
- Entry threshold (the `|r_1h|/σ` cutoff between fade / no-trade / continue): ±25% around
  the Step 4 values
- Exit time: 15:30, 15:45, 15:55, 16:00

**Pass criterion.** The chosen parameter set's Sharpe is within ~0.3 of the median of its
neighborhood for every dimension. If any single parameter shows a sharp spike (chosen
value Sharpe > 2× median), the result is fragile and the kill criterion triggers.

**What this is not.** This is not parameter optimization. We do not adopt the best-Sharpe
parameter set found in the sweep. We confirm the originally-chosen set sits in a stable
neighborhood, then keep going with it.

**Done when.** Sensitivity plots are saved and the chosen parameter set has passed the
neighborhood-stability check, or a kill triggers.

---

### Step 6 — Cost Stress

**Objective.** Verify the strategy survives realistic-pessimistic costs.

**Method.** Re-run the Step 4 backtest with:
- 2× the Step 4 commission rate
- 2× the Step 4 slippage assumption
- An additional "open spread" penalty if the entry is at 10:30 — debatable how relevant
  this is for SPY/QQQ but worth modeling

**Pass criterion.** Net Sharpe > 0.5 (per kill criteria above).

**Why this matters here.** Even though SPY/QQQ have tight spreads, a 10:30 entry is in the
*tail* of the U-shape, not the trough. Spreads and impact are non-trivially higher at
10:30 than 12:00. Pretending otherwise is the kind of cost-model error that turns
backtests into paper profits.

**Done when.** Cost-stressed metrics are documented or kill triggers.

---

### Step 7 — Out-of-Sample (One-Shot)

**Objective.** Single, final, no-iteration evaluation on held-out data (2022–2024 or
whatever Step 2 locked in).

**Rules of engagement.**
- Run exactly once with the parameters and strategy code locked from Step 6.
- No look-and-tweak. If OOS fails the kill criteria, the project stops.
- "Failure on OOS suggests a different parameter would work better" is the most dangerous
  sentence in this entire document. Do not write it.

**Done when.** OOS metrics are computed, documented, and compared to IS. Decision: proceed
to paper or kill.

---

### Step 8 — Paper Trading

**Objective.** Validate that the live system reproduces the backtested behavior under real
market data, real timing, and real broker semantics — without real capital.

**Setup.**
- Live strategy connected to TWS paper account (port 7497) via `run_live.py`
- Strategy registered and selected by `STRATEGY_NAME` per `STRATEGY.md`
- All orders flow through `orders/order_handler.py` (no `placeOrder` bypass)
- Logging captures every signal, every order, every fill — and the corresponding
  bar data used to generate the signal — so trades can be reconciled against what the
  backtest would have produced on the same bars

**Duration.** Minimum 4 weeks of live paper bars covering a mix of vol regimes. Longer if
the period is unusually quiet.

**Pass criterion.** Per-trade tracking error vs same-day backtest fills < 50 bps on
average, with no unexplained outliers. The point is operational correctness, not P&L —
4 weeks is not a statistically meaningful sample for Sharpe.

**Done when.** Paper trades reconcile to backtest within tolerance for the full window, or
operational issues are surfaced and fixed and the window restarts.

---

### Step 9 — Pre-Live Checklist

Operational items that must all be done before any live capital is connected. Cross-ref
with `RISK.md`.

- [ ] System-wide per-order share-size limit implemented in `orders/order_handler.py`
      (currently a known gap in `RISK.md`)
- [ ] Kill switch flag implemented and tested
- [ ] Daily loss limit implemented (drops new orders when realized + unrealized PnL
      breaches threshold)
- [ ] PDT mitigation in place — either equity buffer + drawdown cutoff, or trade-count
      throttle. Decided in Open Decisions.
- [ ] Account number switched from paper (`DU5231415`) to live in env config
- [ ] TWS port switched from 7497 to 7496
- [ ] Reconnect behavior verified — TWS daily auto-restart does not leave the strategy in
      an inconsistent state (currently a known gap in `IBKR_NOTES.md`)
- [ ] Stale-data guard — strategy refuses to generate signals if last bar is older than
      N seconds
- [ ] Position reconciliation between `self.positions` and IBKR's `reqPositions` at start
      of every session
- [ ] Logging and alerting verified — at minimum, an alert fires on any unexpected
      strategy exit, order rejection, or DB write failure

---

### Step 10 — Live Small

**Objective.** Run the strategy live with real capital at the smallest size that is still
informative.

**Sizing.** Smallest share size that the strategy can express (1 share if the strategy
allows, else the minimum lot). Run for a minimum of 4 weeks. Track every trade against
the backtest equivalent for the same bars.

**Scaling rule.** Scale up only after:
- 4+ weeks of live small with no operational incidents
- Live tracking error within paper-trade tolerance
- Realized Sharpe within 1σ of OOS Sharpe (do not require it to match — sample is small)

**Anti-pattern to avoid.** Scaling up because early live trades happen to be profitable.
The decision to scale is operational and statistical, not a P&L vote.

---

## Cross-References

- `STRATEGY.md` — strategy interface, `OrderRequest`, `RollingWindow`, registry pattern
- `BACKTESTING.md` — `BacktestConfig`, fill assumptions, cost handling, IS/OOS discipline
- `DATA_MODEL.md` — `market_data_bars` schema, datetime normalization
- `RISK.md` — current and missing risk controls, parameters before live
- `IBKR_NOTES.md` — historical data rate limits, reconnect gap, error codes
- `ROADMAP.md` — system-wide order limits, kill switch, reconnect are in Backlog

---

## Handoff summary for Claude Code

Resolve the Open Decisions list in the doc (data source, bar size, IS/OOS split, sizing rule, exit rule, cost model, PDT mitigation). Most of these are research/operational decisions, not coding decisions.
The first thing that needs Claude Code is Step 2 data loading — once you've chosen a data source, Claude Code can build the loader into market_data_bars and verify the quality checks. Hand off at that point with: chosen data source, chosen bar size, chosen date range, and the link to this workflow doc.
Step 3 (signal EDA) happens in a notebook in research/ — that's also Claude Code territory but lower stakes since nothing is being committed to the strategy/orders path yet.

---

## Changelog

- _YYYY-MM-DD_ — Initial draft. Status: Step 1 — Framing.