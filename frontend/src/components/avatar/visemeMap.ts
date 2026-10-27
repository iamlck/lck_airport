/**
 * Viseme constants and mapping for Ready Player Me / ARKit blendshapes.
 * Maps phoneme groups to the corresponding morph target names on the 3D model.
 */

// Standard 15 viseme names used by Ready Player Me avatars
export const VISEME_NAMES = [
  'viseme_sil',  // 0  - Silence / Mouth closed
  'viseme_PP',   // 1  - P, B, M
  'viseme_FF',   // 2  - F, V
  'viseme_TH',   // 3  - TH
  'viseme_DD',   // 4  - T, D, S, Z
  'viseme_kk',   // 5  - K, G
  'viseme_CH',   // 6  - CH, J, SH
  'viseme_SS',   // 7  - S, Z (sibilant)
  'viseme_nn',   // 8  - N, L
  'viseme_RR',   // 9  - R
  'viseme_aa',   // 10 - AA, AH
  'viseme_E',    // 11 - EH, EY
  'viseme_I',    // 12 - IH, IY
  'viseme_O',    // 13 - OW, AO
  'viseme_U',    // 14 - UW, UH
] as const;

export type VisemeName = typeof VISEME_NAMES[number];

// Phoneme-to-viseme mapping (CMU / IPA to viseme index)
export const PHONEME_TO_VISEME: Record<string, number> = {
  // Silence
  'sil': 0, 'sp': 0, 'SIL': 0,
  // Bilabial plosives & nasals
  'P': 1, 'B': 1, 'M': 1, 'p': 1, 'b': 1, 'm': 1,
  // Labiodental fricatives
  'F': 2, 'V': 2, 'f': 2, 'v': 2,
  // Dental fricatives
  'TH': 3, 'DH': 3,
  // Alveolar plosives & fricatives
  'T': 4, 'D': 4, 't': 4, 'd': 4,
  // Velar plosives
  'K': 5, 'G': 5, 'k': 5, 'g': 5,
  // Post-alveolar affricates & fricatives
  'CH': 6, 'JH': 6, 'SH': 6, 'ZH': 6,
  // Sibilants
  'S': 7, 'Z': 7, 's': 7, 'z': 7,
  // Alveolar nasals & laterals
  'N': 8, 'L': 8, 'n': 8, 'l': 8,
  // Retroflex
  'R': 9, 'r': 9,
  // Vowels
  'AA': 10, 'AH': 10, 'AE': 10,
  'EH': 11, 'EY': 11,
  'IH': 12, 'IY': 12,
  'AO': 13, 'OW': 13,
  'UW': 14, 'UH': 14,
};

/**
 * Simple heuristic: given a character of text being spoken,
 * estimate a viseme index. This is used as a fallback when
 * no phoneme-level timing data is available (e.g., Web Speech API TTS).
 */
export function charToVisemeIndex(char: string): number {
  const c = char.toLowerCase();
  if ('aà'.includes(c)) return 10; // aa
  if ('eèé'.includes(c)) return 11; // E
  if ('iìí'.includes(c)) return 12; // I
  if ('oòó'.includes(c)) return 13; // O
  if ('uùú'.includes(c)) return 14; // U
  if ('pbm'.includes(c)) return 1;  // PP
  if ('fv'.includes(c)) return 2;   // FF
  if ('td'.includes(c)) return 4;   // DD
  if ('kg'.includes(c)) return 5;   // kk
  if ('sz'.includes(c)) return 7;   // SS
  if ('nl'.includes(c)) return 8;   // nn
  if ('r'.includes(c)) return 9;    // RR
  if ('jy'.includes(c)) return 6;   // CH
  if (' .,!?;:-'.includes(c)) return 0; // silence
  return 10; // default open mouth for unknown
}

/**
 * Generate a sequence of viseme cues from plain text with estimated timing.
 * Each cue: { time: ms_from_start, visemeIndex: number, duration: ms }
 */
export interface VisemeCue {
  time: number;
  visemeIndex: number;
  duration: number;
}

export function generateVisemeCuesFromText(
  text: string,
  wordsPerMinute: number = 150,
  startOffsetMs: number = 0
): VisemeCue[] {
  const cues: VisemeCue[] = [];
  
  // Average character duration based on speaking speed
  const charsPerSecond = (wordsPerMinute * 5) / 60; // ~5 chars per word
  const charDurationMs = 1000 / charsPerSecond;

  let currentTime = startOffsetMs;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const visemeIndex = charToVisemeIndex(char);

    // Merge consecutive same-viseme cues
    const lastCue = cues[cues.length - 1];
    if (lastCue && lastCue.visemeIndex === visemeIndex) {
      lastCue.duration += charDurationMs;
    } else {
      cues.push({
        time: currentTime,
        visemeIndex,
        duration: charDurationMs,
      });
    }

    currentTime += charDurationMs;
  }

  return cues;
}

