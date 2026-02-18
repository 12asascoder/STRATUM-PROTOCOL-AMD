import { createTheme } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        mode: 'dark',
        background: {
            default: '#0a1929', // Deep blue-black
            paper: '#132f4c',   // Slightly lighter blue for cards
        },
        primary: {
            main: '#00e5ff', // Cyan accent
            contrastText: '#000',
        },
        secondary: {
            main: '#d500f9', // Neon purple accent
        },
        error: {
            main: '#ff1744',
        },
        warning: {
            main: '#ff9100',
        },
        success: {
            main: '#00e676',
        },
        text: {
            primary: '#fff',
            secondary: '#b2ebf2', // Soft cyan-tinted white
        },
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: {
            fontWeight: 700,
        },
        h2: {
            fontWeight: 700,
        },
        h3: {
            fontWeight: 600,
        },
        h4: {
            fontWeight: 600,
            fontFamily: '"Roboto Mono", monospace', // Data-focused headers
        },
        h5: {
            fontWeight: 600,
            letterSpacing: '0.1em',
        },
        h6: {
            fontWeight: 600,
            textTransform: 'uppercase',
            fontSize: '0.875rem',
            letterSpacing: '0.15em',
        },
        subtitle1: {
            color: '#b2ebf2',
        },
        body1: {
            lineHeight: 1.6,
        },
        body2: {
            lineHeight: 1.5,
            color: '#90caf9',
        },
        button: {
            fontWeight: 600,
            textTransform: 'none',
            letterSpacing: '0.05em',
        },
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    scrollbarColor: "#6b6b6b #2b2b2b",
                    "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
                        backgroundColor: "#2b2b2b",
                    },
                    "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
                        borderRadius: 8,
                        backgroundColor: "#6b6b6b",
                        minHeight: 24,
                        border: "3px solid #2b2b2b",
                    },
                    "&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus": {
                        backgroundColor: "#959595",
                    },
                    "&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active": {
                        backgroundColor: "#959595",
                    },
                    "&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover": {
                        backgroundColor: "#959595",
                    },
                    "&::-webkit-scrollbar-corner, & *::-webkit-scrollbar-corner": {
                        backgroundColor: "#2b2b2b",
                    },
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    background: 'rgba(19, 47, 76, 0.7)', // Semi-transparent
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 12,
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    textTransform: 'uppercase',
                    fontWeight: 'bold',
                    padding: '8px 20px',
                },
                containedPrimary: {
                    background: 'linear-gradient(45deg, #00e5ff 30%, #00b0ff 90%)',
                    boxShadow: '0 3px 5px 2px rgba(0, 229, 255, .3)',
                },
            },
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    background: 'rgba(10, 25, 41, 0.7)',
                    backdropFilter: 'blur(20px)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    boxShadow: 'None',
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: 6,
                    fontWeight: 600,
                },
            },
        },
    },
});

export default theme;
