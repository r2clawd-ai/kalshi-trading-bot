"""
Repo Supervisor - Database Operations
Manages SQLite database for market data, positions, and logs
"""

import sqlite3
import os
from .base_supervisor import BaseSupervisor, Worker

class DatabaseWorker(Worker):
    """Handles database operations"""
    
    def __init__(self):
        super().__init__("DatabaseWorker")
        self.db_path = "/Users/r2/.openclaw/workspace/kalshi-bot/data/kalshi.db"
        self.conn = None
    
    async def run(self):
        """Database worker main loop"""
        while True:
            self.heartbeat()
            await asyncio.sleep(10)

class RepoSupervisor(BaseSupervisor):
    """Manages database operations"""
    
    def __init__(self):
        super().__init__("Repo")
        self.db_path = "/Users/r2/.openclaw/workspace/kalshi-bot/data/kalshi.db"
        self.conn = None
    
    async def _initialize(self):
        """Initialize database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                id TEXT PRIMARY KEY,
                ticker TEXT,
                title TEXT,
                category TEXT,
                yes_price REAL,
                no_price REAL,
                volume INTEGER,
                last_updated TIMESTAMP,
                data JSON
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                side TEXT,
                contracts INTEGER,
                entry_price REAL,
                current_price REAL,
                pnl REAL,
                status TEXT,
                opened_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                side TEXT,
                contracts INTEGER,
                price REAL,
                fee REAL,
                executed_at TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                supervisor TEXT,
                message TEXT,
                data JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                ticker TEXT,
                title TEXT,
                score REAL,
                confidence TEXT,
                position_size REAL,
                reason TEXT,
                breakdown JSON,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP
            )
        """)
        
        self.conn.commit()
        
        # Create database worker
        self.workers.append(DatabaseWorker())
    
    async def _main_loop(self):
        """Main loop - check connection health"""
        try:
            self.conn.execute("SELECT 1").fetchone()
        except:
            self.healthy = False
    
    async def _cleanup(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query"""
        return self.conn.execute(query, params)
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def log(self, level: str, supervisor: str, message: str, data: dict = None):
        """Log message to database"""
        import json
        self.execute(
            "INSERT INTO logs (level, supervisor, message, data) VALUES (?, ?, ?, ?)",
            (level, supervisor, message, json.dumps(data) if data else None)
        )
        self.commit()
    
    async def store_opportunities(self, opportunities: list):
        """Store scored opportunities"""
        import json
        for opp in opportunities:
            market = opp['market']
            self.execute("""
                INSERT INTO opportunities 
                (market_id, ticker, title, score, confidence, position_size, reason, breakdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                market.get('id', market.get('ticker')),
                market.get('ticker'),
                market.get('title'),
                opp['score'],
                opp['confidence'],
                opp['position_size'],
                opp['reason'],
                json.dumps(opp['breakdown'])
            ))
        self.commit()
    
    async def get_active_opportunities(self, limit=10):
        """Get active (unexecuted) opportunities, sorted by score"""
        cursor = self.execute("""
            SELECT * FROM opportunities 
            WHERE status = 'active'
            ORDER BY score DESC, created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def mark_opportunity_executed(self, opp_id: int):
        """Mark opportunity as executed"""
        self.execute("""
            UPDATE opportunities 
            SET status = 'executed', executed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (opp_id,))
        self.commit()
