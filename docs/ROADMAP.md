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

---

## In Progress

Things actively being built or recently started.

- **`market_data/` module** — bar storage, live data subscription wiring
- **`contracts/` module** — centralized contract definitions
- **`orders/` module** — order construction and submission layer; `OrderRequest` dataclass
- **`bars` database table** — schema and write path for storing historical and live bar data
- **Strategy interface** — `BaseStrategy` ABC and `on_bar` / `on_fill` / `on_start` / `on_stop` pattern

---

## Backlog

Prioritized things not yet started.

- **`positions/` module** — position query helpers wrapping `ib_app.get_position()`
- **Risk layer in `orders/`** — system-wide order size limits and kill switch; enforced before any `placeOrder` call
- **Backtesting harness** — `BacktestEngine` + simulated `BacktestBroker`; see `BACKTESTING.md`
- **Reconnect logic** — detect connection drop (error codes 1100/1102), re-subscribe to account updates, re-warm strategies
- **Strategy warm-up** — pull lookback bars from local DB on `on_start()`; suppress signals until minimum bar count met
- **First strategy** — signal research → backtest → paper trading (see `STRATEGY.md` for candidates)
- **CONVENTIONS.md** — document coding patterns, naming conventions, error handling rules

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
