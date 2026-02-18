import React, { useState, useEffect, Suspense } from 'react';
import { ThemeProvider, CssBaseline, Box, Grid, CircularProgress, Typography } from '@mui/material';
import { Canvas } from '@react-three/fiber';
import axios from 'axios';
import io from 'socket.io-client';

// Theme
import theme from './theme/theme';

// Components
import Header from './components/Layout/Header';
import StatCard from './components/Dashboard/StatCard';
import AlertFeed from './components/Dashboard/AlertFeed';
import ControlPanel from './components/Dashboard/ControlPanel';
import CityScene from './components/Visualization/CityScene';

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
      setAlerts(prev => [alert, ...prev].slice(0, 50)); // Keep last 50 alerts
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
        // Fallback data for demo purposes if API fails
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

  const runCascadeSimulation = async (node) => {
    try {
      const response = await axios.post('/api/v1/simulate/cascade', {
        initial_failure_nodes: [node.node_id],
        monte_carlo_runs: 1000,
        confidence_level: 0.95
      });

      const resultMessage = `Simulation complete!\nAffected: ${response.data.affected_nodes_ci[0]}-${response.data.affected_nodes_ci[1]}\nImpact: ${response.data.impact_score_mean.toFixed(2)}`;
      alert(resultMessage);

      // Add visual alert for feedback
      setAlerts(prev => [{
        severity: 'info',
        message: `Simulation Result: Impact Score ${response.data.impact_score_mean.toFixed(2)}`,
        timestamp: new Date().toISOString()
      }, ...prev]);

    } catch (error) {
      console.error('Simulation error:', error);
      alert('Simulation failed. Check console for details.');
    }
  };

  // Mock data for sparklines
  const mockTrendData = Array.from({ length: 20 }, (_, i) => ({
    value: Math.random() * 100
  }));

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
          <CircularProgress size={60} color="secondary" />
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <Header />

        <Box sx={{ flexGrow: 1, p: 2, overflow: 'auto' }}>
          <Grid container spacing={2} sx={{ height: '100%' }}>

            {/* Left Column: Stats & Controls */}
            <Grid item xs={12} md={3} sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>

              {/* Stat Cards */}
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <StatCard
                  title="Total Nodes"
                  value={stats.total_nodes || 0}
                  unit=""
                />
                <StatCard
                  title="Critical"
                  value={stats.critical_nodes || 0}
                  color="#ff1744"
                  subValue={stats.critical_nodes > 0 ? "+2 from last hr" : "Stable"}
                />
              </Box>

              <StatCard
                title="System Health"
                value={stats.health_score ? `${(stats.health_score * 100).toFixed(0)}` : '0'}
                unit="%"
                color="#00e676"
                data={mockTrendData}
              />

              <Box sx={{ flexGrow: 1, minHeight: 0 }}>
                <ControlPanel
                  selectedNode={selectedNode}
                  onRunSimulation={runCascadeSimulation}
                />
              </Box>
            </Grid>

            {/* Middle Column: 3D Visualization */}
            <Grid item xs={12} md={6} sx={{ height: '100%' }}>
              <Box sx={{
                height: '100%',
                bgcolor: 'background.paper',
                borderRadius: 2,
                overflow: 'hidden',
                position: 'relative',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 0 20px rgba(0, 229, 255, 0.1)'
              }}>
                <Canvas shadows>
                  <Suspense fallback={null}>
                    <CityScene
                      nodes={nodes}
                      connections={connections}
                      onNodeClick={handleNodeClick}
                    />
                  </Suspense>
                </Canvas>

                {/* Overlay for quick info if needed */}
                <Box sx={{ position: 'absolute', bottom: 16, left: 16, right: 16, zIndex: 10, pointerEvents: 'none' }}>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                    Left Click: Select | Right Click: Pan | Scroll: Zoom
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {/* Right Column: Alerts & More Info */}
            <Grid item xs={12} md={3} sx={{ height: '100%' }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 2 }}>
                <StatCard
                  title="Avg Load"
                  value={stats.avg_load ? `${(stats.avg_load * 100).toFixed(1)}` : '0'}
                  unit="%"
                  color="#ff9100"
                  data={mockTrendData} // Reuse for demo
                />

                <Box sx={{ flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
                  <AlertFeed alerts={alerts} />
                </Box>
              </Box>
            </Grid>

          </Grid>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;
