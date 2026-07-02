import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const particleCount = 2000;

const generatePositions = (count) => {
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 2.5 + Math.random() * 0.1;
      
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
  }
  return pos;
};

const staticPositions = generatePositions(particleCount);

const ParticleSphere = () => {
  const pointsRef = useRef();
  const positions = staticPositions;

  useFrame((state, delta) => {
    if (pointsRef.current) {
        pointsRef.current.rotation.y += delta * 0.15;
        pointsRef.current.rotation.x += delta * 0.05;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute 
            attach="attributes-position" 
            count={particleCount} 
            array={positions} 
            itemSize={3} 
        />
      </bufferGeometry>
      <pointsMaterial 
        size={0.03} 
        color="#00FFD1" 
        transparent={true} 
        opacity={0.8}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
};

const WireframeSphere = () => {
  const meshRef = useRef();
  
  useFrame((state, delta) => {
    if (meshRef.current) {
        meshRef.current.rotation.y -= delta * 0.1;
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[2.4, 16, 16]} />
      <meshBasicMaterial 
        color="#00FFD1" 
        wireframe={true} 
        transparent={true} 
        opacity={0.15} 
      />
    </mesh>
  );
};

export const Globe3D = () => {
  return (
    <div className="w-full h-full absolute top-0 left-0 -z-10 flex items-center justify-center pointer-events-none">
      <Canvas camera={{ position: [0, 0, 7], fov: 45 }}>
        <ParticleSphere />
        <WireframeSphere />
      </Canvas>
      {/* Center Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-jarvis-cyan/10 rounded-full blur-3xl pointer-events-none"></div>
    </div>
  );
};
