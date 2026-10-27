import { useCallback, useEffect, useRef } from 'react';
import { useAppStore } from '../store';
import { useVisemeSync } from './useVisemeSync';

/**
 * Strips markdown symbols, asterisks, citations, and URLs so the TTS
 * produces clean, natural spoken audio.
 */
function cleanTextForSpeech(text: string): string {
  return text
    .replace(/\[\^?\d+\]/g, '') // remove citation brackets like [1]
    .replace(/\(http[s]?:\/\/[^\)]+\)/g, '') // remove markdown link targets
    .replace(/\[([^\]]+)\]/g, '$1') // keep markdown link text
    .replace(/[*_#`~>]/g, '') // remove markdown formatting
    .replace(/Terminal\s*(\d)/gi, 'Terminal $1')
    .replace(/\s+/g, ' ')
    .trim();
}

export function useTTSPlayer() {
  const { language, setIsSpeaking } = useAppStore();
  const { startSpeaking, stopSpeaking, getCurrentViseme } = useVisemeSync();
  const voicesRef = useRef<SpeechSynthesisVoice[]>([]);

  // Load available speech synthesis voices
  useEffect(() => {
    const updateVoices = () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        voicesRef.current = window.speechSynthesis.getVoices();
      }
    };

    updateVoices();
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }, []);

  const stop = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    stopSpeaking();
    setIsSpeaking(false);
  }, [stopSpeaking, setIsSpeaking]);

  const speak = useCallback(
    (rawText: string) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        console.warn('SpeechSynthesis not available in this browser environment');
        return;
      }

      // Stop any ongoing speech
      stop();

      const text = cleanTextForSpeech(rawText);
      if (!text) return;

      const utterance = new SpeechSynthesisUtterance(text);

      // Match voice based on current language
      const voices = voicesRef.current;
      let matchedVoice: SpeechSynthesisVoice | undefined;

      if (language === 'hi') {
        matchedVoice = voices.find((v) => v.lang.startsWith('hi') || v.name.includes('Hindi'));
        utterance.lang = 'hi-IN';
        utterance.rate = 0.95;
      } else if (language === 'es') {
        matchedVoice = voices.find((v) => v.lang.startsWith('es') || v.name.includes('Spanish'));
        utterance.lang = 'es-ES';
        utterance.rate = 1.0;
      } else {
        // English (prefer Indian English if available, fallback to UK/US)
        matchedVoice =
          voices.find((v) => v.lang === 'en-IN' || v.name.includes('India')) ||
          voices.find((v) => v.lang.startsWith('en'));
        utterance.lang = 'en-IN';
        utterance.rate = 1.0;
      }

      if (matchedVoice) {
        utterance.voice = matchedVoice;
      }

      utterance.pitch = 1.0;

      // Start viseme lip-syncing when audio actually starts playing
      utterance.onstart = () => {
        setIsSpeaking(true);
        startSpeaking(text, utterance.rate);
      };

      utterance.onend = () => {
        stopSpeaking();
        setIsSpeaking(false);
      };

      utterance.onerror = (e) => {
        console.error('Speech synthesis error:', e);
        stopSpeaking();
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance);
    },
    [language, stop, startSpeaking, stopSpeaking, setIsSpeaking]
  );

  return { speak, stop, getCurrentViseme };
}

