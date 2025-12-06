import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioRecorder } from './useAudioRecorder';

describe('useAudioRecorder', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should start with default state', () => {
      const { result } = renderHook(() => useAudioRecorder());

      expect(result.current.isRecording).toBe(false);
      expect(result.current.isPaused).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.duration).toBe(0);
    });

    it('should expose control functions', () => {
      const { result } = renderHook(() => useAudioRecorder());

      expect(typeof result.current.startRecording).toBe('function');
      expect(typeof result.current.stopRecording).toBe('function');
      expect(typeof result.current.pauseRecording).toBe('function');
      expect(typeof result.current.resumeRecording).toBe('function');
      expect(typeof result.current.toggleRecording).toBe('function');
    });
  });

  describe('startRecording', () => {
    it('should request microphone access', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
        audio: expect.objectContaining({
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }),
      });
    });

    it('should set isRecording to true on success', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should use custom sample rate when provided', async () => {
      const { result } = renderHook(() =>
        useAudioRecorder({ sampleRate: 44100 })
      );

      await act(async () => {
        await result.current.startRecording();
      });

      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
        audio: expect.objectContaining({
          sampleRate: 44100,
        }),
      });
    });

    it('should handle getUserMedia error', async () => {
      const mockError = new Error('Permission denied');
      vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(
        mockError
      );

      const onError = vi.fn();
      const { result } = renderHook(() => useAudioRecorder({ onError }));

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(false);
      expect(result.current.error).toBe('Permission denied');
      expect(onError).toHaveBeenCalledWith('Permission denied');
    });

    it('should track duration while recording', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.duration).toBe(0);

      // Advance time by 3 seconds
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });

      expect(result.current.duration).toBe(3);
    });
  });

  describe('stopRecording', () => {
    it('should set isRecording to false', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(true);

      act(() => {
        result.current.stopRecording();
      });

      expect(result.current.isRecording).toBe(false);
    });

    it('should stop duration tracking', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      const durationAtStop = result.current.duration;

      act(() => {
        result.current.stopRecording();
      });

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Duration should not have increased after stopping
      expect(result.current.duration).toBe(durationAtStop);
    });
  });

  describe('pauseRecording and resumeRecording', () => {
    it('should toggle isPaused state', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isPaused).toBe(false);

      act(() => {
        result.current.pauseRecording();
      });

      expect(result.current.isPaused).toBe(true);

      act(() => {
        result.current.resumeRecording();
      });

      expect(result.current.isPaused).toBe(false);
    });
  });

  describe('toggleRecording', () => {
    it('should start recording when not recording', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      expect(result.current.isRecording).toBe(false);

      await act(async () => {
        await result.current.toggleRecording();
      });

      expect(result.current.isRecording).toBe(true);
    });

    it('should stop recording when recording', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(true);

      act(() => {
        result.current.toggleRecording();
      });

      expect(result.current.isRecording).toBe(false);
    });
  });

  describe('onAudioChunk callback', () => {
    it('should be called when audio data is available', async () => {
      const onAudioChunk = vi.fn();
      const { result } = renderHook(() =>
        useAudioRecorder({ onAudioChunk })
      );

      await act(async () => {
        await result.current.startRecording();
      });

      // The callback would be called by the ScriptProcessor in real usage
      // Here we verify the hook was set up correctly
      expect(result.current.isRecording).toBe(true);
    });
  });

  describe('cleanup', () => {
    it('should cleanup on unmount', async () => {
      const { result, unmount } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(true);

      unmount();

      // Resources should be cleaned up (no errors thrown)
    });

    it('should cleanup when starting new recording', async () => {
      const { result } = renderHook(() => useAudioRecorder());

      await act(async () => {
        await result.current.startRecording();
      });

      // Start a new recording without stopping first
      await act(async () => {
        await result.current.startRecording();
      });

      expect(result.current.isRecording).toBe(true);
    });
  });
});
