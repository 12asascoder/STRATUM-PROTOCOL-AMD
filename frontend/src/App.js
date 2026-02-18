import React, { useState, useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Html } from '@react-three/drei';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  Grid, 
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import * as THREE from 'three';
import axios from 'axios';
import io from 'socket.io-client';

// =============================================================================
// 3D Infrastructure Node Component
// =============================================================================

function InfrastructureNode({ node, position, onClick }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // Animate based on stress level
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
      
      // Pulse effect for stressed nodes
      if (node.load_percentage > 0.8) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
        meshRef.current.scale.set(scale, scale, scale);
      }
    }
  });
  
  // Color based on health status
  const getColor = () => {
    if (node.load_percentage > 0.9) return '#ff0000'; // Critical
    if (node.load_percentage > 0.7) return '#ff9800'; // Warning
    return '#4caf50'; // Healthy
  };
  
  return (
    <mesh
      ref={meshRef}
      position={position}
      onClick={() => onClick(node)}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <boxGeometry args={[1, 2, 1]} />
      <meshStandardMaterial 
        color={getColor()} 
        emissive={hovered ? '#ffffff' : '#000000'}
        emissiveIntensity={hovered ? 0.3 : 0}
      />
      
      {hovered && (
        <Html>
          <div style={{
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            minWidth: '200px'
          }}>
            <strong>{node.name}</strong><br/>
            Type: {node.node_type}<br/>
            Load: {(node.load_percentage * 100).toFixed(1)}%<br/>
            Capacity: {node.capacity}
          </div>
        </Html>
      )}
    </mesh>
  );
}

// =============================================================================
// Connection Lines between Infrastructure
// =============================================================================

function ConnectionLine({ start, end, strength }) {
  const points = [
    new THREE.Vector3(...start),
    new THREE.Vector3(...end)
  ];
  
  const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
  
  const color = strength > 0.7 ? '#4caf50' : strength > 0.4 ? '#ff9800' : '#f44336';
  
  return (
    <line geometry={lineGeometry}>
      <lineBasicMaterial color={color} linewidth={2} />
    </line>
  );
}

// =============================================================================
// 3D City Scene
// =============================================================================

function CityScene({ nodes, connections, onNodeClick }) {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <spotLight position={[-10, 20, 10]} angle={0.3} penumbra={1} />
      
      {/* Infrastructure Nodes */}
      {nodes.map((node, idx) => (
        <InfrastructureNode
          key={node.node_id}
          node={node}
          position={[
            (idx % 10) * 3 - 15,
            0,
            Math.floor(idx / 10) * 3 - 15
          ]}
          onClick={onNodeClick}
        />
      ))}
      
      {/* Connection Lines */}
      {connections.map((conn, idx) => (
        <ConnectionLine
          key={idx}
          start={conn.start}
          end={conn.end}
          strength={conn.strength}
        />
      ))}
      
      {/* Ground Plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1, 0]}>
        <planeGeometry args={[100, 100]} />
        <meshStandardMaterial color="#1a237e" opacity={0.3} transparent />
      </mesh>
      
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        maxPolarAngle={Math.PI / 2}
      />
      <PerspectiveCamera makeDefault position={[0, 20, 30]} />
    </>
  );
}

// =============================================================================
// Dashboard Stats Component
// =============================================================================

function DashboardStats({ stats }) {
  return (
    <Grid container spacing={2}>
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Nodes
            </Typography>
            <Typography variant="h4">
              {stats.total_nodes || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Critical Nodes
            </Typography>
            <Typography variant="h4" color="error">
              {stats.critical_nodes || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Average Load
            </Typography>
            <Typography variant="h4" color="warning.main">
              {stats.avg_load ? `${(stats.avg_load * 100).toFixed(1)}%` : '0%'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              System Health
            </Typography>
            <Typography variant="h4" color="success.main">
              {stats.health_score ? `${(stats.health_score * 100).toFixed(0)}%` : '0%'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

// =============================================================================
// Main Application Component
// =============================================================================

function App() {
  const [nodes, setNodes] = useState([]);
  const [connections, setConnections] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedNode, setSelectedNode] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Initialize WebSocket connection
  useEffect(() => {
    const socket = io('http://localhost:8001');
    
    socket.on('connect', () => {
      console.log('WebSocket connected');
    });
    
    socket.on('infrastructure_update', (data) => {
      setNodes(prevNodes => {
        const updated = [...prevNodes];
        const index = updated.findIndex(n => n.node_id === data.node_id);
        if (index >= 0) {
          updated[index] = { ...updated[index], ...data };
        }
        return updated;
      });
    });
    
    socket.on('alert', (alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 5));
    });
    
    return () => socket.disconnect();
  }, []);
  
  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch nodes from knowledge graph
        const nodesResponse = await axios.get('/api/v1/graph/nodes');
        setNodes(nodesResponse.data);
        
        // Calculate stats
        const criticalCount = nodesResponse.data.filter(
          n => n.load_percentage > 0.9
        ).length;
        const avgLoad = nodesResponse.data.reduce(
          (sum, n) => sum + n.load_percentage, 0
        ) / nodesResponse.data.length;
        
        setStats({
          total_nodes: nodesResponse.data.length,
          critical_nodes: criticalCount,
          avg_load: avgLoad,
          health_score: 1 - avgLoad
        });
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    
    return () => clearInterval(interval);
  }, []);
  
  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };
  
  const runCascadeSimulation = async () => {
    if (!selectedNode) return;
    
    try {
      const response = await axios.post('/api/v1/simulate/cascade', {
        initial_failure_nodes: [selectedNode.node_id],
        monte_carlo_runs: 1000,
        confidence_level: 0.95
      });
      
      alert(`Simulation complete!\nAffected nodes: ${response.data.affected_nodes_ci[0]}-${response.data.affected_nodes_ci[1]}\nImpact score: ${response.data.impact_score_mean.toFixed(2)}`);
    } catch (error) {
      console.error('Simulation error:', error);
    }
  };
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }
  
  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <AppBar position="static" sx={{ background: 'linear-gradient(45deg, #1a237e 30%, #311b92 90%)' }}>
        <Toolbar>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            🏙️ STRATUM PROTOCOL - Urban Decision Intelligence
          </Typography>
          <Typography variant="body2">
            Real-Time Infrastructure Monitoring
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Alerts */}
      <Box sx={{ p: 2 }}>
        {alerts.map((alert, idx) => (
          <Alert key={idx} severity={alert.severity} sx={{ mb: 1 }}>
            {alert.message}
          </Alert>
        ))}
      </Box>
      
      {/* Stats Dashboard */}
      <Box sx={{ p: 2 }}>
        <DashboardStats stats={stats} />
      </Box>
      
      {/* 3D Visualization */}
      <Box sx={{ height: '600px', border: '2px solid #1a237e', borderRadius: 2, m: 2 }}>
        <Canvas>
          <Suspense fallback={null}>
            <CityScene 
              nodes={nodes} 
              connections={connections}
              onNodeClick={handleNodeClick}
            />
          </Suspense>
        </Canvas>
      </Box>
      
      {/* Control Panel */}
      <Box sx={{ p: 2 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Control Panel
            </Typography>
            
            {selectedNode ? (
              <>
                <Typography variant="body1">
                  Selected: <strong>{selectedNode.name}</strong>
                </Typography>
                <Button 
                  variant="contained" 
                  color="primary" 
                  sx={{ mt: 2 }}
                  onClick={runCascadeSimulation}
                >
                  Run Cascade Simulation
                </Button>
              </>
            ) : (
              <Typography color="textSecondary">
                Click on a node to select and run simulations
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}

export default App;
