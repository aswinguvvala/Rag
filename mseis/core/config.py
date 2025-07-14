# core/config.py
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
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

class Config:
    """Main configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
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
        """Load configuration from environment variables"""
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
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "mseis-vectors"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
            nasa_api_key=os.getenv("NASA_API_KEY", ""),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD")
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

# Global configuration instance
config = Config() 