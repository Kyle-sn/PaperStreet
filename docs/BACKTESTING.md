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

```
  bars table / flat file
        │
        │  chronological bar iteration
        ▼
  BacktestEngine
        │  calls strategy.on_bar(bar, position=portfolio.position)
        ▼
  Strategy instance
        │  returns OrderRequest | None  (one symbol per instance)
        ▼
  Portfolio (simulated fills)
        │  updates simulated position / cash
        ▼
  Results / metrics
```

> Current state: `BacktestEngine` + `Portfolio` fill a single `OrderRequest` at **bar close**
> with no slippage/costs (see `engine.py`, `portfolio.py`). The richer fill model below
> (`BacktestBroker`, next-bar-open fills, `on_fill` callbacks, transaction costs) is the
> intended target, not yet built.

### BacktestBroker (simulated, planned)

The planned simulated broker handles `OrderRequest`s with simple fill assumptions:

- **Market orders**: fill at the next bar's open price
- **Limit orders**: fill if the next bar's high (for buys) or low (for sells) crosses the limit
- No partial fills simulated (all-or-nothing)
- No queue position modeled

These are optimistic assumptions. Real fill quality at mid-frequency will be worse, especially
in illiquid names or around data releases.

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

The backtest engine enforces rule 1 by design (market orders fill at next bar's open). Rules
2-4 are the responsibility of the strategy author.

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

---

## Status

Backtesting infrastructure is not yet built. This document describes the intended design.
