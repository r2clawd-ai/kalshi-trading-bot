#!/usr/bin/env python3
"""
Market Scoring Engine
Evaluates Kalshi markets for trading opportunities
Uses multiple factors: liquidity, edge, timeframe, category
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

class MarketScorer:
    """
    Scores Kalshi markets for trading opportunity
    Output: 0-100 score + confidence level
    """
    
    # Category weights (0-1, sums to 1.0)
    WEIGHTS = {
        'liquidity': 0.25,      # Can we enter/exit easily?
        'edge': 0.35,           # Do we have an advantage?
        'timeframe': 0.20,      # Time to expiry
        'volatility': 0.10,     # Price movement potential
        'risk': 0.10,           # Downside protection
    }
    
    # Risk tolerance settings
    MIN_LIQUIDITY_USD = 500    # Don't trade if <$500 daily volume
    MAX_POSITION_SIZE = 0.15   # Max 15% of capital per trade
    MIN_EDGE = 0.05            # Need 5%+ edge to consider
    
    def __init__(self, capital: float = 100.0):
        self.capital = capital
    
    def score_market(self, market: Dict) -> Tuple[float, str, Dict]:
        """
        Score a single market
        
        Args:
            market: Market dict from Kalshi API
        
        Returns:
            (score, confidence, breakdown)
            score: 0-100
            confidence: 'low' | 'medium' | 'high'
            breakdown: Dict of component scores
        """
        
        # Calculate component scores
        liquidity_score = self._score_liquidity(market)
        edge_score = self._score_edge(market)
        timeframe_score = self._score_timeframe(market)
        volatility_score = self._score_volatility(market)
        risk_score = self._score_risk(market)
        
        # Weighted total
        total_score = (
            liquidity_score * self.WEIGHTS['liquidity'] +
            edge_score * self.WEIGHTS['edge'] +
            timeframe_score * self.WEIGHTS['timeframe'] +
            volatility_score * self.WEIGHTS['volatility'] +
            risk_score * self.WEIGHTS['risk']
        ) * 100
        
        # Confidence based on data quality
        confidence = self._calculate_confidence(market, {
            'liquidity': liquidity_score,
            'edge': edge_score,
            'timeframe': timeframe_score,
            'volatility': volatility_score,
            'risk': risk_score,
        })
        
        breakdown = {
            'liquidity': liquidity_score,
            'edge': edge_score,
            'timeframe': timeframe_score,
            'volatility': volatility_score,
            'risk': risk_score,
            'total': total_score,
            'confidence': confidence,
        }
        
        return total_score, confidence, breakdown
    
    def _score_liquidity(self, market: Dict) -> float:
        """
        Score market liquidity (0-1)
        Based on volume, open interest, bid-ask spread
        """
        volume = market.get('volume_24h', 0)
        open_interest = market.get('open_interest', 0)
        yes_bid = market.get('yes_bid', 0)
        yes_ask = market.get('yes_ask', 100)
        
        # Volume score (0-1)
        volume_score = min(1.0, volume / 5000)  # $5k daily = perfect
        
        # Open interest score (0-1)
        oi_score = min(1.0, open_interest / 10000)  # 10k contracts = perfect
        
        # Spread score (0-1, tighter = better)
        spread = yes_ask - yes_bid
        if spread == 0:
            spread_score = 0  # No market
        else:
            spread_score = max(0, 1.0 - (spread / 10.0))  # 10¢ spread = 0
        
        # Combine (volume most important, then spread, then OI)
        liquidity = (
            volume_score * 0.5 +
            spread_score * 0.3 +
            oi_score * 0.2
        )
        
        return liquidity
    
    def _score_edge(self, market: Dict) -> float:
        """
        Score our edge (0-1)
        Do we have information/analysis that gives us an advantage?
        """
        yes_price = market.get('last_price', 50)
        
        # Categories where we might have edge
        category = market.get('category', '').lower()
        ticker = market.get('ticker', '').lower()
        
        edge_categories = {
            'sports': 0.3,       # Moderate edge (stats-based)
            'politics': 0.4,     # Good edge (polling data)
            'economics': 0.5,    # Strong edge (macro analysis)
            'weather': 0.2,      # Low edge (random)
            'entertainment': 0.2, # Low edge (random)
        }
        
        base_edge = 0.3  # Default: some edge
        for cat, score in edge_categories.items():
            if cat in category or cat in ticker:
                base_edge = score
                break
        
        # Price-based edge (contrarian when extreme)
        if yes_price < 20:
            # Underpriced? Could be opportunity
            price_edge = (20 - yes_price) / 20 * 0.3
        elif yes_price > 80:
            # Overpriced? Could short (buy NO)
            price_edge = (yes_price - 80) / 20 * 0.3
        else:
            price_edge = 0
        
        total_edge = min(1.0, base_edge + price_edge)
        
        return total_edge
    
    def _score_timeframe(self, market: Dict) -> float:
        """
        Score timeframe (0-1)
        Prefer 7-30 days (sweet spot for analysis)
        Too short = no time to react
        Too long = capital tied up
        """
        close_time_str = market.get('close_time')
        if not close_time_str:
            return 0.3  # Unknown = medium score
        
        try:
            close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
            days_left = (close_time - datetime.now()).days
        except:
            return 0.3
        
        # Scoring curve: peaks at 14-21 days
        if days_left < 3:
            return 0.2  # Too short
        elif days_left < 7:
            return 0.5  # Acceptable
        elif days_left < 14:
            return 0.8  # Good
        elif days_left < 30:
            return 1.0  # Perfect
        elif days_left < 60:
            return 0.7  # Decent
        elif days_left < 90:
            return 0.5  # Long
        else:
            return 0.3  # Too long
    
    def _score_volatility(self, market: Dict) -> float:
        """
        Score volatility potential (0-1)
        Higher = more movement expected = more profit opportunity
        """
        yes_price = market.get('last_price', 50)
        
        # Markets near 50¢ are most volatile (most uncertainty)
        # Markets near 0¢ or 100¢ are stable (consensus reached)
        
        distance_from_50 = abs(yes_price - 50)
        volatility = 1.0 - (distance_from_50 / 50.0)
        
        # Boost if we see recent volume spikes (indicator of interest)
        volume_24h = market.get('volume_24h', 0)
        if volume_24h > 2000:
            volatility = min(1.0, volatility * 1.2)
        
        return volatility
    
    def _score_risk(self, market: Dict) -> float:
        """
        Score risk/safety (0-1)
        Higher = safer trade
        Based on downside protection and market clarity
        """
        yes_price = market.get('last_price', 50)
        
        # Binary outcome markets are safer (clear resolution)
        is_binary = market.get('cap_strike') is None
        binary_bonus = 0.3 if is_binary else 0
        
        # Price-based risk: extreme prices have defined max loss
        if yes_price < 30:
            # Buying YES: max loss = yes_price
            price_risk = 1.0 - (yes_price / 30)
        elif yes_price > 70:
            # Buying NO: max loss = 100 - yes_price
            no_price = 100 - yes_price
            price_risk = 1.0 - (no_price / 30)
        else:
            # Mid-range: higher risk (50/50)
            price_risk = 0.5
        
        # Liquidity = safety (can exit if wrong)
        liquidity = self._score_liquidity(market)
        
        risk_score = (
            price_risk * 0.4 +
            liquidity * 0.4 +
            binary_bonus * 0.2
        )
        
        return risk_score
    
    def _calculate_confidence(self, market: Dict, scores: Dict) -> str:
        """
        Determine confidence level based on data quality
        """
        # High confidence: good liquidity + clear edge
        if scores['liquidity'] > 0.6 and scores['edge'] > 0.5:
            return 'high'
        
        # Low confidence: poor liquidity OR no edge
        if scores['liquidity'] < 0.3 or scores['edge'] < 0.3:
            return 'low'
        
        return 'medium'
    
    def rank_markets(self, markets: List[Dict]) -> List[Tuple[Dict, float, str, Dict]]:
        """
        Score and rank all markets
        
        Returns:
            List of (market, score, confidence, breakdown) tuples, sorted best first
        """
        scored = []
        
        for market in markets:
            score, confidence, breakdown = self.score_market(market)
            scored.append((market, score, confidence, breakdown))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored


if __name__ == "__main__":
    # Test with mock market data
    test_markets = [
        {
            'ticker': 'NFL-SUPERBOWL',
            'title': 'Will Chiefs win Super Bowl?',
            'category': 'sports',
            'last_price': 65,
            'yes_bid': 64,
            'yes_ask': 66,
            'volume_24h': 15000,
            'open_interest': 50000,
            'close_time': (datetime.now() + timedelta(days=10)).isoformat(),
        },
        {
            'ticker': 'ECON-GDP',
            'title': 'GDP growth >3% Q1?',
            'category': 'economics',
            'last_price': 42,
            'yes_bid': 40,
            'yes_ask': 44,
            'volume_24h': 3000,
            'open_interest': 8000,
            'close_time': (datetime.now() + timedelta(days=45)).isoformat(),
        },
    ]
    
    scorer = MarketScorer(capital=100.0)
    
    print("=" * 60)
    print("KALSHI MARKET SCORING TEST")
    print("=" * 60)
    
    ranked = scorer.rank_markets(test_markets)
    
    for i, (market, score, confidence, breakdown) in enumerate(ranked, 1):
        print(f"\n#{i}: {market['title']}")
        print(f"   Score: {score:.1f}/100 (confidence: {confidence})")
        print(f"   Price: {market['last_price']}¢")
        print(f"   Breakdown:")
        for component, value in breakdown.items():
            if component not in ('total', 'confidence'):
                print(f"      {component}: {value:.2f}")
