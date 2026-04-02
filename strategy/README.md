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

### 3. Wire it into `run_backtest.py`

Same swap — just change the import and instantiation:

```python
from strategy.my_strategy import MyStrategy

strategy = MyStrategy(...)
```

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

| File                         | Class                   | Description                                             |
|------------------------------|-------------------------|---------------------------------------------------------|
| `base_strategy.py`           | `BaseStrategy`          | Abstract base class. All strategies inherit from this.  |
| `mean_reversion_strategy.py` | `MeanReversionStrategy` | SMA + volatility band mean reversion. Inventory-aware.  |
| `moving_average.py`          | `MovingAverageStrategy` | Simple SMA crossover baseline. No position awareness.   |

---

## Research Workflow

Use `research/explore.ipynb` to prototype and validate before implementing a strategy. The notebook is organized as a sequential pipeline — each stage feeds the next.

### Pipeline Overview

```
Fetch → Indicator Analysis → Feature Engineering → ML → Parameter Optimization → best_params → Signal Overlay → Out-of-Sample Validation
```

### What each stage does

**Fetch (section 2)**
Pull historical bars for a symbol via the IBKR session. Set `SYMBOL`, `BAR_SIZE`, and `DURATION` here. All downstream cells operate on this data.

**Indicator Analysis (section 4)**
Set strategy parameters manually (`WINDOW`, `SPREAD_MULTIPLIER`, `MAX_POSITION`, `ORDER_SIZE`) and compute the indicators the strategy uses internally: SMA, volatility, bands, deviation. This is your starting point for exploration — adjust these values and re-run to see how the indicators respond.

**Feature Engineering**
Derives ML-ready features from the indicators computed in section 4, and computes forward return labels (did price move up meaningfully N bars later?). Two key variables to tune:

- `FORWARD_BARS` — how far ahead to look when defining a profitable trade
- `PROFIT_THRESHOLD` — minimum return required to label a bar as profitable

**ML — Random Forest**
Trains a binary classifier to predict whether a signal will be profitable. Answers the question: *given these indicator conditions, is this signal worth acting on?*

Interpret the output via the classification report:
- Focus on the `1` row (predicted profitable) — precision and recall tell you how reliably the model identifies good signals
- 70% accuracy with poor `1` recall means the model is just predicting "don't trade" most of the time — get more data
- After training, check `model.feature_importances_` to see which features the model found useful

**Parameter Optimization**
Systematically tests combinations of `WINDOW` and `SPREAD_MULTIPLIER` (and any other parameters you add) across a grid and ranks them by PnL. Answers the question: *what parameter settings produce the most profitable signals historically?*

This is separate from ML — it finds the best settings, ML then filters individual signals at those settings.

**best_params cell**
Captures the parameters you landed on after optimization and ML analysis into a single dict. Run this when you are satisfied with your research. The signal overlay reads from here automatically.

```python
best_params = {
    "window":            WINDOW,
    "spread_multiplier": SPREAD_MULTIPLIER,
    "max_position":      MAX_POSITION,
    "order_size":        ORDER_SIZE,
}
```

**Signal Overlay (section 5)**
Visualizes BUY and SELL signals on the price chart using parameters from `best_params`. Falls back to section 4 values if `best_params` has not been run.

**Out-of-Sample Validation**
The most important step before trusting any results. Splits the data into two non-overlapping periods:

- **In-sample** — the period used for optimization and ML training (earlier data)
- **Out-of-sample** — a held-out period never touched during research (later data)

Re-runs the parameter optimization and signal simulation on the out-of-sample period using the parameters found in-sample. If PnL and signal quality hold up on data the model has never seen, the results are more likely to generalize to live trading. If they collapse, the parameters were overfitting to the specific in-sample period and should not be trusted.

**Never use out-of-sample data during research.** It exists only for final validation. Peeking at it during parameter tuning invalidates it.

### Key rules to avoid fooling yourself

**Always use `shuffle=False` for train/test splits.** With time series data, the test set must always be in the future relative to the training set. Shuffling creates lookahead bias — your results will look great but be completely fake.

**Never optimize on out-of-sample data.** Define the split once, run all research on in-sample only, then evaluate on out-of-sample once at the end.

**More data beats a better model.** One week of 1-minute bars (~1,950 rows) is too thin to trust. Pull several months across multiple symbols before drawing conclusions.

**Be skeptical of strong results on small datasets.** If accuracy looks surprisingly good, check for lookahead bias first.

### Typical research session

1. Fetch several months of data for one or more symbols
2. Set a reasonable starting point in section 4 (e.g. `WINDOW=20`, `SPREAD_MULTIPLIER=1.0`)
3. Run feature engineering — adjust `FORWARD_BARS` and `PROFIT_THRESHOLD` until label distribution is roughly balanced
4. Run ML — check feature importances to understand which indicators matter
5. Run parameter optimization — identify the top-performing parameter combinations
6. Update section 4 with the best parameters, re-run indicators
7. Run `best_params` cell to lock in the values
8. Run out-of-sample validation — only trust results that hold up here
9. If validation passes, implement the strategy as a class in this directory

Once the signal behavior looks right in the notebook, implement it as a strategy class here and wire it into `run_live.py` and `run_backtest.py` as described above.