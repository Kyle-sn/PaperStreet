# Backtesting

Design notes and conventions for PaperStreet's backtesting harness.

---

## Purpose

The `backtesting/` module provides a way to evaluate strategy logic against historical bar data
without connecting to TWS or submitting real orders. A strategy that passes backtest validation
is a prerequisite for running it in paper trading.

Backtesting in PaperStreet is intentionally simple — no order book simulation, no intraday
tick replay, no multi-asset portfolio optimization. The goal is fast iteration on signal quality
and basic parameter validation at mid-frequency bar resolution.

---

## Frequency and Data

Strategies target **minutes-to-days** hold times, so the primary testing resolution is:

- **1-minute bars** for intraday strategies
- **Daily bars** for multi-day / swing strategies

Bar data comes from the local `bars` database table (see `DATA_MODEL.md`). If data is not
available locally, it can be fetched from IBKR via `reqHistoricalData` and stored before
running a backtest.

IBKR historical data availability (approximate):
- 1-min bars: up to 30 days back
- 5-min bars: up to 6 months back
- Daily bars: up to 20 years back (for most liquid instruments)

For deeper history, alternative sources (Yahoo Finance via `yfinance`, Polygon.io, etc.) can
supplement IBKR data. Store everything in the same `bars` table schema for uniformity.

---

## Architecture

The backtesting harness is a lightweight event loop that replays bars in chronological order
and calls the same strategy interface used in live trading. A strategy should not know whether
it is running live or in a backtest.

It is deliberately an **event loop**, not a vectorized engine. Every PaperStreet strategy is
inventory-aware (see `STRATEGY.md` → Position Awareness): signals are gated on the position
realized by prior fills, so the strategy is path-dependent. A bar-by-bar loop that feeds
`portfolio.position` back into `on_bar` is the natural fit; vectorized libraries (vectorbt etc.)
assume signals are independent of inventory and so are not used (see `ROADMAP.md` → Decided
Against). When research needs parameter sweeps, loop this engine rather than reaching for one of
those libraries.

A run is fully described by a single `BacktestConfig` (`backtesting/config.py`) — strategy
name + params, symbol, data window, and cost/fill model. `run_backtest(config)`
(`backtesting/runner.py`) is the one-call entry point; it builds the strategy by name from the
same registry the live loop uses, so swapping anything is a config change, not an engine edit.

```
  BacktestConfig  (strategy name + params, symbol, window, costs, fill model)
        │
        ▼
  BarDataSource (backtesting/data.py)        cache-first: market_data_bars → IBKR on miss
        │  DataFrame: datetime + OHLCV
        ▼
  BacktestEngine (backtesting/engine.py)
        │  per bar: fill prior signal → strategy.on_bar(bar, portfolio.position) → queue
        ▼
  SimBroker (backtesting/broker.py)          fills + commission + slippage → Fill
        │
        ▼
  Portfolio (backtesting/portfolio.py)       long/short cash + position + realized PnL
        │
        ▼
  compute_metrics → BacktestResult           equity curve + trades + metrics; .summary()
```

Module map:

| File | Responsibility |
|---|---|
| `config.py` | `BacktestConfig` — the declarative run spec |
| `data.py` | `load_bars()` — cache-first loader (`db` / `ibkr` / `auto`) |
| `broker.py` | `SimBroker` — fill model, commission, slippage; emits `Fill` |
| `portfolio.py` | `Portfolio` — cash/position accounting with long & short support |
| `engine.py` | `BacktestEngine` — the replay loop (enforces no-lookahead) |
| `metrics.py` | `compute_metrics()` — the output-metrics table below |
| `result.py` | `BacktestResult` — equity + trades + metrics, `.summary()` / frames |
| `runner.py` | `run_backtest(config)` — orchestration entry point |
| `run_backtest.py` | thin CLI with a `CONFIG` block, like `run_live.py` |

### SimBroker fill assumptions

`SimBroker` handles `OrderRequest`s with simple, conservative assumptions:

- **Market orders**: fill at the next bar's open (`fill="next_open"`, the default and only
  lookahead-safe model), then pay `slippage_bps` of that price — buys fill higher, sells lower.
- **Limit orders**: fill only if the bar trades through the limit (buy: low ≤ limit; sell:
  high ≥ limit), at the better of the limit and the reference price. Limit fills pay no slippage.
- Commission is `max(commission_min, commission_per_share × qty)` per fill.
- Good-for-one-bar: an unfilled limit is dropped, not carried forward. No partial fills, no
  queue position.

