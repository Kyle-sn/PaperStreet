# strategy/

This directory contains all trading strategies. Each strategy inherits from `BaseStrategy` and implements a single method: `on_bar`.

---

## Adding a New Strategy

### 1. Create your strategy file here in `strategy/`

Inherit from `BaseStrategy` and implement `on_bar`. That is the only contract required.

```python
# strategy/my_strategy.py

from strategy.base_strategy import BaseStrategy
from utils.log_config import setup_logger

logger = setup_logger(__name__)


class MyStrategy(BaseStrategy):

    def __init__(self, ...):
        # Store parameters
        # Initialize any internal indicator state (e.g. price history)
        # Do NOT initialize a position counter here — see Position Rule below
        ...

    def on_bar(self, bar: dict, position: float = 0.0) -> dict | None:
        # Process the incoming bar
        # Return a signal dict or None
        ...
```

### 2. Wire it into `run_live.py`

Only `initialize_strategy()` needs to change:

```python
from strategy.my_strategy import MyStrategy

def initialize_strategy():
    strategy = MyStrategy(...)
    contract = ContractHandler.get_contract("SPY")
    return strategy, contract
```

The trading loop, signal execution, and position fetching all remain untouched. They only depend on the `on_bar` interface, not the concrete strategy.

---

## The `on_bar` Interface

Every strategy must implement this signature:

```python
def on_bar(self, bar: dict, position: float = 0.0) -> dict | None:
```

**`bar`** is a dict with the following keys:

| Key        | Type    | Description              |
|------------|---------|--------------------------|
| `datetime` | str     | Timestamp of the bar     |
| `open`     | float   | Open price               |
| `high`     | float   | High price               |
| `low`      | float   | Low price                |
| `close`    | float   | Close price              |
| `volume`   | float   | Volume                   |

**`position`** is the current net shares held. See the Position Rule below.

**Return value** is either `None` (no action) or a signal dict:

```python
{"action": "BUY" | "SELL", "quantity": int}
```

---

## Position Rule

**Strategies must not track their own position internally.**

Position is always injected via the `position` parameter of `on_bar`:

- **In live trading** — the caller passes `IBApp.get_position(symbol)`, which is populated by the `updatePortfolio` EWrapper callback from TWS. This is the broker-confirmed position.
- **In backtesting** — the engine passes `Portfolio.position`, which is updated after each processed signal.

Self-tracking causes drift: the strategy's internal count can diverge from reality if the portfolio layer rejects a signal or if a fill is partial. Injecting position from the authoritative source keeps both contexts consistent.

---

## Existing Strategies

| File                        | Class                    | Description                                                    |
|-----------------------------|--------------------------|----------------------------------------------------------------|
| `base_strategy.py`          | `BaseStrategy`           | Abstract base class. All strategies inherit from this.         |
| `mean_reversion_strategy.py`| `MeanReversionStrategy`  | SMA + volatility band mean reversion. Inventory-aware.         |
| `moving_average.py`         | `MovingAverageStrategy`  | Simple SMA crossover baseline. No position awareness.          |

---

## Researching a New Strategy

Use `research/explore.ipynb` to prototype before implementing. The notebook lets you:

- Fetch intraday or daily bars for any symbol via the IBKR session
- Compute and visualize indicators interactively
- Simulate signal generation using the same logic as `on_bar`
- Tune parameters (`WINDOW`, `SPREAD_MULTIPLIER`, `MAX_POSITION`, `ORDER_SIZE`) and see the effect on signals immediately

Once the signal behavior looks right in the notebook, implement it as a strategy class here.