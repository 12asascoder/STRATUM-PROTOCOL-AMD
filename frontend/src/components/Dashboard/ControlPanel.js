import React from 'react';
import {
    Paper, Typography, Box, Button, Slider, FormControlLabel, Switch, Grid, Chip
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AutoModeIcon from '@mui/icons-material/AutoMode';

const ControlPanel = ({ selectedNode, onRunSimulation }) => {
    const handleSimulation = () => {
        if (selectedNode) {
            onRunSimulation(selectedNode);
        }
    };

    return (
        <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoModeIcon color="primary" /> Simulation Controls
            </Typography>

            <Box sx={{ my: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Selected Infrastructure Node
                </Typography>
                {selectedNode ? (
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1, border: '1px solid rgba(255,255,255,0.1)' }}>
                        <Typography variant="h6" color="primary">{selectedNode.name}</Typography>
                        <Typography variant="body2" color="text.secondary">ID: {selectedNode.node_id}</Typography>
                        <Typography variant="body2" color="text.secondary">Type: {selectedNode.node_type}</Typography>
                        <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                            <Chip label={selectedNode.status} size="small" color={selectedNode.status === 'operational' ? 'success' : 'warning'} />
                            <Chip label={`Load: ${(selectedNode.load_percentage * 100).toFixed(0)}%`} size="small" variant="outlined" />
                        </Box>
                    </Box>
                ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                        Select a node from the 3D map to configure simulations.
                    </Typography>
                )}
            </Box>

            <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>Cascade Probability Threshold</Typography>
                <Slider defaultValue={75} aria-label="Default" valueLabelDisplay="auto" />
            </Box>

            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <FormControlLabel control={<Switch defaultChecked />} label="Auto-Stop on Critical Failure" />
                </Grid>
                <Grid item xs={12}>
                    <Button
                        fullWidth
                        variant="contained"
                        startIcon={<PlayArrowIcon />}
                        disabled={!selectedNode}
                        onClick={handleSimulation}
                        sx={{ py: 1.5 }}
                    >
                        Run Cascade Simulation
                    </Button>
                </Grid>
            </Grid>
        </Paper>
    );
};

export default ControlPanel;
