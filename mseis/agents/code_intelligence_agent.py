# agents/code_intelligence_agent.py
import ast
import os
import git
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import asyncio
import httpx
from datetime import datetime
import tempfile
import shutil

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from agents.base_agent import BaseAgent, QueryContext
from storage.neo4j_manager import Neo4jManager
from storage.cache_manager import CacheManager
from core.config import config
from utils.monitoring import monitor_performance
from utils.logging_config import get_logger

logger = get_logger(__name__)

class CodeIntelligenceAgent(BaseAgent):
    """Agent for analyzing GitHub repositories and providing architectural insights"""
    
    def __init__(self):
        super().__init__(
            name="CodeIntelligenceAgent",
            config=config.get("agents.code_intelligence", {})
        )
        self.neo4j_manager = None
        self.cache_manager = None
        self.llm = None
        self.text_splitter = None
        self.github_client = None
        
    async def _setup(self):
        """Initialize code analysis components"""
        # Initialize storage
        self.neo4j_manager = Neo4jManager()
        await self.neo4j_manager.initialize()
        
        self.cache_manager = CacheManager()
        await self.cache_manager.initialize()
        
        # Initialize LLM for code analysis
        self.llm = ChatOpenAI(
            model=config.api.openai_model,
            temperature=0.1,
            openai_api_key=config.api.openai_api_key
        )
        
        # Initialize text splitter for large codebases
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\nclass ", "\n\ndef ", "\n\n", "\n", " ", ""]
        )
        
        # Initialize GitHub client
        self.github_client = httpx.AsyncClient(
            headers={"Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"},
            timeout=30.0
        )
        
    async def _process_query(self, context: QueryContext) -> Tuple[str, List[Dict], float]:
        """Process a code analysis query"""
        query = context.original_query
        
        # Extract GitHub URL or repository name from query
        repo_info = self._extract_repo_info(query)
        if not repo_info:
            return "Please provide a valid GitHub repository URL or owner/repo name.", [], 0.0
            
        # Check cache first
        cache_key = f"code_analysis_{repo_info['owner']}_{repo_info['repo']}"
        cached_result = await self.cache_manager.get(cache_key, namespace="code_analysis")
        
        if cached_result and not context.metadata.get("force_refresh", False):
            return cached_result["content"], cached_result["sources"], cached_result["confidence"]
            
        try:
            # Clone repository
            repo_path = await self._clone_repository(repo_info)
            
            # Analyze repository structure
            analysis_results = await self._analyze_repository(repo_path, repo_info)
            
            # Generate insights using LLM
            insights = await self._generate_insights(analysis_results, context.user_expertise_level)
            
            # Store analysis in Neo4j for future reference
            await self._store_analysis_in_graph(repo_info, analysis_results)
            
            # Cache results
            result = {
                "content": insights["summary"],
                "sources": analysis_results["sources"],
                "confidence": insights["confidence"]
            }
            await self.cache_manager.set(cache_key, result, namespace="code_analysis", ttl=86400)
            
            # Cleanup
            shutil.rmtree(repo_path, ignore_errors=True)
            
            return result["content"], result["sources"], result["confidence"]
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            return f"Error analyzing repository: {str(e)}", [], 0.0
            
    def _extract_repo_info(self, query: str) -> Optional[Dict[str, str]]:
        """Extract repository information from query"""
        import re
        
        # GitHub URL pattern
        github_url_pattern = r'github\.com/([^/]+)/([^/\s]+)'
        match = re.search(github_url_pattern, query)
        
        if match:
            return {"owner": match.group(1), "repo": match.group(2).rstrip('.git')}
            
        # Owner/repo pattern
        owner_repo_pattern = r'([a-zA-Z0-9\-]+)/([a-zA-Z0-9\-_.]+)'
        match = re.search(owner_repo_pattern, query)
        
        if match and '/' in query and not '.' in match.group(0):
            return {"owner": match.group(1), "repo": match.group(2)}
            
        return None
        
    async def _clone_repository(self, repo_info: Dict[str, str]) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp()
        repo_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}.git"
        
        try:
            # Clone with depth=1 for faster cloning
            repo = git.Repo.clone_from(repo_url, temp_dir, depth=1)
            logger.info(f"Successfully cloned {repo_url}")
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
            
    @monitor_performance("code_intelligence", "analyze_repository")
    async def _analyze_repository(self, repo_path: str, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Comprehensive repository analysis"""
        analysis = {
            "repo_info": repo_info,
            "structure": {},
            "dependencies": {},
            "code_metrics": {},
            "architecture_patterns": [],
            "sources": []
        }
        
        # Analyze directory structure
        analysis["structure"] = self._analyze_directory_structure(repo_path)
        
        # Analyze dependencies
        analysis["dependencies"] = await self._analyze_dependencies(repo_path)
        
        # Analyze code files
        analysis["code_metrics"] = await self._analyze_code_metrics(repo_path)
        
        # Detect architecture patterns
        analysis["architecture_patterns"] = self._detect_architecture_patterns(repo_path, analysis["structure"])
        
        # Add sources for transparency
        analysis["sources"] = [
            {
                "type": "repository_analysis",
                "repo": f"{repo_info['owner']}/{repo_info['repo']}",
                "analyzed_files": analysis["code_metrics"].get("total_files", 0),
                "analysis_timestamp": datetime.now().isoformat()
            }
        ]
        
        return analysis
        
    def _analyze_directory_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository directory structure"""
        structure = {
            "total_files": 0,
            "total_directories": 0,
            "file_types": {},
            "main_directories": [],
            "config_files": [],
            "documentation": []
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            structure["total_directories"] += len(dirs)
            structure["total_files"] += len(files)
            
            # Track main directories
            if root == repo_path:
                structure["main_directories"] = dirs.copy()
                
            for file in files:
                if file.startswith('.'):
                    continue
                    
                # File type analysis
                ext = Path(file).suffix.lower()
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Configuration files
                if file in ['package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml', 'config.yaml', 'setup.py']:
                    structure["config_files"].append(file)
                    
                # Documentation
                if file.lower().startswith('readme') or ext in ['.md', '.rst', '.txt']:
                    structure["documentation"].append(file)
                    
        return structure
        
    async def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {
            "python": {},
            "javascript": {},
            "docker": {},
            "other": {}
        }
        
        # Python dependencies
        requirements_file = Path(repo_path) / "requirements.txt"
        if requirements_file.exists():
            dependencies["python"] = self._parse_requirements(requirements_file)
            
        # Node.js dependencies
        package_json = Path(repo_path) / "package.json"
        if package_json.exists():
            dependencies["javascript"] = self._parse_package_json(package_json)
            
        # Docker
        dockerfile = Path(repo_path) / "Dockerfile"
        if dockerfile.exists():
            dependencies["docker"] = self._parse_dockerfile(dockerfile)
            
        return dependencies
        
    def _parse_requirements(self, requirements_file: Path) -> Dict[str, List[str]]:
        """Parse Python requirements.txt"""
        try:
            with open(requirements_file, 'r') as f:
                lines = f.readlines()
                
            packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)
                    
            return {"packages": packages, "count": len(packages)}
        except Exception:
            return {"packages": [], "count": 0}
            
    def _parse_package_json(self, package_json: Path) -> Dict[str, Any]:
        """Parse Node.js package.json"""
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                
            return {
                "dependencies": list(data.get("dependencies", {}).keys()),
                "dev_dependencies": list(data.get("devDependencies", {}).keys()),
                "scripts": list(data.get("scripts", {}).keys())
            }
        except Exception:
            return {"dependencies": [], "dev_dependencies": [], "scripts": []}
            
    def _parse_dockerfile(self, dockerfile: Path) -> Dict[str, Any]:
        """Parse Dockerfile for base images and commands"""
        try:
            with open(dockerfile, 'r') as f:
                lines = f.readlines()
                
            base_images = []
            commands = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('FROM'):
                    base_images.append(line.split()[1])
                elif line.startswith('RUN'):
                    commands.append(line)
                    
            return {"base_images": base_images, "commands": len(commands)}
        except Exception:
            return {"base_images": [], "commands": 0}
            
    async def _analyze_code_metrics(self, repo_path: str) -> Dict[str, Any]:
        """Analyze code metrics using AST parsing"""
        metrics = {
            "total_files": 0,
            "python_files": 0,
            "classes": 0,
            "functions": 0,
            "lines_of_code": 0,
            "complexity_score": 0,
            "main_technologies": []
        }
        
        python_files = list(Path(repo_path).rglob("*.py"))
        metrics["python_files"] = len(python_files)
        
        for py_file in python_files[:50]:  # Limit analysis to prevent timeout
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                
                # Count classes and functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        metrics["classes"] += 1
                    elif isinstance(node, ast.FunctionDef):
                        metrics["functions"] += 1
                        
                metrics["lines_of_code"] += len(content.splitlines())
                
            except Exception:
                continue
                
        # Detect main technologies
        metrics["main_technologies"] = self._detect_technologies(repo_path)
        
        return metrics
        
    def _detect_technologies(self, repo_path: str) -> List[str]:
        """Detect main technologies used in the repository"""
        technologies = []
        
        # Check for common framework files
        tech_indicators = {
            "React": ["package.json", "src/App.js", "public/index.html"],
            "Django": ["manage.py", "settings.py"],
            "Flask": ["app.py", "wsgi.py"],
            "FastAPI": ["main.py", "uvicorn"],
            "Docker": ["Dockerfile", "docker-compose.yml"],
            "Kubernetes": ["deployment.yaml", "service.yaml"],
            "TensorFlow": ["requirements.txt"],  # Check content for tensorflow
            "PyTorch": ["requirements.txt"],     # Check content for torch
            "Next.js": ["next.config.js", "pages/"],
            "Vue.js": ["vue.config.js", "src/main.js"]
        }
        
        for tech, indicators in tech_indicators.items():
            for indicator in indicators:
                if Path(repo_path, indicator).exists():
                    technologies.append(tech)
                    break
                    
        return technologies
        
    def _detect_architecture_patterns(self, repo_path: str, structure: Dict[str, Any]) -> List[str]:
        """Detect common architecture patterns"""
        patterns = []
        main_dirs = structure.get("main_directories", [])
        
        # MVC Pattern
        if any(d in main_dirs for d in ["models", "views", "controllers"]):
            patterns.append("MVC (Model-View-Controller)")
            
        # Microservices
        if "services" in main_dirs or "microservices" in main_dirs:
            patterns.append("Microservices Architecture")
            
        # Clean Architecture
        if any(d in main_dirs for d in ["domain", "infrastructure", "application"]):
            patterns.append("Clean Architecture")
            
        # Layered Architecture
        if any(d in main_dirs for d in ["api", "business", "data", "presentation"]):
            patterns.append("Layered Architecture")
            
        # Component-based (React/Vue)
        if "components" in main_dirs:
            patterns.append("Component-Based Architecture")
            
        # Repository Pattern
        if "repositories" in main_dirs or "repo" in main_dirs:
            patterns.append("Repository Pattern")
            
        return patterns
        
    async def _generate_insights(self, analysis: Dict[str, Any], expertise_level: str) -> Dict[str, Any]:
        """Generate architectural insights using LLM"""
        
        # Create a comprehensive analysis summary
        analysis_text = f"""
Repository Analysis for {analysis['repo_info']['owner']}/{analysis['repo_info']['repo']}:

STRUCTURE:
- Total Files: {analysis['structure']['total_files']}
- Main Directories: {', '.join(analysis['structure']['main_directories'])}
- File Types: {', '.join([f"{ext}({count})" for ext, count in analysis['structure']['file_types'].items()])}

CODE METRICS:
- Python Files: {analysis['code_metrics']['python_files']}
- Classes: {analysis['code_metrics']['classes']}
- Functions: {analysis['code_metrics']['functions']}
- Lines of Code: {analysis['code_metrics']['lines_of_code']}

TECHNOLOGIES:
{', '.join(analysis['code_metrics']['main_technologies'])}

ARCHITECTURE PATTERNS:
{', '.join(analysis['architecture_patterns']) if analysis['architecture_patterns'] else 'No clear patterns detected'}

DEPENDENCIES:
- Python Packages: {analysis['dependencies']['python'].get('count', 0)}
- JavaScript Dependencies: {len(analysis['dependencies']['javascript'].get('dependencies', []))}
"""
        
        # Generate expertise-appropriate insights
        expertise_prompts = {
            "student": "Explain in simple terms suitable for a computer science student",
            "general": "Provide a balanced technical analysis accessible to developers",
            "expert": "Give detailed technical insights for senior engineers and architects"
        }
        
        prompt = f"""
{expertise_prompts.get(expertise_level, expertise_prompts['general'])}.

Analyze this repository and provide:
1. Overall architecture assessment
2. Code quality observations
3. Technology choices evaluation
4. Potential improvements
5. Scalability considerations

{analysis_text}

Provide a structured analysis that would be valuable for code review or technical assessment.
"""
        
        try:
            messages = [
                SystemMessage(content="You are a senior software architect providing code analysis."),
                HumanMessage(content=prompt)
            ]
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.llm.invoke,
                messages
            )
            
            return {
                "summary": response.content,
                "confidence": 0.9,
                "analysis_depth": "comprehensive"
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                "summary": f"Technical analysis completed. Found {analysis['code_metrics']['classes']} classes and {analysis['code_metrics']['functions']} functions across {analysis['code_metrics']['python_files']} Python files. Architecture patterns detected: {', '.join(analysis['architecture_patterns']) if analysis['architecture_patterns'] else 'Standard patterns'}.",
                "confidence": 0.6,
                "analysis_depth": "basic"
            }
            
    async def _store_analysis_in_graph(self, repo_info: Dict[str, str], analysis: Dict[str, Any]):
        """Store repository analysis in Neo4j for future reference"""
        try:
            # Create repository node
            repo_data = {
                "name": f"{repo_info['owner']}/{repo_info['repo']}",
                "owner": repo_info['owner'],
                "repo": repo_info['repo'],
                "analyzed_at": datetime.now().isoformat(),
                "total_files": analysis['structure']['total_files'],
                "classes": analysis['code_metrics']['classes'],
                "functions": analysis['code_metrics']['functions'],
                "lines_of_code": analysis['code_metrics']['lines_of_code'],
                "technologies": analysis['code_metrics']['main_technologies'],
                "architecture_patterns": analysis['architecture_patterns']
            }
            
            # Store in Neo4j
            await self.neo4j_manager.create_node("Repository", repo_data)
            
        except Exception as e:
            logger.error(f"Error storing analysis in graph: {str(e)}") 