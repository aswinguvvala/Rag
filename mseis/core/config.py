# core/config.py
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SystemConfig(BaseModel):
    """System-wide configuration settings"""
    name: str = Field(default="MSEIS")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    max_workers: int = Field(default=4)

class LLMConfig(BaseModel):
    """Enhanced LLM provider configuration"""
    primary_provider: str = Field(default="ollama")
    
    class OpenAIConfig(BaseModel):
        api_key: str = Field(default="")
        model: str = Field(default="gpt-4-turbo-preview")
        embedding_model: str = Field(default="text-embedding-3-large")
        temperature: float = Field(default=0.1)
        max_tokens: int = Field(default=4096)
        timeout: int = Field(default=60)
        max_retries: int = Field(default=3)
    
    class OllamaConfig(BaseModel):
        base_url: str = Field(default="http://localhost:11434")
        model: str = Field(default="llama3.1:8b")
        temperature: float = Field(default=0.1)
        max_tokens: int = Field(default=4096)
        timeout: int = Field(default=120)
        stream: bool = Field(default=False)
    
    class FallbackConfig(BaseModel):
        enabled: bool = Field(default=True)
        provider: str = Field(default="openai")
        max_attempts: int = Field(default=3)
        retry_delay: int = Field(default=1)
    
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)

class EmbeddingsConfig(BaseModel):
    """Enhanced embeddings configuration"""
    primary_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    openai_model: str = Field(default="text-embedding-3-large")
    recruitment_model: str = Field(default="sentence-transformers/all-mpnet-base-v2")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    batch_size: int = Field(default=32)

class VectorDBConfig(BaseModel):
    """Enhanced vector database configuration"""
    provider: str = Field(default="chroma")
    
    class ChromaConfig(BaseModel):
        persist_directory: str = Field(default="./storage/chroma_db")
        collection_name: str = Field(default="recruitment_knowledge")
    
    class FAISSConfig(BaseModel):
        index_path: str = Field(default="./storage/faiss_index")
        dimension: int = Field(default=1536)
    
    class PineconeConfig(BaseModel):
        api_key: str = Field(default="")
        environment: str = Field(default="")
        index_name: str = Field(default="recruitment-intelligence")
        embedding_dimensions: int = Field(default=1536)
        metric: str = Field(default="cosine")
    
    chroma: ChromaConfig = Field(default_factory=ChromaConfig)
    faiss: FAISSConfig = Field(default_factory=FAISSConfig)
    pinecone: PineconeConfig = Field(default_factory=PineconeConfig)

class RAGConfig(BaseModel):
    """Advanced RAG configuration"""
    class RetrievalConfig(BaseModel):
        strategy: str = Field(default="adaptive")
        top_k: int = Field(default=20)
        rerank_top_k: int = Field(default=5)
        similarity_threshold: float = Field(default=0.7)
        vector_weight: float = Field(default=0.7)
        keyword_weight: float = Field(default=0.2)
        graph_weight: float = Field(default=0.1)
    
    class SelfRAGConfig(BaseModel):
        enabled: bool = Field(default=True)
        reflection_threshold: float = Field(default=0.6)
        max_iterations: int = Field(default=3)
        critique_model: str = Field(default="same")
        confidence_calibration: bool = Field(default=True)
    
    class CRAGConfig(BaseModel):
        enabled: bool = Field(default=True)
        confidence_threshold: float = Field(default=0.8)
        max_corrections: int = Field(default=2)
        verification_sources: List[str] = Field(default=["fact_check", "cross_reference"])
        enable_web_search: bool = Field(default=False)
    
    class AgenticConfig(BaseModel):
        enabled: bool = Field(default=True)
        max_agents: int = Field(default=5)
        agent_timeout: int = Field(default=300)
        enable_collaboration: bool = Field(default=True)
        coordination_strategy: str = Field(default="consensus")
    
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    self_rag: SelfRAGConfig = Field(default_factory=SelfRAGConfig)
    crag: CRAGConfig = Field(default_factory=CRAGConfig)
    agentic: AgenticConfig = Field(default_factory=AgenticConfig)

class RecruitmentDataConfig(BaseModel):
    """Recruitment-specific data sources configuration"""
    job_boards: List[str] = Field(default=["indeed", "linkedin", "glassdoor"])
    company_data: List[str] = Field(default=["company_websites", "annual_reports"])
    industry_reports: List[str] = Field(default=["market_research", "salary_surveys"])

class APIConfig(BaseModel):
    """API keys and endpoints configuration"""
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4-1106-preview")
    openai_embedding_model: str = Field(default="text-embedding-3-large")
    anthropic_api_key: Optional[str] = Field(default=None)
    pinecone_api_key: str = Field(default="")
    pinecone_environment: str = Field(default="")
    pinecone_index_name: str = Field(default="mseis-vectors")
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="")
    nasa_api_key: str = Field(default="")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)
    # Recruitment API keys
    linkedin_api_key: str = Field(default="")
    indeed_api_key: str = Field(default="")
    glassdoor_api_key: str = Field(default="")

