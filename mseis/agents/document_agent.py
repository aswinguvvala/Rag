# agents/document_agent.py
from typing import Dict, Any, List, Tuple, Optional
import asyncio
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI

from agents.base_agent import BaseAgent, QueryContext
from storage.pinecone_manager import PineconeManager
from storage.cache_manager import CacheManager
from core.config import config
from core.retrievers import HybridRetriever
from utils.monitoring import monitor_performance

class DocumentAgent(BaseAgent):
    """Agent for processing and retrieving NASA documents and technical papers"""
    
    def __init__(self):
        super().__init__(
            name="DocumentAgent",
            config=config.get("agents.document", {})
        )
        self.pinecone_manager = None
        self.cache_manager = None
        self.embeddings = None
        self.text_splitter = None
        self.llm = None
        self.retriever = None
        
    async def _setup(self):
        """Initialize document processing components"""
        # Initialize storage
        self.pinecone_manager = PineconeManager()
        await self.pinecone_manager.initialize()
        
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=config.api.openai_embedding_model,
            openai_api_key=config.api.openai_api_key
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get("chunk_size", 1000),
            chunk_overlap=self.config.get("chunk_overlap", 200),
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.1,
            openai_api_key=config.api.openai_api_key
        )
        
        # Initialize retriever
        self.retriever = HybridRetriever(
            pinecone_manager=self.pinecone_manager,
            embeddings=self.embeddings,
            namespace="nasa-docs"
        )
        
    @monitor_performance("document_agent", "process_documents")
    async def process_documents(
        self,
        documents: List[Document],
        metadata_extractors: Optional[List[callable]] = None
    ) -> Dict[str, Any]:
        """Process and index documents"""
        try:
            all_chunks = []
            
            for doc in documents:
                # Extract metadata
                metadata = doc.metadata or {}
                
                if metadata_extractors:
                    for extractor in metadata_extractors:
                        extracted = extractor(doc)
                        metadata.update(extracted)
                        
                # Split document
                chunks = self.text_splitter.split_text(doc.page_content)
                
                # Create chunk documents
                for i, chunk in enumerate(chunks):
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "source_doc_id": metadata.get("doc_id", doc.metadata.get("source", "unknown"))
                    }
                    
                    all_chunks.append(Document(
                        page_content=chunk,
                        metadata=chunk_metadata
                    ))
                    
            # Generate embeddings
            texts = [chunk.page_content for chunk in all_chunks]
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embeddings.embed_documents,
                texts
            )
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
                vector_id = f"doc_{chunk.metadata['source_doc_id']}_chunk_{i}"
                vectors.append((
                    vector_id,
                    embedding,
                    {
                        "text": chunk.page_content,
                        **chunk.metadata
                    }
                ))
                
            # Upsert to Pinecone
            result = await self.pinecone_manager.upsert_vectors(
                vectors=vectors,
                namespace="nasa-docs"
            )
            
            self.logger.info(
                "Documents processed successfully",
                num_documents=len(documents),
                num_chunks=len(all_chunks),
                upserted=result["total_upserted"]
            )
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "chunks_created": len(all_chunks),
                "vectors_upserted": result["total_upserted"]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing documents: {str(e)}")
            raise
            
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process a document-related query"""
        # Check cache first
        cache_key = {
            "query": context.original_query,
            "agent": "document",
            "expertise_level": context.user_expertise_level
        }
        
        cached_result = await self.cache_manager.get(cache_key, namespace="agent_responses")
        if cached_result:
            return cached_result["content"], cached_result["sources"], cached_result["confidence"]
            
        # Retrieve relevant documents
        relevant_docs = await self.retriever.get_relevant_documents(
            query=context.original_query,
            top_k=self.config.get("retrieval.top_k", 10)
        )
        
        if not relevant_docs:
            return "No relevant documents found for your query.", [], 0.0
            
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True
        )
        
        # Add expertise level to prompt
        expertise_prompt = self._get_expertise_prompt(context.user_expertise_level)
        full_query = f"{expertise_prompt}\n\nQuestion: {context.original_query}"
        
        # Get response
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            qa_chain,
            {"query": full_query}
        )
        
        # Extract sources
        sources = []
        for doc in result.get("source_documents", []):
            sources.append({
                "content": doc.page_content[:200] + "...",
                "metadata": doc.metadata,
                "relevance_score": doc.metadata.get("score", 0.8)
            })
            
        # Calculate confidence based on source quality and quantity
        confidence = self._calculate_confidence(sources, result["result"])
        
        # Cache result
        await self.cache_manager.set(
            cache_key,
            {
                "content": result["result"],
                "sources": sources,
                "confidence": confidence
            },
            namespace="agent_responses",
            ttl=3600
        )
        
        return result["result"], sources, confidence
        
    def _get_expertise_prompt(self, level: str) -> str:
        """Get prompt modifier based on expertise level"""
        prompts = {
            "student": "Explain in simple terms suitable for a student learning about space exploration. Use analogies and avoid too much technical jargon.",
            "general": "Provide a clear explanation balancing technical accuracy with accessibility.",
            "expert": "Provide a detailed technical response with specific data, equations, and technical terminology as appropriate."
        }
        return prompts.get(level, prompts["general"])
        
    def _calculate_confidence(self, sources: List[Dict], response: str) -> float:
        """Calculate confidence score based on sources and response"""
        if not sources:
            return 0.0
            
        # Base confidence on number and quality of sources
        avg_relevance = sum(s.get("relevance_score", 0) for s in sources) / len(sources)
        source_factor = min(len(sources) / 5, 1.0)  # More sources = higher confidence
        
        # Check if response seems complete
        response_length_factor = min(len(response) / 500, 1.0)
        
        confidence = (avg_relevance * 0.6 + source_factor * 0.3 + response_length_factor * 0.1)
        
        return round(confidence, 2) 