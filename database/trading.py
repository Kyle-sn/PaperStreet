from typing import Optional
from .db import get_connection


def save_order(
    symbol: str,
    action: str,
    order_type: str,
    quantity: float,
    sec_type: str = "STK",
    tif: str = "DAY",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    trail_percent: Optional[float] = None,
    trail_amount: Optional[float] = None,
    outside_rth: bool = False,
    ib_order_id: Optional[int] = None,
    ib_parent_id: Optional[int] = None,
    strategy_name: Optional[str] = None,
) -> int:
    """Insert a new order row and return its local primary key."""
    sql = """
        INSERT INTO orders
            (symbol, sec_type, action, order_type, tif, quantity,
             limit_price, stop_price, trail_percent, trail_amount,
             outside_rth, ib_order_id, ib_parent_id, remaining_quantity, strategy_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (
            symbol, sec_type, action, order_type, tif, quantity,
            limit_price, stop_price, trail_percent, trail_amount,
            1 if outside_rth else 0,
            ib_order_id, ib_parent_id, quantity, strategy_name,
        ))
        return cur.lastrowid


def update_order_status(
    order_id: int,
    status: str,
    filled_quantity: float = 0,
    remaining_quantity: Optional[float] = None,
    avg_fill_price: Optional[float] = None,
    last_fill_price: Optional[float] = None,
    ib_perm_id: Optional[int] = None,
    why_held: Optional[str] = None,
) -> None:
    """Update an order's status from an orderStatus() callback."""
    sql = """
        UPDATE orders SET
            status             = ?,
            filled_quantity    = ?,
            remaining_quantity = ?,
            avg_fill_price     = ?,
            last_fill_price    = ?,
            ib_perm_id         = COALESCE(?, ib_perm_id),
            why_held           = ?,
            updated_at         = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        WHERE id = ?
    """
    with get_connection() as conn:
        conn.execute(sql, (
            status, filled_quantity, remaining_quantity,
            avg_fill_price, last_fill_price, ib_perm_id, why_held, order_id,
        ))


def link_ib_order_id(order_id: int, ib_order_id: int) -> None:
    """Associate an IB-assigned order ID with a locally-created order row."""
    with get_connection() as conn:
        conn.execute("UPDATE orders SET ib_order_id = ? WHERE id = ?", (ib_order_id, order_id))


def save_execution(
    symbol: str,
    side: str,
    shares: float,
    price: float,
    executed_at: str,
    ib_exec_id: Optional[str] = None,
    ib_order_id: Optional[int] = None,
    order_id: Optional[int] = None,
    account: Optional[str] = None,
    sec_type: str = "STK",
    cum_qty: Optional[float] = None,
    avg_price: Optional[float] = None,
    commission: Optional[float] = None,
    commission_currency: Optional[str] = None,
    realized_pnl: Optional[float] = None,
    liquidation: bool = False,
    exchange: Optional[str] = None,
) -> int:
    """Record a fill from an execDetails() + commissionReport() callback. Idempotent on ib_exec_id."""
    sql = """
        INSERT OR IGNORE INTO executions
            (order_id, ib_exec_id, ib_order_id, account, symbol, sec_type,
             side, shares, price, cum_qty, avg_price,
             commission, commission_currency, realized_pnl, liquidation, exchange, executed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (
            order_id, ib_exec_id, ib_order_id, account, symbol, sec_type,
            side, shares, price, cum_qty, avg_price,
            commission, commission_currency, realized_pnl,
            1 if liquidation else 0, exchange, executed_at,
        ))
        return cur.lastrowid


def save_signal(
    strategy_name: str,
    symbol: str,
    action: Optional[str],
    quantity: Optional[int],
    bar_datetime: Optional[str] = None,
    bar_close: Optional[float] = None,
) -> int:
    """Persist a signal emitted by a strategy (None action = no-op bar)."""
    sql = """
        INSERT INTO strategy_signals
            (strategy_name, symbol, action, quantity, bar_datetime, bar_close)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (strategy_name, symbol, action, quantity, bar_datetime, bar_close))
        return cur.lastrowid


def mark_signal_executed(signal_id: int, order_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE strategy_signals SET executed = 1, order_id = ? WHERE id = ?",
            (order_id, signal_id),
        )


def get_order_db_id(ib_order_id: int) -> Optional[int]:
    """Return the local primary key for an order given IB's order ID, or None."""
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM orders WHERE ib_order_id = ?", (ib_order_id,)).fetchone()
    return row[0] if row else None


def update_order_status_by_ib_id(
    ib_order_id: int,
    status: str,
    filled_quantity: float = 0,
    remaining_quantity: Optional[float] = None,
    avg_fill_price: Optional[float] = None,
    last_fill_price: Optional[float] = None,
    ib_perm_id: Optional[int] = None,
    why_held: Optional[str] = None,
) -> None:
    """Update order status using IB's order ID (as received in orderStatus callback)."""
    sql = """
        UPDATE orders SET
            status             = ?,
            filled_quantity    = ?,
            remaining_quantity = ?,
            avg_fill_price     = ?,
            last_fill_price    = ?,
            ib_perm_id         = COALESCE(?, ib_perm_id),
            why_held           = ?,
            updated_at         = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        WHERE ib_order_id = ?
    """
    with get_connection() as conn:
        conn.execute(sql, (
            status, filled_quantity, remaining_quantity,
            avg_fill_price, last_fill_price, ib_perm_id, why_held, ib_order_id,
        ))


def update_execution_commission(
    ib_exec_id: str,
    commission: Optional[float] = None,
    commission_currency: Optional[str] = None,
    realized_pnl: Optional[float] = None,
) -> None:
    """Patch commission data onto an existing execution row from a commissionReport callback."""
    sql = """
        UPDATE executions SET
            commission          = COALESCE(?, commission),
            commission_currency = COALESCE(?, commission_currency),
            realized_pnl        = COALESCE(?, realized_pnl)
        WHERE ib_exec_id = ?
    """
    with get_connection() as conn:
        conn.execute(sql, (commission, commission_currency, realized_pnl, ib_exec_id))
