import React from 'react';
import * as THREE from 'three';
import { OrbitControls, PerspectiveCamera, Stars } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import InfrastructureNode from './InfrastructureNode';

// Connection Lines between Infrastructure
function ConnectionLine({ start, end, strength }) {
    const points = [
        new THREE.Vector3(...start),
        new THREE.Vector3(...end)
    ];

    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);

    const color = strength > 0.7 ? '#00e676' : strength > 0.4 ? '#ff9100' : '#ff1744';

    return (
        <line geometry={lineGeometry}>
            <lineBasicMaterial color={color} linewidth={2} transparent opacity={0.6} />
        </line>
    );
}

function CityScene({ nodes, connections, onNodeClick }) {
    return (
        <>
            {/* Lighting */}
            <ambientLight intensity={0.2} />
            <pointLight position={[10, 10, 10]} intensity={1} color="#00e5ff" />
            <spotLight position={[-10, 20, 10]} angle={0.3} penumbra={1} intensity={2} color="#d500f9" />

            {/* Environment */}
            <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

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

            {/* Ground Plane Grid */}
            <gridHelper args={[100, 100, 0x00e5ff, 0x1a237e]} position={[0, -1, 0]} />

            {/* Post Processing */}
            <EffectComposer>
                <Bloom luminanceThreshold={0.5} luminanceSmoothing={0.9} height={300} intensity={1.5} />
            </EffectComposer>

            {/* Controls */}
            <OrbitControls
                enablePan={true}
                enableZoom={true}
                maxPolarAngle={Math.PI / 2.1} // Prevent going below ground
                minDistance={5}
                maxDistance={50}
                dampingFactor={0.05}
            />
            <PerspectiveCamera makeDefault position={[0, 20, 30]} />
        </>
    );
}

export default CityScene;
