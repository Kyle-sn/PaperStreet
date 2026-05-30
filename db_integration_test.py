"""
db_integration_test.py

End-to-end test: connect to TWS (paper account), exercise every database
table, and print a pass/fail report.

Run from the project root with TWS open and logged into the paper account:

    .venv\\Scripts\\python.exe db_integration_test.py

What gets tested
----------------
  market_data_bars   — fetch 1-month SPY daily bars, save, read back
  account_snapshots  — subscribe to account updates, save snapshot
  position_snapshots — save current positions (or a zero-position sentinel)
  strategy_signals   — insert a test signal row
  orders             — place a 1-share MKT BUY on the paper account,
                       verify orderStatus callback writes status to DB
  executions         — request last-24h executions; if none exist, the
                       row from the order above is used once it arrives

The order will reach "PreSubmitted" → "Submitted" regardless of market
hours, which is enough to confirm the callback → DB path works. If the
market happens to be open the order will fill and an execution row will
also be written.
"""

import sqlite3
import threading
import time
import types

from contracts.contract_handler import ContractHandler
from database import get_db_path, initialize_db
from database import account as adb
from database import market_data as mdb
from database import trading as tdb
from ibapi.execution import ExecutionFilter
from orders.order_handler import connect_orders_handler, wait_for_next_id
from orders.order_types import market_order
from research.session import Session
from utils.connection_constants import (
    ACCOUNT_NUMBER,
    EXECUTIONS_REQUEST_ID,
)

SYMBOL = "SPY"
ORDER_QTY = 1

# ── Formatting helpers ─────────────────────────────────────────────────────────

