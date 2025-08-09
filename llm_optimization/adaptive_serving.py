from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict, Tuple

import numpy as np
import psutil

from .quantization_pipeline import ModelProfile


@dataclass
class QueryComplexity:
    """Analyzed characteristics of an incoming query"""
    estimated_tokens: int
    complexity_score: float  # 0-1, where 1 is most complex
    domain: str  # 'general', 'technical', 'creative', etc.
    requires_reasoning: bool
    requires_factual_accuracy: bool


class AdaptiveModelServer:
    """
    Intelligent routing system that selects the optimal model variant.
    """

    def __init__(self, model_profiles: Dict[str, ModelProfile]):
        self.model_profiles = model_profiles
        self.loaded_models: Dict[str, object] = {}
        self.performance_history = []  # Track routing decisions

    def analyze_query_complexity(self, query: str) -> QueryComplexity:
        estimated_tokens = int(len(query.split()) * 1.3)
        indicators = {
            'length': len(query) > 100,
            'technical_terms': any(t in query.lower() for t in ['algorithm', 'implement', 'optimize', 'analyze']),
            'reasoning_required': any(w in query.lower() for w in ['why', 'how', 'explain', 'compare']),
            'code_generation': ('code' in query.lower()) or ('function' in query.lower()),
            'creative_writing': any(w in query.lower() for w in ['story', 'write', 'create', 'imagine'])
        }
        complexity_score = float(sum(indicators.values()) / len(indicators))
        if indicators['code_generation']:
            domain = 'technical'
        elif indicators['creative_writing']:
            domain = 'creative'
        else:
            domain = 'general'
        return QueryComplexity(
            estimated_tokens=estimated_tokens,
            complexity_score=complexity_score,
            domain=domain,
            requires_reasoning=indicators['reasoning_required'],
            requires_factual_accuracy=indicators['technical_terms']
        )

    async def route_query(self, query: str) -> Tuple[str, ModelProfile]:
        complexity = self.analyze_query_complexity(query)
        available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        selected = self._select_optimal_model(complexity, available_memory_gb)
        self.performance_history.append({
            'query': query[:120],
            'complexity': asdict(complexity),
            'selected_model': selected.model_id,
            'timestamp': time.time()
        })
        return selected.model_id, selected

    def _select_optimal_model(self, complexity: QueryComplexity, available_memory_gb: float) -> ModelProfile:
        viable = []
        for _, profile in self.model_profiles.items():
            required_memory = float(profile.hardware_requirements.get('min_ram_gb', 1.0))
            if required_memory > available_memory_gb:
                continue
            suitability = self._calculate_suitability(profile, complexity)
            viable.append((profile, suitability))

        if not viable:
            # Fallback to smallest memory footprint
            return min(self.model_profiles.values(), key=lambda p: p.memory_usage_mb)

        viable.sort(key=lambda x: x[1], reverse=True)
        return viable[0][0]

    def _calculate_suitability(self, profile: ModelProfile, complexity: QueryComplexity) -> float:
        # Quality match
        quality_match = 1.0 - abs(float(profile.quality_score) - float(complexity.complexity_score))
        # Speed
        speed_score = min(float(profile.avg_tokens_per_second) / 100.0, 1.0)
        # Efficiency bonus for simple queries
        efficiency_bonus = (1.0 - float(complexity.complexity_score)) * 0.2
        score = quality_match * 0.5 + speed_score * 0.3 + efficiency_bonus * 0.2
        return float(score)


