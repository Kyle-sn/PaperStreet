# Roadmap

A living record of what's built, what's actively in progress, and what's been decided against.
Update this file as decisions are made. The "Decided Against" section is as important as the rest.

---

## Working

Things that are functional and reasonably reliable.

- **IBApp core** — EWrapper/EClient combined class, connection to IB Gateway, reader thread
- **Account state** — `updateAccountValue` → `self.account` dict with cash, margins, PnL fields
- **Position state** — `updatePortfolio` → `self.positions` dict keyed by symbol; closed positions removed
- **Order status tracking** — `orderStatus` callback → DB update via `update_order_status_by_ib_id()`
- **Execution persistence** — `execDetails` + `commissionReport` → DB records with commission and realized PnL
- **Historical data fetch** — `reqHistoricalData` with threading.Event blocking pattern
- **Account/position snapshots** — written to DB on `accountDownloadEnd` and `updatePortfolio`
- **Thread-safe order ID management** — `get_next_order_id()` with lock
- **Logging** — centralized via `utils/log_config.py`; `setup_logger(__name__)` pattern
- **Strategy framework** — `BaseStrategy` / `BaseQuotingStrategy` ABCs, typed `OrderRequest`
  signal (`strategy/signal.py`), `RollingWindow` indicator state (`strategy/indicators.py`),
  name-based registry + `build_strategy` factory, lifecycle hooks. Runners select strategies by
  config. Contract test in `tests/test_strategy_contract.py`. (see `STRATEGY.md`)
- **Backtesting harness (bar family)** — config-driven `run_backtest(BacktestConfig)`
  (`backtesting/`): cache-first `BarDataSource`, `SimBroker` with next-bar-open fills + limit
  crossing + commission/slippage, long/short `Portfolio`, `compute_metrics` (Sharpe, drawdown,
  win rate, …), and a `BacktestResult` with `.summary()`. Hermetic tests in
  `tests/test_backtest.py`. (see `BACKTESTING.md`)

---

## In Progress

Things actively being built or recently started.

- **`market_data/` module** — bar storage, live data subscription wiring
- **`contracts/` module** — centralized contract definitions
- **`orders/` module** — order construction and submission layer; `order_from_request` translates `OrderRequest` → ibapi `Order`
- **`bars` database table** — schema and write path for storing historical and live bar data

---

## Backlog

Prioritized things not yet started.

- **`positions/` module** — position query helpers wrapping `ib_app.get_position()`
- **Risk layer in `orders/`** — system-wide pre-order checks enforced in `place_order()` before any `placeOrder` call: per-order share size limit, kill switch flag, and buying power / max exposure check against `self.account`
- **Daily loss limit** — session-level circuit breaker that halts new order submissions after realized + unrealized PnL drops below a configured threshold; reads from `self.account`
- **Backtesting: quoting family** — event-replay backtester for `BaseQuotingStrategy`
  (settlement/estimate stream, not OHLCV bars); the bar-family harness is built (see Working)
- **Multi-symbol / portfolio backtester** — a portfolio-level extension (or sibling) of the
  bar-family engine that holds a *basket* of instruments under one cash/risk account:
  portfolio sizing across instruments (inverse-vol weighting, vol-targeting), point-in-time
  vol estimation, and cross-instrument accounting. **Hard prerequisite for any cross-sectional
  / diversified strategy** — the current engine is single-symbol / one-instance (`STRATEGY.md`),
  so a basket sized as a single portfolio cannot be expressed or validated. Blocks the parked
  diversified-trend strategy (`research/diversified_trend_strategy_notes.md`). Stays the custom
  engine (extended), consistent with "Decided Against: third-party / vectorized backtesters."
- **Secrets manager** — replace hardcoded credentials and account number with a secrets manager (e.g. Windows Credential Manager, AWS Secrets Manager, or similar) before switching to IB Gateway
- **IB Gateway + IBC** — switch from TWS to headless IB Gateway; use IBC for automated login; blocked on secrets manager being in place first
- **Reconnect logic** — detect connection drop (error codes 1100/1102), re-subscribe to account updates, re-warm strategies
- **Strategy warm-up** — pull lookback bars from local DB on `on_start()`; suppress signals until minimum bar count met
- **Research parameter sweeps on the custom engine** — thin grid-search wrapper that loops
  `run_backtest()` over a parameter grid (optionally multiprocessed), feeding the research
  workflow. Built on the custom engine rather than a vectorized library so sweeps honor the
  same inventory-aware, path-dependent fills as validation (see Decided Against). Output is
  candidate parameter sets that must still pass a single `run_backtest()` before paper trading.
- **CONVENTIONS.md** — document coding patterns, naming conventions, error handling rules
- **Portfolio-level backtest evaluation** — combine equity curves across independent
  single-symbol backtests to compute portfolio Sharpe, combined drawdown, and cross-strategy
  correlation. Much lighter than the multi-symbol backtester above (post-processing on
  independent results, not a new engine); deferred until a second strategy reaches production.
- **Capital allocation across strategies** — explicit framework for splitting account equity
  across multiple concurrently live strategies (see `STRATEGY.md` → Multi-Strategy Operation).
  Allocation is implicit today; deferred until more than one strategy reaches paper trading.

---

## Decided Against / Parked

Things considered and explicitly not being pursued, with the reason.

| Item | Decision | Reason |
|---|---|---|
| Java (v1 architecture) | Abandoned | Rewriting in Python for development speed and ecosystem (pandas, numpy, Jupyter) |
| HFT / sub-second strategies | Out of scope | Infrastructure (Python, IBKR API) not suited to it; not the goal |
| Tick-level order book data | Not pursuing | Overkill for mid-frequency; IBKR's Level 2 data is expensive and adds complexity |
| Options strategies | Parked | Infrastructure not built; consider after equities are working end-to-end |
| Multi-account support | Parked | Single personal account for now; `reqAccountUpdates` only supports one subscription at a time anyway |
| External broker / exchange | Not planned | IBKR is the broker; no plans to add Alpaca, Tradier, etc. |
| Real-time dashboard / UI | Not planned | Logging + DB queries are sufficient for monitoring at this stage |
| Cloud deployment | Not planned | Runs locally against IB Gateway; cloud adds operational complexity with no clear benefit yet |
| Third-party / vectorized backtesters (vectorbt, backtrader, zipline, backtesting.py) | Not planned | Every such library imposes its own strategy API, breaking the live/backtest parity that the custom `on_bar`/`OrderRequest` contract exists to guarantee. Vectorized engines (vectorbt) also assume signals are independent of realized inventory — but **all PaperStreet strategies are inventory-aware** (position-gated, e.g. `position < max_position`), which is path-dependent and exactly what those engines model poorly. The custom engine stays the single source of truth. |
