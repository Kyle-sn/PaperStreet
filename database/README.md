# Database

SQLite persistence layer for PaperStreet. The database file lives at
`data/paperstreet.db` and is excluded from version control.

## Setup

Call `initialize_db()` once on first run or after adding new tables.
It is idempotent — safe to call on every startup if preferred.

```python
from database import initialize_db
initialize_db()
```

For adding columns to an existing table use `ALTER TABLE` directly:

```python
import sqlite3
from database import get_db_path

conn = sqlite3.connect(str(get_db_path()))
conn.execute("ALTER TABLE orders ADD COLUMN new_field TEXT")
conn.commit()
conn.close()
```

## Module layout

| File | Responsibility |
|------|----------------|
| `db.py` | `get_connection()`, `initialize_db()`, `get_db_path()` |
| `schema.sql` | All `CREATE TABLE IF NOT EXISTS` DDL |
| `market_data.py` | `upsert_bars()`, `get_bars()`, `get_latest_bar_date()` |
| `trading.py` | Orders, executions, signals |
| `account.py` | Position and account snapshots |

## Tables

### `market_data_bars`
Historical OHLCV bars fetched from IB. Keyed on
`(symbol, sec_type, bar_size, bar_datetime, what_to_show)` so
re-fetching the same range is idempotent. Populated automatically
by `ibkr_client._fetch()` after every `reqHistoricalData` response.
`bar_datetime` is normalized to a canonical ISO string on write
(`_normalize_bar_datetime`) so the idempotency key holds regardless of
the caller's input format; `migrate_bar_datetimes()` (run by
`initialize_db`) heals legacy rows written before this existed.

### `orders`
One row per order submitted to IB via `place_order()`. Written before
the order is sent so the row exists when `orderStatus` callbacks fire.
`ib_order_id` is IB's ID; `id` is the local primary key used to link
signals and executions.

### `executions`
One row per fill from `execDetails`. Idempotent on `ib_exec_id`.
Commission and realized PnL are patched in separately when the
`commissionReport` callback fires.

### `position_snapshots`
Append-only time-series of position state. Written on every
`updatePortfolio` callback, which fires on connect and on each
position change.

### `account_snapshots`
Append-only time-series of account state (cash, margins, PnL, etc.).
Written once per session in `accountDownloadEnd` after the initial
account data download completes.

### `strategy_signals`
Every signal emitted by a strategy, including no-ops (`action=NULL`).
Linked to the resulting order via `order_id` once the order is placed.

## Automatic DB writes

The following IB callbacks write to the database without any extra
code in your scripts:

| Callback | Table |
|----------|-------|
| `accountDownloadEnd` | `account_snapshots` |
| `updatePortfolio` | `position_snapshots` |
| `orderStatus` | `orders` |
| `execDetails` | `executions` |
| `commissionReport` | `executions` (commission + PnL patch) |
| `historicalData` (via `ibkr_client`) | `market_data_bars` |

All DB calls inside callbacks are wrapped in `try/except` so a
database error never crashes an IB callback thread.

## Inspecting the database

Open `data/paperstreet.db` directly in VS Code with the
**SQLite Viewer** extension, or use **DB Browser for SQLite**
(`sqlitebrowser.org`) for ad-hoc queries and row editing.
