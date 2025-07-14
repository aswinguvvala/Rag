# agents/image_agent.py
import base64
import io
from PIL import Image
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import asyncio
import torch
from transformers import CLIPModel, CLIPProcessor

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from agents.base_agent import BaseAgent, QueryContext
from storage.pinecone_manager import PineconeManager
from storage.cache_manager import CacheManager
from core.config import config
from utils.monitoring import monitor_performance

class ImageAgent(BaseAgent):
    """Agent for processing and analyzing space imagery"""
    
    def __init__(self):
        super().__init__(
            name="ImageAgent",
            config=config.get("agents.image", {})
        )
        self.clip_model = None
        self.clip_processor = None
        self.pinecone_manager = None
        self.cache_manager = None
        self.vision_llm = None
        
    async def _setup(self):
        """Initialize image processing components"""
        # Initialize storage
        self.pinecone_manager = PineconeManager()
        await self.pinecone_manager.initialize()
        
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        # Initialize CLIP model
        model_name = self.config.get("model", "openai/clip-vit-base-patch32")
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(model_name)
        
        # Initialize vision-capable LLM
        self.vision_llm = ChatOpenAI(
            model="gpt-4-vision-preview",
            temperature=0.1,
            openai_api_key=config.api.openai_api_key,
            max_tokens=1000
        )
        
    @monitor_performance("image_agent", "process_images")
    async def process_images(
        self,
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process and index space images
        
        Args:
            images: List of dicts with 'image_path', 'metadata'
        """
        try:
            vectors = []
            
            for img_data in images:
                # Load image
                image = Image.open(img_data["image_path"])
                
                # Resize if needed
                max_res = self.config.get("max_resolution", 1024)
                if max(image.size) > max_res:
                    image.thumbnail((max_res, max_res), Image.Resampling.LANCZOS)
                    
                # Generate CLIP embedding
                inputs = self.clip_processor(images=image, return_tensors="pt")
                
                with torch.no_grad():
                    image_features = self.clip_model.get_image_features(**inputs)
                    
                embedding = image_features.squeeze().numpy().tolist()
                
                # Prepare metadata
                metadata = {
                    **img_data.get("metadata", {}),
                    "image_path": img_data["image_path"],
                    "width": image.size[0],
                    "height": image.size[1],
                    "processed_at": datetime.now().isoformat()
                }
                
                # Create vector
                vector_id = f"img_{metadata.get('image_id', img_data['image_path'])}"
                vectors.append((vector_id, embedding, metadata))
                
            # Upsert to Pinecone
            result = await self.pinecone_manager.upsert_vectors(
                vectors=vectors,
                namespace="space-images"
            )
            
            self.logger.info(
                "Images processed successfully",
                num_images=len(images),
                vectors_upserted=result["total_upserted"]
            )
            
            return {
                "success": True,
                "images_processed": len(images),
                "vectors_upserted": result["total_upserted"]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing images: {str(e)}")
            raise
            
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process an image-related query"""
        # Check if query contains an image
        has_image = context.metadata.get("image_data") is not None
        
        if has_image:
            return await self._process_image_query(context)
        else:
            return await self._process_text_query(context)
            
    async def _process_text_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process text query to find relevant images"""
        # Generate text embedding
        inputs = self.clip_processor(text=[context.original_query], return_tensors="pt")
        
        with torch.no_grad():
            text_features = self.clip_model.get_text_features(**inputs)
            
        text_embedding = text_features.squeeze().numpy().tolist()
        
        # Search for similar images
        results = await self.pinecone_manager.query_vectors(
            query_embedding=text_embedding,
            namespace="space-images",
            top_k=5,
            include_metadata=True
        )
        
        if not results:
            return "No relevant space images found for your query.", [], 0.0
            
        # Format response
        response_parts = [f"Found {len(results)} relevant space images for '{context.original_query}':\n"]
        sources = []
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            response_parts.append(
                f"\n{i}. {metadata.get('title', 'Untitled')} "
                f"(Score: {result['score']:.2f})"
            )
            
            if metadata.get("description"):
                response_parts.append(f"   - {metadata['description']}")
                
            if metadata.get("mission"):
                response_parts.append(f"   - Mission: {metadata['mission']}")
                
            if metadata.get("date"):
                response_parts.append(f"   - Date: {metadata['date']}")
                
            sources.append({
                "type": "image",
                "metadata": metadata,
                "relevance_score": result["score"]
            })
            
        # Calculate confidence
        avg_score = sum(r["score"] for r in results) / len(results)
        confidence = min(avg_score * 1.2, 1.0)  # Boost confidence slightly
        
        return "\n".join(response_parts), sources, confidence
        
    async def _process_image_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process query with an uploaded image"""
        image_data = context.metadata["image_data"]
        
        # Analyze image with vision model
        messages = [
            SystemMessage(content="You are an expert in space imagery analysis. Analyze the provided space-related image and answer questions about it."),
            HumanMessage(
                content=[
                    {"type": "text", "text": context.original_query},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            )
        ]
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            self.vision_llm.invoke,
            messages
        )
        
        # Find similar images in database
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        inputs = self.clip_processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            
        embedding = image_features.squeeze().numpy().tolist()
        
        similar_images = await self.pinecone_manager.query_vectors(
            query_embedding=embedding,
            namespace="space-images",
            top_k=3,
            include_metadata=True
        )
        
        sources = [
            {
                "type": "similar_image",
                "metadata": img.get("metadata", {}),
                "relevance_score": img["score"]
            }
            for img in similar_images
        ]
        
        return response.content, sources, 0.9 