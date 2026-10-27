import React, { useRef, useState } from 'react';
import { useAppStore } from '../../store';
import { Mic, MicOff, Send, Sparkles } from 'lucide-react';

interface VoiceChatControlsProps {
  onSpeakResponse: (text: string) => void;
}

export const VoiceChatControls: React.FC<VoiceChatControlsProps> = ({ onSpeakResponse }) => {
  const { 
    isListening, 
    setIsListening, 
    language, 
    strategy, 
    sessionId, 
    addMessage 
  } = useAppStore();

  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const recognitionRef = useRef<any>(null);

  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please type your query.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language === 'hi' ? 'hi-IN' : language === 'es' ? 'es-ES' : 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript) {
        handleSendQuery(transcript);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const handleSendQuery = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    addMessage({
      id: 'msg_' + Date.now(),
      sender: 'user',
      text: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    });

    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          strategy: strategy,
          language: language,
          session_id: sessionId,
          stream: false
        })
      });

      if (!response.ok) throw new Error(`Server returned ${response.status}`);

      const data = await response.json();

      addMessage({
        id: 'msg_res_' + Date.now(),
        sender: 'assistant',
        text: data.answer,
        strategy: data.strategy_used,
        citations: data.citations,
        abstained: data.abstained,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });

      // Trigger TTS + avatar lip-sync
      onSpeakResponse(data.answer);

    } catch (err: any) {
      addMessage({
        id: 'msg_err_' + Date.now(),
        sender: 'assistant',
        text: "I am having trouble connecting to the airport server. Please try again or visit an inquiry counter.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const quickQuestions = language === 'hi' 
    ? ["टर्मिनल 2 लाउंज कहाँ है?", "पार्किंग शुल्क क्या है?", "प्रार्थना कक्ष कहाँ है?"]
    : language === 'es'
    ? ["¿Dónde está la sala VIP?", "¿Tarifas de estacionamiento?", "¿Sala de oración?"]
    : ["Where is Terminal 2 lounge?", "Car parking tariffs?", "Allowed baggage items?", "Prayer rooms & medical?"];

  return (
    <div className="w-full max-w-3xl mx-auto flex flex-col gap-3">
      {/* Quick Airport Questions */}
      <div className="flex gap-2 overflow-x-auto pb-1 text-xs text-cyan-300 scrollbar-thin">
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSendQuery(q)}
            disabled={isLoading}
            className="whitespace-nowrap bg-slate-800/80 hover:bg-cyan-950/60 border border-cyan-500/20 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1.5 disabled:opacity-40"
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
            {q}
          </button>
        ))}
      </div>

      {/* Main Input Bar */}
      <div className="flex items-center gap-2 bg-slate-900/90 border border-cyan-500/30 p-2 rounded-2xl shadow-xl backdrop-blur-md">
        <button
          onClick={toggleListening}
          disabled={isLoading}
          className={`p-3 rounded-xl transition-all ${
            isListening 
              ? 'bg-rose-500 text-white animate-pulse shadow-lg shadow-rose-500/50' 
              : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-md shadow-cyan-500/30'
          } disabled:opacity-40`}
          title={isListening ? "Listening... Click to stop" : "Speak to Assistant"}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendQuery(inputText)}
          placeholder={isLoading ? "Thinking..." : isListening ? "Listening..." : "Ask about LCK Airport..."}
          disabled={isLoading}
          className="flex-1 bg-transparent px-3 py-2 text-white placeholder-slate-400 focus:outline-none text-sm md:text-base disabled:opacity-50"
        />

        {isLoading ? (
          <div className="p-3">
            <div className="w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
          </div>
        ) : (
          <button
            onClick={() => handleSendQuery(inputText)}
            disabled={!inputText.trim()}
            className="p-3 bg-slate-800 hover:bg-slate-700 text-cyan-400 disabled:opacity-40 rounded-xl transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};

