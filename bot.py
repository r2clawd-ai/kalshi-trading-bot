#!/usr/bin/env python3
"""
Kalshi Trading Bot - AgentFlywheel Architecture
Inspired by Jeffrey Emanuel's approach (@doodlestein)

9 Supervisors:
- Repo: Database operations
- Ingest: Market data ingestion
- Markets: Market analysis
- Sports: Sports market specialization
- Trading: Order execution
- Capital: Portfolio management
- Simulation: Backtesting
- Observability: Monitoring
- Dashboard: Web interface
"""

import asyncio
import signal
import sys
from datetime import datetime
from supervisors.orchestrator import SupervisorOrchestrator

class KalshiBot:
    def __init__(self):
        self.orchestrator = SupervisorOrchestrator()
        self.running = False
    
    async def start(self):
        """Start all supervisors"""
        print("=" * 60)
        print("🤖 Kalshi Trading Bot - AgentFlywheel Architecture")
        print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await self.orchestrator.start_all()
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            raise
        
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all supervisors gracefully"""
        print("\n🛑 Shutting down gracefully...")
        self.running = False
        await self.orchestrator.stop_all()
        print("✅ Shutdown complete")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n⚠️  Received signal {signum}")
        self.running = False

async def main():
    bot = KalshiBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⚠️  Keyboard interrupt")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
