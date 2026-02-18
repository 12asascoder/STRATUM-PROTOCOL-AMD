import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';

function InfrastructureNode({ node, position, onClick }) {
    const meshRef = useRef();
    const [hovered, setHovered] = useState(false);

    // Animate based on stress level
    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.rotation.y += 0.005;

            // Pulse effect for stressed nodes
            if (node.load_percentage > 0.8) {
                const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
                meshRef.current.scale.set(scale, scale, scale);
            }
        }
    });

    // Color based on health status
    const getColor = () => {
        if (node.load_percentage > 0.9) return '#ff1744'; // Critical
        if (node.load_percentage > 0.7) return '#ff9100'; // Warning
        return '#00e676'; // Healthy
    };

    return (
        <mesh
            ref={meshRef}
            position={position}
            onClick={(e) => {
                e.stopPropagation();
                onClick(node);
            }}
            onPointerOver={(e) => {
                e.stopPropagation();
                setHovered(true);
            }}
            onPointerOut={() => setHovered(false)}
        >
            <boxGeometry args={[1, 2, 1]} />
            <meshStandardMaterial
                color={getColor()}
                emissive={hovered ? '#ffffff' : '#000000'}
                emissiveIntensity={hovered ? 0.5 : 0}
                metalness={0.8}
                roughness={0.2}
            />

            {hovered && (
                <Html distanceFactor={10}>
                    <div style={{
                        background: 'rgba(10, 25, 41, 0.9)',
                        color: '#b2ebf2',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid rgba(0, 229, 255, 0.3)',
                        minWidth: '200px',
                        backdropFilter: 'blur(4px)',
                        boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
                    }}>
                        <strong style={{ color: '#fff', fontSize: '1.1em' }}>{node.name}</strong><br />
                        <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />
                        Type: {node.node_type}<br />
                        Load: <span style={{ color: getColor() }}>{(node.load_percentage * 100).toFixed(1)}%</span><br />
                        Capacity: {node.capacity}
                    </div>
                </Html>
            )}
        </mesh>
    );
}

export default InfrastructureNode;
