# agents/visual_architecture_generator.py
import asyncio
from typing import Dict, Any, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import json
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)

class VisualArchitectureGenerator:
    """Generates visual architecture diagrams from code analysis results"""
    
    def __init__(self):
        self.color_palette = {
            "frontend": "#3b82f6",  # Blue
            "backend": "#10b981",   # Green
            "database": "#f59e0b",  # Amber
            "api": "#8b5cf6",       # Purple
            "service": "#ef4444",   # Red
            "component": "#06b6d4", # Cyan
            "utility": "#6b7280",   # Gray
            "config": "#ec4899"     # Pink
        }
        
    async def create_architecture_diagram(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive architecture diagram"""
        try:
            # Extract key information
            structure = analysis_data.get("structure", {})
            dependencies = analysis_data.get("dependencies", {})
            technologies = analysis_data.get("code_metrics", {}).get("main_technologies", [])
            patterns = analysis_data.get("architecture_patterns", [])
            
            # Create network graph
            G = nx.DiGraph()
            
            # Add nodes for main directories
            main_dirs = structure.get("main_directories", [])
            for directory in main_dirs:
                node_type = self._classify_directory(directory)
                G.add_node(directory, type=node_type, size=30)
                
            # Add technology nodes
            for tech in technologies:
                G.add_node(tech, type="technology", size=20)
                
            # Add edges based on common patterns
            self._add_dependency_edges(G, main_dirs, technologies)
            
            # Create visualization
            fig = self._create_network_visualization(G, analysis_data)
            
            # Add additional charts
            fig_combined = self._create_comprehensive_dashboard(analysis_data, fig)
            
            return {
                "main_diagram": fig_combined.to_json(),
                "architecture_summary": self._generate_architecture_summary(analysis_data),
                "diagram_type": "comprehensive_architecture",
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating architecture diagram: {str(e)}")
            return {
                "error": str(e),
                "fallback_diagram": self._create_fallback_diagram(analysis_data)
            }
            
    def _classify_directory(self, directory: str) -> str:
        """Classify directory type for visualization"""
        directory_lower = directory.lower()
        
        if any(keyword in directory_lower for keyword in ["frontend", "client", "ui", "components", "pages"]):
            return "frontend"
        elif any(keyword in directory_lower for keyword in ["backend", "server", "api", "routes"]):
            return "backend"
        elif any(keyword in directory_lower for keyword in ["database", "db", "storage", "models"]):
            return "database"
        elif any(keyword in directory_lower for keyword in ["service", "services", "microservice"]):
            return "service"
        elif any(keyword in directory_lower for keyword in ["config", "configuration", "settings"]):
            return "config"
        elif any(keyword in directory_lower for keyword in ["utils", "utilities", "helpers", "common"]):
            return "utility"
        else:
            return "component"
            
    def _add_dependency_edges(self, G: nx.DiGraph, directories: List[str], technologies: List[str]):
        """Add edges based on common architectural patterns"""
        # Common frontend -> backend patterns
        frontend_dirs = [d for d in directories if self._classify_directory(d) == "frontend"]
        backend_dirs = [d for d in directories if self._classify_directory(d) == "backend"]
        
        for frontend in frontend_dirs:
            for backend in backend_dirs:
                G.add_edge(frontend, backend, type="api_call")
                
        # Backend -> database patterns
        database_dirs = [d for d in directories if self._classify_directory(d) == "database"]
        for backend in backend_dirs:
            for database in database_dirs:
                G.add_edge(backend, database, type="data_access")
                
        # Technology connections
        for tech in technologies:
            if tech.lower() in ["react", "vue", "angular"]:
                for frontend in frontend_dirs:
                    G.add_edge(tech, frontend, type="framework")
            elif tech.lower() in ["django", "flask", "fastapi", "express"]:
                for backend in backend_dirs:
                    G.add_edge(tech, backend, type="framework")
                    
    def _create_network_visualization(self, G: nx.DiGraph, analysis_data: Dict[str, Any]) -> go.Figure:
        """Create network visualization using Plotly"""
        # Calculate positions using spring layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare node traces
        node_traces = {}
        for node_type in set(nx.get_node_attributes(G, 'type').values()):
            node_traces[node_type] = {
                'x': [], 'y': [], 'text': [], 'size': [],
                'color': self.color_palette.get(node_type, '#6b7280')
            }
            
        for node in G.nodes():
            x, y = pos[node]
            node_type = G.nodes[node].get('type', 'component')
            node_traces[node_type]['x'].append(x)
            node_traces[node_type]['y'].append(y)
            node_traces[node_type]['text'].append(node)
            node_traces[node_type]['size'].append(G.nodes[node].get('size', 20))
            
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        # Create figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(125, 125, 125, 0.5)'),
            hoverinfo='none',
            mode='lines',
            name='Dependencies'
        ))
        
        # Add nodes by type
        for node_type, trace_data in node_traces.items():
            if trace_data['x']:  # Only add if there are nodes of this type
                fig.add_trace(go.Scatter(
                    x=trace_data['x'],
                    y=trace_data['y'],
                    mode='markers+text',
                    marker=dict(
                        size=trace_data['size'],
                        color=trace_data['color'],
                        line=dict(width=2, color='white'),
                        opacity=0.8
                    ),
                    text=trace_data['text'],
                    textposition="middle center",
                    textfont=dict(size=10, color='white'),
                    name=node_type.title(),
                    hovertemplate=f'<b>%{{text}}</b><br>Type: {node_type}<extra></extra>'
                ))
                
        # Update layout
        fig.update_layout(
            title=f"Architecture Overview - {analysis_data.get('repo_info', {}).get('repo', 'Repository')}",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Interactive Architecture Diagram - Hover for details",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002, xanchor='left', yanchor='bottom',
                font=dict(color="#888", size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
        
    def _create_comprehensive_dashboard(self, analysis_data: Dict[str, Any], main_fig: go.Figure) -> go.Figure:
        """Create a comprehensive dashboard with multiple visualizations"""
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Architecture Network', 'Technology Stack', 'Code Metrics', 'Complexity Analysis'),
            specs=[[{"type": "xy"}, {"type": "domain"}],
                   [{"type": "xy"}, {"type": "xy"}]],
            vertical_spacing=0.08,
            horizontal_spacing=0.08
        )
        
        # Add main architecture diagram to subplot 1,1
        for trace in main_fig.data:
            fig.add_trace(trace, row=1, col=1)
            
        # Technology stack pie chart (subplot 1,2)
        technologies = analysis_data.get("code_metrics", {}).get("main_technologies", [])
        if technologies:
            fig.add_trace(
                go.Pie(
                    labels=technologies,
                    values=[1] * len(technologies),  # Equal sizes for demo
                    hole=0.3,
                    marker_colors=[self.color_palette.get("api"), self.color_palette.get("backend"), 
                                 self.color_palette.get("frontend"), self.color_palette.get("database")][:len(technologies)]
                ),
                row=1, col=2
            )
        
        # Code metrics bar chart (subplot 2,1)
        metrics = analysis_data.get("code_metrics", {})
        metric_names = []
        metric_values = []
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key != "main_technologies":
                metric_names.append(key.replace("_", " ").title())
                metric_values.append(value)
                
        if metric_names:
            fig.add_trace(
                go.Bar(
                    x=metric_names,
                    y=metric_values,
                    marker_color=self.color_palette.get("service"),
                    name="Metrics"
                ),
                row=2, col=1
            )
        
        # Complexity trend (subplot 2,2) - Mock data for demo
        complexity_data = self._generate_complexity_trend(analysis_data)
        fig.add_trace(
            go.Scatter(
                x=complexity_data["dates"],
                y=complexity_data["complexity"],
                mode='lines+markers',
                name='Complexity Trend',
                line=dict(color=self.color_palette.get("frontend"), width=3)
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Complete Architecture Analysis - {analysis_data.get('repo_info', {}).get('repo', 'Repository')}",
            title_x=0.5,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Update subplot layouts
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
        
        return fig
        
    def _generate_complexity_trend(self, analysis_data: Dict[str, Any]) -> Dict[str, List]:
        """Generate mock complexity trend data"""
        import datetime as dt
        
        dates = []
        complexity = []
        
        # Generate trend for last 30 days
        base_complexity = analysis_data.get("code_metrics", {}).get("lines_of_code", 1000) / 1000
        
        for i in range(30):
            date = dt.datetime.now() - dt.timedelta(days=29-i)
            dates.append(date.strftime("%Y-%m-%d"))
            # Add some variation to make it look realistic
            variation = 0.9 + (i % 7) * 0.02
            complexity.append(base_complexity * variation)
            
        return {"dates": dates, "complexity": complexity}
        
    def _generate_architecture_summary(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the architecture"""
        structure = analysis_data.get("structure", {})
        patterns = analysis_data.get("architecture_patterns", [])
        technologies = analysis_data.get("code_metrics", {}).get("main_technologies", [])
        
        summary = {
            "total_files": structure.get("total_files", 0),
            "total_directories": structure.get("total_directories", 0),
            "architecture_patterns": patterns,
            "main_technologies": technologies,
            "complexity_assessment": self._assess_complexity(analysis_data),
            "scalability_score": self._calculate_scalability_score(analysis_data),
            "maintainability_score": self._calculate_maintainability_score(analysis_data)
        }
        
        return summary
        
    def _assess_complexity(self, analysis_data: Dict[str, Any]) -> str:
        """Assess overall complexity level"""
        metrics = analysis_data.get("code_metrics", {})
        total_files = metrics.get("python_files", 0)
        functions = metrics.get("functions", 0)
        classes = metrics.get("classes", 0)
        
        complexity_score = (total_files * 0.1) + (functions * 0.05) + (classes * 0.2)
        
        if complexity_score < 10:
            return "Low - Simple project structure"
        elif complexity_score < 50:
            return "Medium - Moderate complexity"
        elif complexity_score < 100:
            return "High - Complex architecture"
        else:
            return "Very High - Enterprise-level complexity"
            
    def _calculate_scalability_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate scalability score based on architecture patterns"""
        patterns = analysis_data.get("architecture_patterns", [])
        score = 0.5  # Base score
        
        # Bonus for good patterns
        if "Microservices Architecture" in patterns:
            score += 0.3
        if "Clean Architecture" in patterns:
            score += 0.2
        if "Repository Pattern" in patterns:
            score += 0.1
            
        # Bonus for technology choices
        technologies = analysis_data.get("code_metrics", {}).get("main_technologies", [])
        if "Docker" in technologies:
            score += 0.1
        if "Kubernetes" in technologies:
            score += 0.1
            
        return min(score, 1.0)
        
    def _calculate_maintainability_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate maintainability score"""
        structure = analysis_data.get("structure", {})
        config_files = len(structure.get("config_files", []))
        documentation = len(structure.get("documentation", []))
        
        score = 0.4  # Base score
        
        # Bonus for good practices
        if config_files > 0:
            score += 0.2
        if documentation > 0:
            score += 0.2
        if "Clean Architecture" in analysis_data.get("architecture_patterns", []):
            score += 0.2
            
        return min(score, 1.0)
        
    def _create_fallback_diagram(self, analysis_data: Dict[str, Any]) -> str:
        """Create a simple fallback diagram in case of errors"""
        structure = analysis_data.get("structure", {})
        
        simple_fig = go.Figure()
        simple_fig.add_trace(go.Bar(
            x=["Files", "Directories", "Config Files"],
            y=[
                structure.get("total_files", 0),
                structure.get("total_directories", 0),
                len(structure.get("config_files", []))
            ],
            marker_color=self.color_palette.get("service")
        ))
        
        simple_fig.update_layout(
            title="Repository Overview",
            xaxis_title="Component",
            yaxis_title="Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return simple_fig.to_json()
        
    async def create_flow_diagram(self, decision_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a flow diagram showing decision pathways"""
        try:
            # Create a flow chart from decision data
            fig = go.Figure()
            
            # Add decision nodes
            for i, decision in enumerate(decision_data):
                fig.add_trace(go.Scatter(
                    x=[i],
                    y=[decision.get("confidence", 0.5)],
                    mode='markers+text',
                    marker=dict(
                        size=20,
                        color=self.color_palette.get(decision.get("agent_name", "component").lower().split("agent")[0], "#6b7280")
                    ),
                    text=[decision.get("decision_type", "Decision")],
                    textposition="middle center",
                    name=decision.get("agent_name", "Unknown Agent")
                ))
                
            fig.update_layout(
                title="Decision Flow Pathway",
                xaxis_title="Decision Sequence",
                yaxis_title="Confidence Level",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            return {
                "flow_diagram": fig.to_json(),
                "total_decisions": len(decision_data),
                "avg_confidence": sum(d.get("confidence", 0.5) for d in decision_data) / max(len(decision_data), 1)
            }
            
        except Exception as e:
            logger.error(f"Error creating flow diagram: {str(e)}")
            return {"error": str(e)} 