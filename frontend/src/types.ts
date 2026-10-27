export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  strategy?: string;
  citations?: Array<{
    document_title: string;
    snippet: string;
  }>;
  abstained?: boolean;
}

export type LanguageCode = 'en' | 'hi' | 'es';

export interface AppState {
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
}

