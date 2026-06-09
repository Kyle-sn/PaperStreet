# PaperStreet — System Architecture

## Overview

PaperStreet is a Python-based automated trading system built on the Interactive Brokers TWS API.
It is designed for mid-frequency strategies (signal horizons of minutes to days) trading equities
and potentially futures via a personal IBKR account. The system prioritizes clean separation
between infrastructure (connectivity, data persistence, order management) and strategy logic so
that strategies can be developed, tested, and swapped without touching core plumbing.

The system is **not** a low-latency/HFT system. Network round-trips to TWS/Gateway, Python's GIL,
and IBKR's own rate limits are all acceptable constraints at mid-frequency hold times.

---

## Repository Layout

```
PaperStreet/
├── ib_app.py              # Core IBApp class (EWrapper + EClient combined)
├── IBApp.md               # Architecture notes for the IB API layer
├── database/
│   ├── account.py         # Account/position snapshot persistence
│   └── trading.py         # Order and execution persistence
├── market_data/           # Market data requests, bar handling, storage
├── contracts/             # Contract definitions and helpers
├── orders/                # Order construction and submission logic
├── positions/             # Position state helpers (wraps ib_app.positions)
├── strategy/              # Strategy implementations
├── backtesting/           # Offline backtesting harness
├── research/              # Notebooks, signal research, exploratory work
├── utils/
│   └── log_config.py      # Centralized logging setup
└── tests/                 # Unit and integration tests
```

---

## Component Responsibilities

### `ib_app.py` — IBApp

The central object of the live system. It is both the EClient (sends requests to TWS) and the
EWrapper (receives callbacks from TWS). All stateful information that comes from IBKR lives here
or is written to the database from here.

Responsibilities:
- Maintain in-memory account state (`self.account` dict)
- Maintain in-memory position state (`self.positions` dict, keyed by symbol)
- Persist account snapshots, position snapshots, order status updates, and execution records to the database
- Manage the `nextOrderId` counter in a thread-safe way
- Receive and buffer historical data, signaling completion via a threading.Event

IBApp is **not** responsible for strategy logic. It is infrastructure only.

### `database/`

Two submodules with thin persistence functions:

- `account.py` — `save_account_snapshot()`, `save_position_snapshot()`
- `trading.py` — `save_execution()`, `update_execution_commission()`, `update_order_status_by_ib_id()`, `get_order_db_id()`

The database backend is SQLite (or Postgres — see `DATA_MODEL.md`). All DB writes from IBApp
callbacks are wrapped in try/except so that a DB error never crashes the callback thread.

### `market_data/`

Handles all market data interactions with IBKR:
- Constructing and issuing `reqHistoricalData` calls
- Constructing and issuing `reqMktData` / `reqRealTimeBars` calls for live data
- Storing bars to the database for offline use and backtesting

This module is the primary data source for strategy signal generation during live trading.

### `contracts/`

Contract object construction and lookup helpers. Since IBKR requires fully specified `Contract`
objects for every request, this module centralizes them to avoid duplication across the codebase.

### `orders/`

Order construction and submission logic:
- Building IBKR `Order` objects (market, limit, bracket, etc.)
- Calling `ib_app.placeOrder()` with a fresh order ID from `get_next_order_id()`
- Potentially maintaining a local order registry for tracking in-flight orders

Orders should only be submitted from this layer — strategies should never call `placeOrder` directly.

### `positions/`

Helpers that read position state from `ib_app.positions`. This layer translates the raw dict into
useful queries (e.g. "are we flat?", "what is our current exposure?"). It reads but does not write
to IBApp state.

### `strategy/`

Strategy implementations. See `STRATEGY.md` for the expected interface and design constraints.
Strategies receive market data events or bar callbacks, compute signals, and emit order requests
to the `orders/` layer.

### `backtesting/`

Offline backtesting harness. Uses historical bar data (from the database or flat files) to simulate
strategy execution without connecting to TWS. See `BACKTESTING.md`.

### `research/`

Jupyter notebooks and exploratory scripts for signal research, data analysis, and strategy
prototyping. Code here is not held to production standards and is not imported by the live system.

### `utils/`

Shared utilities. Currently: `log_config.py` provides `setup_logger(__name__)` which all modules
call to get a consistently configured logger.

---

## Data Flow — Live Trading

```
  TWS / IB Gateway
       │
       │  EWrapper callbacks (on reader thread)
       ▼
  ib_app.py  ──────────────────────────────────────────────────►  database/
  (IBApp)                                                          (persists account,
       │                                                            positions,
       │  market data (bars, ticks)                                 orders,
       ▼                                                            executions)
  market_data/
       │
       │  bar / signal data
       ▼
  strategy/
       │
       │  order requests (symbol, side, qty, type, price)
       ▼
  orders/
       │
       │  EClient calls (placeOrder, cancelOrder)
       ▼
  TWS / IB Gateway
```

---

## Threading Model

The IBKR Python API runs its socket reader on a **background thread** managed by `EClient.run()`.
All EWrapper callbacks fire on that thread.

Rules:
1. EWrapper callbacks (anything that overrides a method on EWrapper) run on the reader thread.
   Do not perform slow I/O or blocking operations in callbacks beyond the DB writes already present.
2. EClient request methods (`reqHistoricalData`, `placeOrder`, etc.) can be called from any thread.
   The underlying socket write is not externally synchronized by IBKR — avoid concurrent calls
   from multiple threads without coordination.
3. `self.account` and `self.positions` are guarded by `self._account_lock`. Always acquire this
   lock before reading or writing these dicts from outside the callback thread.
4. `self.nextOrderId` is guarded by `self._id_lock` via `get_next_order_id()`. Always use that
   method — never increment `nextOrderId` directly.
5. `self._historical_data_event` (a `threading.Event`) is the approved pattern for blocking a
   calling thread until a historical data request completes. Check `historicalDataEnd` for usage.

---

## Connection Setup

The system currently connects via **TWS** (Trader Workstation). IB Gateway is the preferred
long-term target for unattended operation, but TWS is what is running now. The typical startup
sequence is:

1. Instantiate `IBApp()`
2. Call `app.connect(host, port, clientId)`
3. Start the reader thread: `threading.Thread(target=app.run, daemon=True).start()`
4. Wait for `nextValidId` to fire (signals the connection is ready) — use a `threading.Event`
5. Subscribe to account updates: `app.reqAccountUpdates(True, account_str)`
6. Begin market data subscriptions or historical data pulls

---

## Environment and Configuration

Secrets and configuration (TWS host/port, account number, client ID) are stored in the `env` file
(not committed). Load with `python-dotenv` or equivalent before instantiating `IBApp`. Never
hardcode credentials or account numbers in source files.
