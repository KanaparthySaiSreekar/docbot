import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface DNAHelixProps {
  basePairs?: number;
}

export function DNAHelix({ basePairs: basePairsProp }: DNAHelixProps) {
  const groupRef = useRef<THREE.Group>(null);

  const { spheres, bonds } = useMemo(() => {
    const sphereData: { position: [number, number, number]; color: string }[] = [];
    const bondData: { start: [number, number, number]; end: [number, number, number] }[] = [];

    const basePairs = basePairsProp ?? 30;
    const radius = 1.2;
    const ySpacing = 0.4;
    const offset = (basePairs * ySpacing) / 2;

    for (let i = 0; i < basePairs; i++) {
      const angle = (i / basePairs) * Math.PI * 4;
      const y = i * ySpacing - offset;

      // Strand 1
      const x1 = Math.cos(angle) * radius;
      const z1 = Math.sin(angle) * radius;

      // Strand 2 (opposite)
      const x2 = Math.cos(angle + Math.PI) * radius;
      const z2 = Math.sin(angle + Math.PI) * radius;

      const color1 = i % 2 === 0 ? '#14b8a6' : '#0d9488';
      const color2 = i % 2 === 0 ? '#3b82f6' : '#2563eb';

      sphereData.push({ position: [x1, y, z1], color: color1 });
      sphereData.push({ position: [x2, y, z2], color: color2 });

      // Bond connecting the pair
      if (i % 2 === 0) {
        bondData.push({
          start: [x1, y, z1],
          end: [x2, y, z2],
        });
      }
    }

    return { spheres: sphereData, bonds: bondData };
  }, [basePairsProp]);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.3;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Nucleotide spheres */}
      {spheres.map((sphere, i) => (
        <mesh key={`sphere-${i}`} position={sphere.position}>
          <sphereGeometry args={[0.12, 16, 16]} />
          <meshStandardMaterial color={sphere.color} roughness={0.3} metalness={0.1} />
        </mesh>
      ))}

      {/* Bonds */}
      {bonds.map((bond, i) => {
        const start = new THREE.Vector3(...bond.start);
        const end = new THREE.Vector3(...bond.end);
        const mid = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        const dir = end.clone().sub(start).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);

        return (
          <mesh key={`bond-${i}`} position={mid} quaternion={quat}>
            <cylinderGeometry args={[0.02, 0.02, length, 8]} />
            <meshStandardMaterial color="#d6d3d1" roughness={0.5} transparent opacity={0.6} />
          </mesh>
        );
      })}

      {/* Backbone connections - strand 1 */}
      {spheres.filter((_, i) => i % 2 === 0).map((sphere, i, arr) => {
        if (i >= arr.length - 1) return null;
        const start = new THREE.Vector3(...sphere.position);
        const end = new THREE.Vector3(...arr[i + 1].position);
        const mid = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        const dir = end.clone().sub(start).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);

        return (
          <mesh key={`backbone1-${i}`} position={mid} quaternion={quat}>
            <cylinderGeometry args={[0.04, 0.04, length, 8]} />
            <meshStandardMaterial color="#14b8a6" roughness={0.4} metalness={0.1} />
          </mesh>
        );
      })}

      {/* Backbone connections - strand 2 */}
      {spheres.filter((_, i) => i % 2 === 1).map((sphere, i, arr) => {
        if (i >= arr.length - 1) return null;
        const start = new THREE.Vector3(...sphere.position);
        const end = new THREE.Vector3(...arr[i + 1].position);
        const mid = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        const dir = end.clone().sub(start).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);

        return (
          <mesh key={`backbone2-${i}`} position={mid} quaternion={quat}>
            <cylinderGeometry args={[0.04, 0.04, length, 8]} />
            <meshStandardMaterial color="#3b82f6" roughness={0.4} metalness={0.1} />
          </mesh>
        );
      })}

      {/* Floating particles */}
      {Array.from({ length: 30 }).map((_, i) => {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;
        const r = 2.5 + Math.random() * 1.5;
        return (
          <mesh
            key={`particle-${i}`}
            position={[
              r * Math.sin(phi) * Math.cos(theta),
              (Math.random() - 0.5) * 6,
              r * Math.sin(phi) * Math.sin(theta),
            ]}
          >
            <sphereGeometry args={[0.03, 8, 8]} />
            <meshStandardMaterial
              color={i % 2 === 0 ? '#14b8a6' : '#3b82f6'}
              transparent
              opacity={0.4}
            />
          </mesh>
        );
      })}
    </group>
  );
}
