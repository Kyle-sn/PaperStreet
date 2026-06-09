# IBKR API Notes

Operational notes, gotchas, and decisions specific to the Interactive Brokers Python API.
This document supplements `IBApp.md` (which covers the EWrapper/EClient architecture) with
practical knowledge accumulated from building and running PaperStreet.

---

## Connection

### TWS vs. IB Gateway

We currently use **TWS** (Trader Workstation) for API connections, not IB Gateway. IB Gateway is
headless and lighter-weight, and is the preferred choice for unattended automated operation — but
TWS is what is running now.

- TWS paper trading port: `7497`
- TWS live trading port: `7496`
- IB Gateway paper trading port: `4002`
- IB Gateway live trading port: `4001`

TWS must be running and configured to allow API connections (Enable ActiveX and Socket Clients in
Global Configuration → API → Settings). Note that TWS has a daily auto-logout that will drop the
connection unless disabled or worked around.

### Client ID

Each connection to Gateway requires a unique `clientId` (integer). If two connections attempt to
use the same `clientId`, the second will be rejected. Use a consistent, documented `clientId` per
use case (e.g. `clientId=1` for the main app, `clientId=2` for a separate data-pull script).

### Connection Readiness

Do **not** assume the connection is ready to use immediately after `connect()` returns. The system
is ready when `nextValidId` fires on the EWrapper. Use a `threading.Event` to block the main thread
until that callback is received:

```python
connected_event = threading.Event()

def nextValidId(self, order_id):
    self.nextOrderId = order_id
    connected_event.set()

app.connect("127.0.0.1", 4002, clientId=1)
thread = threading.Thread(target=app.run, daemon=True)
thread.start()
connected_event.wait(timeout=10)
```

### Reconnect Behavior

The IBKR API does not auto-reconnect. If Gateway restarts (e.g. daily auto-restart) the socket
connection drops, `error()` fires with error code `1100` (connectivity lost) or `1102` (restored),
and `nextValidId` fires again when connectivity is restored. Currently PaperStreet does not
implement automatic reconnect logic — this is a known gap.

---

## Order IDs

### nextValidId and get_next_order_id()

IBKR requires that every `placeOrder` call use an order ID that is strictly greater than any
previously used ID. The `nextValidId` callback provides the starting point on connection.

`IBApp.get_next_order_id()` is the only correct way to obtain an order ID. It is thread-safe
(locked by `_id_lock`) and auto-increments. Never read or write `self.nextOrderId` directly.

### permId vs orderId

IBKR assigns two IDs to every order:
- `orderId` — the client-assigned ID passed to `placeOrder`. Used to match `orderStatus` callbacks.
- `permId` — a permanent, globally unique ID assigned by IBKR. Persisted to the DB via
  `update_order_status_by_ib_id()`. Use `permId` for any long-term record keeping.

---

## Market Data

### Subscription Types

| Method | Use Case | Notes |
|---|---|---|
| `reqMktData` | Live streaming quotes (bid/ask/last) | Requires market data subscription |
| `reqRealTimeBars` | 5-second OHLCV bars, live | Limited to 5-sec resolution |
| `reqHistoricalData` | OHLCV bars, historical or live "keep up to date" | Primary data source for mid-freq strategies |

For mid-frequency strategies, `reqHistoricalData` with `keepUpToDate=True` is the recommended
pattern — it backfills history on connect, then delivers new bars as they complete.

### Historical Data Rate Limits

IBKR enforces hard rate limits on `reqHistoricalData`:
- **Maximum 60 historical data requests per 10 minutes** (6 per minute)
- **Maximum 2 identical (same contract + bar size + duration) requests within 15 seconds**
- Exceeding limits results in error code `162` ("Historical Market Data Service error")

Mitigation: serialize historical data requests, add a brief delay between calls, and cache
results to the database rather than re-fetching data you already have.

### Bar Sizes (reqHistoricalData)

Valid `barSizeSetting` strings for mid-frequency use:
```
"1 min", "2 mins", "3 mins", "5 mins", "10 mins", "15 mins", "20 mins", "30 mins",
"1 hour", "2 hours", "3 hours", "4 hours", "8 hours", "1 day"
```
Note the plural-vs-singular inconsistency in IBKR's API — "1 min" but "2 mins".

### `whatToShow` Parameter

Common values for `reqHistoricalData`:
- `"TRADES"` — actual trade prices. Use this for most strategy work on equities.
- `"MIDPOINT"` — midpoint of bid/ask. Useful for instruments that trade wide.
- `"BID"` / `"ASK"` — one side of the spread.