def header(title: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")

def ok(label: str, detail: str = "") -> None:
    suffix = f"  ({detail})" if detail else ""
    print(f"  [ OK ] {label}{suffix}")

def fail(label: str, detail: str = "") -> None:
    suffix = f"  ({detail})" if detail else ""
    print(f"  [FAIL] {label}{suffix}")

def check(label: str, condition: bool, detail: str = "") -> None:
    (ok if condition else fail)(label, detail)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Initialise DB
# ══════════════════════════════════════════════════════════════════════════════

header("1. Initialise database")
initialize_db()
ok(f"DB ready", str(get_db_path()))


# ══════════════════════════════════════════════════════════════════════════════
# 2. Connect to TWS
# ══════════════════════════════════════════════════════════════════════════════

header("2. Connect to TWS (paper account)")
session = Session(account=ACCOUNT_NUMBER, timeout=10)
check("Session connected", session.is_connected)
app = session._app   # direct access to the underlying IBApp


# ══════════════════════════════════════════════════════════════════════════════
# 3. market_data_bars
# ══════════════════════════════════════════════════════════════════════════════

header(f"3. market_data_bars — {SYMBOL} 1-month daily")

df = session.market_data.get_daily_bars(SYMBOL, duration="1 M")
check("DataFrame returned from IB", df is not None and len(df) > 0, f"{len(df)} bars")

bars = [
    {
        "datetime": str(idx.date()),
        "open":      float(row["open"]),
        "high":      float(row["high"]),
        "low":       float(row["low"]),
        "close":     float(row["close"]),
        "volume":    float(row["volume"]),
        "wap":       float(row["wap"])       if "wap"       in row and row["wap"]       else None,
        "bar_count": int(row["bar_count"])   if "bar_count" in row and row["bar_count"] else None,
    }
    for idx, row in df.iterrows()
]

n = mdb.upsert_bars(SYMBOL, bars, bar_size="1 day")
check("Bars saved to market_data_bars", n >= 0, f"{n} new rows")

fetched = mdb.get_bars(SYMBOL)
check("Bars readable from DB", fetched is not None and len(fetched) > 0, f"{len(fetched)} rows")


# ══════════════════════════════════════════════════════════════════════════════
# 4. account_snapshots
# ══════════════════════════════════════════════════════════════════════════════

header("4. account_snapshots")

# The updateAccountValue callback fires immediately on subscribe and then every
# 3 minutes. Give it a few seconds to deliver the initial burst.
print("  Waiting 4s for account update callbacks…")
time.sleep(4)

cash         = app.get_current_cash_balance()
maint_margin = app.get_current_maintenance_margin()
init_margin  = app.get_current_initial_margin()
unrealized   = app.get_unrealized_pnl()
realized     = app.get_realized_pnl()

check("Cash balance received from IB", cash is not None, str(cash))

snap_id = adb.save_account_snapshot(
    account=ACCOUNT_NUMBER,
    cash_balance=cash,
    maintenance_margin=maint_margin,
    initial_margin=init_margin,
    unrealized_pnl=unrealized,
    realized_pnl=realized,
)
check("Account snapshot saved", snap_id > 0, f"row id={snap_id}")

latest = adb.get_latest_account_snapshot(ACCOUNT_NUMBER)
check(
    "Account snapshot readable and matches",
    latest is not None and latest["cash_balance"] == cash,
)


# ══════════════════════════════════════════════════════════════════════════════
# 5. position_snapshots
# ══════════════════════════════════════════════════════════════════════════════

header("5. position_snapshots")

positions = session.get_all_positions() or {}

if positions:
    for sym, pos in positions.items():
        pid = adb.save_position_snapshot(
            account=ACCOUNT_NUMBER,
            symbol=sym,
            position=pos["position"],
            market_price=pos.get("market_price"),
            market_value=pos.get("market_value"),
            average_cost=pos.get("average_cost"),
            unrealized_pnl=pos.get("unrealized_pnl"),
            realized_pnl=pos.get("realized_pnl"),
        )
    ok(f"{len(positions)} position snapshot(s) saved", ", ".join(positions.keys()))
else:
    # No open positions — write a zero-position sentinel so the table gets a row
    pid = adb.save_position_snapshot(
        account=ACCOUNT_NUMBER,
        symbol="_TEST_NO_POSITION",
        position=0.0,
    )
    check("Zero-position sentinel saved (no open positions)", pid > 0, f"row id={pid}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. strategy_signals
# ══════════════════════════════════════════════════════════════════════════════

header("6. strategy_signals")

sig_id = tdb.save_signal(
    strategy_name="MeanReversion",
    symbol=SYMBOL,
    action="BUY",
    quantity=ORDER_QTY,
    bar_datetime=str(df.index[-1].date()),
    bar_close=float(df["close"].iloc[-1]),
)
check("Signal row saved", sig_id > 0, f"row id={sig_id}")


# ══════════════════════════════════════════════════════════════════════════════
# 7. orders — place 1-share MKT BUY (paper account)
# ══════════════════════════════════════════════════════════════════════════════

header(f"7. orders — 1-share MKT BUY {SYMBOL} on paper account")

status_received = threading.Event()
order_db_id     = None
status_log      = {}

# Connect the order app (clientId=0 — Master Client ID)
order_app = connect_orders_handler()
wait_for_next_id(order_app)

# Patch orderStatus so DB is updated when IB calls back
_orig_order_status = type(order_app).orderStatus

def _patched_orderStatus(self, order_id, status, filled, remaining,
                          avg_fill_price, perm_id, parent_id, last_fill_price,
                          client_id, why_held, mkt_cap_price):
    _orig_order_status(self, order_id, status, filled, remaining,
                       avg_fill_price, perm_id, parent_id, last_fill_price,
                       client_id, why_held, mkt_cap_price)
    if order_db_id is not None:
        tdb.update_order_status(
            order_id=order_db_id,
            status=status,
            filled_quantity=float(filled),
            remaining_quantity=float(remaining),
            avg_fill_price=avg_fill_price if avg_fill_price else None,
            last_fill_price=last_fill_price if last_fill_price else None,
            ib_perm_id=perm_id if perm_id else None,
            why_held=why_held if why_held else None,
        )
        status_log.update({"status": status, "filled": float(filled)})
        status_received.set()

order_app.orderStatus = types.MethodType(_patched_orderStatus, order_app)

# Patch execDetails so fills are captured too
exec_received = threading.Event()
exec_rows     = []

_orig_exec_details = type(order_app).execDetails

def _patched_execDetails(self, req_id, contract, execution):
    _orig_exec_details(self, req_id, contract, execution)
    exec_rows.append({
        "symbol":      contract.symbol,
        "sec_type":    contract.secType,
        "ib_exec_id":  execution.execId,
        "ib_order_id": execution.orderId,
        "account":     execution.acctNumber,
        "side":        execution.side,
        "shares":      float(execution.shares),
        "price":       execution.price,
        "cum_qty":     float(execution.cumQty),
        "avg_price":   execution.avgPrice,
        "exchange":    execution.exchange,
        "executed_at": execution.time,
    })
    exec_received.set()

order_app.execDetails = types.MethodType(_patched_execDetails, order_app)

# Place the order
contract   = ContractHandler.get_contract(SYMBOL)
ib_order   = market_order("BUY", ORDER_QTY)
ib_order_id = order_app.get_next_order_id()
order_app.placeOrder(ib_order_id, contract, ib_order)

order_db_id = tdb.save_order(
    symbol=SYMBOL,
    action="BUY",
    order_type="MKT",
    quantity=ORDER_QTY,
    tif="DAY",
    ib_order_id=ib_order_id,
    strategy_name="MeanReversion",
)
check("Order row saved before callback", order_db_id > 0, f"row id={order_db_id}")
tdb.mark_signal_executed(sig_id, order_db_id)

# Wait for at least one orderStatus callback (PreSubmitted or Submitted is enough)
got_status = status_received.wait(timeout=10)
if got_status:
    ok("orderStatus callback fired and DB updated", f"status={status_log.get('status')}")
else:
    fail("orderStatus callback not received within 10s")

# Also request any executions from the last 24h (covers the case where the
# market is open and the order filled, or fills from earlier today)
print("  Requesting executions from last 24h…")
order_app.reqExecutions(EXECUTIONS_REQUEST_ID, ExecutionFilter())
exec_received.wait(timeout=5)


# ══════════════════════════════════════════════════════════════════════════════
# 8. executions — save whatever came back
# ══════════════════════════════════════════════════════════════════════════════

header("8. executions")

if exec_rows:
    saved = 0
    for e in exec_rows:
        eid = tdb.save_execution(
            symbol=e["symbol"],
            side=e["side"],
            shares=e["shares"],
            price=e["price"],
            executed_at=e["executed_at"],
            ib_exec_id=e["ib_exec_id"],
            ib_order_id=e["ib_order_id"],
            order_id=order_db_id if e["ib_order_id"] == ib_order_id else None,
            account=e["account"],
            sec_type=e["sec_type"],
            cum_qty=e["cum_qty"],
            avg_price=e["avg_price"],
            exchange=e["exchange"],
        )
        if eid:
            saved += 1
    check("Execution rows saved", saved > 0, f"{saved} of {len(exec_rows)}")
else:
    print("  No executions received (market closed or no fills today — that's OK).")
    print("  The executions table will populate the next time an order fills.")


# ══════════════════════════════════════════════════════════════════════════════
# 9. Final row-count verification
# ══════════════════════════════════════════════════════════════════════════════

header("9. Row counts")

conn = sqlite3.connect(str(get_db_path()))
tables = [
    "market_data_bars",
    "orders",
    "executions",
    "position_snapshots",
    "account_snapshots",
    "strategy_signals",
]
for table in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    check(f"{table}", count > 0, f"{count} row(s)")
conn.close()

session.disconnect()
if order_app.isConnected():
    order_app.disconnect()
print("\nDone.\n")
