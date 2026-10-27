import { useRef, useCallback } from 'react';
import { VISEME_NAMES, VisemeCue, generateVisemeCuesFromText } from '../components/avatar/visemeMap';

interface VisemeSyncState {
  isActive: boolean;
  currentVisemeIndex: number;
  cues: VisemeCue[];
  startTime: number;
}

/**
 * Hook that drives avatar lip-sync by generating viseme cues from text
 * and providing a method to query the current viseme at any point in time.
 *
 * Usage in the render loop:
 *   const { getCurrentViseme, startSpeaking, stopSpeaking } = useVisemeSync();
 *   useFrame(() => { const v = getCurrentViseme(); ... });
 */
export function useVisemeSync() {
  const stateRef = useRef<VisemeSyncState>({
    isActive: false,
    currentVisemeIndex: 0,
    cues: [],
    startTime: 0,
  });

  const startSpeaking = useCallback((text: string, speechRate: number = 1.0) => {
    // Estimate WPM based on speech rate
    const wpm = 150 * speechRate;
    const cues = generateVisemeCuesFromText(text, wpm);
    stateRef.current = {
      isActive: true,
      currentVisemeIndex: 0,
      cues,
      startTime: performance.now(),
    };
  }, []);

  const stopSpeaking = useCallback(() => {
    stateRef.current.isActive = false;
    stateRef.current.currentVisemeIndex = 0;
    stateRef.current.cues = [];
  }, []);

  /**
   * Call this every frame (inside useFrame) to get the current viseme.
   * Returns { visemeName, weight } where weight is 0-1.
   */
  const getCurrentViseme = useCallback((): { visemeName: string; weight: number } => {
    const state = stateRef.current;

    if (!state.isActive || state.cues.length === 0) {
      return { visemeName: VISEME_NAMES[0], weight: 0 };
    }

    const elapsed = performance.now() - state.startTime;

    // Find the current cue
    let activeCue: VisemeCue | null = null;
    for (let i = state.cues.length - 1; i >= 0; i--) {
      if (elapsed >= state.cues[i].time) {
        activeCue = state.cues[i];
        break;
      }
    }

    if (!activeCue) {
      return { visemeName: VISEME_NAMES[0], weight: 0 };
    }

    // Check if we've passed the last cue entirely
    const lastCue = state.cues[state.cues.length - 1];
    if (elapsed > lastCue.time + lastCue.duration) {
      state.isActive = false;
      return { visemeName: VISEME_NAMES[0], weight: 0 };
    }

    // Calculate weight with smooth attack/release envelope
    const cueElapsed = elapsed - activeCue.time;
    const attackMs = 40;   // ramp up
    const releaseMs = 60;  // ramp down

    let weight = 1.0;
    if (cueElapsed < attackMs) {
      weight = cueElapsed / attackMs; // ramp up
    } else if (cueElapsed > activeCue.duration - releaseMs) {
      weight = Math.max(0, (activeCue.duration - cueElapsed) / releaseMs); // ramp down
    }

    // Silence viseme gets reduced weight
    if (activeCue.visemeIndex === 0) {
      weight *= 0.1;
    }

    const visemeName = VISEME_NAMES[activeCue.visemeIndex] || VISEME_NAMES[0];
    return { visemeName, weight: Math.min(1, Math.max(0, weight)) };
  }, []);

  return { startSpeaking, stopSpeaking, getCurrentViseme };
}