### WAP (Weighted Average Price)

Historical bars include `bar.average` which is the volume-weighted average price (WAP/VWAP) for
that bar. This is distinct from `(open + close) / 2` and is often more useful for signal work.

---

## Account and Position Updates

### reqAccountUpdates vs. reqPositions

There are two ways to get position data from IBKR:

1. `reqAccountUpdates(True, account)` — subscribes to `updateAccountValue` and `updatePortfolio`
   callbacks. This is what PaperStreet uses. It provides a richer data set (PnL, margins, etc.)
   and fires an initial full snapshot followed by incremental updates on every change.
2. `reqPositions()` — fires `position()` callbacks with a one-time snapshot of all positions.
   The `position()` callback is implemented in IBApp but is not the primary position tracking
   mechanism.

Use `reqAccountUpdates` for live operation. `reqPositions` is useful for a one-off check or
debugging.

### Update Frequency

`updateAccountValue` and `updatePortfolio` fire:
- Once on initial subscription (full snapshot of all values)
- Subsequently only when a value changes, **or** every 3 minutes at most (IBKR pushes a
  heartbeat update even with no changes)

This means `self.account` and `self.positions` can be slightly stale between heartbeats. For a
mid-frequency system this is acceptable, but do not treat them as tick-accurate.

### Closed Positions

When `updatePortfolio` fires with `position == 0`, IBApp removes that symbol from `self.positions`.
After a full exit, `get_position(symbol)` will return `0.0` as expected.

---

## Orders and Execution

### Order Status Lifecycle

IBKR order statuses (received via `orderStatus`):
```
PreSubmitted → Submitted → Filled
                         → Cancelled
                         → Inactive  (e.g. outside trading hours)
```

Not all statuses fire on every order. The key ones to handle are:
- `Submitted` — order is live at the exchange
- `Filled` — completely filled (also confirmed by `execDetails`)
- `Cancelled` — user or system cancellation

Partial fills arrive as `orderStatus` with `filled > 0` and `remaining > 0`, followed by
`execDetails` for each partial execution.

### execDetails vs. orderStatus

Both callbacks fire on fills, but they contain different information:
- `orderStatus` — broker-level fill summary (filled qty, avg price, remaining)
- `execDetails` — individual execution record (exchange, execution ID, timestamp, side)
- `commissionReport` — commission and realized PnL, fires after `execDetails`

All three are persisted to the database. Use `execDetails` as the authoritative fill record;
`commissionReport` is linked to it via `execId`.

### Error Codes to Know

| Code | Meaning | Action |
|---|---|---|
| `2104` | Market data farm connection OK | Informational, log and ignore |
| `2106` | HMDS data farm connection OK | Informational, log and ignore |
| `2158` | Sec-def data farm connection OK | Informational, log and ignore |
| `162` | Historical data rate limit | Back off and retry |
| `200` | No security definition found | Bad contract definition |
| `201` | Order rejected | Check order parameters |
| `354` | Requested market data not subscribed | Missing market data subscription |
| `1100` | Connectivity lost | Begin reconnect procedure |
| `1102` | Connectivity restored | Re-subscribe to account updates |
| `10147` | OrderId not found (cancel) | Order may already be done |

Codes `2104`, `2106`, `2158` are handled in `IBApp.error()` as INFO-level, not errors. All others
log at ERROR level.

---

## Known Limitations and Gotchas

- **No auto-reconnect**: If Gateway restarts, the connection drops silently. Manual restart or
  custom reconnect logic is required.
- **Historical data threading**: `reqHistoricalData` is asynchronous. Use `_historical_data_event`
  to block until `historicalDataEnd` fires. Do not assume data is available immediately after
  the request call.
- **Contract qualification**: Some contracts require `reqContractDetails` to obtain the full
  `conId` before use. Unqualified contracts can result in error `200`.
- **Fractional shares**: IBKR supports fractional shares for some securities, but order quantity
  must be specified carefully. The `Decimal` type is used for position sizes in IBKR callbacks
  for this reason.
- **Paper vs. Live**: Paper trading accounts have slightly different behavior (fill simulation,
  not real market fills). Strategies validated in paper may behave differently live, especially
  around limit order fills and partial fills.
- **reqMktData snapshot mode**: Passing `snapshot=True` to `reqMktData` returns a one-time quote
  rather than a live stream. This counts against request limits differently.
