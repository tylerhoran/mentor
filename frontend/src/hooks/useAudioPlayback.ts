import { useState, useCallback, useRef } from 'react';

interface AudioPlaybackState {
  isPlaying: boolean;
  duration: number;
  currentTime: number;
  error: string | null;
}

interface UseAudioPlaybackOptions {
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
  onError?: (error: string) => void;
}

export function useAudioPlayback(options: UseAudioPlaybackOptions = {}) {
  const { onPlayStart, onPlayEnd, onError } = options;

  const [state, setState] = useState<AudioPlaybackState>({
    isPlaying: false,
    duration: 0,
    currentTime: 0,
    error: null,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const startTimeRef = useRef<number>(0);
  const audioBufferRef = useRef<AudioBuffer | null>(null);

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      audioContextRef.current = new AudioContext();
    }
    return audioContextRef.current;
  }, []);

  const playAudio = useCallback(async (audioData: ArrayBuffer): Promise<void> => {
    const audioContext = getAudioContext();

    // Resume context if suspended (browser autoplay policy)
    if (audioContext.state === 'suspended') {
      await audioContext.resume();
    }

    // Stop any currently playing audio
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch {
        // Ignore if already stopped
      }
    }

    try {
      // Decode audio data
      const audioBuffer = await audioContext.decodeAudioData(audioData.slice(0));
      audioBufferRef.current = audioBuffer;

      // Create source and play
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);

      currentSourceRef.current = source;
      startTimeRef.current = audioContext.currentTime;

      setState(prev => ({
        ...prev,
        isPlaying: true,
        duration: audioBuffer.duration,
        currentTime: 0,
        error: null,
      }));

      onPlayStart?.();

      source.start();

      // Return promise that resolves when playback ends
      return new Promise<void>((resolve) => {
        source.onended = () => {
          currentSourceRef.current = null;
          setState(prev => ({
            ...prev,
            isPlaying: false,
            currentTime: prev.duration,
          }));
          onPlayEnd?.();
          resolve();
        };
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to play audio';
      setState(prev => ({
        ...prev,
        isPlaying: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
      throw error;
    }
  }, [getAudioContext, onPlayStart, onPlayEnd, onError]);

  const stopAudio = useCallback(() => {
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
        currentSourceRef.current = null;
      } catch {
        // Ignore if already stopped
      }
    }

    setState(prev => ({
      ...prev,
      isPlaying: false,
    }));
  }, []);

  const pauseAudio = useCallback(() => {
    const audioContext = audioContextRef.current;
    if (audioContext && audioContext.state === 'running') {
      audioContext.suspend();
      setState(prev => ({
        ...prev,
        isPlaying: false,
      }));
    }
  }, []);

  const resumeAudio = useCallback(() => {
    const audioContext = audioContextRef.current;
    if (audioContext && audioContext.state === 'suspended') {
      audioContext.resume();
      setState(prev => ({
        ...prev,
        isPlaying: true,
      }));
    }
  }, []);

  const getCurrentTime = useCallback(() => {
    const audioContext = audioContextRef.current;
    if (audioContext && state.isPlaying) {
      return audioContext.currentTime - startTimeRef.current;
    }
    return state.currentTime;
  }, [state.isPlaying, state.currentTime]);

  // Queue for playing multiple audio segments
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isProcessingQueueRef = useRef(false);

  const processQueue = useCallback(async () => {
    if (isProcessingQueueRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    isProcessingQueueRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const audio = audioQueueRef.current.shift();
      if (audio) {
        try {
          await playAudio(audio);
        } catch {
          // Continue with next audio in queue
        }
      }
    }

    isProcessingQueueRef.current = false;
  }, [playAudio]);

  const queueAudio = useCallback((audioData: ArrayBuffer) => {
    audioQueueRef.current.push(audioData);
    processQueue();
  }, [processQueue]);

  const clearQueue = useCallback(() => {
    audioQueueRef.current = [];
    stopAudio();
  }, [stopAudio]);

  return {
    ...state,
    playAudio,
    stopAudio,
    pauseAudio,
    resumeAudio,
    getCurrentTime,
    queueAudio,
    clearQueue,
    queueLength: audioQueueRef.current.length,
  };
}
