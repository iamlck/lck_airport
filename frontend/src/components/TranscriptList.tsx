import React, { useRef, useEffect } from 'react';
import { useAppStore } from '../store';
import { User, CheckCircle2 } from 'lucide-react';

export const TranscriptList: React.FC = () => {
  const { messages } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto pr-2 space-y-4 max-h-[460px]">
      {messages.map((m) => (
        <div
          key={m.id}
          className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          {m.sender === 'assistant' && (
            <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 border border-cyan-400/50 shadow-sm mt-1">
              <img src="/app-icon.jpg" alt="LCK Bot" className="w-full h-full object-cover" />
            </div>
          )}

          <div
            className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-lg ${
              m.sender === 'user'
                ? 'bg-gradient-to-r from-sky-600 to-blue-700 text-white rounded-tr-none'
                : 'bg-slate-900/80 border border-cyan-500/20 text-slate-100 rounded-tl-none'
            }`}
          >
            <p className="whitespace-pre-wrap">{m.text}</p>

            {/* Citations and metadata */}
            {m.citations && m.citations.length > 0 && (
              <div className="mt-3 pt-2 border-t border-slate-700/60 text-xs text-cyan-300">
                <span className="font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                  Verified Airport Document:
                </span>
                <span className="italic block mt-0.5 text-slate-300">{m.citations[0].document_title}</span>
              </div>
            )}

            <div className="mt-2 text-[10px] text-right opacity-60">
              {m.timestamp} {m.strategy && `• [${m.strategy.toUpperCase()}]`}
            </div>
          </div>

          {m.sender === 'user' && (
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 text-cyan-300 mt-1">
              <User className="w-4 h-4" />
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

