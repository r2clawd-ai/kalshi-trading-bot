"""
Base Supervisor Class
All supervisors inherit from this with common functionality
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
import abc

class Worker:
    """Base worker class"""
    def __init__(self, name: str):
        self.name = name
        self.task = None
        self.healthy = True
        self.last_heartbeat = datetime.now()
    
    async def start(self):
        """Start the worker"""
        self.task = asyncio.create_task(self.run(), name=self.name)
    
    async def stop(self):
        """Stop the worker"""
        if self.task:
            self.task.cancel()
    
    @abc.abstractmethod
    async def run(self):
        """Worker main loop - override in subclass"""
        pass
    
    def heartbeat(self):
        """Update heartbeat"""
        self.last_heartbeat = datetime.now()
        self.healthy = True

class BaseSupervisor(abc.ABC):
    """Base class for all supervisors"""
    
    def __init__(self, name: str):
        self.name = name
        self.workers: List[Worker] = []
        self.config: Dict[str, Any] = {}
        self.started = False
        self.healthy = True
    
    async def start(self):
        """Initialize and start all workers"""
        await self._initialize()
        
        for worker in self.workers:
            await worker.start()
        
        self.started = True
    
    async def stop(self):
        """Stop all workers"""
        for worker in self.workers:
            await worker.stop()
        
        await self._cleanup()
        self.started = False
    
    async def run(self):
        """Main supervisor loop"""
        while self.started:
            try:
                await self._main_loop()
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                print(f"⚠️  {self.name} error: {e}")
                await asyncio.sleep(5)
    
    def is_healthy(self) -> bool:
        """Check if supervisor and all workers are healthy"""
        if not self.healthy:
            return False
        
        # Check all workers
        for worker in self.workers:
            if not worker.healthy:
                return False
            
            # Check heartbeat (5 minute timeout)
            if (datetime.now() - worker.last_heartbeat).total_seconds() > 300:
                return False
        
        return True
    
    @abc.abstractmethod
    async def _initialize(self):
        """Initialize supervisor - override in subclass"""
        pass
    
    @abc.abstractmethod
    async def _main_loop(self):
        """Main supervisor logic - override in subclass"""
        pass
    
    async def _cleanup(self):
        """Cleanup resources - optional override"""
        pass
