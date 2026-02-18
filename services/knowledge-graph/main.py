"""
STRATUM PROTOCOL - Urban Knowledge Graph Service
Multi-layer infrastructure graph with GNN-based criticality scoring
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from neo4j import AsyncGraphDatabase, AsyncDriver
import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GAT
from torch_geometric.data import Data
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class GraphNode(BaseModel):
    """Node in the urban knowledge graph"""
    node_id: str
    node_type: str  # infrastructure, zone, service
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    coordinates: Optional[tuple[float, float]] = None
    criticality_score: float = Field(default=0.5, ge=0, le=1)
    health_status: float = Field(default=1.0, ge=0, le=1)
    capacity: Optional[float] = None
    current_load: Optional[float] = None


class GraphEdge(BaseModel):
    """Edge in the urban knowledge graph"""
    edge_id: str = Field(default_factory=lambda: str(uuid4()))
    source_node_id: str
    target_node_id: str
    relationship_type: str  # depends_on, supplies, controls, connected_to
    strength: float = Field(default=1.0, ge=0, le=1)
    properties: Dict[str, Any] = Field(default_factory=dict)
    failure_propagation_prob: float = Field(default=0.5, ge=0, le=1)


class GraphQuery(BaseModel):
    """Query for graph traversal"""
    node_ids: List[str]
    max_depth: int = Field(default=3, ge=1, le=10)
    relationship_types: Optional[List[str]] = None
    include_properties: bool = True


class CriticalityAnalysisRequest(BaseModel):
    """Request for criticality analysis"""
    node_ids: Optional[List[str]] = None
    use_gnn: bool = True
    update_scores: bool = False


class SubgraphRequest(BaseModel):
    """Request for subgraph extraction"""
    center_node_id: str
    radius_hops: int = Field(default=2, ge=1, le=5)
    filters: Optional[Dict[str, Any]] = None


# =============================================================================
# GRAPH NEURAL NETWORK MODELS
# =============================================================================

class CriticalityGNN(torch.nn.Module):
    """
    Graph Neural Network for infrastructure criticality scoring
    Uses Graph Attention Network (GAT) architecture
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, output_dim: int = 1, heads: int = 4):
        super(CriticalityGNN, self).__init__()
        self.conv1 = GAT(input_dim, hidden_dim, heads=heads, dropout=0.6)
        self.conv2 = GAT(hidden_dim * heads, hidden_dim, heads=1, concat=False, dropout=0.6)
        self.fc = torch.nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x, edge_index):
        """
        Forward pass
        
        Args:
            x: Node features [num_nodes, input_dim]
            edge_index: Edge connectivity [2, num_edges]
            
        Returns:
            Criticality scores [num_nodes, 1]
        """
        x = F.dropout(x, p=0.6, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv2(x, edge_index)
        x = torch.sigmoid(self.fc(x))
        return x


class DependencyGCN(torch.nn.Module):
    """
    Graph Convolutional Network for dependency analysis
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super(DependencyGCN, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, 1)
    
    def forward(self, x, edge_index, edge_weight=None):
        x = F.relu(self.conv1(x, edge_index, edge_weight))
        x = F.dropout(x, p=0.5, training=self.training)
        x = F.relu(self.conv2(x, edge_index, edge_weight))
        x = self.conv3(x, edge_index, edge_weight)
        return torch.sigmoid(x)


# =============================================================================
# KNOWLEDGE GRAPH SERVICE
# =============================================================================

class KnowledgeGraphService:
    """Urban infrastructure knowledge graph service"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver: Optional[AsyncDriver] = None
        
        # GNN models
        self.criticality_model: Optional[CriticalityGNN] = None
        self.dependency_model: Optional[DependencyGCN] = None
        
        # Cache
        self.node_cache: Dict[str, GraphNode] = {}
        
        logger.info("Knowledge Graph Service initialized")
    
    async def start(self):
        """Start the service"""
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Verify connectivity
        await self.driver.verify_connectivity()
        logger.info("Connected to Neo4j")
        
        # Initialize schema
        await self._init_schema()
        
        # Load GNN models
        self._load_gnn_models()
    
    async def stop(self):
        """Stop the service"""
        if self.driver:
            await self.driver.close()
    
    async def _init_schema(self):
        """Initialize graph schema with constraints and indexes"""
        async with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:InfrastructureNode) REQUIRE n.node_id IS UNIQUE",
                "CREATE INDEX node_type_index IF NOT EXISTS FOR (n:InfrastructureNode) ON (n.node_type)",
                "CREATE INDEX criticality_index IF NOT EXISTS FOR (n:InfrastructureNode) ON (n.criticality_score)",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning(f"Schema creation warning: {e}")
        
        logger.info("Graph schema initialized")
    
    def _load_gnn_models(self):
        """Load or initialize GNN models"""
        # Initialize with default architecture
        self.criticality_model = CriticalityGNN(input_dim=16, hidden_dim=64)
        self.dependency_model = DependencyGCN(input_dim=16, hidden_dim=128)
        
        # In production, load trained weights
        # self.criticality_model.load_state_dict(torch.load('models/criticality_model.pt'))
        
        self.criticality_model.eval()
        self.dependency_model.eval()
        
        logger.info("GNN models loaded")
    
    async def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph"""
        async with self.driver.session() as session:
            query = """
            MERGE (n:InfrastructureNode {node_id: $node_id})
            SET n.name = $name,
                n.node_type = $node_type,
                n.properties = $properties,
                n.coordinates = $coordinates,
                n.criticality_score = $criticality_score,
                n.health_status = $health_status,
                n.capacity = $capacity,
                n.current_load = $current_load,
                n.updated_at = datetime()
            RETURN n
            """
            
            result = await session.run(
                query,
                node_id=node.node_id,
                name=node.name,
                node_type=node.node_type,
                properties=node.properties,
                coordinates=list(node.coordinates) if node.coordinates else None,
                criticality_score=node.criticality_score,
                health_status=node.health_status,
                capacity=node.capacity,
                current_load=node.current_load
            )
            
            await result.single()
            self.node_cache[node.node_id] = node
            logger.info(f"Added node: {node.node_id}")
            return True
    
    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge (relationship) to the graph"""
        async with self.driver.session() as session:
            query = """
            MATCH (source:InfrastructureNode {node_id: $source_id})
            MATCH (target:InfrastructureNode {node_id: $target_id})
            MERGE (source)-[r:DEPENDS_ON {edge_id: $edge_id}]->(target)
            SET r.relationship_type = $rel_type,
                r.strength = $strength,
                r.properties = $properties,
                r.failure_propagation_prob = $failure_prob,
                r.updated_at = datetime()
            RETURN r
            """
            
            result = await session.run(
                query,
                edge_id=edge.edge_id,
                source_id=edge.source_node_id,
                target_id=edge.target_node_id,
                rel_type=edge.relationship_type,
                strength=edge.strength,
                properties=edge.properties,
                failure_prob=edge.failure_propagation_prob
            )
            
            await result.single()
            logger.info(f"Added edge: {edge.source_node_id} -> {edge.target_node_id}")
            return True
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID"""
        # Check cache first
        if node_id in self.node_cache:
            return self.node_cache[node_id]
        
        async with self.driver.session() as session:
            query = "MATCH (n:InfrastructureNode {node_id: $node_id}) RETURN n"
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if record:
                node_data = dict(record["n"])
                coords = node_data.get("coordinates")
                node = GraphNode(
                    node_id=node_data["node_id"],
                    node_type=node_data["node_type"],
                    name=node_data["name"],
                    properties=node_data.get("properties", {}),
                    coordinates=tuple(coords) if coords else None,
                    criticality_score=node_data.get("criticality_score", 0.5),
                    health_status=node_data.get("health_status", 1.0),
                    capacity=node_data.get("capacity"),
                    current_load=node_data.get("current_load")
                )
                self.node_cache[node_id] = node
                return node
        
        return None
    
    async def get_neighbors(
        self,
        node_id: str,
        max_depth: int = 1,
        relationship_types: Optional[List[str]] = None
    ) -> List[GraphNode]:
        """Get neighbors of a node"""
        async with self.driver.session() as session:
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""
            MATCH (n:InfrastructureNode {{node_id: $node_id}})
            MATCH (n)-[{rel_filter}*1..{max_depth}]-(neighbor)
            RETURN DISTINCT neighbor
            """
            
            result = await session.run(query, node_id=node_id)
            records = await result.data()
            
            neighbors = []
            for record in records:
                node_data = record["neighbor"]
                coords = node_data.get("coordinates")
                neighbor = GraphNode(
                    node_id=node_data["node_id"],
                    node_type=node_data["node_type"],
                    name=node_data["name"],
                    properties=node_data.get("properties", {}),
                    coordinates=tuple(coords) if coords else None,
                    criticality_score=node_data.get("criticality_score", 0.5),
                    health_status=node_data.get("health_status", 1.0),
                    capacity=node_data.get("capacity"),
                    current_load=node_data.get("current_load")
                )
                neighbors.append(neighbor)
            
            return neighbors
    
    async def find_critical_nodes(self, top_k: int = 10) -> List[GraphNode]:
        """Find the most critical nodes in the graph"""
        async with self.driver.session() as session:
            query = """
            MATCH (n:InfrastructureNode)
            RETURN n
            ORDER BY n.criticality_score DESC
            LIMIT $limit
            """
            
            result = await session.run(query, limit=top_k)
            records = await result.data()
            
            critical_nodes = []
            for record in records:
                node_data = record["n"]
                coords = node_data.get("coordinates")
                node = GraphNode(
                    node_id=node_data["node_id"],
                    node_type=node_data["node_type"],
                    name=node_data["name"],
                    properties=node_data.get("properties", {}),
                    coordinates=tuple(coords) if coords else None,
                    criticality_score=node_data.get("criticality_score", 0.5),
                    health_status=node_data.get("health_status", 1.0),
                    capacity=node_data.get("capacity"),
                    current_load=node_data.get("current_load")
                )
                critical_nodes.append(node)
            
            return critical_nodes
    
    async def compute_criticality_scores(
        self,
        node_ids: Optional[List[str]] = None,
        use_gnn: bool = True
    ) -> Dict[str, float]:
        """
        Compute criticality scores using GNN
        
        Args:
            node_ids: Specific nodes to score (None = all nodes)
            use_gnn: Whether to use GNN (else use centrality metrics)
            
        Returns:
            Dict mapping node_id to criticality score
        """
        if not use_gnn:
            return await self._compute_centrality_scores(node_ids)
        
        # Load graph into PyTorch Geometric format
        graph_data = await self._load_graph_for_gnn(node_ids)
        
        if graph_data is None:
            return {}
        
        # Run GNN inference
        with torch.no_grad():
            scores = self.criticality_model(
                graph_data.x,
                graph_data.edge_index
            )
        
        # Map scores back to node IDs
        node_id_list = graph_data.node_id_mapping
        scores_dict = {
            node_id_list[i]: float(scores[i].item())
            for i in range(len(node_id_list))
        }
        
        return scores_dict
    
    async def _load_graph_for_gnn(
        self,
        node_ids: Optional[List[str]] = None
    ) -> Optional[Data]:
        """Load graph into PyTorch Geometric Data format"""
        async with self.driver.session() as session:
            # Get nodes
            if node_ids:
                node_filter = "WHERE n.node_id IN $node_ids"
                params = {"node_ids": node_ids}
            else:
                node_filter = ""
                params = {}
            
            node_query = f"""
            MATCH (n:InfrastructureNode)
            {node_filter}
            RETURN n.node_id AS node_id,
                   n.capacity AS capacity,
                   n.current_load AS current_load,
                   n.health_status AS health_status,
                   n.criticality_score AS criticality_score
            """
            
            result = await session.run(node_query, **params)
            node_records = await result.data()
            
            if not node_records:
                return None
            
            # Create node feature matrix
            node_id_mapping = {r["node_id"]: i for i, r in enumerate(node_records)}
            num_nodes = len(node_records)
            
            # Feature engineering (16-dimensional features)
            features = []
            for record in node_records:
                capacity = record.get("capacity", 1.0) or 1.0
                load = record.get("current_load", 0.0) or 0.0
                health = record.get("health_status", 1.0) or 1.0
                
                feature_vector = [
                    load / capacity if capacity > 0 else 0,  # Load ratio
                    health,                                   # Health status
                    record.get("criticality_score", 0.5),    # Current criticality
                    1.0,  # Degree centrality (placeholder)
                    0.5,  # Betweenness centrality (placeholder)
                    0.5,  # Closeness centrality (placeholder)
                    1.0 if capacity > 1000 else 0.0,         # High capacity flag
                    1.0 if load / capacity > 0.8 else 0.0,   # Stressed flag
                ] + [0.0] * 8  # Additional features
                
                features.append(feature_vector)
            
            x = torch.tensor(features, dtype=torch.float32)
            
            # Get edges
            edge_query = """
            MATCH (source:InfrastructureNode)-[r:DEPENDS_ON]->(target:InfrastructureNode)
            RETURN source.node_id AS source_id,
                   target.node_id AS target_id,
                   r.strength AS strength
            """
            
            result = await session.run(edge_query)
            edge_records = await result.data()
            
            # Create edge index and edge weights
            edge_list = []
            edge_weights = []
            
            for record in edge_records:
                source_id = record["source_id"]
                target_id = record["target_id"]
                
                if source_id in node_id_mapping and target_id in node_id_mapping:
                    source_idx = node_id_mapping[source_id]
                    target_idx = node_id_mapping[target_id]
                    edge_list.append([source_idx, target_idx])
                    edge_weights.append(record.get("strength", 1.0))
            
            if not edge_list:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                edge_attr = torch.empty((0,), dtype=torch.float32)
            else:
                edge_index = torch.tensor(edge_list, dtype=torch.long).t()
                edge_attr = torch.tensor(edge_weights, dtype=torch.float32)
            
            # Create PyTorch Geometric Data object
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data.node_id_mapping = list(node_id_mapping.keys())
            
            return data
    
    async def _compute_centrality_scores(
        self,
        node_ids: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Compute criticality using graph centrality metrics"""
        async with self.driver.session() as session:
            # Use PageRank as proxy for criticality
            query = """
            CALL gds.pageRank.stream('infrastructure-graph')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).node_id AS node_id, score
            ORDER BY score DESC
            """
            
            try:
                result = await session.run(query)
                records = await result.data()
                
                scores = {r["node_id"]: r["score"] for r in records}
                
                if node_ids:
                    scores = {k: v for k, v in scores.items() if k in node_ids}
                
                return scores
            except Exception as e:
                logger.warning(f"Centrality computation failed: {e}")
                return {}
    
    async def get_subgraph(
        self,
        center_node_id: str,
        radius_hops: int = 2
    ) -> Dict[str, Any]:
        """Extract a subgraph around a center node"""
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (center:InfrastructureNode {{node_id: $node_id}})-[*1..{radius_hops}]-(connected)
            WITH center, connected, relationships(path) as rels
            RETURN center, collect(DISTINCT connected) as nodes, collect(DISTINCT rels) as edges
            """
            
            result = await session.run(query, node_id=center_node_id)
            record = await result.single()
            
            if not record:
                return {"nodes": [], "edges": []}
            
            # Process nodes
            nodes = []
            if record["center"]:
                center_data = dict(record["center"])
                nodes.append(self._node_dict_to_model(center_data))
            
            for node_data in record["nodes"]:
                nodes.append(self._node_dict_to_model(dict(node_data)))
            
            # Process edges
            edges = []
            for edge_list in record["edges"]:
                for edge in edge_list:
                    edge_data = dict(edge)
                    edges.append({
                        "source": edge.start_node["node_id"],
                        "target": edge.end_node["node_id"],
                        "type": edge_data.get("relationship_type", "unknown"),
                        "properties": edge_data
                    })
            
            return {"nodes": nodes, "edges": edges}
    
    def _node_dict_to_model(self, node_data: Dict) -> GraphNode:
        """Convert Neo4j node dict to GraphNode model"""
        coords = node_data.get("coordinates")
        return GraphNode(
            node_id=node_data["node_id"],
            node_type=node_data["node_type"],
            name=node_data["name"],
            properties=node_data.get("properties", {}),
            coordinates=tuple(coords) if coords else None,
            criticality_score=node_data.get("criticality_score", 0.5),
            health_status=node_data.get("health_status", 1.0),
            capacity=node_data.get("capacity"),
            current_load=node_data.get("current_load")
        )


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

