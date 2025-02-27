import logging
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    def __init__(self):
        self.scaler = MinMaxScaler()
        
    def calculate_risk_score(self, indicators):
        """Calculate risk score from 1-10 (10 being highest risk)"""
        try:
            # Weight different risk factors
            weights = {
                'honeypot_risk': 0.3,
                'contract_verified': 0.15,
                'liquidity_analysis': 0.2,
                'holder_distribution': 0.2,
                'social_sentiment': 0.15
            }
            
            score = 0
            for factor, weight in weights.items():
                if factor in indicators:
                    if factor == 'contract_verified':
                        # Inverse the score for verified contracts (verified = good)
                        score += (1 - indicators[factor]) * weight
                    else:
                        score += indicators[factor] * weight
            
            # Scale to 1-10 range
            return min(max(score * 10, 1), 10)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 10  # Return maximum risk on error
