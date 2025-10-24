from dataclasses import dataclass
from typing import Dict, List
def score_candidate(progress: float, recency_gap_days: float, tag_gap: float, hint_rate: float):
    progress_inverse=100-progress
    w={'progress_inverse':0.6,'recency_gap_days':0.3,'tag_gap':0.2,'hint_rate':-0.2}
    features={'progress_inverse':progress_inverse,'recency_gap_days':recency_gap_days,'tag_gap':tag_gap,'hint_rate':hint_rate}
    score=w['progress_inverse']*(progress_inverse/100)+w['recency_gap_days']*(recency_gap_days/10)+w['tag_gap']*tag_gap+w['hint_rate']*hint_rate
    return score, features
def to_confidence(score: float)->float:
    import math
    return max(0.0,min(1.0,1/(1+math.exp(-score))))
