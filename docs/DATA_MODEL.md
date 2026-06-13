# Data Model

Data structures, database schema, and storage conventions for PaperStreet.

---

## Storage Backend

PaperStreet uses **SQLite** for local persistence. The database file lives at a path defined in
the `env` configuration. SQLite is sufficient for a single-machine, single-user system at
mid-frequency scale — query volume is low and the dataset fits comfortably in a single file.

All database access is centralized in the `database/` module:
- `database/account.py` — account and position snapshots
- `database/trading.py` — orders and executions

No other module should issue raw SQL. If new persistence is needed, add a function to the
appropriate submodule.

---

## In-Memory State (IBApp)

These dicts live on the `IBApp` instance and represent the current broker-confirmed state.
They are the source of truth during a live session. They are **not** persisted as-is — snapshots
are written to the DB on every update callback.

### `self.account`

```python
{
    "cash_balance":        float | None,   # TotalCashBalance (USD)
    "net_liquidation":     float | None,   # NetLiquidation (USD)
    "gross_position_value": float | None,  # GrossPositionValue (USD)
    "buying_power":        float | None,   # BuyingPower (USD)
    "excess_liquidity":    float | None,   # ExcessLiquidity (USD)
    "maintenance_margin":  float | None,   # MaintMarginReq (USD)
    "initial_margin":      float | None,   # InitMarginReq (USD)
    "realized_pnl":        float | None,   # RealizedPnL (USD)
    "unrealized_pnl":      float | None,   # UnrealizedPnL (USD)
}
```

Updated by `updateAccountValue` callbacks. Protected by `_account_lock`.
Access via `get_current_cash_balance()`, `get_realized_pnl()`, etc.

### `self.positions`

```python
{
    "AAPL": {
        "position":      float,   # Net shares held. Negative = short.
        "market_price":  float,   # Last known market price from IBKR
        "market_value":  float,   # position * market_price
        "average_cost":  float,   # Cost basis per share (includes commissions)
        "unrealized_pnl": float,
        "realized_pnl":  float,
    },
    # ... one entry per symbol with non-zero position
}
```

Updated by `updatePortfolio` callbacks. Symbols with `position == 0` are removed.
Protected by `_account_lock`. `get_position(symbol)` is the access path for position state; it is
also what feeds the `position` argument injected into strategies — see `STRATEGY.md` → Position
Awareness for that rule.

Note: keyed by `contract.symbol` (e.g. `"AAPL"`), not by `conId`. For most equity strategies
this is unambiguous. If the system ever trades instruments where the same symbol appears on
multiple exchanges or in multiple currencies, this key scheme will need revision.

---

## Database Tables

### `account_snapshots`

Point-in-time snapshots of the account summary, written on every `accountDownloadEnd` callback.

```sql
CREATE TABLE account_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account             TEXT    NOT NULL,
    captured_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cash_balance        REAL,
    net_liquidation     REAL,
    gross_position_value REAL,
    buying_power        REAL,
    excess_liquidity    REAL,
    maintenance_margin  REAL,
    initial_margin      REAL,
    realized_pnl        REAL,
    unrealized_pnl      REAL
);
```

### `position_snapshots`

Point-in-time snapshots of individual positions, written on every `updatePortfolio` callback.
This creates a time series of position state — useful for PnL attribution and debugging.

```sql
CREATE TABLE position_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account         TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    captured_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    position        REAL    NOT NULL,
    sec_type        TEXT,
    currency        TEXT,
    con_id          INTEGER,
    market_price    REAL,
    market_value    REAL,
    average_cost    REAL,
    unrealized_pnl  REAL,
    realized_pnl    REAL
);
```

### `orders`

One row per order submitted to IBKR. Written at order submission time; updated as `orderStatus`
callbacks arrive.

