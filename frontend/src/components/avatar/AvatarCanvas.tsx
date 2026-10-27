import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { AvatarModel } from './AvatarModel';
import { useAppStore } from '../../store';
import { Volume2, UserCheck, RefreshCw } from 'lucide-react';

interface AvatarCanvasProps {
  getCurrentViseme: () => { visemeName: string; weight: number };
  onTestSpeech?: () => void;
}

const AvatarLoadingSpinner: React.FC = () => (
  <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm z-30">
    <div className="w-12 h-12 border-3 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-3" />
    <p className="text-xs font-semibold text-cyan-300">Loading 3D Human Avatar...</p>
    <p className="text-[10px] text-slate-400 mt-1">Initializing facial blendshapes & visemes</p>
  </div>
);

export const AvatarCanvas: React.FC<AvatarCanvasProps> = ({ getCurrentViseme, onTestSpeech }) => {
  const { isSpeaking, isListening } = useAppStore();
  const [modelType, setModelType] = useState<'female' | 'avaturn'>('female');

  const modelUrl = modelType === 'female' ? '/avatars/lck_assistant.glb' : '/avatars/avaturn.glb';

  return (
    <div className="relative w-full h-[460px] md:h-[520px] rounded-3xl overflow-hidden bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border border-cyan-500/30 shadow-2xl flex flex-col">
      {/* Outer Glow Halo on Speech */}
      <div
        className={`absolute inset-0 transition-opacity duration-500 pointer-events-none z-10 ${
          isSpeaking
            ? 'opacity-100 shadow-[inset_0_0_60px_rgba(6,182,212,0.3)]'
            : isListening
            ? 'opacity-100 shadow-[inset_0_0_60px_rgba(245,158,11,0.25)]'
            : 'opacity-0'
        }`}
      />

      {/* Top Header Badge & Model Switcher */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20 pointer-events-auto">
        <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-md border border-cyan-500/30 px-3 py-1.5 rounded-full shadow-lg">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-white tracking-wide">LCK Passenger Officer</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping ml-1" />
        </div>

        <div className="flex items-center gap-2">
          {onTestSpeech && (
            <button
              onClick={onTestSpeech}
              disabled={isSpeaking}
              className="text-xs bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-300 px-3 py-1.5 rounded-full transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md"
              title="Test Voice & Lip-sync"
            >
              <Volume2 className="w-3.5 h-3.5" />
              <span>Test Voice</span>
            </button>
          )}

          <button
            onClick={() => setModelType((prev) => (prev === 'female' ? 'avaturn' : 'female'))}
            className="text-xs bg-slate-800/80 hover:bg-slate-700 border border-slate-600 text-slate-200 px-2.5 py-1.5 rounded-full transition-all flex items-center gap-1 shadow-md"
            title="Switch Human Avatar Model"
          >
            <RefreshCw className="w-3 h-3 text-cyan-400" />
            <span className="hidden sm:inline">{modelType === 'female' ? 'Officer 1' : 'Officer 2'}</span>
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div className="flex-1 w-full h-full relative">
        <Suspense fallback={<AvatarLoadingSpinner />}>
          <Canvas
            camera={{ position: [0, 0, 0.95], fov: 32 }}
            gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
            style={{ width: '100%', height: '100%' }}
          >
            {/* Ambient Lighting */}
            <ambientLight intensity={0.8} />

            {/* Key Light */}
            <directionalLight position={[2, 3, 3]} intensity={1.5} castShadow />

            {/* Soft Fill Light */}
            <directionalLight position={[-2, 1, 2]} intensity={0.7} color="#a5f3fc" />

            {/* Cyber / Aviation Cyan Rim Light from behind */}
            <pointLight position={[0, 2, -2]} intensity={1.2} color="#06b6d4" />

            {/* Studio Environment for realistic skin & eyes reflection */}
            <Environment preset="city" />

            {/* Avatar Human Model */}
            <AvatarModel
              key={modelUrl}
              url={modelUrl}
              getCurrentViseme={getCurrentViseme}
              isSpeaking={isSpeaking}
            />

            {/* Floor Contact Shadow */}
            <ContactShadows position={[0, -1.55, 0]} opacity={0.5} scale={4} blur={2.5} />

            {/* Orbit Controls (constrained to front-facing angles) */}
            <OrbitControls
              enableZoom={false}
              enablePan={false}
              minPolarAngle={Math.PI / 2.3}
              maxPolarAngle={Math.PI / 1.8}
              minAzimuthAngle={-Math.PI / 5}
              maxAzimuthAngle={Math.PI / 5}
              target={[0, 0.05, 0]}
            />
          </Canvas>
        </Suspense>
      </div>

      {/* Status Overlay Indicator */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 z-20 pointer-events-none">
        {isSpeaking && (
          <div className="bg-gradient-to-r from-cyan-500 to-sky-500 text-slate-950 px-4 py-1.5 rounded-full text-xs font-extrabold uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-cyan-500/40 animate-pulse">
            <Volume2 className="w-4 h-4 animate-bounce" />
            Speaking & Lip-Syncing
          </div>
        )}
        {isListening && !isSpeaking && (
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 px-4 py-1.5 rounded-full text-xs font-extrabold uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-amber-500/40 animate-pulse">
            🎤 Listening to query...
          </div>
        )}
      </div>
    </div>
  );
};
