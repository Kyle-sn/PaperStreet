# Strategy

Design guidelines, conventions, and constraints for strategy development in PaperStreet.

---

## Frequency and Scope

PaperStreet targets **mid-frequency strategies**. This means:

- Signal horizons of **minutes to days** — not tick-by-tick, not monthly rebalancing
- Primary data resolution: **1-minute to 1-day OHLCV bars**
- Acceptable latency for signal computation and order submission is on the order of seconds
- Strategies are not latency-sensitive; a few seconds of slippage between signal and execution
  is acceptable and expected at this frequency

This scope is a deliberate constraint. The infrastructure (Python, IBKR API, SQLite) is well-suited
to mid-frequency and would require significant re-architecture for HFT.

---

## Strategy Interface

Every strategy should be implemented as a class that follows a consistent interface. This allows
the system to run, test, and swap strategies without changing the surrounding infrastructure.

Proposed base interface (to be formalized as a Python ABC):

```python
class BaseStrategy:
    name: str                          # unique identifier, used for logging and DB tagging

    def on_bar(self, symbol: str, bar: dict) -> list[OrderRequest]:
        """
        Called when a new completed bar is available for the given symbol.
        Returns a (possibly empty) list of OrderRequests.
        """
        ...

    def on_fill(self, symbol: str, side: str, qty: float, price: float):
        """
        Called when an execution is confirmed for this strategy.
        Allows the strategy to update internal state (e.g. position tracking).
        """
        ...

    def on_start(self):
        """Called once when the strategy is started. Load any warm-up state here."""
        ...

    def on_stop(self):
        """Called once when the strategy is stopped. Clean up state here."""
        ...
```

### OrderRequest

Strategies should not build IBKR `Order` objects directly. They return `OrderRequest` objects
(a plain dataclass) that the `orders/` layer translates into IBKR calls:

```python
@dataclass
class OrderRequest:
    symbol:      str
    side:        str        # 'BUY' or 'SELL'
    quantity:    float
    order_type:  str        # 'MKT', 'LMT'
    limit_price: float | None = None
    tif:         str = 'DAY'
    strategy:    str = ''   # populated automatically from strategy.name
```

---

## Data Flow Into a Strategy

Strategies receive data through `on_bar()` callbacks. The bar dict has the same shape as what
comes out of `IBApp.historicalData` (see `DATA_MODEL.md`):

```python
{
    "datetime":  str,
    "open":      float,
    "high":      float,
    "low":       float,
    "close":     float,
    "volume":    Decimal,
    "wap":       float,
    "bar_count": int,
}
```

Strategies maintain their own internal bar history (e.g. a `deque` or pandas `DataFrame`) and
compute signals from it. They should not reach into `IBApp` directly for market data.

---

## Position Awareness

A strategy should know its current position to avoid double-entry and to size exit orders
correctly. There are two approaches:

1. **Track internally**: maintain a `self._position` counter updated by `on_fill()`. Simple,
   but can drift if fills come from outside the strategy (e.g. manual trades, liquidations).
2. **Query IBApp**: call `ib_app.get_position(symbol)` as the authoritative source. Slightly
   more latency, but always reflects broker-confirmed state.

Recommended: use the `get_position()` query as the source of truth, and use an internal counter
only as a sanity check.

---

## Risk Controls

Risk checks belong at two layers:

1. **In the strategy**: strategy-specific logic (e.g. max loss per day, max position size,
   entry conditions). The strategy should simply not emit `OrderRequest`s that violate its rules.

2. **In the orders layer**: system-wide hard limits that no strategy can bypass (e.g. maximum
   single-order size, kill switch for all new orders). This layer is not yet implemented.

Every strategy must implement at least:
- Position size limit: never request more than `MAX_POSITION_SIZE` shares in a single order
- Flat-at-close logic (if applicable): exit positions before market close for day-trade strategies

---

## Naming and File Conventions

- Each strategy lives in its own file under `strategy/`
- File name matches strategy class name in snake_case: `strategy/mean_reversion.py` → `class MeanReversion`
- The `strategy/` `__init__.py` does not auto-import strategies — import explicitly where needed
- Strategy `name` attribute must be unique across all strategies, as it is used to tag orders
  and executions in the database

---

## State and Warm-Up

Mid-frequency strategies typically require a lookback period before generating valid signals
(e.g. a 20-period moving average needs 20 bars of history). Handle this in `on_start()`:

1. Pull the required lookback from the `bars` database table (preferred — no IBKR call needed)
2. If unavailable locally, request via `reqHistoricalData` on startup
3. Mark the strategy as "warming up" and suppress signals until the minimum bar count is met

Never generate signals from an insufficiently populated bar window — this is a common source of
spurious trades at system start.

---

## What This Is Not

- **Not a signal research environment**: use `research/` notebooks for that
- **Not a backtester**: strategies should be backtested in `backtesting/` before being wired
  into the live system (see `BACKTESTING.md`)
- **Not responsible for order routing**: strategies emit `OrderRequest`s and do not call
  `placeOrder` directly

---

## Strategy Ideas / Research Status

_(Update this section as research progresses.)_

| Strategy | Status | Notes |
|---|---|---|
| — | Not started | |

Signals under consideration:
- Momentum / trend following on daily bars
- Mean reversion on intraday bars (1-min, 5-min)
- Volatility-based position sizing
- Gap fade (overnight gap continuation or reversal)

Signals not being pursued:
- Tick-level microstructure (outside mid-frequency scope)
- Options strategies (infrastructure not built out)
