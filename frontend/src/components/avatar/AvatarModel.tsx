import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';
import { VISEME_NAMES } from './visemeMap';

interface AvatarModelProps {
  url: string;
  getCurrentViseme: () => { visemeName: string; weight: number };
  isSpeaking: boolean;
}

/**
 * Loads a photorealistic Ready Player Me / Avaturn 3D human avatar and drives its
 * facial blendshapes (morph targets) for realistic lip-sync in sync with voice output.
 *
 * Applies:
 * 1. Synchronized viseme morph targets on face, teeth, and tongue.
 * 2. Dynamic jaw opening & vowel shaping.
 * 3. Natural human eye blinking.
 * 4. Micro head-turn and natural breathing.
 */
export const AvatarModel: React.FC<AvatarModelProps> = ({ url, getCurrentViseme, isSpeaking }) => {
  const { scene, animations } = useGLTF(url);
  const { actions } = useAnimations(animations, scene);
  
  // Store all meshes with morph targets (Wolf3D_Head, Wolf3D_Teeth, EyeLeft, EyeRight, etc.)
  const morphMeshesRef = useRef<THREE.SkinnedMesh[]>([]);
  const headBoneRef = useRef<THREE.Bone | null>(null);
  const blinkTimerRef = useRef(0);
  const breathTimerRef = useRef(0);
  const prevWeightsRef = useRef<Record<string, number>>({});

  useEffect(() => {
    const meshes: THREE.SkinnedMesh[] = [];
    morphMeshesRef.current = meshes;

    scene.traverse((child) => {
      if ((child as THREE.SkinnedMesh).isSkinnedMesh) {
        const sm = child as THREE.SkinnedMesh;
        if (sm.morphTargetDictionary && sm.morphTargetInfluences) {
          meshes.push(sm);
        }
      }
      // Locate head bone for realistic micro-sway
      if ((child as THREE.Bone).isBone && child.name.toLowerCase().includes('head')) {
        headBoneRef.current = child as THREE.Bone;
      }
    });

    // Enable cast shadows
    scene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    // Play idle animation if present in the GLB
    if (actions && Object.keys(actions).length > 0) {
      const idleAction = actions['idle'] || actions['Idle'] || Object.values(actions)[0];
      if (idleAction) {
        idleAction.reset().fadeIn(0.5).play();
      }
    }
  }, [scene, actions, url]);

  useFrame((state, delta) => {
    const meshes = morphMeshesRef.current;
    if (!meshes.length) return;

    // ============================================
    // 1. LIP-SYNC VISEMES & JAW DROP
    // ============================================
    const { visemeName, weight } = getCurrentViseme();
    const lerpSpeed = Math.min(1, delta * 24); // fast, responsive facial reaction

    // Extra jaw opening for vowel visemes
    const isOpenVowel = ['viseme_aa', 'viseme_O', 'viseme_E', 'viseme_I', 'viseme_U'].includes(visemeName);
    const targetJawOpen = isOpenVowel ? weight * 0.45 : isSpeaking ? weight * 0.15 : 0;

    for (const vName of VISEME_NAMES) {
      const targetWeight = vName === visemeName ? weight * 0.85 : 0;
      const prevWeight = prevWeightsRef.current[vName] || 0;
      const newWeight = THREE.MathUtils.lerp(prevWeight, targetWeight, lerpSpeed);
      prevWeightsRef.current[vName] = newWeight;

      for (const mesh of meshes) {
        const dict = mesh.morphTargetDictionary;
        const influences = mesh.morphTargetInfluences;
        if (!dict || !influences) continue;

        const idx = dict[vName];
        if (idx !== undefined) {
          influences[idx] = newWeight;
        }
      }
    }

    // Apply jaw / mouth open across all target meshes
    for (const mesh of meshes) {
      const dict = mesh.morphTargetDictionary;
      const influences = mesh.morphTargetInfluences;
      if (!dict || !influences) continue;

      const jawIdx = dict['jawOpen'] ?? dict['JawOpen'] ?? dict['mouthOpen'];
      if (jawIdx !== undefined) {
        influences[jawIdx] = THREE.MathUtils.lerp(influences[jawIdx] || 0, targetJawOpen, lerpSpeed);
      }

      // Friendly subtle smile for customer service warmth
      const smileIdx = dict['mouthSmile'] ?? dict['mouthSmileLeft'] ?? dict['MouthSmile'];
      if (smileIdx !== undefined && !isSpeaking) {
        influences[smileIdx] = 0.15;
      }
    }

    // ============================================
    // 2. NATURAL HUMAN EYE BLINKING
    // ============================================
    blinkTimerRef.current += delta;
    const blinkInterval = 3.5 + Math.sin(state.clock.elapsedTime * 0.4); // every 2.5 - 4.5 seconds

    let blinkVal = 0;
    const blinkPhase = blinkTimerRef.current % blinkInterval;
    if (blinkPhase < 0.16) {
      blinkVal = blinkPhase < 0.08 ? blinkPhase / 0.08 : 1 - (blinkPhase - 0.08) / 0.08;
    }

    for (const mesh of meshes) {
      const dict = mesh.morphTargetDictionary;
      const influences = mesh.morphTargetInfluences;
      if (!dict || !influences) continue;

      const eyeL = dict['eyeBlinkLeft'] ?? dict['EyeBlinkLeft'] ?? dict['eyesClosed'];
      const eyeR = dict['eyeBlinkRight'] ?? dict['EyeBlinkRight'] ?? dict['eyesClosed'];
      if (eyeL !== undefined) influences[eyeL] = blinkVal;
      if (eyeR !== undefined) influences[eyeR] = blinkVal;
    }

    // ============================================
    // 3. HUMAN MICRO-MOVEMENTS & BREATHING
    // ============================================
    breathTimerRef.current += delta;
    const breath = Math.sin(breathTimerRef.current * 1.3) * 0.005;

    if (headBoneRef.current) {
      const t = state.clock.elapsedTime;
      // Gentle natural idle motion
      const idleHeadY = Math.sin(t * 0.4) * 0.02;
      const idleHeadX = Math.sin(t * 0.7) * 0.015 + breath;
      // Subtle conversational nods when speaking
      const speechNod = isSpeaking ? Math.sin(t * 4.0) * 0.02 : 0;

      headBoneRef.current.rotation.y = THREE.MathUtils.lerp(
        headBoneRef.current.rotation.y,
        idleHeadY,
        delta * 2
      );
      headBoneRef.current.rotation.x = THREE.MathUtils.lerp(
        headBoneRef.current.rotation.x,
        idleHeadX + speechNod,
        delta * 3
      );
    }
  });

  // Human upper-bust portrait framing: head is positioned right at y ≈ 0
  return <primitive object={scene} position={[0, -1.55, 0]} scale={1.0} />;
};

// Preload models for instant render
useGLTF.preload('/avatars/lck_assistant.glb');
useGLTF.preload('/avatars/avaturn.glb');
