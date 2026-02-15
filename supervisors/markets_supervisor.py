"""
Markets Supervisor - Market Analysis, Scoring, and Opportunity Detection
Analyzes Kalshi markets, scores opportunities, sizes positions
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisors.base_supervisor import BaseSupervisor, Worker
from market_scorer import MarketScorer
from position_sizer import PositionSizer


class MarketAnalysisWorker(Worker):
    """Analyzes markets and generates scored opportunities"""
    
    def __init__(self, repo_supervisor, ingest_supervisor, capital_supervisor):
        super().__init__("MarketAnalysisWorker")
        self.repo = repo_supervisor
        self.ingest = ingest_supervisor
        self.capital = capital_supervisor
        self.scorer = None
        self.sizer = None
    
    async def run(self):
        """Market analysis loop"""
        while True:
            try:
                # Get current capital
                balance = await self.capital.get_balance()
                current_exposure = await self.capital.get_total_exposure()
                
                # Initialize scoring engines if needed
                if not self.scorer or not self.sizer:
                    self.scorer = MarketScorer(capital=balance)
                    self.sizer = PositionSizer(capital=balance)
                
                # Fetch active markets from Kalshi
                markets = await self.ingest.fetch_active_markets()
                
                if not markets:
                    self.heartbeat()
                    await asyncio.sleep(60)
                    continue
                
                # Score all markets
                scored_markets = self.scorer.rank_markets(markets)
                
                # Filter to top opportunities
                opportunities = []
                for market, score, confidence, breakdown in scored_markets:
                    if score >= 50:  # Only consider decent scores
                        # Calculate position size
                        size, reason = self.sizer.calculate_position(
                            market, score, confidence, breakdown, current_exposure
                        )
                        
                        if size > 0:
                            opportunities.append({
                                'market': market,
                                'score': score,
                                'confidence': confidence,
                                'breakdown': breakdown,
                                'position_size': size,
                                'reason': reason,
                                'timestamp': datetime.now().isoformat(),
                            })
                
                # Store opportunities in database
                if opportunities:
                    await self.repo.store_opportunities(opportunities)
                    print(f"✅ Found {len(opportunities)} trading opportunities")
                    for opp in opportunities[:3]:  # Show top 3
                        print(f"   {opp['market']['title']}: {opp['reason']}")
                
                self.heartbeat()
                
            except Exception as e:
                print(f"⚠️  Market analysis error: {e}")
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(60)  # Analyze every minute


class OpportunityMonitor(Worker):
    """Monitors opportunities for execution signals"""
    
    def __init__(self, repo_supervisor):
        super().__init__("OpportunityMonitor")
        self.repo = repo_supervisor
    
    async def run(self):
        """Monitor loop"""
        while True:
            try:
                # Get latest opportunities
                opportunities = await self.repo.get_active_opportunities()
                
                # Check if any are ready to execute
                # (This will be wired to Trading Supervisor in Day 2)
                
                self.heartbeat()
                
            except Exception as e:
                print(f"⚠️  Opportunity monitor error: {e}")
            
            await asyncio.sleep(10)


class MarketsSupervisor(BaseSupervisor):
    """Manages market analysis and opportunity detection"""
    
    def __init__(self, repo_supervisor, ingest_supervisor, capital_supervisor):
        super().__init__("Markets")
        self.repo = repo_supervisor
        self.ingest = ingest_supervisor
        self.capital = capital_supervisor
    
    async def _initialize(self):
        """Initialize market analysis workers"""
        self.workers.append(MarketAnalysisWorker(
            self.repo, self.ingest, self.capital
        ))
        self.workers.append(OpportunityMonitor(self.repo))
    
    async def _main_loop(self):
        """Monitor market analysis health"""
        await asyncio.sleep(1)
    
    # Public API methods
    async def get_top_opportunities(self, limit=10):
        """Get top scored opportunities"""
        return await self.repo.get_active_opportunities(limit=limit)
    
    async def refresh_analysis(self):
        """Force refresh of market analysis"""
        # Signal to workers to run immediately
        # (Implementation detail)
        pass
