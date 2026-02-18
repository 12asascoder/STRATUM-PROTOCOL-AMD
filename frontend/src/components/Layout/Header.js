import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Chip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SettingsIcon from '@mui/icons-material/Settings';

const Header = () => {
    return (
        <AppBar position="sticky" elevation={0} sx={{ zIndex: 1201 }}>
            <Toolbar>
                <IconButton
                    edge="start"
                    color="inherit"
                    aria-label="menu"
                    sx={{ mr: 2 }}
                >
                    <MenuIcon />
                </IconButton>

                <Typography variant="h6" component="div" sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
                    <Box component="span" sx={{ mr: 1, fontSize: '1.5rem' }}>🏙️</Box>
                    STRATUM PROTOCOL
                    <Chip
                        label="LIVE"
                        color="secondary"
                        size="small"
                        sx={{ ml: 2, height: 20, fontSize: '0.625rem' }}
                    />
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <IconButton color="inherit">
                        <NotificationsIcon />
                    </IconButton>
                    <IconButton color="inherit">
                        <SettingsIcon />
                    </IconButton>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Header;
