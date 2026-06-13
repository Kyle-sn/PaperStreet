# Risk Controls

Documents the risk controls currently in place, where they live in the code, and known gaps.
Read this before touching `orders/`, `strategy/`, or `run_live.py`.

---

## Current State

PaperStreet is running on a **paper trading account only**. No real money is at risk today.
That said, the risk architecture should be built as if it were live — retrofitting risk controls
after going live is dangerous. The gaps below are known and should be closed before any live
account connection.

---

## Controls In Place

### Strategy-level position cap

`MeanReversionStrategy` (and all strategies should) enforce a `max_position` parameter. The
strategy will not emit a BUY signal if `position >= max_position`, preventing runaway inventory
accumulation during a trending move. This is strategy-specific logic — each strategy is
responsible for its own position cap.

Current live config (`run_live.py`):
```python
MeanReversionStrategy(window=3, spread_multiplier=1.0, max_position=50, order_size=10)
```

### Strategy-level order sizing

`order_size` on the strategy controls shares per signal. All order types in `order_types.py`
accept `quantity` as a parameter — there is no automatic sizing at the order layer.

### Duplicate signal suppression

`run_live.py` tracks `last_signal` and suppresses consecutive signals in the same direction.
This prevents re-submitting the same directional order on every bar when the strategy keeps
firing the same action without a fill or position change in between.

### Long-only, DAY orders only

Current strategies only go long (BUY to enter, SELL to flatten). No short positions are taken.
All orders constructed in `order_types.py` use `tif = "DAY"` — no GTC orders that could
persist across sessions and execute unexpectedly.

### Broker-authoritative position

Strategies receive position via `IBApp.get_position(symbol)`, which is populated by the
`updatePortfolio` EWrapper callback — not self-tracked. This means position used for signal
gating always reflects broker-confirmed state, not an internal counter that could drift.

---

## Known Gaps

These controls do not yet exist. Do not assume they are enforced anywhere.

### No system-wide order size limit

There is no check in `place_order()` or anywhere in `orders/` that rejects an order with an
unreasonably large quantity. A buggy strategy returning `quantity=10000` would be submitted
directly to IBKR. **This must be added to `orders/order_handler.py` before going live.**

### No kill switch

There is no mechanism to halt all new order submissions system-wide without stopping the
process. A kill switch should be a flag checked in `place_order()` before calling
`app.placeOrder()`. This is in the Roadmap backlog.

### No max portfolio exposure check

There is no check against total portfolio value or available cash before placing an order.
The system relies entirely on IBKR to reject orders that exceed buying power.

### No daily loss limit

There is no circuit breaker that stops trading after a threshold loss is reached in a session.
This would need to compare realized + unrealized PnL from `self.account` against a configured
limit.

### No reconnect / stale-data guard

If TWS drops the connection, the live loop will attempt to fetch market data from a
disconnected app. There is no check that the connection is alive before trading. See
`IBKR_NOTES.md` for error codes 1100/1102.

---

## Where Risk Checks Belong

Risk is enforced at two layers. This is the authoritative description; `STRATEGY.md` covers the
strategy author's obligations within layer 1 and points here for the rest.

1. **Strategy layer** — strategy-specific rules (max position, entry conditions, flat-at-close).
   Enforced by the strategy not emitting a signal. Already partially in place.

2. **Orders layer (`orders/order_handler.py`)** — system-wide hard limits that no strategy can
   bypass. Enforced in `place_order()` before calling `app.placeOrder()`. **Not yet implemented.**
   When built, this layer should reject or clamp:
   - Orders exceeding a per-order share limit
   - Orders when the kill switch is active
   - Orders when the connection is not confirmed live

Strategies should never call `app.placeOrder()` directly — all orders flow through `place_order()`
so the orders layer can enforce system-wide rules consistently.

---

## Parameters to Set Before Going Live

These are currently configured for paper trading. Review and tighten before connecting a live
account:

| Parameter | Current (paper) | Notes |
|---|---|---|
| `max_position` | 50 shares | Per-strategy cap; set per instrument |
| `order_size` | 10 shares | Per-signal quantity |
| `ACCOUNT_NUMBER` | `DU5231415` | Paper account; must change for live |
| `BROKER_CONNECTION_PORT` | `7497` | Paper TWS port; `7496` for live TWS |
| System-wide order size limit | Not implemented | Add before live |
| Kill switch | Not implemented | Add before live |

- Starting capital is $50k; hard floor is $25k (PDT). The buffer is $25k of drawdown capacity in absolute terms — design risk limits against the floor, not against starting equity.
- Account-level limits (kill switch, daily loss limit, total margin usage, PDT proximity alert) apply across the sum of all running strategies, not per-strategy. When the kill switch is implemented, it must halt all strategy instances, not just one.
- Per-strategy risk controls (position cap, order sizing) remain the strategy's responsibility but are not a substitute for account-level limits.
