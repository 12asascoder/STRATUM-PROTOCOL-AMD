import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

const StatCard = ({ title, value, unit, color = 'primary', subValue = null, data = [] }) => {
    return (
        <Card sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {title}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                        {value}
                    </Typography>
                    {unit && (
                        <Typography variant="h6" color="text.secondary" sx={{ ml: 0.5 }}>
                            {unit}
                        </Typography>
                    )}
                </Box>

                {subValue && (
                    <Typography variant="body2" color={subValue.includes('+') ? 'success.main' : 'error.main'}>
                        {subValue}
                    </Typography>
                )}

                {/* Sparkline */}
                {data.length > 0 && (
                    <Box sx={{ height: 60, mt: 'auto', mx: -2, mb: -2 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke={color}
                                    strokeWidth={2}
                                    dot={false}
                                    isAnimationActive={false}
                                />
                                {/* Hide axis but keep domain/range logic */}
                                <YAxis domain={['dataMin', 'dataMax']} hide />
                            </LineChart>
                        </ResponsiveContainer>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default StatCard;
