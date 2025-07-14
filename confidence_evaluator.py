from typing import List, Dict, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ConfidenceEvaluator:
    """Evaluates confidence scores for local vs web search decisions"""
    
    def __init__(self, threshold_low: float = 0.6, threshold_high: float = 0.8, model=None):
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
        self.model = model  # SentenceTransformer model for semantic understanding
        
        # Space domain examples for semantic matching
        self.space_domain_examples = [
            "space exploration and astronomy",
            "NASA missions and spacecraft",
            "planets moons and solar system",
            "rockets satellites and space technology", 
            "astronauts and space travel",
            "telescopes and astronomical observations",
            "astrophysics and cosmology research",
            "space agencies and programs",
            "interplanetary missions and probes",
            "stellar phenomena and galaxies"
        ]
    
    def calculate_domain_relevance(self, query: str) -> float:
        """Calculate how relevant the query is to space domain using semantic similarity"""
        if not self.model:
            # Fallback to basic heuristic if no model available
            space_terms = ['space', 'nasa', 'planet', 'moon', 'star', 'galaxy', 'rocket', 'satellite', 'astronaut', 'telescope']
            query_lower = query.lower()
            matches = sum(1 for term in space_terms if term in query_lower)
            return min(1.0, matches / max(1, len(query.split())))
        
        try:
            # Encode query and space domain examples
            query_embedding = self.model.encode([query])
            domain_embeddings = self.model.encode(self.space_domain_examples)
            
            # Calculate cosine similarities
            similarities = np.dot(query_embedding, domain_embeddings.T).flatten()
            
            # Use the maximum similarity as domain relevance
            domain_score = float(np.max(similarities))
            
            # Apply a threshold and scaling to make it more decisive
            if domain_score > 0.7:
                domain_score = min(1.0, domain_score * 1.2)  # Boost high similarities
            elif domain_score < 0.3:
                domain_score = max(0.0, domain_score * 0.8)  # Reduce low similarities
            
            logger.info(f"Semantic domain relevance for '{query}': {domain_score:.3f}")
            return domain_score
            
        except Exception as e:
            logger.error(f"Error in semantic domain detection: {e}")
            # Fallback to simple keyword matching
            space_terms = ['space', 'nasa', 'planet', 'moon', 'star', 'galaxy', 'rocket', 'satellite', 'astronaut', 'telescope']
            query_lower = query.lower()
            matches = sum(1 for term in space_terms if term in query_lower)
            return min(1.0, matches / max(1, len(query.split())))
    
    def evaluate_local_search_confidence(self, query: str, local_results: List[Dict]) -> float:
        """Evaluate confidence in local search results"""
        if not local_results:
            return 0.0
        
        # Factors for confidence calculation
        domain_relevance = self.calculate_domain_relevance(query)
        result_quality = self._evaluate_result_quality(local_results)
        result_count = min(1.0, len(local_results) / 5.0)  # Normalize to 0-1
        coverage_score = self._evaluate_query_coverage(query, local_results)
        
        # Weighted combination
        confidence = (
            domain_relevance * 0.3 +      # Is this a space query?
            result_quality * 0.3 +        # How good are the results?
            result_count * 0.2 +          # Do we have enough results?
            coverage_score * 0.2          # Do results cover the query well?
        )
        
        logger.info(f"Local search confidence: {confidence:.2f} "
                   f"(domain: {domain_relevance:.2f}, quality: {result_quality:.2f}, "
                   f"count: {result_count:.2f}, coverage: {coverage_score:.2f})")
        
        return min(1.0, confidence)
    
    def _evaluate_result_quality(self, results: List[Dict]) -> float:
        """Evaluate quality of search results based on relevance scores"""
        if not results:
            return 0.0
        
        relevance_scores = [result.get('relevance_score', 0.0) for result in results]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # Bonus for having multiple high-quality results
        high_quality_count = sum(1 for score in relevance_scores if score > 0.7)
        quality_bonus = min(0.3, high_quality_count * 0.1)
        
        return min(1.0, avg_relevance + quality_bonus)
    
    def _evaluate_query_coverage(self, query: str, results: List[Dict]) -> float:
        """Evaluate how well results cover the query terms"""
        if not results:
            return 0.0
        
        query_terms = set(query.lower().split())
        
        coverage_scores = []
        for result in results:
            # Combine title and content for coverage analysis
            text = f"{result.get('title', '')} {result.get('content', '')}".lower()
            
            # Count how many query terms appear in this result
            covered_terms = sum(1 for term in query_terms if term in text)
            coverage = covered_terms / len(query_terms) if query_terms else 0
            coverage_scores.append(coverage)
        
        # Use the best coverage from any single result
        return max(coverage_scores) if coverage_scores else 0.0
    
    def should_use_web_search(self, query: str, local_results: List[Dict]) -> Tuple[bool, str]:
        """Determine if web search should be used"""
        domain_relevance = self.calculate_domain_relevance(query)
        local_confidence = self.evaluate_local_search_confidence(query, local_results)
        
        # Decision logic
        if domain_relevance < 0.3:
            reason = f"Query appears to be outside space domain (semantic relevance: {domain_relevance:.3f})"
            return True, reason
        
        if local_confidence < self.threshold_low:
            reason = f"Local search confidence too low: {local_confidence:.2f} < {self.threshold_low}"
            return True, reason
        
        if local_confidence > self.threshold_high:
            reason = f"Local search confidence sufficient: {local_confidence:.2f} > {self.threshold_high}"
            return False, reason
        
        # In between thresholds - use hybrid approach
        reason = f"Using hybrid approach for medium confidence: {local_confidence:.2f}"
        return True, reason
    
    def evaluate_combined_confidence(self, local_results: List[Dict], web_results: List[Dict]) -> float:
        """Evaluate confidence when combining local and web results"""
        local_conf = self._evaluate_result_quality(local_results) if local_results else 0
        web_conf = self._evaluate_result_quality(web_results) if web_results else 0
        
        # Give slight preference to local results (curated data)
        if local_results and web_results:
            return max(local_conf * 1.1, web_conf)
        elif local_results:
            return local_conf
        elif web_results:
            return web_conf
        else:
            return 0.0 