import Tts from 'react-native-tts';
import type { LanguageCode } from '../data/diseaseClasses';
import { LANGUAGES } from '../data/diseaseClasses';

// This IS the local-language voice interaction the hackathon brief asks
// for (§6: "at least one interaction is in a local language, by voice or
// text"). On-device TTS rather than pre-recorded clips: scales to any
// crop/disease/language combination without recording audio by hand, and
// works fully offline as long as the OS has that language's voice data
// installed (true on-device for most common languages on a modern phone;
// an uncommon language pack may need a one-time download the first time —
// exactly the trade-off this challenge asks entries to be upfront about).
//
// Every react-native-tts call below returns a Promise that routinely
// rejects in perfectly normal situations — iOS's setDefaultLanguage()
// rejects with "not_found" whenever AVSpeechSynthesisVoice doesn't have an
// exact match for the locale string (e.g. the Simulator not having "en-US"
// registered even though it can speak English fine under a different
// locale tag), and stop() rejects if nothing was speaking. None of that is
// a real error for this feature — it must never surface as an uncaught
// promise rejection (crashes the app with a red screen in dev), so every
// call here is explicitly caught.
function safeStop(): void {
  try {
    Tts.stop()?.catch(() => {});
  } catch {
    // Synchronous throw (e.g. native module not linked on this platform/
    // build) — still not a real error for this best-effort feature.
  }
}

// Returns a Promise so tests can await it; UI callers are free to fire and
// forget (speaking happens as a side effect, nothing to react to on the
// JS side once it's kicked off).
export async function speakRecommendedAction(text: string, language: LanguageCode): Promise<void> {
  const entry = LANGUAGES.find((l) => l.code === language);
  const locale = entry?.ttsLocale ?? 'en-US';

  safeStop();
  try {
    await Tts.setDefaultLanguage(locale);
  } catch {
    // Exact locale (e.g. "pt-BR") not registered on this device — retry
    // with just the bare language code, which is more likely to match.
    try {
      await Tts.setDefaultLanguage(entry?.code ?? 'en');
    } catch {
      // Still no match: fall through and speak with whatever the device's
      // current default voice is, rather than staying silent.
    }
  }
  try {
    Tts.speak(text);
  } catch {
    // Platform/native-module issue — this is the one place a failure means
    // the farmer gets no audio at all, but it must still never crash the app.
  }
}

export function stopSpeaking(): void {
  safeStop();
}
