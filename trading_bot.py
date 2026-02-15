#!/usr/bin/env python3
"""
Kalshi Autonomous Trading Bot
Manages prediction market positions, risk, and automation
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# Config
CONFIG_DIR = Path(__file__).parent / "config"
DATA_DIR = Path(__file__).parent / "data"
CONFIG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

@dataclass
class Position:
    """Trading position"""
    id: str
    market: str
    yes_no: str  # "yes" or "no"
    cost: float
    quantity: int
    timestamp: str
    status: str  # "open", "won", "lost"

@dataclass
class TradeSignal:
    """Trade signal from analysis"""
    market: str
    yes_no: str
    confidence: float  # 0-100
    reason: str
    size_recommendation: float  # % of bankroll

class TradingBot:
    """Autonomous trading bot for Kalshi"""
    
    def __init__(self):
        self.config_path = CONFIG_DIR / "bot_config.json"
        self.positions_path = DATA_DIR / "positions.json"
        self.log_path = DATA_DIR / "trading_log.json"
        
        # Load or create config
        self.config = self.load_config()
        self.positions = self.load_positions()
        
        # Set from environment or config
        self.api_key = os.environ.get('KALSHI_API_KEY') or self.config.get('api_key')
        self.private_key = os.environ.get('KALSHI_PRIVATE_KEY') or self.config.get('private_key')
        
        # Trading parameters
        self.max_position_pct = 0.15  # Max 15% per position
        self.max_exposure_pct = 0.60  # Max 60% total exposure
        self.min_confidence = 65  # Min confidence to trade
        
    def load_config(self) -> Dict:
        """Load bot configuration"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {
            "max_position_pct": 0.15,
            "max_exposure_pct": 0.60,
            "min_confidence": 65,
            "auto_rebalance": True
        }
    
    def load_positions(self) -> List[Position]:
        """Load trading positions"""
        if self.positions_path.exists():
            with open(self.positions_path) as f:
                data = json.load(f)
                return [Position(**p) for p in data]
        return []
    
    def save_positions(self):
        """Save trading positions"""
        with open(self.positions_path, 'w') as f:
            json.dump([asdict(p) for p in self.positions], f, indent=2)
    
    def log_trade(self, action: str, details: Dict):
        """Log trading activity"""
        log = []
        if self.log_path.exists():
            with open(self.log_path) as f:
                log = json.load(f)
        
        log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
        
        # Keep last 100 entries
        log = log[-100:]
        
        with open(self.log_path, 'w') as f:
            json.dump(log, f, indent=2)
    
    def get_balance(self) -> float:
        """Get account balance from API"""
        try:
            # Use existing kalshi_client
            result = subprocess.run(
                ["python3", "/Users/r2/.openclaw/workspace/kalshi_client.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.split('\n'):
                if 'Balance:' in line:
                    # Extract "$126.13" from "Balance: $126.13"
                    balance_str = line.split('$')[-1].strip()
                    return float(balance_str)
                    
        except Exception as e:
            print(f"⚠️ Could not fetch balance: {e}")
        
        return 0.0
    
    def get_open_positions(self) -> List[Position]:
        """Get currently open positions"""
        return [p for p in self.positions if p.status == "open"]
    
    def calculate_position_size(self, balance: float, confidence: float) -> float:
        """Calculate position size using Kelly criterion"""
        # Simplified Kelly: bet based on confidence
        # Higher confidence = larger position
        
        confidence_mult = (confidence - 50) / 50  # 0 to 1
        base_size = balance * self.max_position_pct
        adjusted = base_size * confidence_mult
        
        return min(adjusted, balance * self.max_position_pct)
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Analyze a market and generate trade signal"""
        # This would be where AI analysis happens
        # For now, return None (no signals)
        
        market = market_data.get('title', 'Unknown')
        volume = market_data.get('volume', 0)
        
        # Skip low volume
        if volume < 10000:
            return None
        
        # This is where we'd add analysis logic
        # For now, no signals generated automatically
        return None
    
    def place_trade(self, signal: TradeSignal, balance: float) -> bool:
        """Place a trade based on signal"""
        position_size = self.calculate_position_size(balance, signal.confidence)
        
        if position_size < 1.0:
            print(f"⚠️ Position too small: ${position_size:.2f}")
            return False
        
        # Check exposure
        open_positions = self.get_open_positions()
        current_exposure = sum(p.cost * p.quantity for p in open_positions)
        
        if current_exposure + position_size > balance * self.max_exposure_pct:
            print(f"⚠️ Max exposure reached")
            return False
        
        # Log the trade
        self.log_trade("PLACE_ORDER", {
            "market": signal.market,
            "side": signal.yes_no,
            "size": position_size,
            "confidence": signal.confidence,
            "reason": signal.reason
        })
        
        print(f"📝 Would place trade: {signal.market} {signal.yes_no} @ ${position_size:.2f}")
        print(f"   Reason: {signal.reason}")
        
        # In production, this would call the API
        # For now, just log it
        
        return True
    
    def report_daily(self) -> str:
        """Generate daily performance report"""
        balance = self.get_balance()
        open_positions = self.get_open_positions()
        
        initial_balance = 100.0
        pnl = balance - initial_balance
        pnl_pct = (pnl / initial_balance) * 100
        
        report = f"""
📊 KALSHI DAILY REPORT - {datetime.now().strftime('%B %d, %Y')}
{'='*50}

💰 ACCOUNT:
   Balance: ${balance:.2}
   Initial: $100.00
   P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)

📊 POSITIONS:
   Open: {len(open_positions)}
   
"""
        
        if open_positions:
            report += "   Active Trades:\n"
            for p in open_positions:
                report += f"   • {p.market[:40]}... {p.yes_no} @ ${p.cost:.2f}\n"
        
        report += f"""
📈 STATS:
   Total Trades: {len(self.positions)}
   Win Rate: {self.calculate_win_rate():.1f}%
   
🤖 Bot Status: {"Active" if open_positions else "Watching"}
"""
        
        return report
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate from closed positions"""
        closed = [p for p in self.positions if p.status != "open"]
        if not closed:
            return 0.0
        
        won = len([p for p in closed if p.status == "won"])
        return (won / len(closed)) * 100
    
    def run(self, action: str = "report"):
        """Run bot action"""
        if action == "report":
            print(self.report_daily())
        elif action == "check":
            balance = self.get_balance()
            print(f"💰 Balance: ${balance:.2}")
            print(f"📊 Open positions: {len(self.get_open_positions())}")
        elif action == "analyze":
            # Would analyze markets and potentially place trades
            print("🔍 Analyzing markets...")
            # Placeholder for analysis

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kalshi Trading Bot")
    parser.add_argument("--action", "-a", default="report", 
                       choices=["report", "check", "analyze"],
                       help="Action to perform")
    args = parser.parse_args()
    
    bot = TradingBot()
    bot.run(args.action)

if __name__ == "__main__":
    main()
