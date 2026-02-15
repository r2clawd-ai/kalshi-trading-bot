#!/usr/bin/env python3
"""
Position Sizing Engine
Determines how much to bet on each market
Uses Kelly Criterion + risk constraints
"""

from typing import Dict, Optional, Tuple
import math

class PositionSizer:
    """
    Calculates optimal position size for each trade
    Balances Kelly Criterion (maximize growth) with risk limits
    """
    
    def __init__(
        self,
        capital: float,
        max_position_pct: float = 0.15,     # Max 15% per position
        max_total_exposure: float = 0.60,   # Max 60% of capital deployed
        kelly_fraction: float = 0.25,       # Use 1/4 Kelly (conservative)
        min_bet: float = 2.0,               # Min $2 per trade (Kalshi minimum)
    ):
        self.capital = capital
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.kelly_fraction = kelly_fraction
        self.min_bet = min_bet
    
    def calculate_position(
        self,
        market: Dict,
        score: float,
        confidence: str,
        breakdown: Dict,
        current_exposure: float = 0.0
    ) -> Tuple[float, str]:
        """
        Calculate position size for a market
        
        Args:
            market: Market dict from Kalshi
            score: Overall market score (0-100)
            confidence: 'low' | 'medium' | 'high'
            breakdown: Component scores
            current_exposure: Current capital already deployed
        
        Returns:
            (position_size, reason)
            position_size: Dollar amount to bet (0 = skip)
            reason: Why this size was chosen
        """
        
        # Check if we have room for more positions
        available_capital = self.capital - current_exposure
        max_exposure_left = self.capital * self.max_total_exposure - current_exposure
        
        if max_exposure_left < self.min_bet:
            return 0.0, "No capital available (at max exposure)"
        
        # Extract key metrics
        yes_price = market.get('last_price', 50)
        edge_score = breakdown.get('edge', 0)
        risk_score = breakdown.get('risk', 0)
        liquidity_score = breakdown.get('liquidity', 0)
        
        # Skip if score too low
        if score < 40:
            return 0.0, f"Score too low ({score:.1f}/100)"
        
        # Skip if no edge
        if edge_score < 0.3:
            return 0.0, f"Insufficient edge ({edge_score:.2f})"
        
        # Skip if liquidity too poor
        if liquidity_score < 0.2:
            return 0.0, f"Poor liquidity ({liquidity_score:.2f})"
        
        # Calculate Kelly position
        # Kelly = (edge * odds) / odds
        # For Kalshi: edge = (true_prob - price) / (1 - price)
        
        # Estimate true probability from our edge score
        # If yes_price = 50¢ and edge = 0.5, true_prob ≈ 60¢
        edge_adjustment = (edge_score - 0.3) * 20  # 0-20¢ adjustment
        true_prob = yes_price + edge_adjustment
        true_prob = max(0, min(100, true_prob))  # Clamp 0-100
        
        # Kelly fraction
        if true_prob > yes_price:
            # Buy YES
            edge = (true_prob - yes_price) / 100
            kelly_pct = edge * self.kelly_fraction
            direction = "YES"
        else:
            # Buy NO
            no_price = 100 - yes_price
            true_no_prob = 100 - true_prob
            edge = (true_no_prob - no_price) / 100
            kelly_pct = edge * self.kelly_fraction
            direction = "NO"
        
        if edge <= 0:
            return 0.0, "No positive edge detected"
        
        # Calculate base position size
        kelly_amount = self.capital * kelly_pct
        
        # Apply confidence multiplier
        confidence_multipliers = {
            'low': 0.5,
            'medium': 0.75,
            'high': 1.0,
        }
        confidence_mult = confidence_multipliers.get(confidence, 0.75)
        adjusted_amount = kelly_amount * confidence_mult
        
        # Apply risk adjustment (lower risk = can size up slightly)
        risk_mult = 0.8 + (risk_score * 0.4)  # 0.8-1.2x
        adjusted_amount *= risk_mult
        
        # Apply max position constraint
        max_position = self.capital * self.max_position_pct
        adjusted_amount = min(adjusted_amount, max_position)
        
        # Apply max exposure constraint
        adjusted_amount = min(adjusted_amount, max_exposure_left)
        
        # Round to $1 increments
        adjusted_amount = math.floor(adjusted_amount)
        
        # Check minimum
        if adjusted_amount < self.min_bet:
            return 0.0, f"Position too small (${adjusted_amount:.2f} < ${self.min_bet})"
        
        reason = (
            f"{direction} ${adjusted_amount:.0f} "
            f"(Kelly: ${kelly_amount:.0f}, "
            f"conf: {confidence}, "
            f"edge: {edge:.2%})"
        )
        
        return adjusted_amount, reason
    
    def update_capital(self, new_capital: float):
        """Update available capital"""
        self.capital = new_capital


def test_position_sizer():
    """Test position sizing logic"""
    
    sizer = PositionSizer(capital=66.13)  # Current balance
    
    test_cases = [
        {
            'market': {
                'ticker': 'TEST-HIGH',
                'title': 'High confidence trade',
                'last_price': 45,
            },
            'score': 75.0,
            'confidence': 'high',
            'breakdown': {
                'edge': 0.6,
                'risk': 0.8,
                'liquidity': 0.9,
            },
        },
        {
            'market': {
                'ticker': 'TEST-MEDIUM',
                'title': 'Medium confidence trade',
                'last_price': 60,
            },
            'score': 62.0,
            'confidence': 'medium',
            'breakdown': {
                'edge': 0.4,
                'risk': 0.6,
                'liquidity': 0.7,
            },
        },
        {
            'market': {
                'ticker': 'TEST-LOW',
                'title': 'Low score trade',
                'last_price': 80,
            },
            'score': 35.0,
            'confidence': 'low',
            'breakdown': {
                'edge': 0.2,
                'risk': 0.4,
                'liquidity': 0.3,
            },
        },
    ]
    
    print("=" * 60)
    print("POSITION SIZING TEST")
    print(f"Capital: ${sizer.capital:.2f}")
    print("=" * 60)
    
    current_exposure = 0.0
    
    for case in test_cases:
        market = case['market']
        score = case['score']
        confidence = case['confidence']
        breakdown = case['breakdown']
        
        size, reason = sizer.calculate_position(
            market, score, confidence, breakdown, current_exposure
        )
        
        print(f"\n{market['title']}")
        print(f"  Score: {score:.1f}/100 ({confidence})")
        print(f"  Price: {market['last_price']}¢")
        print(f"  Edge: {breakdown['edge']:.2f}")
        print(f"  Position: {reason}")
        
        if size > 0:
            current_exposure += size
            print(f"  Total exposure: ${current_exposure:.2f} ({current_exposure/sizer.capital:.1%})")


if __name__ == "__main__":
    test_position_sizer()
