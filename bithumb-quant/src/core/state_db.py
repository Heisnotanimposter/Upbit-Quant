import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("StateDB")

class StateDB:
    """
    SQLite persistent database manager for crash-resilient bot operations.
    Enables Write-Ahead Logging (WAL) for concurrency and durability.
    """

    def __init__(self, db_path: str = "bithumb_quant.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high performance and durability
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        """Creates database schema if tables do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Active Positions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                entry_price REAL NOT NULL,
                amount REAL NOT NULL,
                invested_krw REAL NOT NULL,
                stop_loss_price REAL NOT NULL,
                trailing_peak REAL NOT NULL,
                opened_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN'
            );
            """)

            # Trade History Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                value_krw REAL NOT NULL,
                fee REAL DEFAULT 0,
                pnl_krw REAL DEFAULT 0,
                pnl_pct REAL DEFAULT 0,
                reason TEXT,
                timestamp TEXT NOT NULL
            );
            """)

            # Daily Performance Log Table with Turnover Tracking
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                start_balance_krw REAL NOT NULL,
                end_balance_krw REAL NOT NULL,
                realized_pnl_krw REAL DEFAULT 0,
                trade_count INTEGER DEFAULT 0,
                win_count INTEGER DEFAULT 0,
                turnover_volume_krw REAL DEFAULT 0
            );
            """)

            # AI Market Regime Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                regime TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                position_multiplier REAL NOT NULL,
                reasoning TEXT
            );
            """)
            conn.commit()
            logger.info("SQLite State Database initialized successfully.")

    # --- POSITIONS MANAGEMENT ---

    def save_position(self, symbol: str, entry_price: float, amount: float, invested_krw: float, stop_loss_price: float):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO positions (symbol, entry_price, amount, invested_krw, stop_loss_price, trailing_peak, opened_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN');
            """, (symbol, entry_price, amount, invested_krw, stop_loss_price, entry_price, now))
            conn.commit()
        logger.info(f"DB: Saved position for {symbol} @ {entry_price:,.0f} KRW")

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN';", (symbol,)).fetchone()
            return dict(row) if row else None

    def get_all_open_positions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM positions WHERE status = 'OPEN';").fetchall()
            return [dict(r) for r in rows]

    def update_trailing_peak(self, symbol: str, new_peak: float, new_stop_loss: float):
        with self._get_connection() as conn:
            conn.execute("""
            UPDATE positions SET trailing_peak = ?, stop_loss_price = ? WHERE symbol = ? AND status = 'OPEN';
            """, (new_peak, new_stop_loss, symbol))
            conn.commit()

    def close_position(self, symbol: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM positions WHERE symbol = ?;", (symbol,))
            conn.commit()
        logger.info(f"DB: Closed position for {symbol}")

    # --- TRADES & TURNOVER LOGGING ---

    def log_trade(self, symbol: str, side: str, price: float, amount: float, value_krw: float, fee: float = 0.0, pnl_krw: float = 0.0, pnl_pct: float = 0.0, reason: str = ""):
        now = datetime.now().isoformat()
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO trades (symbol, side, price, amount, value_krw, fee, pnl_krw, pnl_pct, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (symbol, side, price, amount, value_krw, fee, pnl_krw, pnl_pct, reason, now))

            # Update daily turnover volume & trade count
            conn.execute("""
            INSERT INTO daily_stats (date, start_balance_krw, end_balance_krw, realized_pnl_krw, trade_count, win_count, turnover_volume_krw)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                realized_pnl_krw = realized_pnl_krw + excluded.realized_pnl_krw,
                trade_count = trade_count + 1,
                win_count = win_count + excluded.win_count,
                turnover_volume_krw = turnover_volume_krw + excluded.turnover_volume_krw;
            """, (today, value_krw, value_krw, pnl_krw, 1 if pnl_krw > 0 else 0, value_krw))
            conn.commit()

    def get_today_turnover_stats(self) -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM daily_stats WHERE date = ?;", (today,)).fetchone()
            if row:
                return dict(row)
            return {"date": today, "turnover_volume_krw": 0.0, "realized_pnl_krw": 0.0, "trade_count": 0, "win_count": 0}

    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?;", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # --- AI LOGS ---

    def log_ai_assessment(self, regime: str, risk_level: str, multiplier: float, reasoning: str):
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO ai_logs (timestamp, regime, risk_level, position_multiplier, reasoning)
            VALUES (?, ?, ?, ?, ?);
            """, (now, regime, risk_level, multiplier, reasoning))
            conn.commit()
