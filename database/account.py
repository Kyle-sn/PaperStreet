from typing import Optional
from .db import get_connection


def save_position_snapshot(
    account: str,
    symbol: str,
    position: float,
    sec_type: str = "STK",
    currency: str = "USD",
    con_id: Optional[int] = None,
    market_price: Optional[float] = None,
    market_value: Optional[float] = None,
    average_cost: Optional[float] = None,
    unrealized_pnl: Optional[float] = None,
    realized_pnl: Optional[float] = None,
) -> int:
    sql = """
        INSERT INTO position_snapshots
            (account, con_id, symbol, sec_type, currency, position, market_price,
             market_value, average_cost, unrealized_pnl, realized_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (
            account, con_id, symbol, sec_type, currency, position, market_price,
            market_value, average_cost, unrealized_pnl, realized_pnl,
        ))
        return cur.lastrowid


def save_account_snapshot(
    account: str,
    cash_balance: Optional[float] = None,
    net_liquidation: Optional[float] = None,
    gross_position_value: Optional[float] = None,
    buying_power: Optional[float] = None,
    excess_liquidity: Optional[float] = None,
    maintenance_margin: Optional[float] = None,
    initial_margin: Optional[float] = None,
    realized_pnl: Optional[float] = None,
    unrealized_pnl: Optional[float] = None,
) -> int:
    sql = """
        INSERT INTO account_snapshots
            (account, cash_balance, net_liquidation, gross_position_value,
             buying_power, excess_liquidity, maintenance_margin,
             initial_margin, realized_pnl, unrealized_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, (
            account, cash_balance, net_liquidation, gross_position_value,
            buying_power, excess_liquidity, maintenance_margin,
            initial_margin, realized_pnl, unrealized_pnl,
        ))
        return cur.lastrowid


def get_latest_account_snapshot(account: str) -> Optional[dict]:
    sql = """
        SELECT * FROM account_snapshots
        WHERE account = ?
        ORDER BY snapshot_at DESC
        LIMIT 1
    """
    with get_connection() as conn:
        row = conn.execute(sql, (account,)).fetchone()
    return dict(row) if row else None


def get_latest_positions(account: str) -> list[dict]:
    """Return the most recent snapshot row for each symbol in an account."""
    sql = """
        SELECT p.*
        FROM position_snapshots p
        INNER JOIN (
            SELECT symbol, MAX(snapshot_at) AS max_at
            FROM position_snapshots
            WHERE account = ?
            GROUP BY symbol
        ) latest ON p.symbol = latest.symbol AND p.snapshot_at = latest.max_at
        WHERE p.account = ?
        ORDER BY p.symbol
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (account, account)).fetchall()
    return [dict(r) for r in rows]
