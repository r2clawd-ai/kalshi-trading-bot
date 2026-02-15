# Kalshi Trading Bot - AgentFlywheel Architecture

**Inspired by:** Jeffrey Emanuel's AgentFlywheel approach (@doodlestein)  
**Started:** Feb 12, 2026 02:12 CST  
**Status:** Building (ETA 2-3 days)

---

## Architecture Overview

Multi-supervisor trading system with automatic fault tolerance and recovery.

### 9 Core Supervisors

1. **Repo** - Database operations (SQLite)
2. **Ingest** - Market data ingestion (Kalshi API)
3. **Markets** - Market analysis and scoring
4. **Sports** - Sports market specialization
5. **Trading** - Order execution and management
6. **Capital** - Portfolio and risk management
7. **Simulation** - Backtesting and strategy testing
8. **Observability** - System monitoring and alerts
9. **Dashboard** - Web interface and reporting

Each supervisor manages multiple worker processes with automatic restart on failure.

---

## System Design

```
┌─────────────────────────────────────────────────────────┐
│                  Supervisor Orchestrator                 │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Repo   │  │  Ingest  │  │ Markets  │  ...         │
│  │          │  │          │  │          │              │
│  │ Workers: │  │ Workers: │  │ Workers: │              │
│  │  • DB    │  │  • API   │  │  • Score │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
           ↓              ↓              ↓
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ SQLite   │   │  Kalshi  │   │ Analysis │
    │ Database │   │   API    │   │  Engine  │
    └──────────┘   └──────────┘   └──────────┘
```

---

## Features

### Core Trading
- ✅ Multi-market monitoring
- ✅ Automatic position management
- ✅ Risk-adjusted sizing
- ✅ Stop-loss / take-profit
- ✅ Market maker detection

### Observability
- ✅ Real-time health monitoring
- ✅ Automatic supervisor restart
- ✅ Performance metrics
- ✅ Trade logging
- ✅ PnL tracking

### Intelligence
- 🔄 Market scoring algorithms
- 🔄 Sports-specific analysis
- 🔄 Backtesting framework
- 🔄 Strategy optimization
- 🔄 Predictive models

---

## Project Structure

```
kalshi-bot/
├── bot.py                     # Main entry point
├── supervisors/
│   ├── orchestrator.py       # Supervisor coordinator
│   ├── base_supervisor.py    # Base class
│   ├── repo_supervisor.py    # Database ops
│   ├── ingest_supervisor.py  # Market data
│   ├── markets_supervisor.py # Market analysis
│   ├── sports_supervisor.py  # Sports specialization
│   ├── trading_supervisor.py # Order execution
│   ├── capital_supervisor.py # Portfolio management
│   ├── simulation_supervisor.py  # Backtesting
│   ├── observability_supervisor.py  # Monitoring
│   └── dashboard_supervisor.py  # Web interface
├── workers/
│   ├── market_scanner.py     # Scan all markets
│   ├── position_manager.py   # Manage positions
│   ├── risk_calculator.py    # Calculate risk
│   └── trade_executor.py     # Execute trades
├── models/
│   ├── market.py             # Market data models
│   ├── position.py           # Position models
│   └── strategy.py           # Strategy models
├── utils/
│   ├── scoring.py            # Market scoring
│   ├── signals.py            # Trading signals
│   └── logger.py             # Logging utilities
└── data/
    └── kalshi.db             # SQLite database
```

---

## Development Timeline

### Phase 1: Core Infrastructure (Day 1 - Feb 12)
- [x] Project structure
- [x] Base supervisor class
- [x] Orchestrator
- [x] Repo supervisor (database)
- [x] Ingest supervisor (API)
- [ ] Remaining 7 supervisors
- [ ] Database schema complete
- [ ] Health monitoring

### Phase 2: Trading Logic (Day 2 - Feb 13)
- [ ] Market scoring algorithms
- [ ] Position sizing logic
- [ ] Risk management
- [ ] Order execution
- [ ] Sports market specialization

### Phase 3: Intelligence & Testing (Day 3 - Feb 14)
- [ ] Backtesting framework
- [ ] Strategy optimization
- [ ] Performance metrics
- [ ] Dashboard UI
- [ ] End-to-end testing

### Phase 4: Production (Day 4 - Feb 15)
- [ ] Live trading with $66.13
- [ ] Monitor for 24 hours
- [ ] Tune parameters
- [ ] Add to morning briefing

---

## Running the Bot

```bash
# Start bot
cd /Users/r2/.openclaw/workspace/kalshi-bot
python3 bot.py

# View logs
tail -f data/kalshi.log

# Check status
curl http://localhost:8080/status
```

---

## Configuration

Edit `config.json`:

```json
{
  "capital": {
    "initial_balance": 66.13,
    "max_position_size": 0.1,
    "max_portfolio_risk": 0.3
  },
  "trading": {
    "min_edge": 0.05,
    "max_spread": 0.1,
    "rebalance_interval": 3600
  },
  "markets": {
    "categories": ["politics", "sports", "economics"],
    "min_liquidity": 1000,
    "max_markets": 100
  }
}
```

---

## Monitoring

### Health Check
```bash
# Check supervisor status
curl http://localhost:8080/health

# View current positions
curl http://localhost:8080/positions

# View recent trades
curl http://localhost:8080/trades
```

### Logs
```bash
# Tail all logs
tail -f data/kalshi.log

# Query database
sqlite3 data/kalshi.db "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10"
```

---

## Performance Targets

- **Uptime:** 99.9%
- **Response time:** <100ms per market
- **Trade execution:** <5s
- **Data freshness:** <60s
- **Supervisor restarts:** Automatic within 5s

---

## Safety Features

1. **Circuit breakers** - Stop trading on anomalies
2. **Position limits** - Max 10% per position
3. **Portfolio limits** - Max 30% total risk
4. **Stop losses** - Automatic exit at -20%
5. **Rate limiting** - Respect API limits
6. **Health monitoring** - Auto-restart on failure

---

## Next Steps

1. Complete all 9 supervisors
2. Implement market scoring
3. Build position management
4. Add backtesting
5. Deploy with live capital

---

**Last Updated:** Feb 12, 2026 02:15 CST  
**Status:** Infrastructure building  
**Completion:** ~20% (2/9 supervisors done)
