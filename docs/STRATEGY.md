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

## Multi-Strategy Operation

PaperStreet is designed to run multiple single-symbol strategies concurrently. Each strategy instance trades one symbol (existing constraint). Portfolio-level diversification emerges from running several uncorrelated strategies in parallel — not from any single strategy being internally diversified.

Implications:

- Each strategy must be Sharpe-positive on its own. Do not pursue strategies that depend on cross-sectional effects (inverse-vol weighting across instruments, basket-level vol targeting, cross-asset relative value) — those require multi-symbol infrastructure not yet built.
- Strategies are selected for standalone viability. Naturally single-symbol strategies (intraday patterns, mean reversion, calendar effects, single-instrument vol/term-structure trades) fit. Cross-sectional strategies (TSMOM on a basket, pairs, cross-asset RV) do not.
- Account-level constraints (PDT floor, total margin, daily loss limit, kill switch) apply across all running strategies — they are not per-strategy limits.
- Capital allocation between strategies is currently implicit. When more than one strategy reaches paper trading, an explicit allocation rule needs to be committed.

---

## Strategy Interface

There are two strategy families, kept deliberately separate because they consume different
inputs and cannot be used interchangeably:

- **Bar strategies** (`strategy/base_strategy.py::BaseStrategy`) — consume OHLCV bars via
  `on_bar` and emit `OrderRequest`s. This is the default family.
- **Quoting strategies** (`strategy/base_quoting_strategy.py::BaseQuotingStrategy`) — consume
  fair-value estimates via `on_estimate` and return a two-sided quote dict (e.g. the ERCOT
  market maker).

### One instance, one symbol

A strategy instance trades exactly one symbol. To trade multiple symbols, run multiple
instances. This keeps per-strategy state trivial (no per-symbol bookkeeping) and is why
`on_bar` takes a bar but not a symbol — the symbol is fixed on the instance (`self.symbol`,
set by the registry factory).

### BaseStrategy (bar family)

```python
class BaseStrategy(ABC):
    name: str                          # unique id; set by @register_strategy; used for DB tagging
    symbol: str                        # set by build_strategy() at construction

    def on_bar(self, bar: dict, position: float = 0.0) -> OrderRequest | None: ...

    # Order-construction helpers (auto-tag symbol + strategy name):
    def buy(self, quantity, order_type="MKT", limit_price=None, tif="DAY") -> OrderRequest: ...
    def sell(self, quantity, order_type="MKT", limit_price=None, tif="DAY") -> OrderRequest: ...

    # Lifecycle hooks — default to no-ops, override as needed:
    def on_start(self): ...            # load warm-up history here
    def on_stop(self): ...             # clean up here
    def on_fill(self, action, quantity, price): ...
```

A strategy returns a single `OrderRequest` (or `None`) per bar — not a list. Build it with
`self.buy()` / `self.sell()` so `symbol` and `strategy` are tagged automatically.

### OrderRequest

Strategies never build IBKR `Order` objects directly. They return `OrderRequest` objects
(`strategy/signal.py`, a plain dataclass) that the execution layer translates: `Portfolio`
in backtest, `orders/order_types.py::order_from_request` → `placeOrder` in live.

```python
@dataclass
class OrderRequest:
    action:      str        # 'BUY' or 'SELL'
    quantity:    float
    order_type:  str = 'MKT'   # 'MKT' or 'LMT'
    limit_price: float | None = None
    tif:         str = 'DAY'
    symbol:      str = ''   # populated automatically by buy()/sell()
    strategy:    str = ''   # populated automatically from strategy.name
```

The field is `action` (not `side`) to match `orders/order_types.py` and `Portfolio`, so it
threads through to IBKR without remapping. `__post_init__` validates action, order_type,
limit_price presence, and positive quantity.

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

**Inventory awareness is a requirement, not an option — every PaperStreet strategy is
inventory-aware.** Signals are gated on the current position (e.g. `position < max_position`
before adding, `position > 0` before selling) so the strategy never double-enters or oversizes
an exit. This is a deliberate, system-wide design constraint with two consequences worth stating:

- Strategies are **path-dependent**: the decision on bar N depends on fills realized over bars
  1…N-1. This is why backtesting uses the custom event-loop engine and not a vectorized library
  that assumes signals are independent of inventory (see `ROADMAP.md` → Decided Against, and
  `BACKTESTING.md`).
- Position must come from an authoritative source, injected per call (below), so the strategy's
  view of inventory matches reality in both live and backtest.

A strategy should know its current position to avoid double-entry and to size exit orders
correctly. There are two approaches:

1. **Track internally**: maintain a `self._position` counter updated by `on_fill()`. Simple,
   but can drift if fills come from outside the strategy (e.g. manual trades, liquidations).
2. **Query IBApp**: call `ib_app.get_position(symbol)` as the authoritative source. Slightly
   more latency, but always reflects broker-confirmed state.

Recommended (and what the shipped strategies do): do not self-track. Position is injected into
`on_bar(bar, position)` by the caller — `session.get_position(symbol)` live, `Portfolio.position`
in backtest. This eliminates drift when a signal is rejected downstream.

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

## Registry and Selection

Strategies are selected **by name**, not by import. Each concrete strategy registers itself
with a decorator:

```python
@register_strategy("mean_reversion")        # bar family
class MeanReversionStrategy(BaseStrategy): ...

@register_quoting_strategy("ercot_market_making")   # quoting family
class ERCOTMarketMakingStrategy(BaseQuotingStrategy): ...
```

`strategy/__init__.py` imports every concrete module so the registries are populated on
`import strategy`. Entry points then build by name + config — no imports to edit when swapping:

```python
from strategy.registry import build_strategy
s = build_strategy("mean_reversion", symbol="SPY",
                   params={"window": 20, "spread_multiplier": 0.5})
```

`run_live.py` drives off a `STRATEGY_NAME` / `STRATEGY_PARAMS` config block at the top of the
file; `backtesting/run_backtest.py` drives off a `CONFIG = BacktestConfig(strategy_name=...,
strategy_params=...)` block (see `BACKTESTING.md`). Both select the strategy by name — no import
edits when swapping.

## Naming and File Conventions

- Each strategy lives in its own file under `strategy/`
- File name matches strategy class name in snake_case
- Strategy `name` must be unique across all strategies — it is the registry key and tags
  orders/executions in the database. The `@register_*` decorator sets `cls.name` for you.

---

## State and Warm-Up

Mid-frequency strategies typically require a lookback period before generating valid signals
(e.g. a 20-period moving average needs 20 bars of history).

Use `strategy/indicators.py::RollingWindow` for bounded rolling state — it is a `deque` with
fixed `maxlen`, so memory stays constant in a long-running live loop (a plain list grows
without bound). `RollingWindow.ready` is `True` once the window is full; gate signals on it:

```python
self.prices.append(bar["close"])
if not self.prices.ready:
    return None        # warm-up
```

For a faster start, pre-load the lookback in `on_start()` (preferred: from the `bars` table;
otherwise `reqHistoricalData`). Never generate signals from an under-populated window — a common
source of spurious trades at system start.

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
