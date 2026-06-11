"""
Hermetic backtest tests — synthetic bars, no TWS, no database.

These pin the behaviors the old harness got wrong: filling at the next bar's
open (no lookahead), short support, the long-only guard, commission/slippage,
limit-order crossing, and the metrics math.
"""

import pandas as pd
import pytest

from backtesting.broker import SimBroker, Fill
from backtesting.engine import BacktestEngine
from backtesting.metrics import compute_metrics, _max_drawdown
from backtesting.portfolio import Portfolio
from strategy.base_strategy import BaseStrategy
from strategy.signal import OrderRequest


def make_bars(closes, opens=None, highs=None, lows=None):
    opens = opens or closes
    highs = highs or [max(o, c) for o, c in zip(opens, closes)]
    lows = lows or [min(o, c) for o, c in zip(opens, closes)]
    return pd.DataFrame({
        "datetime": list(range(len(closes))),
        "open": opens, "high": highs, "low": lows, "close": closes,
        "volume": [100] * len(closes),
    })


class BuyOnceStrategy(BaseStrategy):
    """Buys `qty` on the first bar only, then holds."""
    def __init__(self, qty=10):
        self.qty = qty
        self._done = False

    def on_bar(self, bar, position=0.0):
        if self._done:
            return None
        self._done = True
        return self.buy(self.qty)


class AlwaysSellStrategy(BaseStrategy):
    def __init__(self, qty=10):
        self.qty = qty

    def on_bar(self, bar, position=0.0):
        return self.sell(self.qty)


# ---------------------------------------------------------------------------
# Engine: no lookahead
# ---------------------------------------------------------------------------

def _run(strategy, bars, fill="next_open", allow_short=True, **broker_kw):
    pf = Portfolio(starting_cash=100_000, allow_short=allow_short)
    broker = SimBroker(**broker_kw)
    engine = BacktestEngine(bars, strategy, pf, broker, fill=fill)
    equity, ts = engine.run()
    return pf, equity


def test_next_open_fills_at_next_bar_open_not_signal_bar_close():
    # Signal fires on bar 0 (close=10). It must fill at bar 1's OPEN (20),
    # never at bar 0's own close.
    bars = make_bars(closes=[10, 30], opens=[10, 20])
    pf, _ = _run(BuyOnceStrategy(qty=5), bars, commission_per_share=0, commission_min=0)
    assert pf.position == 5
    assert pf.avg_cost == 20  # bar 1 open, not bar 0 close (10)


def test_close_model_fills_on_signal_bar_close():
    bars = make_bars(closes=[10, 30], opens=[10, 20])
    pf, _ = _run(BuyOnceStrategy(qty=5), bars, fill="close",
                 commission_per_share=0, commission_min=0)
    assert pf.position == 5
    assert pf.avg_cost == 10  # bar 0 close


def test_last_bar_signal_never_fills_under_next_open():
    # A signal on the final bar has no next bar to fill against -> no position.
    bars = make_bars(closes=[10])
    pf, _ = _run(BuyOnceStrategy(qty=5), bars, commission_per_share=0, commission_min=0)
    assert pf.position == 0


# ---------------------------------------------------------------------------
# Short support and long-only guard
# ---------------------------------------------------------------------------

def test_allows_short_when_enabled():
    bars = make_bars(closes=[10, 10, 10], opens=[10, 10, 10])
    pf, _ = _run(AlwaysSellStrategy(qty=10), bars, allow_short=True,
                 commission_per_share=0, commission_min=0)
    assert pf.position < 0


def test_long_only_guard_caps_sell_at_position():
    bars = make_bars(closes=[10, 10, 10], opens=[10, 10, 10])
    pf, _ = _run(AlwaysSellStrategy(qty=10), bars, allow_short=False,
                 commission_per_share=0, commission_min=0)
    assert pf.position == 0  # never goes net short


# ---------------------------------------------------------------------------
# Portfolio accounting
# ---------------------------------------------------------------------------

def test_round_trip_realized_pnl_and_cash():
    pf = Portfolio(starting_cash=1000, allow_short=True)
    pf.apply(Fill(datetime=0, action="BUY", quantity=10, price=10, commission=0))
    assert pf.position == 10 and pf.avg_cost == 10 and pf.cash == 900
    pf.apply(Fill(datetime=1, action="SELL", quantity=10, price=12, commission=0))
    assert pf.position == 0
    assert pf.realized_pnl == pytest.approx(20)  # (12-10)*10
    assert pf.cash == pytest.approx(1020)


