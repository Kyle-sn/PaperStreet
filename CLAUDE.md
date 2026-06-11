# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Documentation

Detailed reference docs live in `docs/`. Before starting any task that touches a given area, read the relevant file(s) there first:

- `docs/ARCHITECTURE.md` — overall system design, component responsibilities, threading model, and data flow
- `docs/IBKR_NOTES.md` — IBKR API behavior, rate limits, error codes, and known gotchas
- `docs/RISK.md` — risk controls in place, known gaps, and parameters to review before going live
- `docs/DATA_MODEL.md` — database schema and in-memory state structures (`self.account`, `self.positions`, bar dicts)
- `docs/STRATEGY.md` — strategy interface, `OrderRequest` dataclass, and design constraints
- `docs/BACKTESTING.md` — backtesting harness design, fill assumptions, and lookahead bias rules
- `docs/ROADMAP.md` — what's built, in progress, and decided against

---

## Before Committing

Before committing any change, update documentation to reflect the work:

1. **`docs/` files** — if the change affects a component covered by a doc (e.g. adding a new module, changing an interface, adding a table), update the relevant file. Pay particular attention to `ROADMAP.md` — move items between Working / In Progress / Backlog as their status changes.
2. **Inline comments** — if the changed code has non-obvious behavior (threading invariants, IBKR-specific quirks, sentinel values), ensure the comment still accurately describes it. Remove or correct comments that no longer match the code.

Do not add comments just to document what the code does — only where the *why* is non-obvious.

---

## Commands

**Run tests:**
```bash
pytest                          # all tests
pytest tests/test_order_handler.py   # single file
pytest tests/ -k "test_name"    # single test by name
```

**Run live trading:**
```bash
python run_live.py
```

**Run backtests:**
```bash
python backtesting/run_backtest.py
```

**Fetch + cache historical data (for offline backtests):**
```bash
python -m backtesting.data SYMBOL [bar_size] [duration]   # e.g. SPY "1 day" "5 Y"
```

## Architecture

This is a Python automated trading system connecting to Interactive Brokers TWS via their official `ibapi` package. TWS must be running locally on port `7497` (paper) or `7496` (live) for any real connection to work.

### Core pattern: IBApp

`ib_app.py` contains `IBApp`, which inherits from both `EWrapper` (receives callbacks from IB) and `EClient` (sends requests to IB). This single class is the broker interface. Overriding `EWrapper` methods is how market data, order events, and account updates are received. Each IB callback that fires during live operation also writes to the SQLite database.

### Multiple connections via client IDs

Every connection to TWS requires a unique `clientId`. These are fixed in `utils/connection_constants.py`:
- `ORDERS_CLIENT_ID = 0` — order placement
- `POSITIONS_CLIENT_ID = 4001` — account/position subscriptions
- `LIVE_ENGINE_CLIENT_ID = 5001` — live trading loop
- `RESEARCH_CLIENT_ID = 6001` — notebooks and scripts

Using a mismatched or already-in-use client ID will cause a connection error.

### Session (research entry point)

`research/session.py::Session` is the preferred way to connect for scripts and notebooks. It handles the `IBApp` lifecycle (connect, thread, wait for `nextValidId`) and exposes `session.market_data` (a `MarketDataService`) and account accessors. Use `with Session() as session:` for auto-disconnect.

### Market data flow

`market_data/base.py` → `market_data/ibkr_client.py` (wraps `reqHistoricalData` and blocks on `threading.Event` until `historicalDataEnd` fires) → `market_data/market_data_service.py` (usability layer with `get_daily_bars`, `get_intraday_bars`, etc.). Multi-symbol fetches **must be sequential** — IBKR enforces a 60-request/10-minute pacing limit.

### Strategy interface

Bar strategies inherit `strategy/base_strategy.py::BaseStrategy` and implement `on_bar(bar: dict, position: float) -> OrderRequest | None`, building the return with `self.buy()`/`self.sell()` (`OrderRequest` is the typed signal in `strategy/signal.py`). The strategy does not execute trades — it only produces signals. Strategies are selected by name via `strategy/registry.py::build_strategy` (config-driven), not by import. Quoting strategies (e.g. ERCOT) are a separate family under `strategy/base_quoting_strategy.py::BaseQuotingStrategy`. See `docs/STRATEGY.md`.

### Backtesting

Config-driven and plug-and-play to match the strategy layer. A run is described by a `backtesting/config.py::BacktestConfig` (strategy name + params, symbol, data window, cost/fill model); `backtesting/runner.py::run_backtest(config)` builds the strategy by name from the registry, loads bars cache-first via `backtesting/data.py::load_bars` (`market_data_bars` → IBKR on a miss), and replays them through `backtesting/engine.py::BacktestEngine`. The engine fills the previous bar's signal at the current bar's open (`fill="next_open"`, lookahead-safe) via `backtesting/broker.py::SimBroker` (commission + slippage), accounts long/short in `backtesting/portfolio.py::Portfolio`, and returns a `backtesting/result.py::BacktestResult` with an equity curve, trade log, and metrics (`backtesting/metrics.py`). Bar-family only; the quoting/ERCOT family has no backtester yet. See `docs/BACKTESTING.md`.

### Live trading loop

`run_live.py` creates a `Session` and a separate `connect_orders_handler()` (its own `IBApp` on `ORDERS_CLIENT_ID`), then loops: fetch latest bar → strategy signal → place order via `orders/order_handler.py::place_order`. The order handler saves the order to the DB before calling `app.placeOrder`.

### Database

SQLite at `data/paperstreet.db` (WAL mode, foreign keys on). Schema lives in `database/schema.sql`. Tables: `orders`, `executions`, `position_snapshots`, `account_snapshots`, `market_data_bars`, `strategy_signals`. Database functions are organized by domain: `database/account.py`, `database/trading.py`, `database/market_data.py`. Initialize with `database/db.py::initialize_db()`.

### Test setup

`tests/conftest.py` provides a `mock_app` fixture (an `IBApp` with a mocked `EClient` so no real TWS connection is needed) and a `make_contract` fixture. Database tests are hermetic: `tests/test_database.py` exercises every table against a throwaway SQLite file (via a `temp_db` fixture that redirects `database.db._DB_PATH`) — no TWS, no real orders. `market_data/test_market_data.py` is the only suite that requires a live TWS connection (it fetches real bars); skip it when TWS is not running.