class Config:
    """Main configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Try to find config.yaml in mseis directory or current directory
            mseis_config = Path(__file__).parent.parent / "config.yaml"
            current_config = Path("config.yaml")
            
            if mseis_config.exists():
                self.config_path = str(mseis_config)
            elif current_config.exists():
                self.config_path = str(current_config)
            else:
                self.config_path = "config.yaml"
        else:
            self.config_path = config_path
            
        self._load_config()
        self._load_env_vars()
        
    def _load_config(self):
        """Load configuration from YAML file"""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
        else:
            self.config_data = {}
            
    def _load_env_vars(self):
        """Load configuration from environment variables with enhanced support"""
        self.system = SystemConfig(
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_workers=int(os.getenv("MAX_WORKERS", "4"))
        )
        
        self.api = APIConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4-1106-preview"),
            openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
            pinecone_environment=os.getenv("PINECONE_ENVIRONMENT", ""),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "recruitment-intelligence"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
            nasa_api_key=os.getenv("NASA_API_KEY", ""),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            # Recruitment API keys
            linkedin_api_key=os.getenv("LINKEDIN_API_KEY", ""),
            indeed_api_key=os.getenv("INDEED_API_KEY", ""),
            glassdoor_api_key=os.getenv("GLASSDOOR_API_KEY", "")
        )
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def get_llm_config(self) -> LLMConfig:
        """Get enhanced LLM configuration"""
        llm_data = self.config_data.get('llm', {})
        
        # Create nested configs
        openai_config = LLMConfig.OpenAIConfig(**llm_data.get('openai', {}))
        ollama_config = LLMConfig.OllamaConfig(**llm_data.get('ollama', {}))
        fallback_config = LLMConfig.FallbackConfig(**llm_data.get('fallback', {}))
        
        return LLMConfig(
            primary_provider=llm_data.get('primary_provider', 'ollama'),
            openai=openai_config,
            ollama=ollama_config,
            fallback=fallback_config
        )
    
    def get_embeddings_config(self) -> EmbeddingsConfig:
        """Get embeddings configuration"""
        return EmbeddingsConfig(**self.config_data.get('embeddings', {}))
    
    def get_vector_db_config(self) -> VectorDBConfig:
        """Get vector database configuration"""
        vector_data = self.config_data.get('vector_db', {})
        
        chroma_config = VectorDBConfig.ChromaConfig(**vector_data.get('chroma', {}))
        faiss_config = VectorDBConfig.FAISSConfig(**vector_data.get('faiss', {}))
        pinecone_config = VectorDBConfig.PineconeConfig(**vector_data.get('pinecone', {}))
        
        return VectorDBConfig(
            provider=vector_data.get('provider', 'chroma'),
            chroma=chroma_config,
            faiss=faiss_config,
            pinecone=pinecone_config
        )
    
    def get_rag_config(self) -> RAGConfig:
        """Get advanced RAG configuration"""
        rag_data = self.config_data.get('rag', {})
        
        retrieval_config = RAGConfig.RetrievalConfig(**rag_data.get('retrieval', {}))
        self_rag_config = RAGConfig.SelfRAGConfig(**rag_data.get('self_rag', {}))
        crag_config = RAGConfig.CRAGConfig(**rag_data.get('crag', {}))
        agentic_config = RAGConfig.AgenticConfig(**rag_data.get('agentic', {}))
        
        return RAGConfig(
            retrieval=retrieval_config,
            self_rag=self_rag_config,
            crag=crag_config,
            agentic=agentic_config
        )
    
    def get_recruitment_config(self) -> RecruitmentDataConfig:
        """Get recruitment data sources configuration"""
        data_sources = self.config_data.get('data_sources', {})
        recruitment_data = data_sources.get('recruitment', {})
        return RecruitmentDataConfig(**recruitment_data)
    
    def is_recruitment_mode(self) -> bool:
        """Check if system is configured for recruitment use case"""
        return self.get('system.use_case', 'recruitment') == 'recruitment'
    
    def get_environment_vars(self) -> Dict[str, str]:
        """Get all environment variable substitutions"""
        env_vars = {}
        
        # Recursively find all ${VAR} patterns
        def find_env_vars(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    find_env_vars(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
                var_name = obj[2:-1]
                env_vars[path] = {
                    'variable': var_name,
                    'value': os.getenv(var_name, 'NOT_SET')
                }
        
        find_env_vars(self.config_data)
        return env_vars

# Global configuration instance
config = Config() 