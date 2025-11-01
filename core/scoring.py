"""
Scoring algorithms for scanner signals
Multi-factor composite scoring system
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4
    EXTREME = 5


@dataclass
class SignalScore:
    """Container for signal scores"""
    composite: float  # 0-10
    flow: Optional[float] = None
    gex: Optional[float] = None
    dark_pool: Optional[float] = None
    institutional: Optional[float] = None
    sentiment: Optional[float] = None
    
    strength: SignalStrength = SignalStrength.MODERATE
    confidence: float = 0.5  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'composite': self.composite,
            'flow': self.flow,
            'gex': self.gex,
            'dark_pool': self.dark_pool,
            'institutional': self.institutional,
            'sentiment': self.sentiment,
            'strength': self.strength.name,
            'confidence': self.confidence
        }


class ScoringEngine:
    """
    Multi-factor scoring engine for trading signals
    
    Combines various data sources into a composite score
    """
    
    def __init__(self):
        # Scoring weights (sum to 1.0)
        self.weights = {
            'flow': 0.35,
            'gex': 0.25,
            'dark_pool': 0.15,
            'institutional': 0.15,
            'sentiment': 0.10
        }
    
    def calculate_composite_score(
        self,
        flow_score: Optional[float] = None,
        gex_score: Optional[float] = None,
        dark_pool_score: Optional[float] = None,
        institutional_score: Optional[float] = None,
        sentiment_score: Optional[float] = None
    ) -> SignalScore:
        """
        Calculate composite score from individual scores
        
        Args:
            Individual scores (0-10 scale)
        
        Returns:
            SignalScore with composite and strength
        """
        scores = {
            'flow': flow_score,
            'gex': gex_score,
            'dark_pool': dark_pool_score,
            'institutional': institutional_score,
            'sentiment': sentiment_score
        }
        
        # Calculate weighted composite
        composite = 0.0
        total_weight = 0.0
        available_scores = 0
        
        for key, score in scores.items():
            if score is not None:
                composite += score * self.weights[key]
                total_weight += self.weights[key]
                available_scores += 1
        
        # Normalize by available weights
        if total_weight > 0:
            composite = composite / total_weight * 10
        
        # Calculate confidence based on data availability
        confidence = available_scores / len(scores)
        
        # Determine strength
        if composite >= 9:
            strength = SignalStrength.EXTREME
        elif composite >= 7.5:
            strength = SignalStrength.VERY_STRONG
        elif composite >= 6:
            strength = SignalStrength.STRONG
        elif composite >= 4:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        return SignalScore(
            composite=composite,
            flow=flow_score,
            gex=gex_score,
            dark_pool=dark_pool_score,
            institutional=institutional_score,
            sentiment=sentiment_score,
            strength=strength,
            confidence=confidence
        )
    
    def score_flow_signal(
        self,
        premium: float,
        volume: int,
        unusual_factor: float = 1.0
    ) -> float:
        """
        Score options flow signal
        
        Args:
            premium: Total premium in dollars
            volume: Contract volume
            unusual_factor: Multiplier for unusual activity
        
        Returns:
            Score 0-10
        """
        # Premium component (0-5)
        premium_score = min(5, premium / 200000)  # $200k = 5 points
        
        # Volume component (0-3)
        volume_score = min(3, volume / 500)  # 500 contracts = 3 points
        
        # Unusual factor (0-2)
        unusual_score = min(2, unusual_factor)
        
        return premium_score + volume_score + unusual_score
    
    def score_gex_signal(
        self,
        gex_value: float,
        distance_from_spot_pct: float,
        threshold: float = 1000000
    ) -> float:
        """
        Score GEX pivot signal
        
        Args:
            gex_value: Gamma exposure value
            distance_from_spot_pct: Distance from current price (%)
            threshold: GEX significance threshold
        
        Returns:
            Score 0-10
        """
        # Magnitude component (0-6)
        magnitude_score = min(6, abs(gex_value) / threshold * 6)
        
        # Proximity component (0-4) - closer = higher score
        if abs(distance_from_spot_pct) < 0.5:
            proximity_score = 4
        elif abs(distance_from_spot_pct) < 1.0:
            proximity_score = 3
        elif abs(distance_from_spot_pct) < 2.0:
            proximity_score = 2
        elif abs(distance_from_spot_pct) < 5.0:
            proximity_score = 1
        else:
            proximity_score = 0
        
        return magnitude_score + proximity_score
    
    def score_dark_pool_signal(
        self,
        trade_count: int,
        total_value: float,
        price_concentration: float = 1.0
    ) -> float:
        """
        Score dark pool level signal
        
        Args:
            trade_count: Number of trades at level
            total_value: Total dollar value
            price_concentration: How concentrated at price level (0-1)
        
        Returns:
            Score 0-10
        """
        # Trade frequency component (0-4)
        frequency_score = min(4, trade_count / 3)
        
        # Value component (0-4)
        value_score = min(4, total_value / 2000000)  # $2M = 4 points
        
        # Concentration component (0-2)
        concentration_score = price_concentration * 2
        
        return frequency_score + value_score + concentration_score
    
    def score_institutional_signal(
        self,
        position_size: float,
        change_pct: float,
        institution_quality: float = 0.5
    ) -> float:
        """
        Score institutional activity signal
        
        Args:
            position_size: Position size in dollars
            change_pct: Percent change in position
            institution_quality: Quality score of institution (0-1)
        
        Returns:
            Score 0-10
        """
        # Size component (0-4)
        size_score = min(4, position_size / 25000000)  # $25M = 4 points
        
        # Change component (0-4)
        change_score = min(4, abs(change_pct) / 25)  # 25% change = 4 points
        
        # Quality component (0-2)
        quality_score = institution_quality * 2
        
        return size_score + change_score + quality_score
    
    def rank_signals(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank and sort signals by composite score
        
        Args:
            signals: List of signal dictionaries
        
        Returns:
            Sorted signals with scores
        """
        scored_signals = []
        
        for signal in signals:
            # Calculate composite if not present
            if 'score' not in signal:
                score = self.calculate_composite_score(
                    flow_score=signal.get('flow_score'),
                    gex_score=signal.get('gex_score'),
                    dark_pool_score=signal.get('dark_pool_score'),
                    institutional_score=signal.get('institutional_score'),
                    sentiment_score=signal.get('sentiment_score')
                )
                signal['score'] = score.composite
                signal['strength'] = score.strength.name
                signal['confidence'] = score.confidence
            
            scored_signals.append(signal)
        
        # Sort by score descending
        scored_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return scored_signals


if __name__ == '__main__':
    # Test scoring engine
    engine = ScoringEngine()
    
    # Test flow score
    flow_score = engine.score_flow_signal(
        premium=500000,
        volume=1000,
        unusual_factor=1.5
    )
    print(f"Flow Score: {flow_score:.2f}/10")
    
    # Test GEX score
    gex_score = engine.score_gex_signal(
        gex_value=2000000,
        distance_from_spot_pct=0.8
    )
    print(f"GEX Score: {gex_score:.2f}/10")
    
    # Test composite
    composite = engine.calculate_composite_score(
        flow_score=flow_score,
        gex_score=gex_score,
        dark_pool_score=6.0
    )
    print(f"\nComposite Score: {composite.composite:.2f}/10")
    print(f"Strength: {composite.strength.name}")
    print(f"Confidence: {composite.confidence:.2%}")
