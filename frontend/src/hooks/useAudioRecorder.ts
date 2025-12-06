import { useState, useCallback, useRef } from 'react';

interface AudioRecorderOptions {
  sampleRate?: number;
  onAudioChunk?: (chunk: Float32Array) => void;
  onError?: (error: string) => void;
}

interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  error: string | null;
  duration: number;
}

export function useAudioRecorder(options: AudioRecorderOptions = {}) {
  const { sampleRate = 16000, onAudioChunk, onError } = options;

  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    error: null,
    duration: 0,
  });

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const startTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    // Stop duration tracking
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    // Disconnect processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // Clean up any existing recording
      cleanup();

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      mediaStreamRef.current = stream;

      // Create audio context
      const audioContext = new AudioContext({ sampleRate });
      audioContextRef.current = audioContext;

      // Create source from stream
      const source = audioContext.createMediaStreamSource(stream);

      // Create processor for raw audio access
      // Note: ScriptProcessorNode is deprecated but worklet requires more setup
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (state.isPaused) return;

        const inputData = event.inputBuffer.getChannelData(0);
        const audioChunk = new Float32Array(inputData);
        onAudioChunk?.(audioChunk);
      };

      // Connect nodes
      source.connect(processor);
      processor.connect(audioContext.destination);

      // Start duration tracking
      startTimeRef.current = Date.now();
      durationIntervalRef.current = window.setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Math.floor((Date.now() - startTimeRef.current) / 1000)
        }));
      }, 1000);

      setState({
        isRecording: true,
        isPaused: false,
        error: null,
        duration: 0,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
      setState(prev => ({
        ...prev,
        isRecording: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [sampleRate, onAudioChunk, onError, cleanup, state.isPaused]);

  const stopRecording = useCallback(() => {
    cleanup();
    setState(prev => ({
      ...prev,
      isRecording: false,
      isPaused: false,
    }));
  }, [cleanup]);

  const pauseRecording = useCallback(() => {
    setState(prev => ({
      ...prev,
      isPaused: true,
    }));
  }, []);

  const resumeRecording = useCallback(() => {
    setState(prev => ({
      ...prev,
      isPaused: false,
    }));
  }, []);

  const toggleRecording = useCallback(() => {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [state.isRecording, startRecording, stopRecording]);

  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    toggleRecording,
  };
}
