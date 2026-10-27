import { create } from 'zustand';
import { LanguageCode, Message } from './types';

interface AppState {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  strategy: 'okf' | 'rag';
  setStrategy: (strat: 'okf' | 'rag') => void;
  sessionId: string;
  messages: Message[];
  addMessage: (msg: Message) => void;
  isListening: boolean;
  setIsListening: (listening: boolean) => void;
  isSpeaking: boolean;
  setIsSpeaking: (speaking: boolean) => void;
  currentSpeechText: string;
  setCurrentSpeechText: (text: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  language: 'en',
  setLanguage: (lang: LanguageCode) => set({ language: lang }),
  strategy: 'okf',
  setStrategy: (strat: 'okf' | 'rag') => set({ strategy: strat }),
  sessionId: 'session_' + Math.random().toString(36).substring(2, 9),
  messages: [
    {
      id: 'init_welcome',
      sender: 'assistant',
      text: 'Namaste! Welcome to Chaudhary Charan Singh International Airport (LCK). How may I assist your journey today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ],
  addMessage: (msg: Message) => set((state) => ({ messages: [...state.messages, msg] })),
  isListening: false,
  setIsListening: (listening: boolean) => set({ isListening: listening }),
  isSpeaking: false,
  setIsSpeaking: (speaking: boolean) => set({ isSpeaking: speaking }),
  currentSpeechText: '',
  setCurrentSpeechText: (text: string) => set({ currentSpeechText: text }),
}));
