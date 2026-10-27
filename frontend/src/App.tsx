import React, { useEffect } from 'react';
import { useAppStore } from './store';
import { AvatarCanvas } from './components/avatar/AvatarCanvas';
import { TranscriptList } from './components/TranscriptList';
import { VoiceChatControls } from './components/voice/VoiceChatControls';
import { useTTSPlayer } from './hooks/useTTSPlayer';
import { Globe2, Cpu, ShieldCheck, Plane, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const { language, setLanguage, strategy, setStrategy, messages } = useAppStore();
  const { speak, stop, getCurrentViseme } = useTTSPlayer();

  // Auto-speak or provide welcome message trigger on first user interaction
  const handleTestSpeech = () => {
    const welcome =
      language === 'hi'
        ? 'नमस्ते! चौधरी चरण सिंह अंतर्राष्ट्रीय हवाई अड्डे पर आपका स्वागत है। मैं आपकी क्या सहायता कर सकता हूँ?'
        : language === 'es'
        ? '¡Hola! Bienvenido al Aeropuerto Internacional Chaudhary Charan Singh. ¿Cómo puedo ayudarte hoy?'
        : 'Namaste and welcome to Chaudhary Charan Singh International Airport, Lucknow. How may I assist your journey today?';
    speak(welcome);
  };

  // Stop TTS if user switches language mid-speech
  useEffect(() => {
    stop();
  }, [language, stop]);

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(14,116,144,0.35),rgba(2,6,23,0.95))] text-slate-100">
      {/* Top Header Bar */}
      <header className="border-b border-cyan-500/20 bg-slate-900/60 backdrop-blur-md px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between sticky top-0 z-50 gap-3">
        <div className="flex items-center gap-3">
          <img
            src="/app-icon.jpg"
            alt="LCK Logo"
            className="w-10 h-10 rounded-xl border border-cyan-400/50 shadow-md object-cover"
          />
          <div>
            <h1 className="text-base sm:text-lg font-bold text-white tracking-wide flex items-center gap-2">
              LCK Airport AI Assistant
              <span className="text-[11px] bg-cyan-950 text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded-full font-mono font-medium">
                LCK / VILK
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">
              Chaudhary Charan Singh International Airport, Lucknow
            </p>
          </div>
        </div>

        {/* Top Controls: Strategy & Multilingual Selectors */}
        <div className="flex items-center gap-3">
          {/* Strategy Selector (OKF / RAG) */}
          <div className="flex items-center bg-slate-900/90 border border-slate-700 rounded-xl p-1 text-xs">
            <button
              onClick={() => setStrategy('okf')}
              className={`px-3 py-1 rounded-lg transition-all font-semibold flex items-center gap-1.5 ${
                strategy === 'okf'
                  ? 'bg-cyan-500 text-slate-950 shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
              title="Open-Knowledge Full Context Strategy"
            >
              <Cpu className="w-3.5 h-3.5" />
              OKF
            </button>
            <button
              onClick={() => setStrategy('rag')}
              className={`px-3 py-1 rounded-lg transition-all font-semibold flex items-center gap-1.5 ${
                strategy === 'rag'
                  ? 'bg-cyan-500 text-slate-950 shadow-sm'
                  : 'text-slate-300 hover:text-white'
              }`}
              title="Retrieval-Augmented Generation Strategy"
            >
              <Cpu className="w-3.5 h-3.5" />
              RAG
            </button>
          </div>

          {/* Multilingual Selector */}
          <div className="flex items-center bg-slate-900/90 border border-slate-700 rounded-xl p-1 text-xs">
            <Globe2 className="w-4 h-4 text-cyan-400 ml-1.5 mr-1" />
            {(['en', 'hi', 'es'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setLanguage(lang)}
                className={`px-2.5 py-1 rounded-lg uppercase font-bold transition-all ${
                  language === lang
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Kiosk Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: 3D Photorealistic Human Avatar Canvas */}
        <section className="lg:col-span-5 flex flex-col gap-4">
          <AvatarCanvas
            getCurrentViseme={getCurrentViseme}
            onTestSpeech={handleTestSpeech}
          />

          {/* Assistant Info & Badges */}
          <div className="bg-slate-900/50 border border-cyan-500/15 rounded-2xl p-4 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-2 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Guardrail Safety Filter</span>
            </div>
            <div className="flex items-center gap-2">
              <Plane className="w-4 h-4 text-cyan-400" />
              <span>Real-time Viseme Lip-Sync</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>3D Ready Player Me / Avaturn</span>
            </div>
          </div>
        </section>

        {/* Right Column: Dialogue Transcripts & Voice Input */}
        <section className="lg:col-span-7 flex flex-col h-[520px] md:h-[580px] bg-slate-900/40 border border-cyan-500/20 rounded-3xl p-5 shadow-2xl backdrop-blur-md">
          <div className="pb-3 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Plane className="w-4 h-4 text-cyan-400" />
              Passenger Assistance Terminal
            </span>
            <span className="text-[11px] text-cyan-400/80">
              {messages.length} interaction{messages.length === 1 ? '' : 's'}
            </span>
          </div>

          {/* Scrollable Conversation Transcript */}
          <TranscriptList />

          {/* Voice Input & Query Bar */}
          <div className="pt-4 border-t border-slate-800/80 mt-2">
            <VoiceChatControls onSpeakResponse={(text) => speak(text)} />
          </div>
        </section>
      </main>
    </div>
  );
};
