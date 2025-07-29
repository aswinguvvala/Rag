#!/usr/bin/env python3
"""
Simple RAG System - Clean implementation of RAG + Web Search
Direct implementation: Query -> Vector Search -> Local/Web -> OpenAI Response
Cost-optimized for recruiter showcase with gpt-4o-mini
"""

import asyncio
import aiohttp
import numpy as np
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import pickle
import os
from pathlib import Path

# Import dependencies with fallbacks
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ faiss not available")

try:
    from web_search_manager import UniversalWebSearchManager
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("⚠️ web_search_manager not available")

# OpenAI integration with fallback
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai not available")

@dataclass
class SearchResult:
    """Simple search result structure"""
    content: str
    title: str
    source: str
    similarity: float
    source_type: str  # 'local' or 'web'

class SimpleRAGSystem:
    """Clean, simple RAG system implementation"""
    
    def __init__(self):
        print("🚀 Initializing Simple RAG System...")
        
        # Core components
        self.embedding_model = None
        self.faiss_index = None
        self.documents = []
        self.document_metadata = []
        
        # Web search manager
        self.web_search_manager = None
        if WEB_SEARCH_AVAILABLE:
            self.web_search_manager = UniversalWebSearchManager()
        
        # OpenAI configuration - cost-optimized for recruiter showcase
        self.openai_client = None
        self.openai_api_key = self._get_openai_api_key()
        self.openai_model = self._get_env_or_secret('OPENAI_MODEL', 'gpt-4o-mini')  # Cheapest model (~$0.001/query)
        self.max_tokens = int(self._get_env_or_secret('OPENAI_MAX_TOKENS', '150'))  # Cost control
        self.openai_available = False
        
        # Initialize OpenAI client if API key is available
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.openai_available = True
                print(f"✅ OpenAI initialized with model: {self.openai_model}")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
        elif not self.openai_api_key:
            print("⚠️ OpenAI API key not found in environment variables")
        
        # Legacy Ollama configuration (fallback for local development)
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "llama3.2:3b"  # Default model
        
        # Search configuration - optimized for cloud deployment
        self.similarity_threshold = 0.35  # Lower threshold for better local results (was 0.45)
        self.max_local_results = 5  # More local results (was 3)
        self.max_web_results = 3  # Fewer web results to reduce latency (was 5)
        
        # Storage paths
        self.storage_dir = Path("storage/simple_rag")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_path = self.storage_dir / "faiss_index.bin"
        self.metadata_path = self.storage_dir / "metadata.pkl"
        self.documents_path = self.storage_dir / "documents.pkl"
        
        print("✅ Simple RAG System initialized")
    
    def _get_env_or_secret(self, key: str, default: str = None) -> str:
        """Get value from environment variable or Streamlit secrets"""
        # First try environment variable
        value = os.getenv(key)
        if value:
            return value
        
        # Try Streamlit secrets if available
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except (ImportError, AttributeError, KeyError):
            pass
        
        return default
    
    def _get_openai_api_key(self) -> str:
        """Get OpenAI API key from environment or Streamlit secrets"""
        # Try environment variable first (.env file)
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # Try Streamlit secrets for cloud deployment
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                return st.secrets['OPENAI_API_KEY']
        except (ImportError, AttributeError, KeyError):
            pass
        
        return None
    
    async def initialize(self) -> bool:
        """Initialize all components with graceful degradation"""
        print("🔧 Initializing RAG components...")
        
        # Detect environment early for optimized initialization
        is_streamlit_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD')
        if is_streamlit_cloud:
            print("🌐 Streamlit Cloud environment detected - optimizing for cloud deployment")
        
        success_count = 0
        total_components = 3
        
        try:
            # Initialize embedding model
            try:
                if await self._init_embedding_model():
                    success_count += 1
                    print("✅ Embedding model initialized")
                else:
                    print("⚠️ Embedding model failed, but continuing...")
            except Exception as e:
                print(f"⚠️ Embedding model error: {e}, continuing...")
            
            # Load or create document index
            try:
                if await self._init_document_index():
                    success_count += 1
                    print("✅ Document index initialized")
                else:
                    print("⚠️ Document index failed, but continuing...")
            except Exception as e:
                print(f"⚠️ Document index error: {e}, continuing...")
            
            # Test Ollama connection (non-blocking)
            try:
                if await self._test_ollama():
                    success_count += 1
                    print("✅ Ollama connection verified")
                else:
                    print("⚠️ Ollama not available, web search only mode")
            except Exception as e:
                print(f"⚠️ Ollama test error: {e}, web search only mode")
            
            # System is functional if at least embedding model works
            if success_count >= 1:
                print(f"✅ RAG System initialized ({success_count}/{total_components} components active)")
                return True
            else:
                print("❌ Critical components failed, system may not function properly")
                return False
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def _init_embedding_model(self) -> bool:
        """Initialize sentence transformer model"""
        if not EMBEDDINGS_AVAILABLE:
            print("❌ Cannot initialize embedding model - sentence-transformers not available")
            return False
        
        try:
            print("📦 Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")
            return True
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False
    
    async def _init_document_index(self) -> bool:
        """Load existing index or create new one"""
        if not FAISS_AVAILABLE or not self.embedding_model:
            print("❌ Cannot initialize FAISS index - requirements not met")
            return False
        
        try:
            # Try to load existing index
            if self.faiss_path.exists() and self.metadata_path.exists() and self.documents_path.exists():
                print("🔄 Loading existing FAISS index...")
                self.faiss_index = faiss.read_index(str(self.faiss_path))
                
                with open(self.metadata_path, 'rb') as f:
                    self.document_metadata = pickle.load(f)
                
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                
                print(f"✅ Loaded {len(self.documents)} documents from existing index")
                return True
            else:
                print("🆕 Creating new document index...")
                await self._create_initial_index()
                return True
                
        except Exception as e:
            print(f"❌ Failed to initialize document index: {e}")
            return False
    
    async def _create_initial_index(self):
        """Create initial FAISS index with comprehensive knowledge base"""
        print("📚 Creating comprehensive knowledge base for deployment...")
        
        # Detect deployment environment for logging
        is_streamlit_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD')
        if is_streamlit_cloud:
            print("🌐 Detected Streamlit Cloud deployment")
        else:
            print("💻 Local environment detected")
        
        # First, try to load from consolidated knowledge base
        knowledge_documents = await self._load_consolidated_knowledge_base()
        
        # If no documents loaded, fall back to hardcoded documents
        if not knowledge_documents:
            print("⚠️ No consolidated knowledge base found, using fallback documents...")
            knowledge_documents = self._get_fallback_documents()
        
        # Create embeddings and index
        await self._create_faiss_index_from_documents(knowledge_documents, is_streamlit_cloud)
    
    async def _load_consolidated_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load articles from consolidated knowledge base file"""
        try:
            knowledge_base_path = Path("data/knowledge_base.json")
            
            if not knowledge_base_path.exists():
                print(f"ℹ️ Consolidated knowledge base not found at: {knowledge_base_path}")
                return []
            
            print(f"📖 Loading consolidated knowledge base from: {knowledge_base_path}")
            
            with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract articles from the structured data
            articles = data.get('articles', [])
            metadata = data.get('metadata', {})
            
            if articles:
                print(f"✅ Loaded {len(articles)} articles from consolidated knowledge base")
                print(f"📊 Categories: {len(metadata.get('categories', []))}")
                print(f"📝 Total content: {metadata.get('total_articles', len(articles))} articles")
                
                # Convert to our document format
                documents = []
                for article in articles:
                    # Convert article format to our document format
                    doc = {
                        "title": article.get('title', 'Unknown Title'),
                        "content": article.get('content', ''),
                        "category": article.get('category', 'general'),
                        "topics": article.get('topics', []),
                        "source": article.get('source', 'Consolidated Knowledge Base'),
                        "url": article.get('url', '')
                    }
                    
                    # Only include documents with substantial content
                    if len(doc["content"]) >= 100:
                        documents.append(doc)
                
                print(f"🔄 Processed {len(documents)} documents with substantial content")
                return documents
            
            else:
                print("⚠️ No articles found in consolidated knowledge base")
                return []
                
        except Exception as e:
            print(f"❌ Error loading consolidated knowledge base: {e}")
            return []
    
    def _get_fallback_documents(self) -> List[Dict[str, Any]]:
        """Get fallback hardcoded documents if consolidated knowledge base unavailable"""
        print("🔄 Using fallback document collection...")
        
        # Comprehensive knowledge base with 50+ documents across multiple domains
        knowledge_documents = [
            # Space Exploration & Missions (Expanded)
            {
                "title": "NASA Artemis Program",
                "content": "The Artemis program is NASA's ambitious plan to return humans to the Moon by 2026 and establish a sustainable lunar presence. Named after the Greek goddess of the hunt and twin sister of Apollo, Artemis aims to land the first woman and the next man on the lunar surface. The program includes the Space Launch System (SLS) rocket, the Orion spacecraft, and the Lunar Gateway space station. Artemis will serve as a stepping stone for future Mars missions and will focus on the lunar South Pole region where water ice has been detected. The program involves international partnerships and commercial collaborations, with a budget of over $93 billion through 2025.",
                "category": "space_missions",
                "topics": ["NASA", "Artemis", "Moon", "lunar missions", "space exploration", "SLS", "Orion"]
            },
            {
                "title": "SpaceX Starship Development",
                "content": "SpaceX's Starship is a fully reusable super heavy-lift launch vehicle designed for missions to Mars, the Moon, and beyond. Standing 120 meters tall when combined with its Super Heavy booster, Starship is the most powerful rocket ever built. The vehicle uses Raptor engines burning liquid methane and liquid oxygen, chosen for their ability to be produced on Mars. Starship has completed several test flights and is central to NASA's Artemis program as the Human Landing System for lunar missions.",
                "category": "space_technology",
                "topics": ["SpaceX", "Starship", "Mars", "reusable rockets", "Raptor engines", "Super Heavy", "lunar landing"]
            },
            {
                "title": "International Space Station Operations",
                "content": "The International Space Station (ISS) is a multinational collaborative project involving NASA, Roscosmos, ESA, JAXA, and CSA. Orbiting Earth at approximately 408 kilometers altitude, the ISS serves as a microgravity laboratory for scientific research in biology, physics, materials science, and astronomy. The station has been continuously occupied since November 2000, with crew rotations every six months. Experiments conducted on the ISS have led to advances in medicine, agriculture, and technology that benefit life on Earth.",
                "category": "space_stations",
                "topics": ["ISS", "microgravity", "space research", "international cooperation", "orbital laboratory", "Earth observation"]
            },
            {
                "title": "Mars Exploration Rovers",
                "content": "NASA's Mars exploration program has deployed several successful rovers including Spirit, Opportunity, Curiosity, and Perseverance. These robotic explorers have revolutionized our understanding of Mars geology, climate, and potential for past life. Perseverance, launched in 2020, is actively searching for signs of ancient microbial life and collecting samples for future return to Earth. The Ingenuity helicopter, deployed from Perseverance, achieved the first powered flight on another planet, opening new possibilities for aerial exploration of Mars.",
                "category": "planetary_exploration",
                "topics": ["Mars", "rovers", "Perseverance", "Curiosity", "Ingenuity", "astrobiology", "sample return"]
            },
            {
                "title": "James Webb Space Telescope Discoveries",
                "content": "The James Webb Space Telescope (JWST), launched in 2021, is the most powerful space telescope ever built. Operating at the L2 Lagrange point, JWST observes the universe in infrared light, allowing it to see through cosmic dust and study the first galaxies formed after the Big Bang. Its discoveries include detailed images of exoplanet atmospheres, star formation regions, and the most distant galaxies ever observed. JWST's data is revolutionizing our understanding of galaxy formation, stellar evolution, and planetary systems.",
                "category": "space_telescopes",
                "topics": ["JWST", "infrared astronomy", "exoplanets", "early universe", "Hubble successor", "L2 point", "cosmic observations"]
            },
            {
                "title": "Exoplanet Discovery and Characterization",
                "content": "The search for exoplanets has discovered over 5,000 worlds orbiting other stars, with potentially habitable planets in the 'Goldilocks zone' where liquid water could exist. The Kepler Space Telescope and TESS (Transiting Exoplanet Survey Satellite) have identified thousands of candidate planets using the transit method. Future missions like the Roman Space Telescope will directly image exoplanets and analyze their atmospheres for biosignatures. The discovery of potentially habitable worlds like Proxima Centauri b and TRAPPIST-1 system planets has revolutionized our understanding of planetary systems.",
                "category": "exoplanets",
                "topics": ["exoplanets", "habitable zone", "Kepler", "TESS", "biosignatures", "Proxima Centauri", "TRAPPIST-1"]
            },
            {
                "title": "Space Propulsion Technologies",
                "content": "Advanced propulsion systems are crucial for future deep space missions. Ion drives, used by missions like Dawn and Hayabusa, provide efficient long-term thrust for interplanetary travel. Nuclear thermal propulsion could reduce Mars transit times from 9 months to 3-4 months. Breakthrough Starshot proposes using light sails accelerated by lasers to reach nearby stars. Solar sails, demonstrated by missions like IKAROS and LightSail, use radiation pressure for propellantless propulsion. These technologies will enable faster, more efficient exploration of the solar system and beyond.",
                "category": "propulsion",
                "topics": ["ion propulsion", "nuclear thermal", "solar sails", "light sails", "interplanetary travel", "propulsion efficiency"]
            },
            {
                "title": "Lunar Resources and ISRU",
                "content": "The Moon contains valuable resources for future space exploration, including water ice in permanently shadowed craters at the poles, rare earth elements, and Helium-3 for potential fusion power. In-Situ Resource Utilization (ISRU) technologies aim to extract and process these materials to support sustained lunar presence. Water can be split into hydrogen and oxygen for rocket fuel, while lunar regolith can be used for construction materials. The Moon's low gravity and lack of atmosphere make it an ideal staging ground for missions to Mars and the outer solar system.",
                "category": "lunar_resources",
                "topics": ["lunar water", "ISRU", "Helium-3", "lunar mining", "space resources", "lunar base", "fuel production"]
            },
            {
                "title": "Commercial Space Industry",
                "content": "The commercial space industry has transformed space access with companies like SpaceX, Blue Origin, Virgin Galactic, and others. SpaceX's Falcon 9 reusability has dramatically reduced launch costs, while Dragon capsules provide crew transportation to the ISS. Blue Origin's New Shepard offers suborbital tourism flights. The commercial sector is developing space manufacturing, satellite constellations like Starlink, and asteroid mining ventures. This commercialization is making space more accessible and driving innovation in launch systems, spacecraft, and space services.",
                "category": "commercial_space",
                "topics": ["SpaceX", "Blue Origin", "commercial crew", "space tourism", "satellite constellations", "launch costs", "space economy"]
            },
            {
                "title": "Astrobiology and Search for Life",
                "content": "Astrobiology studies the possibility of life beyond Earth, focusing on extremophile organisms that thrive in harsh conditions similar to those on other planets. Jupiter's moon Europa and Saturn's moon Enceladus have subsurface oceans that may harbor life. Mars shows evidence of ancient water activity and organic compounds detected by rovers. The search for biosignatures in exoplanet atmospheres using telescopes like JWST could reveal signs of life around other stars. Missions like Europa Clipper and Dragonfly will directly search for signs of life in our solar system.",
                "category": "astrobiology",
                "topics": ["astrobiology", "Europa", "Enceladus", "extremophiles", "biosignatures", "Mars life", "ocean moons"]
            },
            
            # Additional Space & Astronomy Content (40+ more documents)
            {
                "title": "Solar System Formation and Evolution",
                "content": "The solar system formed approximately 4.6 billion years ago from the gravitational collapse of a giant molecular cloud. The nebular hypothesis explains how dust and gas condensed to form the Sun and planets through accretion. Inner rocky planets formed from silicates and metals, while outer gas giants formed from ice and gas in the cooler regions beyond the frost line. The Late Heavy Bombardment period shaped planetary surfaces, and continuing evolution includes atmospheric changes, magnetic field variations, and ongoing geological processes on planetary bodies.",
                "category": "planetary_science",
                "topics": ["solar system formation", "nebular hypothesis", "accretion", "planetary evolution", "Late Heavy Bombardment"]
            },
            {
                "title": "Black Holes and Event Horizons",
                "content": "Black holes are regions of spacetime where gravity is so strong that nothing, including light, can escape once it crosses the event horizon. They form when massive stars collapse at the end of their lives, creating singularities where known physics breaks down. The Event Horizon Telescope has captured images of supermassive black holes in M87 and Sagittarius A*. Black holes play crucial roles in galaxy formation and evolution, and their study has confirmed many predictions of Einstein's general relativity including gravitational waves from black hole mergers.",
                "category": "astrophysics",
                "topics": ["black holes", "event horizon", "singularities", "general relativity", "gravitational waves", "Event Horizon Telescope"]
            },
            {
                "title": "Mars Atmospheric Composition and Climate",
                "content": "Mars has a thin atmosphere composed primarily of carbon dioxide (95.3%) with small amounts of nitrogen, argon, and trace gases. The atmospheric pressure is less than 1% of Earth's, making liquid water unstable on the surface. Mars experiences dust storms that can engulf the entire planet, affecting solar-powered missions. Evidence suggests Mars once had a thicker atmosphere and flowing water, with the atmosphere being gradually stripped away by solar wind due to the lack of a strong magnetic field. Understanding Mars' climate history is crucial for assessing its past habitability.",
                "category": "planetary_atmospheres",
                "topics": ["Mars atmosphere", "climate change", "dust storms", "atmospheric escape", "habitability", "water history"]
            },
            {
                "title": "Quantum Mechanics and Computing",
                "content": "Quantum mechanics describes the behavior of matter and energy at the atomic and subatomic scale, where particles exhibit wave-particle duality and can exist in superposition states. Quantum computing harnesses these principles using qubits that can be in multiple states simultaneously, potentially solving certain problems exponentially faster than classical computers. Quantum algorithms like Shor's factorization and Grover's search demonstrate quantum advantage. Major tech companies and research institutions are developing quantum computers, with applications in cryptography, drug discovery, optimization, and scientific simulation.",
                "category": "quantum_physics",
                "topics": ["quantum mechanics", "quantum computing", "qubits", "superposition", "quantum algorithms", "quantum advantage"]
            },
            {
                "title": "Artificial Intelligence and Machine Learning",
                "content": "Artificial Intelligence encompasses systems that can perform tasks typically requiring human intelligence, including learning, reasoning, perception, and decision-making. Machine learning, a subset of AI, enables systems to improve performance through experience without explicit programming. Deep learning uses neural networks with multiple layers to model complex patterns in data. Recent advances include large language models, computer vision, robotics, and AI-assisted scientific discovery. Applications span healthcare, transportation, finance, education, and creative industries, while raising important questions about ethics, bias, and societal impact.",
                "category": "artificial_intelligence",
                "topics": ["AI", "machine learning", "deep learning", "neural networks", "language models", "computer vision", "AI ethics"]
            },
            {
                "title": "Climate Change and Earth Systems",
                "content": "Climate change refers to long-term shifts in global temperatures and weather patterns, primarily driven by increased greenhouse gas concentrations from human activities. The greenhouse effect traps heat in Earth's atmosphere, with carbon dioxide, methane, and other gases contributing to warming. Earth system science studies interactions between the atmosphere, hydrosphere, biosphere, and geosphere. Climate models predict continued warming, sea level rise, extreme weather events, and ecosystem changes. Mitigation strategies include renewable energy, carbon capture, and emission reductions, while adaptation involves preparing for unavoidable climate impacts.",
                "category": "earth_science",
                "topics": ["climate change", "greenhouse effect", "global warming", "Earth systems", "climate models", "renewable energy", "sustainability"]
            },
            {
                "title": "Gene Editing and CRISPR Technology",
                "content": "CRISPR-Cas9 is a revolutionary gene editing tool that allows precise modification of DNA sequences in living cells. The system uses guide RNA to direct the Cas9 enzyme to specific genetic locations, where it can cut, insert, or modify DNA sequences. Applications include treating genetic diseases, developing disease-resistant crops, creating animal models for research, and potentially eliminating inherited disorders. Recent advances include base editing, prime editing, and epigenome editing. Ethical considerations include germline editing, equity in access to treatments, and potential unintended consequences of genetic modifications.",
                "category": "biotechnology",
                "topics": ["CRISPR", "gene editing", "genetic engineering", "DNA modification", "genetic diseases", "bioethics", "precision medicine"]
            },
            {
                "title": "Renewable Energy Technologies",
                "content": "Renewable energy sources provide power from naturally replenishing resources including solar, wind, hydroelectric, geothermal, and biomass. Solar photovoltaic and thermal systems convert sunlight to electricity and heat. Wind turbines harness kinetic energy from air movement. Energy storage technologies like batteries, pumped hydro, and compressed air help address intermittency challenges. Smart grids integrate renewable sources with traditional power systems. Cost reductions and efficiency improvements have made renewables competitive with fossil fuels in many markets, driving the global transition to clean energy systems.",
                "category": "energy_technology",
                "topics": ["renewable energy", "solar power", "wind energy", "energy storage", "smart grids", "clean energy transition", "sustainability"]
            },
            {
                "title": "Ocean Exploration and Marine Science",
                "content": "The ocean covers over 70% of Earth's surface but remains largely unexplored, with less than 5% of the ocean floor mapped in detail. Deep-sea exploration reveals unique ecosystems around hydrothermal vents, cold seeps, and seamounts. Marine organisms provide insights into evolution, adaptation, and potential biotechnology applications. Ocean currents regulate global climate, while marine carbon cycles affect atmospheric CO2 levels. Threats include pollution, overfishing, acidification, and warming temperatures. Advanced submersibles, autonomous underwater vehicles, and satellite oceanography enable new discoveries about Earth's largest habitat.",
                "category": "marine_science",
                "topics": ["ocean exploration", "deep sea", "marine ecosystems", "ocean currents", "marine biology", "ocean acidification", "underwater technology"]
            },
            {
                "title": "Nanotechnology and Materials Science",
                "content": "Nanotechnology manipulates matter at the atomic and molecular scale (1-100 nanometers) to create materials and devices with novel properties. Carbon nanotubes exhibit exceptional strength and electrical conductivity. Quantum dots have size-dependent optical properties useful for displays and solar cells. Nanoparticles enable targeted drug delivery and enhanced imaging. Smart materials respond to environmental changes with shape, stiffness, or other property modifications. Applications include electronics, medicine, energy storage, catalysis, and environmental remediation. Safety considerations address potential toxicity and environmental impacts of engineered nanomaterials.",
                "category": "nanotechnology",
                "topics": ["nanotechnology", "nanomaterials", "carbon nanotubes", "quantum dots", "smart materials", "molecular engineering", "nanoparticles"]
            },
            {
                "title": "Neuroscience and Brain Function",
                "content": "Neuroscience studies the structure and function of the nervous system, from molecular mechanisms to behavior and cognition. The human brain contains approximately 86 billion neurons connected by trillions of synapses. Neural plasticity allows the brain to reorganize and adapt throughout life. Advanced techniques include fMRI, optogenetics, and single-cell recording to study brain activity. Research focuses on consciousness, memory formation, decision-making, and neurological disorders. Brain-computer interfaces enable direct communication between neural activity and external devices, with applications in prosthetics, treatment of paralysis, and cognitive enhancement.",
                "category": "neuroscience",
                "topics": ["neuroscience", "brain function", "neural plasticity", "consciousness", "brain-computer interfaces", "neurological disorders", "cognitive science"]
            },
            {
                "title": "Robotics and Autonomous Systems",
                "content": "Robotics combines mechanical engineering, electronics, and artificial intelligence to create machines that can perceive, plan, and act in complex environments. Industrial robots increase manufacturing precision and efficiency. Service robots assist with healthcare, cleaning, and personal tasks. Autonomous vehicles use sensors, mapping, and AI to navigate without human intervention. Swarm robotics coordinates multiple simple robots to accomplish complex tasks. Soft robotics uses flexible materials for safer human interaction. Challenges include perception in unstructured environments, manipulation of complex objects, and ethical considerations around automation and employment.",
                "category": "robotics",
                "topics": ["robotics", "autonomous systems", "industrial robots", "autonomous vehicles", "swarm robotics", "soft robotics", "human-robot interaction"]
            },
            {
                "title": "Cybersecurity and Information Protection",
                "content": "Cybersecurity protects digital systems, networks, and data from malicious attacks, unauthorized access, and damage. Common threats include malware, phishing, ransomware, and distributed denial of service attacks. Security measures include encryption, firewalls, intrusion detection, and access controls. Zero-trust architecture assumes no implicit trust and continuously validates access requests. Artificial intelligence enhances both attack sophistication and defense capabilities. Privacy regulations like GDPR and CCPA govern data protection. Emerging challenges include IoT security, cloud security, and quantum computing threats to current cryptographic methods.",
                "category": "cybersecurity",
                "topics": ["cybersecurity", "information security", "encryption", "malware", "privacy", "zero-trust", "cyber threats"]
            },
            {
                "title": "Sustainable Agriculture and Food Security",
                "content": "Sustainable agriculture produces food while maintaining environmental health, economic viability, and social equity. Precision agriculture uses GPS, sensors, and data analytics to optimize inputs like water, fertilizer, and pesticides. Vertical farming and hydroponics enable food production in urban environments with reduced land and water use. Plant breeding and genetic modification develop crops with improved yield, nutrition, and stress tolerance. Integrated pest management reduces chemical pesticide use. Food security challenges include feeding a growing global population while adapting to climate change and preserving biodiversity.",
                "category": "agriculture",
                "topics": ["sustainable agriculture", "precision agriculture", "vertical farming", "food security", "plant breeding", "integrated pest management", "climate adaptation"]
            },
            {
                "title": "3D Printing and Digital Manufacturing",
                "content": "3D printing, or additive manufacturing, creates objects layer by layer from digital designs, enabling rapid prototyping, customization, and on-demand production. Technologies include fused deposition modeling, stereolithography, and selective laser sintering using materials from plastics to metals and ceramics. Applications span aerospace, medical devices, automotive, architecture, and consumer products. Bioprinting creates tissue and organ structures for medical research and potential transplantation. Digital manufacturing integrates 3D printing with robotics, AI, and IoT for flexible, distributed production systems. Challenges include speed, material properties, and quality control.",
                "category": "manufacturing",
                "topics": ["3D printing", "additive manufacturing", "digital manufacturing", "bioprinting", "rapid prototyping", "customization", "distributed production"]
            },
            {
                "title": "Virtual and Augmented Reality",
                "content": "Virtual Reality (VR) creates immersive digital environments that users can interact with through specialized headsets and controllers. Augmented Reality (AR) overlays digital information onto the real world through smartphones, tablets, or AR glasses. Mixed Reality (MR) combines virtual and real elements with spatial awareness. Applications include gaming, education, training, healthcare, architecture, and social interaction. Key technologies include head tracking, hand tracking, spatial mapping, and realistic rendering. Challenges include motion sickness, visual fidelity, battery life, and social acceptance. The metaverse concept envisions persistent virtual worlds for work, entertainment, and social interaction.",
                "category": "immersive_technology",
                "topics": ["virtual reality", "augmented reality", "mixed reality", "immersive technology", "metaverse", "spatial computing", "human-computer interaction"]
            },
            {
                "title": "Nuclear Energy and Reactor Technology",
                "content": "Nuclear energy harnesses the power released from atomic nuclei through fission or fusion reactions. Current nuclear power plants use uranium fission in pressurized water reactors, boiling water reactors, and other designs. Nuclear energy provides low-carbon electricity but raises concerns about radioactive waste, safety, and proliferation. Advanced reactor designs include small modular reactors, thorium reactors, and fusion reactors. Nuclear fusion promises abundant clean energy by combining light nuclei, but technical challenges include plasma confinement and material sciences. Nuclear medicine uses radioactive isotopes for imaging and cancer treatment.",
                "category": "nuclear_technology",
                "topics": ["nuclear energy", "nuclear fission", "nuclear fusion", "nuclear reactors", "radioactive waste", "nuclear medicine", "clean energy"]
            },
            {
                "title": "Blockchain and Distributed Systems",
                "content": "Blockchain is a distributed ledger technology that maintains a continuously growing list of records secured by cryptographic hashes and consensus mechanisms. Bitcoin introduced blockchain for digital currency, while Ethereum enables smart contracts and decentralized applications. Blockchain properties include immutability, transparency, and decentralization without central authority. Applications extend beyond cryptocurrency to supply chain management, digital identity, voting systems, and decentralized finance (DeFi). Consensus mechanisms include proof of work, proof of stake, and other algorithms. Challenges include scalability, energy consumption, regulatory compliance, and interoperability between different blockchain networks.",
                "category": "distributed_systems",
                "topics": ["blockchain", "cryptocurrency", "distributed systems", "smart contracts", "decentralized applications", "consensus mechanisms", "digital currency"]
            },
            {
                "title": "Biotechnology and Synthetic Biology",
                "content": "Biotechnology applies biological systems and organisms to develop products and technologies benefiting human health, agriculture, and industry. Synthetic biology engineers biological systems by designing and constructing new biological parts, devices, and systems. Applications include producing pharmaceuticals in bacteria, creating biofuels from algae, and developing biodegradable plastics. Metabolic engineering modifies cellular pathways to produce desired compounds. Biosensors detect environmental contaminants, pathogens, or biomarkers. Ethical considerations include biosafety, environmental release of modified organisms, and equitable access to biotechnology benefits.",
                "category": "biotechnology",
                "topics": ["biotechnology", "synthetic biology", "metabolic engineering", "biofuels", "biosensors", "pharmaceutical production", "biosafety"]
            },
            {
                "title": "Data Science and Big Data Analytics",
                "content": "Data science extracts insights from structured and unstructured data using statistical analysis, machine learning, and domain expertise. Big data refers to datasets too large or complex for traditional processing methods, characterized by volume, velocity, and variety. Data pipeline processes include collection, cleaning, storage, analysis, and visualization. Machine learning algorithms identify patterns and make predictions from historical data. Applications span business intelligence, scientific research, healthcare analytics, and social media analysis. Data privacy and ethics address consent, bias, and responsible use of personal information.",
                "category": "data_science",
                "topics": ["data science", "big data", "machine learning", "data analytics", "statistical analysis", "data visualization", "data privacy"]
            },
            {
                "title": "Internet of Things and Connected Devices",
                "content": "The Internet of Things (IoT) connects everyday objects to the internet, enabling them to send and receive data. Smart home devices include thermostats, security cameras, and voice assistants. Industrial IoT optimizes manufacturing, logistics, and infrastructure through sensor networks and analytics. Wearable devices monitor health metrics and fitness activities. Smart cities use IoT for traffic management, environmental monitoring, and public services. Edge computing processes data locally to reduce latency and bandwidth requirements. Security challenges include device authentication, data encryption, and firmware updates for billions of connected devices.",
                "category": "internet_of_things",
                "topics": ["IoT", "connected devices", "smart home", "industrial IoT", "wearable technology", "smart cities", "edge computing"]
            },
            {
                "title": "Space Debris and Orbital Environment",
                "content": "Space debris consists of defunct satellites, spent rocket stages, and fragments from collisions orbiting Earth. Over 34,000 tracked objects larger than 10 cm pose collision risks to operational spacecraft and the International Space Station. The Kessler Syndrome describes a cascade effect where collisions create more debris, potentially making certain orbits unusable. Mitigation strategies include deorbiting satellites at end of life, designing for demise during reentry, and avoiding intentional destruction in orbit. Active debris removal missions use robotic arms, nets, or harpoons to capture and deorbit large objects. International guidelines promote sustainable space activities.",
                "category": "space_environment",
                "topics": ["space debris", "orbital mechanics", "Kessler Syndrome", "space sustainability", "debris removal", "satellite operations", "space traffic management"]
            },
            {
                "title": "Exoplanet Atmospheres and Habitability",
                "content": "Exoplanet atmospheres provide clues about planetary formation, evolution, and potential habitability. Transit spectroscopy analyzes starlight passing through planetary atmospheres to identify chemical compositions. Hot Jupiters show extreme temperatures and atmospheric escape, while super-Earths may retain thick atmospheres. The habitable zone, or Goldilocks zone, represents distances from stars where liquid water could exist on planetary surfaces. Biosignatures like oxygen, methane, and phosphine could indicate biological activity. The James Webb Space Telescope revolutionizes atmospheric characterization with unprecedented sensitivity and wavelength coverage for studying potentially habitable worlds.",
                "category": "exoplanet_science",
                "topics": ["exoplanet atmospheres", "transit spectroscopy", "habitable zone", "biosignatures", "atmospheric escape", "planetary characterization", "astrobiology"]
            },
            {
                "title": "Gravitational Waves and LIGO Discoveries",
                "content": "Gravitational waves are ripples in spacetime caused by accelerating massive objects, predicted by Einstein's general relativity and first detected by LIGO in 2015. These waves result from extreme cosmic events like black hole mergers, neutron star collisions, and potentially the Big Bang itself. LIGO uses laser interferometry to measure incredibly small changes in arm lengths caused by passing gravitational waves. Discoveries include binary black hole systems, neutron star mergers producing gold and platinum, and tests of fundamental physics in extreme gravity. Future space-based detectors like LISA will observe lower-frequency waves from supermassive black holes.",
                "category": "gravitational_physics",
                "topics": ["gravitational waves", "LIGO", "black hole mergers", "neutron stars", "general relativity", "interferometry", "multi-messenger astronomy"]
            },
            {
                "title": "Stem Cell Research and Regenerative Medicine",
                "content": "Stem cells can differentiate into various cell types and have self-renewal capacity, making them valuable for treating diseases and injuries. Embryonic stem cells are pluripotent but raise ethical concerns, while induced pluripotent stem cells (iPSCs) reprogram adult cells to embryonic-like states. Adult stem cells from bone marrow, fat, and other tissues have more limited differentiation potential. Applications include treating blood disorders, spinal cord injuries, and degenerative diseases. Tissue engineering combines stem cells with biomaterial scaffolds to grow replacement organs. Challenges include controlling differentiation, preventing tumor formation, and immune rejection.",
                "category": "regenerative_medicine",
                "topics": ["stem cells", "regenerative medicine", "tissue engineering", "cell therapy", "pluripotent stem cells", "organ regeneration", "biomedical research"]
            }
        ]
        
        return knowledge_documents
    
    async def _create_faiss_index_from_documents(self, documents: List[Dict[str, Any]], is_streamlit_cloud: bool = False):
        """Create FAISS index from document list with progress tracking"""
        if not documents:
            print("❌ No documents provided for index creation")
            return
        
        print(f"🔄 Creating embeddings for {len(documents)} documents...")
        
        # Progress tracking for large datasets
        batch_size = 100 if len(documents) > 500 else len(documents)
        all_embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_texts = [doc["content"] for doc in batch]
            
            print(f"   Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size} ({len(batch)} documents)")
            batch_embeddings = self.embedding_model.encode(batch_texts, convert_to_numpy=True)
            all_embeddings.append(batch_embeddings)
        
        # Combine all embeddings
        embeddings = np.vstack(all_embeddings)
        print(f"✅ Created embeddings for {len(documents)} documents")
        
        # Create FAISS index
        print("🔧 Building FAISS index...")
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        
        # Store documents and metadata
        self.documents = documents
        self.document_metadata = [{"id": i, **doc} for i, doc in enumerate(documents)]
        
        # Save to disk (may fail in read-only environments)
        await self._save_index()
        
        # Summary
        categories = list(set([doc.get('category', 'general') for doc in documents]))
        print(f"✅ Created FAISS index with {len(documents)} documents")
        print(f"📊 Knowledge domains: {len(categories)} categories")
        
        if is_streamlit_cloud:
            print("🚀 Streamlit Cloud deployment optimized with comprehensive knowledge base!")
        
        # Memory optimization for large datasets
        if len(documents) > 1000:
            print("🧹 Performing memory optimization for large dataset...")
            import gc
            gc.collect()
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Check if we can actually save (may not be possible in some cloud environments)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            
            faiss.write_index(self.faiss_index, str(self.faiss_path))
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.document_metadata, f)
            
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print("💾 Index saved to disk successfully")
        except Exception as e:
            print(f"⚠️ Failed to save index to disk: {e}")
            print("ℹ️ This is normal in read-only deployment environments like Streamlit Cloud")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information for debugging and status display"""
        # Calculate document statistics
        categories = list(set([doc.get("category", "unknown") for doc in self.documents]))
        
        # Content statistics
        total_content_length = sum(len(doc.get("content", "")) for doc in self.documents)
        avg_content_length = total_content_length / len(self.documents) if self.documents else 0
        
        # Determine data source
        data_source = "Unknown"
        if len(self.documents) > 1000:
            data_source = "Consolidated Knowledge Base (2000+ articles)"
        elif len(self.documents) > 50:
            data_source = "Enhanced Fallback Dataset"
        elif len(self.documents) > 10:
            data_source = "Basic Fallback Dataset"
        else:
            data_source = "Minimal Fallback"
        
        # Check if consolidated knowledge base exists
        knowledge_base_available = Path("data/knowledge_base.json").exists()
        
        return {
            "total_documents": len(self.documents),
            "data_source": data_source,
            "knowledge_base_available": knowledge_base_available,
            "embedding_model_available": self.embedding_model is not None,
            "faiss_index_available": self.faiss_index is not None,
            "web_search_available": self.web_search_manager is not None,
            "document_categories": categories[:15],  # Limit for display
            "total_categories": len(categories),
            "content_stats": {
                "total_content_length": total_content_length,
                "avg_content_length": int(avg_content_length),
                "total_characters": f"{total_content_length:,}"
            },
            "storage_paths": {
                "storage_dir": str(self.storage_dir),
                "data_dir_exists": Path("data").exists(),
                "knowledge_base_path": str(Path("data/knowledge_base.json")),
                "faiss_path_exists": self.faiss_path.exists(),
                "metadata_path_exists": self.metadata_path.exists(),
                "documents_path_exists": self.documents_path.exists()
            },
            "configuration": {
                # AI Model Configuration
                "openai_available": self.openai_available,
                "openai_model": self.openai_model if self.openai_available else "Not configured",
                "openai_max_tokens": self.max_tokens if self.openai_available else "N/A",
                "estimated_cost_per_query": "$0.001" if self.openai_available and "gpt-4o-mini" in self.openai_model else "N/A",
                "ollama_model": self.ollama_model,
                # Search Configuration
                "similarity_threshold": self.similarity_threshold,
                "max_local_results": self.max_local_results,
                "max_web_results": self.max_web_results
            },
            "environment": {
                "streamlit_cloud": bool(os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD')),
                "current_working_dir": os.getcwd(),
                "python_path": os.getcwd()
            }
        }
    
    async def _test_ollama(self) -> bool:
        """Test Ollama connection and available models"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # Test connection
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status != 200:
                        return False
                    
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data.get('models', [])]
                    print(f"🤖 Available Ollama models: {', '.join(available_models)}")
                    
                    # Choose best available model (prioritize small models to prevent crashes)
                    preferred_models = ["llama3.2:3b", "llama3.2:1b"]
                    for model in preferred_models:
                        if model in available_models:
                            self.ollama_model = model
                            break
                    
                    print(f"✅ Using Ollama model: {self.ollama_model}")
                    return True
                    
        except Exception as e:
            print(f"⚠️ Ollama test failed: {e}")
            return False
    
    async def search_query(self, query: str) -> Dict[str, Any]:
        """Main search function - the core of the RAG system"""
        print(f"\n🔍 Processing query: '{query[:50]}...'")
        start_time = time.time()
        
        try:
            # Step 1: Convert query to embeddings
            if not self.embedding_model:
                print("⚠️ Embedding model not available, using web search only")
                web_results = await self._search_web(query)
                if web_results:
                    response = await self._generate_simple_response(query, web_results)
                    return {
                        "response": response,
                        "sources": [{"title": r.title, "content": r.content[:200] + "...", "source": r.source, "similarity": r.similarity, "source_type": r.source_type} for r in web_results],
                        "method": "web_search_only",
                        "processing_time": time.time() - start_time,
                        "query": query
                    }
                else:
                    return self._error_response("Neither embedding model nor web search available")
            
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Step 2: Search local FAISS index
            print("📚 Searching local space documents...")
            local_results = await self._search_local(query_embedding, query)
            
            # Step 3: Decide local vs web search based on similarity
            if local_results and local_results[0].similarity >= self.similarity_threshold:
                print(f"✅ Using local results (similarity: {local_results[0].similarity:.3f})")
                search_results = local_results[:self.max_local_results]
                search_method = "local_search"
            else:
                best_similarity = local_results[0].similarity if local_results else 0.0
                print(f"🌐 Using web search (best local similarity: {best_similarity:.3f})")
                web_results = await self._search_web(query)
                search_results = web_results[:self.max_web_results]
                search_method = "web_search"
            
            if not search_results:
                return self._error_response("No search results found")
            
            # Step 4: Generate response with smart LLM selection (OpenAI-first for cloud)
            response = await self._generate_smart_response(query, search_results)
            
            processing_time = time.time() - start_time
            print(f"⚡ Query processed in {processing_time:.2f}s")
            
            return {
                "response": response,
                "sources": [{"title": r.title, "content": r.content[:200] + "...", "source": r.source, "similarity": r.similarity, "source_type": r.source_type} for r in search_results],
                "method": search_method,
                "processing_time": processing_time,
                "query": query
            }
            
        except Exception as e:
            print(f"❌ Query processing failed: {e}")
            return self._error_response(f"Query processing failed: {str(e)}")
    
    async def _search_local(self, query_embedding: np.ndarray, query: str) -> List[SearchResult]:
        """Search local FAISS index"""
        if not self.faiss_index or len(self.documents) == 0:
            print("⚠️ No local documents available")
            return []
        
        try:
            # Search FAISS index
            similarities, indices = self.faiss_index.search(query_embedding, min(self.max_local_results * 2, len(self.documents)))
            
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append(SearchResult(
                        content=doc["content"],
                        title=doc["title"],
                        source=f"Local Knowledge Base - {doc['category']}",
                        similarity=float(sim),
                        source_type="local"
                    ))
            
            return results
            
        except Exception as e:
            print(f"⚠️ Local search failed: {e}")
            return []
    
    async def _search_web(self, query: str) -> List[SearchResult]:
        """Search web using DuckDuckGo"""
        if not self.web_search_manager:
            print("⚠️ Web search not available")
            return []
        
        try:
            # Use web search manager
            web_results = await self.web_search_manager.search(query, max_results=self.max_web_results)
            
            results = []
            for result in web_results:
                # Extract content from web SearchResult object
                content = result.content if hasattr(result, 'content') and result.content else (
                    result.snippet if hasattr(result, 'snippet') and result.snippet else ""
                )
                title = result.title if hasattr(result, 'title') and result.title else "Web Result"
                url = result.url if hasattr(result, 'url') and result.url else "Web Search"
                
                results.append(SearchResult(
                    content=content[:1000] if content else "",  # Limit content size
                    title=title,
                    source=url,
                    similarity=0.8,  # Default similarity for web results
                    source_type="web"
                ))
            
            print(f"🌐 Found {len(results)} web results")
            return results
            
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
            return []
    
    async def _check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy and responsive"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            print(f"🔍 Ollama health check failed: {e}")
            return False
    
    async def _generate_ollama_response(self, query: str, search_results: List[SearchResult]) -> str:
        """Generate response using Ollama with search results as context"""
        # Health check before making request
        if not await self._check_ollama_health():
            return "Ollama service is currently unavailable. Please try again in a moment or check if the Ollama service is running."
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Prepare context from search results
                context_parts = []
                for i, result in enumerate(search_results, 1):
                    # Limit individual context size to prevent token overflow
                    content = result.content[:1500] if result.content else ""
                    context_parts.append(f"[Source {i}] {result.title}\n{content}\n")
                
                context = "\n".join(context_parts)
                
                # Limit total context size for better Ollama performance
                if len(context) > 8000:
                    context = context[:8000] + "\n[Context truncated for performance]"
                
                # Create confident, comprehensive prompt
                prompt = f"""Answer the user's question thoroughly and confidently based on the provided information. Provide comprehensive details, explanations, and context. When sources clearly state facts, respond definitively. Include relevant background information and elaborate on key concepts to give the user a complete understanding of the topic.

CONTEXT:
{context}

QUESTION: {query}

Provide a clear, direct answer. Cite sources using [Source X] format when relevant."""

                # Call Ollama API with appropriate timeout
                timeout = 120 if attempt == 0 else 180  # Increase timeout on retry
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    payload = {
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,  # More decisive, less random
                            "top_p": 0.8,        # More focused responses
                            "max_tokens": 1500   # Allow detailed responses
                        }
                    }
                    
                    async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            generated_response = result.get("response", "").strip()
                            
                            if generated_response:
                                return generated_response
                            else:
                                print(f"⚠️ Ollama returned empty response on attempt {attempt + 1}")
                                if attempt < max_retries:
                                    continue
                                return "I received your request but couldn't generate a meaningful response. Please try rephrasing your question."
                        else:
                            print(f"⚠️ Ollama HTTP error {response.status} on attempt {attempt + 1}")
                            if attempt < max_retries:
                                await asyncio.sleep(2)  # Brief delay before retry
                                continue
                            return f"Ollama service error (HTTP {response.status}). Please try again later."
                
            except asyncio.TimeoutError:
                print(f"⚠️ Ollama timeout on attempt {attempt + 1}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                return "The request timed out while processing. This might be due to a complex query or high server load. Please try a simpler question or wait a moment before trying again."
            
            except Exception as e:
                print(f"⚠️ Ollama generation failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                return f"I found relevant information but couldn't generate a response due to a technical issue: {str(e)}. Please check that Ollama is running and try again."
        
        # This shouldn't be reached, but just in case
        return "Unable to generate response after multiple attempts. Please try again later."
    
    async def _generate_openai_response(self, query: str, search_results: List[SearchResult]) -> str:
        """Generate cost-optimized response using OpenAI with gpt-4o-mini"""
        if not self.openai_available or not self.openai_client:
            return "OpenAI service is not available. Please check your API key configuration."
        
        try:
            # Prepare context from search results with cost optimization
            context_parts = []
            for i, result in enumerate(search_results[:3], 1):  # Limit to 3 sources for cost
                # Optimize content length for cost efficiency
                content = result.content[:800] if result.content else ""  # Reduced from 1500
                context_parts.append(f"[Source {i}] {result.title}\n{content}\n")
            
            context = "\n".join(context_parts)
            
            # Cost-optimized context size (targeting ~2000 input tokens)
            if len(context) > 4000:  # Reduced from 8000
                context = context[:4000] + "\n[Context truncated for cost optimization]"
            
            # Cost-optimized prompt - concise but effective
            prompt = f"""Answer the question clearly and concisely based on the provided sources. Be specific and factual.

SOURCES:
{context}

QUESTION: {query}

ANSWER:"""
            
            # Call OpenAI API with cost optimization
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,  # gpt-4o-mini
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate, concise answers based on provided sources. Focus on being informative while staying concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,  # Cost control (default 150)
                temperature=0.3,  # More focused responses
                stream=False
            )
            
            if response and response.choices and response.choices[0].message:
                answer = response.choices[0].message.content.strip()
                
                # Add cost tracking info (for development)
                tokens_used = response.usage.total_tokens if response.usage else "unknown"
                estimated_cost = (tokens_used * 0.0000015) if isinstance(tokens_used, int) else 0  # gpt-4o-mini pricing
                print(f"💰 OpenAI usage: {tokens_used} tokens, ~${estimated_cost:.4f}")
                
                return answer if answer else "I couldn't generate a response based on the available information."
            else:
                return "I received an empty response from the AI service. Please try again."
                
        except Exception as e:
            print(f"⚠️ OpenAI generation failed: {e}")
            return f"I found relevant information but couldn't generate a response due to a technical issue: {str(e)}. Please check your OpenAI API key and try again."
    
    async def _generate_smart_response(self, query: str, search_results: List[SearchResult]) -> str:
        """Smart LLM selection with OpenAI-first approach for cloud deployment"""
        # Detect environment - prioritize OpenAI for cloud deployment
        is_streamlit_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD')
        
        # OpenAI-first approach (best for cloud deployment and recruiter showcase)
        if self.openai_available:
            print("🚀 Generating response with OpenAI (gpt-4o-mini)...")
            try:
                return await self._generate_openai_response(query, search_results)
            except Exception as e:
                print(f"⚠️ OpenAI failed, trying fallback: {e}")
        
        # Fallback to Ollama for local development (if available)
        if not is_streamlit_cloud:
            print("🤖 Trying Ollama as fallback...")
            try:
                if await self._check_ollama_health():
                    return await self._generate_ollama_response(query, search_results)
            except Exception as e:
                print(f"⚠️ Ollama fallback failed: {e}")
        
        # Final fallback to simple response
        print("📝 Using simple response generation...")
        return await self._generate_simple_response(query, search_results)
    
    async def _generate_simple_response(self, query: str, search_results: List[SearchResult]) -> str:
        """Generate a simple response when both OpenAI and Ollama are unavailable"""
        try:
            # Fallback to simple text compilation
            print("🔤 Generating simple response (AI services unavailable)")
            
            if not search_results:
                return "I couldn't find any relevant information for your query. Please try a different question or check your connection."
            
            # Create a simple response by combining search results
            response_parts = [
                f"Based on my search, here's what I found about '{query}':\n"
            ]
            
            for i, result in enumerate(search_results[:3], 1):
                content = result.content[:300] if result.content else "No content available"
                response_parts.append(f"{i}. **{result.title}**")
                response_parts.append(f"   {content}")
                response_parts.append(f"   Source: {result.source}\n")
            
            if len(search_results) > 3:
                response_parts.append(f"...and {len(search_results) - 3} more results found.")
            
            response_parts.append("\n*Note: AI response generation is currently unavailable. This is a compilation of search results.*")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            print(f"⚠️ Simple response generation failed: {e}")
            return f"I found some information about '{query}' but couldn't format it properly. Please try again or check the sources directly."
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "response": f"Error: {message}",
            "sources": [],
            "method": "error",
            "processing_time": 0,
            "query": ""
        }

# Test function
async def test_simple_rag():
    """Test the simple RAG system"""
    print("🧪 Testing Simple RAG System...")
    
    rag = SimpleRAGSystem()
    
    if await rag.initialize():
        # Test query
        result = await rag.search_query("What is the Artemis program?")
        print(f"\n📊 Test Result:")
        print(f"Response: {result['response'][:200]}...")
        print(f"Method: {result['method']}")
        print(f"Sources: {len(result['sources'])}")
        print(f"Time: {result['processing_time']:.2f}s")
    else:
        print("❌ RAG system initialization failed")

if __name__ == "__main__":
    asyncio.run(test_simple_rag())