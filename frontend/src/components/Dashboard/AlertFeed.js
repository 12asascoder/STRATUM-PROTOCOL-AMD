import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, Chip, alpha, useTheme } from '@mui/material';

const AlertFeed = ({ alerts }) => {
    const theme = useTheme();

    return (
        <Box sx={{
            height: '100%',
            overflowY: 'auto',
            p: 2,
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: 1
        }}>
            <Typography variant="h6" gutterBottom>
                System Alerts
            </Typography>

            {alerts.length === 0 ? (
                <Typography color="text.secondary" align="center" sx={{ mt: 4 }}>
                    No Active Alerts
                </Typography>
            ) : (
                <List>
                    {alerts.map((alert, index) => (
                        <ListItem
                            key={index}
                            sx={{
                                mb: 1,
                                background: alpha(theme.palette[alert.severity].main, 0.1),
                                borderLeft: `4px solid ${theme.palette[alert.severity].main}`,
                                borderRadius: 1
                            }}
                        >
                            <ListItemText
                                primary={alert.message}
                                secondary={new Date(alert.timestamp).toLocaleTimeString()}
                                primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                                secondaryTypographyProps={{ variant: 'caption', color: 'text.secondary' }}
                            />
                            <Chip
                                label={alert.severity.toUpperCase()}
                                color={alert.severity}
                                size="small"
                                variant="outlined"
                            />
                        </ListItem>
                    ))}
                </List>
            )}
        </Box>
    );
};

export default AlertFeed;