service: Optional[KnowledgeGraphService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    service = KnowledgeGraphService(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="dev_password"
    )
    await service.start()
    yield
    await service.stop()

app = FastAPI(
    title="STRATUM PROTOCOL - Knowledge Graph Service",
    description="Urban infrastructure knowledge graph with GNN-based analysis",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "knowledge-graph"}

@app.post("/api/v1/graph/nodes")
async def add_node(node: GraphNode):
    """Add a node to the graph"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    success = await service.add_node(node)
    return {"status": "created", "node_id": node.node_id}

@app.post("/api/v1/graph/edges")
async def add_edge(edge: GraphEdge):
    """Add an edge to the graph"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    success = await service.add_edge(edge)
    return {"status": "created", "edge_id": edge.edge_id}

@app.get("/api/v1/graph/nodes/{node_id}")
async def get_node(node_id: str):
    """Get a node by ID"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    node = await service.get_node(node_id)
    if node:
        return node
    raise HTTPException(status_code=404, detail="Node not found")

@app.get("/api/v1/graph/nodes/{node_id}/neighbors")
async def get_neighbors(node_id: str, max_depth: int = 1):
    """Get neighbors of a node"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    neighbors = await service.get_neighbors(node_id, max_depth)
    return {"node_id": node_id, "neighbors": neighbors, "count": len(neighbors)}

@app.get("/api/v1/graph/critical-nodes")
async def get_critical_nodes(top_k: int = 10):
    """Get the most critical nodes"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    nodes = await service.find_critical_nodes(top_k)
    return {"critical_nodes": nodes, "count": len(nodes)}

@app.post("/api/v1/graph/criticality/compute")
async def compute_criticality(request: CriticalityAnalysisRequest):
    """Compute criticality scores using GNN"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    scores = await service.compute_criticality_scores(
        node_ids=request.node_ids,
        use_gnn=request.use_gnn
    )
    
    return {"scores": scores, "count": len(scores)}

@app.post("/api/v1/graph/subgraph")
async def get_subgraph(request: SubgraphRequest):
    """Extract a subgraph"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    subgraph = await service.get_subgraph(
        center_node_id=request.center_node_id,
        radius_hops=request.radius_hops
    )
    
    return subgraph

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
