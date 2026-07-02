import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { HUDPanel } from './HUDPanel';
import * as THREE from 'three';

const QuantumCore = () => {
  const groupRef = useRef();
  
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y -= delta * 0.4;
      groupRef.current.rotation.x += delta * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Neural Core */}
      <mesh>
        <dodecahedronGeometry args={[1.2, 1]} />
        <meshBasicMaterial color="#3b82f6" wireframe={true} transparent opacity={0.5} />
      </mesh>
      {/* Inner Processing Node */}
      <mesh>
        <octahedronGeometry args={[0.7, 0]} />
        <meshBasicMaterial color="#60a5fa" transparent opacity={0.8} />
      </mesh>
      {/* Outer Data Rings */}
      <mesh rotation-x={Math.PI / 3} rotation-y={Math.PI / 4}>
        <torusGeometry args={[1.6, 0.01, 16, 100]} />
        <meshBasicMaterial color="#00FFD1" transparent opacity={0.6} />
      </mesh>
      <mesh rotation-x={-Math.PI / 3} rotation-y={-Math.PI / 4}>
        <torusGeometry args={[1.6, 0.01, 16, 100]} />
        <meshBasicMaterial color="#00FFD1" transparent opacity={0.6} />
      </mesh>
    </group>
  );
};

export const NeuralCore3D = () => {
  return (
    <HUDPanel title="NEURAL COGNITIVE CORE" className="h-48 overflow-hidden relative mb-4" borderColor="border-blue-500/30">
      <div className="absolute inset-0 pt-6 pointer-events-none flex items-center justify-center">
        <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
          <QuantumCore />
        </Canvas>
      </div>
      
      {/* Overlay UI elements to make it look like a scan */}
      <div className="absolute left-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-blue-400/60 pointer-events-none">
        <span>SYNC: 99%</span>
        <span>LLM: ACT</span>
        <span>NLP: ON</span>
      </div>
      <div className="absolute right-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-blue-400/60 text-right pointer-events-none">
        <span>MEM: 12TB</span>
        <span>LAT: 12ms</span>
        <span>NET: LCL</span>
      </div>
    </HUDPanel>
  );
};
