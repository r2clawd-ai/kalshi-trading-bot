"""
Supervisor Orchestrator
Manages all 9 supervisors with proper lifecycle and error handling
"""

import asyncio
from typing import Dict, List
from datetime import datetime

from .repo_supervisor import RepoSupervisor
from .ingest_supervisor import IngestSupervisor
from .markets_supervisor import MarketsSupervisor
from .sports_supervisor import SportsSupervisor
from .trading_supervisor import TradingSupervisor
from .capital_supervisor import CapitalSupervisor
from .simulation_supervisor import SimulationSupervisor
from .observability_supervisor import ObservabilitySupervisor
from .dashboard_supervisor import DashboardSupervisor

class SupervisorOrchestrator:
    """Coordinates all supervisors"""
    
    def __init__(self):
        # Initialize supervisors in dependency order
        self.supervisors = {
            'repo': RepoSupervisor(),
            'observability': ObservabilitySupervisor(),
            'ingest': IngestSupervisor(),
            'markets': MarketsSupervisor(),
            'sports': SportsSupervisor(),
            'capital': CapitalSupervisor(),
            'trading': TradingSupervisor(),
            'simulation': SimulationSupervisor(),
            'dashboard': DashboardSupervisor(),
        }
        
        self.tasks: Dict[str, asyncio.Task] = {}
        self.health_check_task = None
    
    async def start_all(self):
        """Start all supervisors"""
        print("🚀 Starting all supervisors...\n")
        
        # Start each supervisor
        for name, supervisor in self.supervisors.items():
            try:
                print(f"   Starting {name:15} supervisor...", end=" ")
                await supervisor.start()
                
                # Create background task for supervisor
                task = asyncio.create_task(
                    self._run_supervisor(name, supervisor),
                    name=f"supervisor_{name}"
                )
                self.tasks[name] = task
                
                print(f"✅ PID {id(supervisor):10} running")
            
            except Exception as e:
                print(f"❌ Failed: {e}")
                raise
        
        # Start health checking
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        print()
        print("=" * 60)
        print(f"✅ All {len(self.supervisors)} supervisors running")
        print("=" * 60)
        print()
        self._print_status()
    
    async def _run_supervisor(self, name: str, supervisor):
        """Run a supervisor with automatic restart on failure"""
        restart_count = 0
        max_restarts = 3
        
        while True:
            try:
                await supervisor.run()
            
            except Exception as e:
                restart_count += 1
                print(f"⚠️  {name} supervisor crashed: {e}")
                
                if restart_count >= max_restarts:
                    print(f"❌ {name} supervisor failed {max_restarts} times, giving up")
                    raise
                
                print(f"   Restarting {name} supervisor (attempt {restart_count}/{max_restarts})...")
                await asyncio.sleep(5)  # Backoff before restart
                await supervisor.start()
    
    async def _health_check_loop(self):
        """Periodically check supervisor health"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            unhealthy = []
            for name, supervisor in self.supervisors.items():
                if not supervisor.is_healthy():
                    unhealthy.append(name)
            
            if unhealthy:
                print(f"⚠️  Unhealthy supervisors: {', '.join(unhealthy)}")
    
    async def stop_all(self):
        """Stop all supervisors gracefully"""
        print("\n🛑 Stopping all supervisors...")
        
        # Cancel health check
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Stop supervisors in reverse order
        for name in reversed(list(self.supervisors.keys())):
            try:
                print(f"   Stopping {name:15} supervisor...", end=" ")
                await self.supervisors[name].stop()
                
                # Cancel background task
                if name in self.tasks:
                    self.tasks[name].cancel()
                
                print("✅ Stopped")
            
            except Exception as e:
                print(f"⚠️  Error: {e}")
        
        print("✅ All supervisors stopped\n")
    
    def _print_status(self):
        """Print current system status"""
        print("📊 System Status:")
        print()
        
        # Count workers
        total_workers = sum(
            len(sup.workers) if hasattr(sup, 'workers') else 0
            for sup in self.supervisors.values()
        )
        
        print(f"   Supervisors:  {len(self.supervisors)}")
        print(f"   Workers:      {total_workers}")
        print(f"   Status:       All systems operational")
        print()
    
    def get_status(self) -> dict:
        """Get system status as dict"""
        return {
            'supervisors': {
                name: {
                    'status': 'running' if sup.is_healthy() else 'unhealthy',
                    'pid': id(sup),
                    'workers': len(sup.workers) if hasattr(sup, 'workers') else 0,
                }
                for name, sup in self.supervisors.items()
            },
            'timestamp': datetime.now().isoformat(),
        }
