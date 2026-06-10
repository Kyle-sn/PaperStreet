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

**Fetch historical data:**
```bash
python backtesting/run_ibkr_data.py
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

`backtesting/engine.py::BacktestEngine` iterates bars, calls `strategy.on_bar`, passes signals to `backtesting/portfolio.py::Portfolio`, and returns an equity curve as `list[float]`. Trades fill at bar close with no slippage.

### Live trading loop

`run_live.py` creates a `Session` and a separate `connect_orders_handler()` (its own `IBApp` on `ORDERS_CLIENT_ID`), then loops: fetch latest bar → strategy signal → place order via `orders/order_handler.py::place_order`. The order handler saves the order to the DB before calling `app.placeOrder`.

### Database

SQLite at `data/paperstreet.db` (WAL mode, foreign keys on). Schema lives in `database/schema.sql`. Tables: `orders`, `executions`, `position_snapshots`, `account_snapshots`, `market_data_bars`, `strategy_signals`. Database functions are organized by domain: `database/account.py`, `database/trading.py`, `database/market_data.py`. Initialize with `database/db.py::initialize_db()`.

### Test setup

`tests/conftest.py` provides a `mock_app` fixture (an `IBApp` with a mocked `EClient` so no real TWS connection is needed) and a `make_contract` fixture. Integration tests that do require a live database are in `tests/db_integration_test.py`.
