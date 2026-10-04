import Tts from 'react-native-tts';
import { speakRecommendedAction, stopSpeaking } from '../speak';

describe('speakRecommendedAction', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('speaks the given text', async () => {
    await speakRecommendedAction('Show this to your extension officer.', 'en');
    expect(Tts.speak).toHaveBeenCalledWith('Show this to your extension officer.');
  });

  it('sets the English TTS locale for language "en"', async () => {
    await speakRecommendedAction('hello', 'en');
    expect(Tts.setDefaultLanguage).toHaveBeenCalledWith('en-US');
  });

  it('sets the Portuguese TTS locale for language "pt"', async () => {
    await speakRecommendedAction('mostre ao extensionista', 'pt');
    expect(Tts.setDefaultLanguage).toHaveBeenCalledWith('pt-BR');
  });

  it('stops any in-progress speech before starting a new utterance', async () => {
    await speakRecommendedAction('hello', 'en');
    expect(Tts.stop).toHaveBeenCalled();
  });

  it('still speaks even if setDefaultLanguage rejects for every locale tried (common on devices missing that voice)', async () => {
    (Tts.setDefaultLanguage as jest.Mock).mockRejectedValue(new Error('not_found'));

    await speakRecommendedAction('hello', 'en');

    expect(Tts.setDefaultLanguage).toHaveBeenCalledWith('en-US'); // first try: full locale
    expect(Tts.setDefaultLanguage).toHaveBeenCalledWith('en'); // retry: bare language code
    expect(Tts.speak).toHaveBeenCalledWith('hello'); // still speaks, doesn't give up
  });

  it('never rejects, even when every TTS call fails', async () => {
    (Tts.stop as jest.Mock).mockRejectedValue(new Error('not_ready'));
    (Tts.setDefaultLanguage as jest.Mock).mockRejectedValue(new Error('not_found'));

    await expect(speakRecommendedAction('hello', 'en')).resolves.toBeUndefined();
  });
});

describe('stopSpeaking', () => {
  it('calls Tts.stop', () => {
    jest.clearAllMocks();
    stopSpeaking();
    expect(Tts.stop).toHaveBeenCalled();
  });

  it('does not throw even if Tts.stop rejects (nothing was speaking)', () => {
    (Tts.stop as jest.Mock).mockRejectedValue(new Error('not_ready'));
    expect(() => stopSpeaking()).not.toThrow();
  });

  it('does not throw even if Tts.stop throws synchronously (native module unavailable)', () => {
    (Tts.stop as jest.Mock).mockImplementation(() => {
      throw new Error('native module not linked');
    });
    expect(() => stopSpeaking()).not.toThrow();
  });
});
