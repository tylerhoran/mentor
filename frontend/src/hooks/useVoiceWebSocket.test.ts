import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVoiceWebSocket } from "./useVoiceWebSocket";

describe("useVoiceWebSocket", () => {
  const defaultOptions = {
    courseId: "course-123",
    studentId: "student-456",
  };

  let mockWsInstance: {
    url: string;
    send: ReturnType<typeof vi.fn>;
    close: ReturnType<typeof vi.fn>;
    readyState: number;
    onopen: ((event: Event) => void) | null;
    onclose: ((event: CloseEvent) => void) | null;
    onmessage: ((event: MessageEvent) => void) | null;
    onerror: ((event: Event) => void) | null;
  } | null = null;

  beforeEach(() => {
    vi.useFakeTimers();

    // Create a controllable mock WebSocket
    mockWsInstance = null;

    class TestWebSocket {
      static CONNECTING = 0;
      static OPEN = 1;
      static CLOSING = 2;
      static CLOSED = 3;

      url: string;
      readyState = TestWebSocket.CONNECTING;
      onopen: ((event: Event) => void) | null = null;
      onclose: ((event: CloseEvent) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;
      send = vi.fn();
      close = vi.fn(() => {
        this.readyState = TestWebSocket.CLOSED;
        this.onclose?.(new CloseEvent("close"));
      });

      constructor(url: string) {
        this.url = url;
        mockWsInstance = this;

        // Auto-connect after a tick
        setTimeout(() => {
          this.readyState = TestWebSocket.OPEN;
          this.onopen?.(new Event("open"));
        }, 0);
      }
    }

    // @ts-expect-error - mocking global
    global.WebSocket = TestWebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    mockWsInstance = null;
  });

  describe("initial state", () => {
    it("should start disconnected", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.currentStatus).toBe("idle");
      expect(result.current.sessionId).toBeNull();
      expect(result.current.metrics).toBeNull();
      expect(result.current.isConnected).toBe(false);
    });

    it("should expose control functions", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      expect(typeof result.current.connect).toBe("function");
      expect(typeof result.current.disconnect).toBe("function");
      expect(typeof result.current.sendAudio).toBe("function");
      expect(typeof result.current.sendCommand).toBe("function");
      expect(typeof result.current.reset).toBe("function");
      expect(typeof result.current.getMetrics).toBe("function");
      expect(typeof result.current.endSession).toBe("function");
    });

    it("should have correct initial status flags", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.isListening).toBe(false);
      expect(result.current.isProcessing).toBe(false);
      expect(result.current.isSpeaking).toBe(false);
    });
  });

  describe("connect", () => {
    it("should set connectionState to connecting", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      expect(result.current.connectionState).toBe("connecting");
    });

    it("should create WebSocket with correct URL format", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      expect(mockWsInstance).not.toBeNull();
      expect(mockWsInstance!.url).toContain("course-123");
      expect(mockWsInstance!.url).toContain("student_id=student-456");
    });

    it("should include session_id in URL when provided", () => {
      const options = {
        ...defaultOptions,
        sessionId: "session-789",
      };

      const { result } = renderHook(() => useVoiceWebSocket(options));

      act(() => {
        result.current.connect();
      });

      expect(mockWsInstance!.url).toContain("session_id=session-789");
    });

    it("should set connected state after WebSocket opens", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      // Trigger the onopen callback
      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      expect(result.current.connectionState).toBe("connected");
      expect(result.current.isConnected).toBe(true);
    });
  });

  describe("disconnect", () => {
    it("should close WebSocket and update state", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.isConnected).toBe(false);
    });

    it("should call WebSocket close", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.disconnect();
      });

      expect(mockWsInstance!.close).toHaveBeenCalled();
    });
  });

  describe("sendAudio", () => {
    it("should send audio buffer when connected", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      const audioData = new Float32Array([0.1, 0.2, 0.3]);

      act(() => {
        result.current.sendAudio(audioData);
      });

      expect(mockWsInstance!.send).toHaveBeenCalledWith(audioData.buffer);
    });

    it("should not throw when not connected", () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      const audioData = new Float32Array([0.1, 0.2, 0.3]);

      expect(() => {
        act(() => {
          result.current.sendAudio(audioData);
        });
      }).not.toThrow();
    });
  });

  describe("sendCommand", () => {
    it("should send JSON command when connected", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.sendCommand("test_command", { key: "value" });
      });

      expect(mockWsInstance!.send).toHaveBeenCalledWith(
        JSON.stringify({ command: "test_command", key: "value" }),
      );
    });
  });

  describe("convenience methods", () => {
    it("reset should send reset command", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.reset();
      });

      expect(mockWsInstance!.send).toHaveBeenCalledWith(
        JSON.stringify({ command: "reset" }),
      );
    });

    it("getMetrics should send get_metrics command", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.getMetrics();
      });

      expect(mockWsInstance!.send).toHaveBeenCalledWith(
        JSON.stringify({ command: "get_metrics" }),
      );
    });

    it("endSession should send end command", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.endSession();
      });

      expect(mockWsInstance!.send).toHaveBeenCalledWith(
        JSON.stringify({ command: "end" }),
      );
    });
  });

  describe("message handling", () => {
    it("should update status on status message", async () => {
      const onStatusChange = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onStatusChange,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      // Simulate status message
      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({ status: "listening", data: {} }),
          }),
        );
      });

      expect(result.current.currentStatus).toBe("listening");
      expect(result.current.isListening).toBe(true);
      expect(onStatusChange).toHaveBeenCalledWith("listening", {});
    });

    it("should call onTranscription for transcription message", async () => {
      const onTranscription = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onTranscription,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({
              status: "transcription",
              data: { text: "Hello world" },
            }),
          }),
        );
      });

      expect(onTranscription).toHaveBeenCalledWith("Hello world");
    });

    it("should call onResponse for response message", async () => {
      const onResponse = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onResponse,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({
              status: "response",
              data: { text: "Response text", gaming_confidence: 0.2 },
            }),
          }),
        );
      });

      expect(onResponse).toHaveBeenCalledWith("Response text", 0.2);
    });

    it("should update metrics on metrics message", async () => {
      const { result } = renderHook(() => useVoiceWebSocket(defaultOptions));

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      expect(result.current.metrics).toBeNull();

      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({
              status: "metrics",
              data: {
                total_interactions: 5,
                total_student_speech_ms: 10000,
                total_tutor_speech_ms: 15000,
                average_latency_ms: 200,
                speech_balance: 0.6,
              },
            }),
          }),
        );
      });

      expect(result.current.metrics).toEqual({
        totalInteractions: 5,
        totalStudentSpeechMs: 10000,
        totalTutorSpeechMs: 15000,
        averageLatencyMs: 200,
        speechBalance: 0.6,
      });
    });

    it("should call onError for error message", async () => {
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onError,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({
              status: "error",
              data: { message: "Something went wrong" },
            }),
          }),
        );
      });

      expect(onError).toHaveBeenCalledWith("Something went wrong");
    });

    it("should set sessionId on ready message", async () => {
      const onConnect = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onConnect,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        mockWsInstance!.onmessage?.(
          new MessageEvent("message", {
            data: JSON.stringify({
              status: "ready",
              data: { session_id: "new-session-id", sample_rate: 16000 },
            }),
          }),
        );
      });

      expect(result.current.sessionId).toBe("new-session-id");
      expect(onConnect).toHaveBeenCalledWith({
        sessionId: "new-session-id",
        sampleRate: 16000,
      });
    });
  });

  describe("WebSocket error handling", () => {
    it("should set error state on WebSocket error", async () => {
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          onError,
        }),
      );

      act(() => {
        result.current.connect();
      });

      act(() => {
        mockWsInstance!.onerror?.(new Event("error"));
      });

      expect(result.current.connectionState).toBe("error");
      expect(onError).toHaveBeenCalledWith("WebSocket connection error");
    });
  });

  describe("auto-reconnect", () => {
    it("should not reconnect when manually disconnected", async () => {
      const { result } = renderHook(() =>
        useVoiceWebSocket({
          ...defaultOptions,
          autoReconnect: true,
          reconnectDelay: 1000,
        }),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      act(() => {
        result.current.disconnect();
      });

      // Advance past reconnect delay
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.connectionState).toBe("disconnected");
    });
  });

  describe("cleanup", () => {
    it("should cleanup on unmount", async () => {
      const { result, unmount } = renderHook(() =>
        useVoiceWebSocket(defaultOptions),
      );

      act(() => {
        result.current.connect();
      });

      await act(async () => {
        vi.advanceTimersByTime(1);
      });

      unmount();

      expect(mockWsInstance!.close).toHaveBeenCalled();
    });
  });
});
