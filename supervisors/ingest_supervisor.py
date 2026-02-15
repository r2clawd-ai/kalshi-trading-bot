"""
Ingest Supervisor - Market Data Ingestion
Continuously fetches market data from Kalshi API
"""

import asyncio
import sys
sys.path.insert(0, '/Users/r2/.openclaw/workspace')
from kalshi_client import KalshiClient
from .base_supervisor import BaseSupervisor, Worker

class MarketIngestWorker(Worker):
    """Fetches market data"""
    
    def __init__(self, client: KalshiClient):
        super().__init__("MarketIngestWorker")
        self.client = client
    
    async def run(self):
        """Ingest loop"""
        while True:
            try:
                # Fetch all markets
                markets = self.client.get_markets()
                # Store in database (would connect to repo supervisor)
                self.heartbeat()
            except Exception as e:
                print(f"   Ingest error: {e}")
            
            await asyncio.sleep(60)  # Poll every minute

class IngestSupervisor(BaseSupervisor):
    """Manages market data ingestion"""
    
    def __init__(self):
        super().__init__("Ingest")
        self.client = None
    
    async def _initialize(self):
        """Initialize Kalshi client"""
        self.client = KalshiClient()
        self.workers.append(MarketIngestWorker(self.client))
    
    async def _main_loop(self):
        """Monitor ingest health"""
        await asyncio.sleep(1)
    
    # Public API methods
    async def fetch_active_markets(self):
        """Fetch active markets from Kalshi API"""
        if not self.client:
            return []
        
        try:
            markets = self.client.get_markets(status='active')
            return markets
        except Exception as e:
            print(f"⚠️  Failed to fetch markets: {e}")
            return []
