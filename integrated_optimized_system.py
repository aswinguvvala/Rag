from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional

from simple_rag_system import SimpleRAGSystem
from llm_optimization.quantization_pipeline import QuantizationPipeline, ModelProfile
from llm_optimization.adaptive_serving import AdaptiveModelServer


class OptimizedRAGSystem(SimpleRAGSystem):
    """
    Enhanced RAG system with adaptive model optimization.
    Combines existing RAG capabilities with intelligent model selection.
    """

    def __init__(self):
        super().__init__()
        self.optimization_pipeline: Optional[QuantizationPipeline] = None
        self.adaptive_server: Optional[AdaptiveModelServer] = None
        self.model_profiles: Dict[str, ModelProfile] = {}

    async def initialize_optimization(self, base_model: str = "microsoft/phi-2") -> None:
        """
        Set up the optimization pipeline with a base model and create multiple variants.
        """
        print("🚀 Initializing optimization pipeline...")
        self.optimization_pipeline = QuantizationPipeline(base_model)
        hardware = self.optimization_pipeline.detect_hardware_capabilities()

        if hardware['ram_gb'] >= 16:
            methods = ['dynamic_int8', 'static_int8', 'int4']
        elif hardware['ram_gb'] >= 8:
            methods = ['dynamic_int8', 'int4']
        else:
            methods = ['dynamic_int8']

        for method in methods:
            print(f"Creating {method} variant...")
            try:
                profile = await self.optimization_pipeline.quantize_model(method)
                self.model_profiles[method] = profile
            except Exception as e:
                print(f"⚠️ Failed to create {method} variant: {e}")

        if self.model_profiles:
            self.adaptive_server = AdaptiveModelServer(self.model_profiles)
            print("✅ Optimization pipeline ready!")
        else:
            print("⚠️ No optimized models were created.")

    async def search_query_optimized(self, query: str, override_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced search that uses adaptive model selection. Optionally honor manual override.
        """
        search_results = await self.search_query(query)

        if self.adaptive_server and self.model_profiles:
            if override_model and override_model in self.model_profiles:
                selected_profile = self.model_profiles[override_model]
                selected_id = override_model
            else:
                selected_id, selected_profile = await self.adaptive_server.route_query(query)

            search_results['optimization'] = {
                'model_used': selected_id,
                'quality_score': float(selected_profile.quality_score),
                'tokens_per_second': float(selected_profile.avg_tokens_per_second),
                'memory_usage_mb': float(selected_profile.memory_usage_mb),
                'quantization_method': selected_profile.quantization_method
            }

        return search_results


