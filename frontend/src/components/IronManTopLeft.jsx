import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { HUDPanel } from './HUDPanel';
import * as THREE from 'three';

const ArcReactor3D = () => {
  const groupRef = useRef();

  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.5;
      groupRef.current.rotation.z += delta * 0.2;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Core ring */}
      <mesh>
        <torusGeometry args={[1.5, 0.05, 16, 100]} />
        <meshBasicMaterial color="#00FFD1" wireframe={false} transparent opacity={0.8} />
      </mesh>
      {/* Inner geometric structure */}
      <mesh>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial color="#00FFD1" wireframe={true} transparent opacity={0.4} />
      </mesh>
      {/* Outer spinning ring */}
      <mesh rotation-x={Math.PI / 2}>
        <torusGeometry args={[1.8, 0.02, 16, 100]} />
        <meshBasicMaterial color="#4ade80" transparent opacity={0.5} />
      </mesh>
    </group>
  );
};

export const IronManTopLeft = () => {
  return (
    <HUDPanel title="MK-85 ARC REACTOR" className="h-48 overflow-hidden relative mb-4">
      <div className="absolute inset-0 pt-6 pointer-events-none flex items-center justify-center">
        <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
          <ArcReactor3D />
        </Canvas>
      </div>
      
      {/* Overlay UI elements to make it look like a scan */}
      <div className="absolute left-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-jarvis-cyan/50 pointer-events-none">
        <span>PWR: 98%</span>
        <span>THR: OPT</span>
        <span>ARM: ON</span>
      </div>
      <div className="absolute right-2 top-10 flex flex-col gap-1 text-[8px] font-mono text-jarvis-cyan/50 text-right pointer-events-none">
        <span>INT: 100%</span>
        <span>SYS: NRM</span>
        <span>AI: ON</span>
      </div>
    </HUDPanel>
  );
};