These are optimistic assumptions. Real fill quality at mid-frequency will be worse, especially
in illiquid names or around data releases. A `fill="close"` model (fill on the signalling bar's
own close) exists for quick comparisons only — it is optimistic and not lookahead-safe.

---

## Transaction Costs

Always include transaction costs. IBKR charges approximately:
- **Equities**: $0.005/share, minimum $1.00, maximum 1% of trade value (tiered pricing)
- **No exchange fees** for most retail orders (payment for order flow / PFOF model varies)

Apply a simple per-share commission in the backtest engine rather than ignoring costs. For
mid-frequency strategies with many small trades, commissions can materially erode returns.

Slippage modeling:
- A conservative default: assume you pay **half the average bid-ask spread** per side
- For liquid large-caps (SPY, AAPL, etc.), spread is negligible at mid-frequency sizes
- For small/mid-caps, spread can be a significant cost

---

## Avoiding Lookahead Bias

The most common backtesting error. Rules:

1. A bar signal is computed **after the bar closes** — you cannot use the close price of bar N
   to trade at the open of bar N. You can only trade at the open of bar N+1 or later.
2. Never use future bar data (N+1, N+2, ...) to compute a signal for bar N.
3. When using pandas, avoid `shift()` mistakes — be explicit about which period's data is
   used for signal generation vs. which period's price is used for fill simulation.
4. Volume-weighted features (VWAP, WAP) from bar N are only known after bar N closes.

The backtest engine enforces rule 1 by design: under the default `next_open` model, each bar
first fills the order queued on the *previous* bar (at this bar's open) and only then calls
`strategy.on_bar` on this bar's close, so a signal can never trade on the same bar that produced
it. Rules 2-4 are the responsibility of the strategy author.

---

## Output Metrics

A backtest run should produce at minimum:

| Metric | Description |
|---|---|
| Total return | Cumulative % return over the period |
| Annualized return | Geometric annualized return |
| Sharpe ratio | Risk-adjusted return (annualized, excess over cash) |
| Max drawdown | Peak-to-trough decline as % of portfolio value |
| Win rate | % of trades that were profitable |
| Avg win / avg loss | Ratio of average winning trade to average losing trade |
| Total trades | Number of round-trip trades |
| Total commission | Total commissions paid |

---

## What Backtesting Does Not Validate

- **Execution risk**: slippage, partial fills, order rejections
- **Connectivity risk**: what happens if TWS disconnects mid-trade
- **IBKR-specific behavior**: paper fills ≠ real fills ≠ backtest fills
- **Regime change**: a strategy that worked 2019-2022 may not work in a different volatility regime
- **Overfitting**: running many parameter combinations on the same dataset will produce spurious results

Run any strategy on **out-of-sample data** before paper trading. Split your dataset: use the first
portion for development and the held-out tail for final validation.

Portfolio-level evaluation across multiple strategies is not currently built. Each strategy is backtested in isolation. When multiple strategies are candidates for concurrent live operation, combining their equity curves and computing portfolio-level metrics (combined Sharpe, joint drawdown, cross-strategy correlation) becomes necessary — see ROADMAP.md backlog. This is much lighter work than a full multi-symbol backtester and can be done as post-processing on independent backtest results.

---

## Usage

Programmatic (notebooks, scripts):

```python
from backtesting import BacktestConfig, run_backtest

result = run_backtest(BacktestConfig(
    strategy_name="mean_reversion", symbol="SPY",
    strategy_params={"window": 20, "spread_multiplier": 0.5, "order_size": 10},
    bar_size="1 day", starting_cash=100_000, slippage_bps=1.0,
))
print(result.summary())          # metrics table
result.equity_frame().plot()     # equity curve
result.trades_frame()            # trade log
```

CLI: edit the `CONFIG` block in `backtesting/run_backtest.py`, then
`python backtesting/run_backtest.py`.

Data is read from the local `market_data_bars` cache by default (`data_source="auto"`) and
only fetched from TWS on a miss. Pre-warm a symbol for fully offline iteration with
`python -m backtesting.data SYMBOL [bar_size] [duration]`.

## Status

The **bar-strategy** harness is built (`backtesting/`, see the module map above) with hermetic
tests in `tests/test_backtest.py`. A separate **quoting-family** (event-replay) backtester for
`BaseQuotingStrategy` is not yet built (see `ROADMAP.md`).