def test_crossing_through_zero_resets_avg_cost():
    pf = Portfolio(starting_cash=10_000, allow_short=True)
    pf.apply(Fill(datetime=0, action="BUY", quantity=5, price=10, commission=0))
    pf.apply(Fill(datetime=1, action="SELL", quantity=8, price=12, commission=0))
    assert pf.position == -3
    assert pf.avg_cost == 12  # residual short opened at the sell price
    assert pf.realized_pnl == pytest.approx(10)  # closed 5 @ (12-10)


def test_weighted_average_cost_on_add():
    pf = Portfolio(starting_cash=10_000, allow_short=True)
    pf.apply(Fill(datetime=0, action="BUY", quantity=10, price=10, commission=0))
    pf.apply(Fill(datetime=1, action="BUY", quantity=10, price=20, commission=0))
    assert pf.position == 20
    assert pf.avg_cost == pytest.approx(15)


# ---------------------------------------------------------------------------
# Broker: costs and limit crossing
# ---------------------------------------------------------------------------

def test_commission_min_floor_applied():
    broker = SimBroker(commission_per_share=0.005, commission_min=1.0, slippage_bps=0)
    broker.queue(OrderRequest("BUY", 10))  # 10 * 0.005 = 0.05 -> floored to 1.0
    fill = broker.fill_pending({"datetime": 0, "open": 100, "high": 100, "low": 100, "close": 100})
    assert fill.commission == 1.0


def test_slippage_moves_buy_up_and_sell_down():
    broker = SimBroker(commission_per_share=0, commission_min=0, slippage_bps=100)  # 1%
    bar = {"datetime": 0, "open": 100, "high": 100, "low": 100, "close": 100}
    broker.queue(OrderRequest("BUY", 1))
    assert broker.fill_pending(bar).price == pytest.approx(101)
    broker.queue(OrderRequest("SELL", 1))
    assert broker.fill_pending(bar).price == pytest.approx(99)


def test_limit_buy_fills_only_when_bar_trades_through():
    broker = SimBroker(commission_per_share=0, commission_min=0)
    order = OrderRequest("BUY", 1, order_type="LMT", limit_price=95)
    # Bar low 96 never reaches 95 -> no fill.
    broker.queue(order)
    assert broker.fill_pending({"datetime": 0, "open": 100, "high": 101, "low": 96, "close": 99}) is None
    # Bar low 94 crosses 95 -> fills at min(limit, open) = 95.
    broker.queue(order)
    fill = broker.fill_pending({"datetime": 1, "open": 100, "high": 101, "low": 94, "close": 96})
    assert fill is not None and fill.price == 95


def test_limit_buy_gap_fills_at_open_when_better():
    broker = SimBroker(commission_per_share=0, commission_min=0)
    broker.queue(OrderRequest("BUY", 1, order_type="LMT", limit_price=95))
    # Opens at 90, already below the 95 limit -> fill at the better open price.
    fill = broker.fill_pending({"datetime": 0, "open": 90, "high": 96, "low": 89, "close": 92})
    assert fill.price == 90


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def test_total_return_and_drawdown():
    equity = [100, 120, 60, 90]
    m = compute_metrics(equity, trades=[], bar_size="1 day")
    assert m.total_return == pytest.approx(-0.10)        # 90/100 - 1
    assert m.max_drawdown == pytest.approx(60 / 120 - 1)  # -0.5 peak(120)->trough(60)


def test_max_drawdown_monotonic_up_is_zero():
    assert _max_drawdown([100, 110, 120]) == 0.0


def test_win_rate_uses_only_closing_trades():
    from backtesting.portfolio import Trade
    trades = [
        Trade(0, "BUY", 10, 10, 0, realized=0.0),    # opening — ignored
        Trade(1, "SELL", 10, 12, 0, realized=20.0),  # win
        Trade(2, "BUY", 10, 10, 0, realized=0.0),    # opening — ignored
        Trade(3, "SELL", 10, 8, 0, realized=-20.0),  # loss
    ]
    m = compute_metrics([100, 101], trades, bar_size="1 day")
    assert m.win_rate == pytest.approx(0.5)
    assert m.total_trades == 4
