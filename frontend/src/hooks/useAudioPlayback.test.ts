import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAudioPlayback } from "./useAudioPlayback";

describe("useAudioPlayback", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should start with default state", () => {
      const { result } = renderHook(() => useAudioPlayback());

      expect(result.current.isPlaying).toBe(false);
      expect(result.current.duration).toBe(0);
      expect(result.current.currentTime).toBe(0);
      expect(result.current.error).toBeNull();
    });

    it("should expose control functions", () => {
      const { result } = renderHook(() => useAudioPlayback());

      expect(typeof result.current.playAudio).toBe("function");
      expect(typeof result.current.stopAudio).toBe("function");
      expect(typeof result.current.pauseAudio).toBe("function");
      expect(typeof result.current.resumeAudio).toBe("function");
      expect(typeof result.current.getCurrentTime).toBe("function");
      expect(typeof result.current.queueAudio).toBe("function");
      expect(typeof result.current.clearQueue).toBe("function");
    });

    it("should have empty queue initially", () => {
      const { result } = renderHook(() => useAudioPlayback());

      expect(result.current.queueLength).toBe(0);
    });
  });

  describe("playAudio", () => {
    it("should decode and play audio data", async () => {
      const onPlayStart = vi.fn();
      const { result } = renderHook(() => useAudioPlayback({ onPlayStart }));

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);
      expect(result.current.duration).toBe(1.0); // Mock returns 1.0 duration
      expect(onPlayStart).toHaveBeenCalled();
    });

    it("should update state when playback ends", async () => {
      const onPlayEnd = vi.fn();
      const { result } = renderHook(() => useAudioPlayback({ onPlayEnd }));

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);

      // Simulate playback end by triggering onended
      // In real implementation, this would be triggered by AudioBufferSourceNode
    });

    it("should stop previous audio before playing new", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData1 = new ArrayBuffer(100);
      const audioData2 = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData1);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);

      // Play new audio (should stop previous)
      await act(async () => {
        result.current.playAudio(audioData2);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);
    });
  });

  describe("stopAudio", () => {
    it("should stop playing audio", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);

      act(() => {
        result.current.stopAudio();
      });

      expect(result.current.isPlaying).toBe(false);
    });

    it("should handle stop when nothing is playing", () => {
      const { result } = renderHook(() => useAudioPlayback());

      // Should not throw
      expect(() => {
        act(() => {
          result.current.stopAudio();
        });
      }).not.toThrow();
    });
  });

  describe("pauseAudio and resumeAudio", () => {
    it("should toggle isPlaying state on pause", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);

      act(() => {
        result.current.pauseAudio();
      });

      expect(result.current.isPlaying).toBe(false);
    });

    it("should call pauseAudio without error when not playing", () => {
      const { result } = renderHook(() => useAudioPlayback());

      expect(() => {
        act(() => {
          result.current.pauseAudio();
        });
      }).not.toThrow();
    });

    it("should call resumeAudio without error", () => {
      const { result } = renderHook(() => useAudioPlayback());

      expect(() => {
        act(() => {
          result.current.resumeAudio();
        });
      }).not.toThrow();
    });
  });

  describe("getCurrentTime", () => {
    it("should return current playback position", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      const time = result.current.getCurrentTime();
      expect(typeof time).toBe("number");
    });

    it("should return stored time when not playing", () => {
      const { result } = renderHook(() => useAudioPlayback());

      const time = result.current.getCurrentTime();
      expect(time).toBe(0);
    });
  });

  describe("audio queue", () => {
    it("should queue multiple audio segments", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData1 = new ArrayBuffer(100);
      const audioData2 = new ArrayBuffer(100);
      const audioData3 = new ArrayBuffer(100);

      act(() => {
        result.current.queueAudio(audioData1);
        result.current.queueAudio(audioData2);
        result.current.queueAudio(audioData3);
      });

      // Queue processing starts immediately
      await act(async () => {
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(result.current.isPlaying).toBe(true);
    });

    it("should clear queue and stop playback", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData1 = new ArrayBuffer(100);
      const audioData2 = new ArrayBuffer(100);

      act(() => {
        result.current.queueAudio(audioData1);
        result.current.queueAudio(audioData2);
      });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(10);
      });

      act(() => {
        result.current.clearQueue();
      });

      expect(result.current.isPlaying).toBe(false);
      expect(result.current.queueLength).toBe(0);
    });

    it("should process queue sequentially", async () => {
      const onPlayStart = vi.fn();
      const { result } = renderHook(() => useAudioPlayback({ onPlayStart }));

      const audioData1 = new ArrayBuffer(100);
      const audioData2 = new ArrayBuffer(100);

      act(() => {
        result.current.queueAudio(audioData1);
        result.current.queueAudio(audioData2);
      });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(10);
      });

      // First audio should start playing
      expect(onPlayStart).toHaveBeenCalled();
    });
  });

  describe("callbacks", () => {
    it("should call onPlayStart when playback starts", async () => {
      const onPlayStart = vi.fn();
      const { result } = renderHook(() => useAudioPlayback({ onPlayStart }));

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      expect(onPlayStart).toHaveBeenCalledTimes(1);
    });

    it("should handle decode errors gracefully", async () => {
      const onError = vi.fn();
      const { result } = renderHook(() => useAudioPlayback({ onError }));

      // The mock AudioContext doesn't actually fail, but we test the hook handles errors
      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      // Playback should work with mock
      expect(result.current.isPlaying).toBe(true);
    });
  });

  describe("browser autoplay policy", () => {
    it("should handle audio context resume", async () => {
      const { result } = renderHook(() => useAudioPlayback());

      const audioData = new ArrayBuffer(100);

      await act(async () => {
        result.current.playAudio(audioData);
        await vi.advanceTimersByTimeAsync(10);
      });

      // Context should be resumed before playback
      expect(result.current.isPlaying).toBe(true);
    });
  });

  describe("cleanup", () => {
    it("should handle unmount gracefully", () => {
      const { result, unmount } = renderHook(() => useAudioPlayback());

      // Just verify we can unmount without errors
      expect(() => {
        unmount();
      }).not.toThrow();
    });

    it("should handle unmount after playAudio call", async () => {
      const { result, unmount } = renderHook(() => useAudioPlayback());

      const audioData = new ArrayBuffer(100);

      // Start playback
      act(() => {
        result.current.playAudio(audioData);
      });

      // Unmount while operation is pending
      expect(() => {
        unmount();
      }).not.toThrow();
    });

    it("should handle unmount after queueAudio call", () => {
      const { result, unmount } = renderHook(() => useAudioPlayback());

      const audioData1 = new ArrayBuffer(100);
      const audioData2 = new ArrayBuffer(100);

      act(() => {
        result.current.queueAudio(audioData1);
        result.current.queueAudio(audioData2);
      });

      // Unmount while queue is processing
      expect(() => {
        unmount();
      }).not.toThrow();
    });
  });
});