```sql
CREATE TABLE orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ib_order_id         INTEGER UNIQUE NOT NULL,   -- client-assigned orderId
    ib_perm_id          INTEGER,                   -- IBKR permanent ID (set after submission)
    symbol              TEXT    NOT NULL,
    sec_type            TEXT,
    side                TEXT    NOT NULL,           -- 'BUY' or 'SELL'
    order_type          TEXT    NOT NULL,           -- 'MKT', 'LMT', etc.
    quantity            REAL    NOT NULL,
    limit_price         REAL,
    status              TEXT,                       -- last known IBKR status string
    filled_quantity     REAL,
    remaining_quantity  REAL,
    avg_fill_price      REAL,
    last_fill_price     REAL,
    why_held            TEXT,
    strategy            TEXT,                       -- strategy name that originated the order
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `executions`

One row per execution (partial or full fill). Linked to `orders` via `order_id`. Written by
`execDetails` callback; commission fields updated by `commissionReport`.

```sql
CREATE TABLE executions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER REFERENCES orders(id),
    ib_exec_id          TEXT    UNIQUE NOT NULL,   -- IBKR execution ID
    ib_order_id         INTEGER NOT NULL,
    symbol              TEXT    NOT NULL,
    sec_type            TEXT,
    account             TEXT,
    side                TEXT    NOT NULL,           -- 'BOT' or 'SLD' (IBKR convention)
    shares              REAL    NOT NULL,
    price               REAL    NOT NULL,
    avg_price           REAL,
    cum_qty             REAL,
    executed_at         DATETIME NOT NULL,
    exchange            TEXT,
    liquidation         BOOLEAN NOT NULL DEFAULT FALSE,
    commission          REAL,
    commission_currency TEXT,
    realized_pnl        REAL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `bars` (planned)

Historical and live bar data stored by `market_data/`. Enables backtesting without re-fetching
from IBKR and provides a local history for signal computation on reconnect.

```sql
CREATE TABLE bars (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT    NOT NULL,
    bar_size    TEXT    NOT NULL,   -- e.g. '1 min', '1 day'
    datetime    DATETIME NOT NULL,
    open        REAL    NOT NULL,
    high        REAL    NOT NULL,
    low         REAL    NOT NULL,
    close       REAL    NOT NULL,
    volume      REAL,
    wap         REAL,               -- volume-weighted average price for the bar
    bar_count   INTEGER,            -- number of trades in the bar
    UNIQUE (symbol, bar_size, datetime)
);
CREATE INDEX idx_bars_lookup ON bars (symbol, bar_size, datetime);
```

---

## Key Data Structures (Python)

### Bar (in-memory, from historicalData callback)

Currently stored as a plain dict in `self.historical_data`. The shape is:

```python
{
    "datetime":  str,    # IBKR date string — format varies by bar size
                         # e.g. "20240115 09:30:00 US/Eastern" for intraday
                         #      "20240115" for daily
    "open":      float,
    "high":      float,
    "low":       float,
    "close":     float,
    "volume":    Decimal,
    "wap":       float,   # bar.average — volume-weighted avg price
    "bar_count": int,     # number of trades in the bar
}
```

When consuming bar data for strategy work, convert `datetime` to a proper `datetime` object.
Be mindful of timezone — IBKR returns intraday times in the exchange timezone unless overridden.

### Contract (IBKR)

Use IBKR's `Contract` object from `ibapi.contract`. Minimum fields for a US equity:

```python
from ibapi.contract import Contract

contract = Contract()
contract.symbol   = "AAPL"
contract.secType  = "STK"
contract.currency = "USD"
contract.exchange = "SMART"   # IBKR smart routing
```

For futures or other instruments, additional fields (`lastTradeDateOrContractMonth`, `multiplier`,
`exchange`) must be set correctly. Define all contracts in `contracts/` — never inline them.

### Order (IBKR)

Use IBKR's `Order` object from `ibapi.order`. Minimum fields for a market order:

```python
from ibapi.order import Order

order = Order()
order.action        = "BUY"    # or "SELL"
order.orderType     = "MKT"
order.totalQuantity = 100
order.tif           = "DAY"    # time-in-force: DAY, GTC, IOC, etc.
```

Order construction should live in `orders/` only.

---

## Conventions

- All monetary values are stored as `REAL` (float) in USD unless otherwise noted.
- `bar_datetime` in `market_data_bars` is always stored as a canonical **ISO 8601** string —
  date-only (`"YYYY-MM-DD"`) for daily/weekly/monthly bars, full ISO for intraday.
  `database/market_data.py::_normalize_bar_datetime` coerces every write (raw IBKR
  `"YYYYMMDD"` / `"YYYYMMDD  HH:MM:SS"` or already-ISO) into this form so the UNIQUE key
  dedups correctly. `migrate_bar_datetimes()` (run by `initialize_db`) rewrites any legacy
  non-ISO rows and drops the duplicates they created.
- `executed_at` in `executions` uses the timestamp string from IBKR's `Execution.time` field,
  which is in the format `"YYYYMMDD  HH:MM:SS"` (note double space). Parse before storing if
  you want proper DATETIME indexing.
- IBKR uses `1e308` as a sentinel for "not available" on float fields in `CommissionReport`.
  This is already handled in `commissionReport()` — store `None` when the value is `>= 1e308`.
- `side` in `executions` follows IBKR convention: `"BOT"` (bought) and `"SLD"` (sold).
  In `orders`, use `"BUY"` and `"SELL"` to match IBKR's `Order.action` field.
