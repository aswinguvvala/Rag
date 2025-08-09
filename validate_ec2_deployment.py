#!/usr/bin/env python3
"""
EC2 Deployment Validation Script for IntelliSearch
Comprehensive testing of production deployment
"""

import asyncio
import sys
import os
import json
import time
import requests
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add the project directory to the path
sys.path.insert(0, '/home/ubuntu/intellisearch')

try:
    from simple_rag_system import SimpleRAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ RAG system not available for import")

class EC2DeploymentValidator:
    """Comprehensive EC2 deployment validation"""
    
    def __init__(self):
        self.app_dir = Path("/home/ubuntu/intellisearch")
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_status": "unknown",
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO") -> None:
        """Log with timestamp and level"""
        timestamp = time.strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[0;34m",      # Blue
            "SUCCESS": "\033[0;32m",    # Green  
            "WARNING": "\033[1;33m",    # Yellow
            "ERROR": "\033[0;31m",      # Red
            "RESET": "\033[0m"          # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def run_command(self, command: str) -> Tuple[bool, str]:
        """Run shell command and return success status and output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def test_system_requirements(self) -> Dict[str, Any]:
        """Test basic system requirements"""
        self.log("🔍 Testing system requirements...")
        
        results = {
            "python_version": {"status": False, "details": ""},
            "disk_space": {"status": False, "details": ""},
            "memory": {"status": False, "details": ""},
            "network": {"status": False, "details": ""},
            "ollama_service": {"status": False, "details": ""}
        }
        
        # Python version
        try:
            python_version = sys.version
            if sys.version_info >= (3, 8):
                results["python_version"] = {
                    "status": True, 
                    "details": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                }
            else:
                results["python_version"] = {
                    "status": False, 
                    "details": f"Python {sys.version_info.major}.{sys.version_info.minor} (needs >= 3.8)"
                }
        except Exception as e:
            results["python_version"] = {"status": False, "details": str(e)}
        
        # Disk space
        try:
            disk = psutil.disk_usage(str(self.app_dir))
            free_gb = disk.free / (1024**3)
            results["disk_space"] = {
                "status": free_gb > 1.0,
                "details": f"{free_gb:.1f}GB free"
            }
        except Exception as e:
            results["disk_space"] = {"status": False, "details": str(e)}
        
        # Memory
        try:
            mem = psutil.virtual_memory()
            available_mb = mem.available / (1024**2)
            results["memory"] = {
                "status": available_mb > 200,
                "details": f"{available_mb:.0f}MB available"
            }
        except Exception as e:
            results["memory"] = {"status": False, "details": str(e)}
        
        # Network connectivity
        try:
            response = requests.get("https://httpbin.org/ip", timeout=10)
            public_ip = response.json().get("origin", "unknown")
            results["network"] = {
                "status": response.status_code == 200,
                "details": f"Public IP: {public_ip}"
            }
        except Exception as e:
            results["network"] = {"status": False, "details": str(e)}
        
        # Ollama service
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                results["ollama_service"] = {
                    "status": True,
                    "details": f"Running with models: {', '.join(model_names)}"
                }
            else:
                results["ollama_service"] = {
                    "status": False, 
                    "details": f"HTTP {response.status_code}"
                }
        except Exception as e:
            results["ollama_service"] = {"status": False, "details": str(e)}
        
        return results
    
    def test_application_files(self) -> Dict[str, Any]:
        """Test application file structure and dependencies"""
        self.log("📁 Testing application files...")
        
        results = {
            "app_structure": {"status": False, "details": ""},
            "python_dependencies": {"status": False, "details": ""},
            "environment_config": {"status": False, "details": ""},
            "storage_directories": {"status": False, "details": ""}
        }
        
        # Check essential files
        essential_files = [
            "app.py", "simple_rag_system.py", "requirements.txt", 
            "web_search_manager.py", ".env"
        ]
        
        missing_files = []
        for file in essential_files:
            if not (self.app_dir / file).exists():
                missing_files.append(file)
        
        results["app_structure"] = {
            "status": len(missing_files) == 0,
            "details": f"Missing files: {missing_files}" if missing_files else "All essential files present"
        }
        
        # Check Python dependencies
        try:
            success, output = self.run_command("source /home/ubuntu/intellisearch/venv/bin/activate && pip check")
            results["python_dependencies"] = {
                "status": success,
                "details": "All dependencies satisfied" if success else output
            }
        except Exception as e:
            results["python_dependencies"] = {"status": False, "details": str(e)}
        
        # Environment configuration
        env_file = self.app_dir / ".env"
        if env_file.exists():
            try:
                with open(env_file) as f:
                    env_content = f.read()
                has_openai = "OPENAI_API_KEY" in env_content and "sk-" in env_content  
                results["environment_config"] = {
                    "status": True,
                    "details": f"Environment configured (OpenAI: {'✅' if has_openai else '❌'})"
                }
            except Exception as e:
                results["environment_config"] = {"status": False, "details": str(e)}
        else:
            results["environment_config"] = {"status": False, "details": "No .env file found"}
        
        # Storage directories
        storage_dirs = ["storage", "logs"]
        created_dirs = []
        for dir_name in storage_dirs:
            dir_path = self.app_dir / dir_name
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_name)
                except Exception:
                    pass
        
        results["storage_directories"] = {
            "status": all((self.app_dir / d).exists() for d in storage_dirs),
            "details": f"Created: {created_dirs}" if created_dirs else "All directories exist"
        }
        
        return results
    
    async def test_rag_system(self) -> Dict[str, Any]:
        """Test RAG system functionality"""
        self.log("🧠 Testing RAG system...")
        
        results = {
            "initialization": {"status": False, "details": ""},
            "knowledge_base": {"status": False, "details": ""},
            "query_processing": {"status": False, "details": ""},
            "response_generation": {"status": False, "details": ""}
        }
        
        if not RAG_AVAILABLE:
            error_msg = "RAG system not available for import"
            for key in results:
                results[key] = {"status": False, "details": error_msg}
            return results
        
        try:
            # Initialize RAG system
            rag = SimpleRAGSystem()
            init_success = await rag.initialize()
            
            results["initialization"] = {
                "status": init_success,
                "details": "RAG system initialized successfully" if init_success else "Initialization failed"
            }
            
            if init_success:
                # Check knowledge base
                doc_count = len(rag.documents) if hasattr(rag, 'documents') else 0
                results["knowledge_base"] = {
                    "status": doc_count > 0,
                    "details": f"{doc_count} documents loaded"
                }
                
                # Test query processing
                test_query = "What is artificial intelligence?"
                try:
                    start_time = time.time()
                    result = await rag.search_query(test_query)
                    processing_time = time.time() - start_time
                    
                    if result and result.get('response'):
                        results["query_processing"] = {
                            "status": True,
                            "details": f"Query processed in {processing_time:.2f}s"
                        }
                        
                        response_len = len(result['response'])
                        method = result.get('method', 'unknown')
                        results["response_generation"] = {
                            "status": response_len > 50,
                            "details": f"{response_len} chars via {method}"
                        }
                    else:
                        results["query_processing"] = {"status": False, "details": "No response generated"}
                        results["response_generation"] = {"status": False, "details": "Empty response"}
                        
                except Exception as e:
                    results["query_processing"] = {"status": False, "details": str(e)}
                    results["response_generation"] = {"status": False, "details": "Query processing failed"}
            
        except Exception as e:
            error_msg = f"RAG system error: {str(e)}"
            for key in results:
                if results[key]["details"] == "":
                    results[key] = {"status": False, "details": error_msg}
        
        return results
    
    def test_web_services(self) -> Dict[str, Any]:
        """Test web service accessibility"""
        self.log("🌐 Testing web services...")
        
        results = {
            "streamlit_process": {"status": False, "details": ""},
            "port_binding": {"status": False, "details": ""},
            "http_response": {"status": False, "details": ""},
            "public_access": {"status": False, "details": ""}
        }
        
        # Check if Streamlit process is running
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'python' and any('streamlit' in arg for arg in proc.info['cmdline']):
                    results["streamlit_process"] = {
                        "status": True,
                        "details": f"Running as PID {proc.info['pid']}"
                    }
                    break
            else:
                results["streamlit_process"] = {"status": False, "details": "Streamlit process not found"}
        except Exception as e:
            results["streamlit_process"] = {"status": False, "details": str(e)}
        
        # Check port binding
        try:
            success, output = self.run_command("netstat -tlpn | grep :8501")
            results["port_binding"] = {
                "status": success and ":8501" in output,
                "details": "Port 8501 is bound" if success else "Port 8501 not bound"
            }
        except Exception as e:
            results["port_binding"] = {"status": False, "details": str(e)}
        
        # Test HTTP response
        try:
            response = requests.get("http://localhost:8501", timeout=10)
            results["http_response"] = {
                "status": response.status_code == 200,
                "details": f"HTTP {response.status_code}"
            }
        except Exception as e:
            results["http_response"] = {"status": False, "details": str(e)}
        
        # Test public access
        try:
            # Get public IP
            ip_response = requests.get("https://httpbin.org/ip", timeout=10)
            public_ip = ip_response.json().get("origin", "unknown")
            
            if public_ip != "unknown":
                # Test access from public IP (this might fail due to security groups)
                public_url = f"http://{public_ip}:8501"
                try:
                    public_response = requests.get(public_url, timeout=10)
                    results["public_access"] = {
                        "status": public_response.status_code == 200,
                        "details": f"Accessible at {public_url}"
                    }
                except requests.exceptions.ConnectTimeout:
                    results["public_access"] = {
                        "status": False,
                        "details": f"Timeout accessing {public_url} (check security groups)"
                    }
                except Exception as e:
                    results["public_access"] = {
                        "status": False,
                        "details": f"Cannot access {public_url}: {str(e)}"
                    }
            else:
                results["public_access"] = {"status": False, "details": "Could not determine public IP"}
                
        except Exception as e:
            results["public_access"] = {"status": False, "details": str(e)}
        
        return results
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check system requirements
        system_tests = self.results["tests"].get("system_requirements", {})
        
        if not system_tests.get("memory", {}).get("status", False):
            recommendations.append("⚡ Consider adding more swap space or upgrading instance type")
        
        if not system_tests.get("disk_space", {}).get("status", False):
            recommendations.append("💾 Clean up disk space or expand storage")
        
        if not system_tests.get("ollama_service", {}).get("status", False):
            recommendations.append("🤖 Start Ollama service: sudo systemctl start ollama")
        
        # Check application files
        app_tests = self.results["tests"].get("application_files", {})
        
        if not app_tests.get("python_dependencies", {}).get("status", False):
            recommendations.append("📦 Fix Python dependencies: pip install -r requirements.txt")
        
        if not app_tests.get("environment_config", {}).get("status", False):
            recommendations.append("⚙️ Configure environment variables in .env file")
        
        # Check RAG system
        rag_tests = self.results["tests"].get("rag_system", {})
        
        if not rag_tests.get("knowledge_base", {}).get("status", False):
            recommendations.append("📚 Initialize knowledge base with documents")
        
        if not rag_tests.get("response_generation", {}).get("status", False):
            recommendations.append("🧠 Check LLM configuration (OpenAI/Ollama)")
        
        # Check web services
        web_tests = self.results["tests"].get("web_services", {})
        
        if not web_tests.get("streamlit_process", {}).get("status", False):
            recommendations.append("🌐 Start Streamlit application: ./start_production.sh")
        
        if not web_tests.get("public_access", {}).get("status", False):
            recommendations.append("🔒 Configure EC2 security group to allow port 8501")
        
        # Performance recommendations
        if system_tests.get("memory", {}).get("details", "").startswith("Available memory"):
            available_mem = int(system_tests["memory"]["details"].split()[0].replace("MB", ""))
            if available_mem < 300:
                recommendations.append("🚀 Consider stopping unnecessary services to free memory")
        
        return recommendations
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("\n" + "="*60)
        print("🧪 IntelliSearch EC2 Deployment Validation")
        print("="*60)
        
        # Run all tests
        self.results["tests"]["system_requirements"] = self.test_system_requirements()
        self.results["tests"]["application_files"] = self.test_application_files()
        self.results["tests"]["rag_system"] = await self.test_rag_system()
        self.results["tests"]["web_services"] = self.test_web_services()
        
        # Generate recommendations
        self.results["recommendations"] = self.generate_recommendations()
        
        # Calculate overall status
        all_statuses = []
        for test_category in self.results["tests"].values():
            for test_result in test_category.values():
                all_statuses.append(test_result.get("status", False))
        
        if all(all_statuses):
            self.results["overall_status"] = "excellent"
        elif sum(all_statuses) / len(all_statuses) >= 0.8:
            self.results["overall_status"] = "good"
        elif sum(all_statuses) / len(all_statuses) >= 0.6:
            self.results["overall_status"] = "fair"
        else:
            self.results["overall_status"] = "poor"
        
        return self.results
    
    def print_results(self) -> None:
        """Print formatted validation results"""
        
        # Print test results
        for category, tests in self.results["tests"].items():
            category_name = category.replace("_", " ").title()
            print(f"\n📊 {category_name}")
            print("-" * 40)
            
            for test_name, result in tests.items():
                status_icon = "✅" if result["status"] else "❌"
                test_display = test_name.replace("_", " ").title()
                details = result.get("details", "No details")
                print(f"   {status_icon} {test_display}: {details}")
        
        # Print recommendations
        if self.results["recommendations"]:
            print(f"\n💡 Recommendations")
            print("-" * 40)
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        # Print overall status
        print(f"\n🎯 Overall Status")
        print("-" * 40)
        
        status_colors = {
            "excellent": "\033[0;32m",  # Green
            "good": "\033[1;32m",       # Bright Green
            "fair": "\033[1;33m",       # Yellow
            "poor": "\033[0;31m"        # Red
        }
        
        status = self.results["overall_status"]
        color = status_colors.get(status, "")
        reset = "\033[0m"
        
        status_messages = {
            "excellent": "🎉 Deployment is fully functional and optimized!",
            "good": "✅ Deployment is working well with minor issues",
            "fair": "⚠️ Deployment has some issues that should be addressed",
            "poor": "❌ Deployment has critical issues requiring immediate attention"
        }
        
        print(f"   {color}{status_messages.get(status, 'Unknown status')}{reset}")
        
        # Save results to file
        results_file = self.app_dir / "logs" / "deployment_validation.json"
        try:
            results_file.parent.mkdir(exist_ok=True)
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n📁 Results saved to: {results_file}")
        except Exception:
            pass
        
        print("\n" + "="*60)

async def main():
    """Main validation function"""
    validator = EC2DeploymentValidator()
    
    try:
        await validator.run_validation()
        validator.print_results()
        
        # Exit code based on status
        if validator.results["overall_status"] in ["excellent", "good"]:
            sys.exit(0)
        elif validator.results["overall_status"] == "fair":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())