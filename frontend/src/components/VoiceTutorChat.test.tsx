import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VoiceTutorChat } from "./VoiceTutorChat";

// Mock the hooks
vi.mock("../hooks/useAudioRecorder", () => ({
  useAudioRecorder: vi.fn(() => ({
    isRecording: false,
    isPaused: false,
    error: null,
    duration: 0,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    pauseRecording: vi.fn(),
    resumeRecording: vi.fn(),
    toggleRecording: vi.fn(),
  })),
}));

vi.mock("../hooks/useVoiceWebSocket", () => ({
  useVoiceWebSocket: vi.fn(() => ({
    connectionState: "connected",
    currentStatus: "idle",
    sessionId: "test-session-123",
    metrics: null,
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendAudio: vi.fn(),
    sendCommand: vi.fn(),
    reset: vi.fn(),
    getMetrics: vi.fn(),
    endSession: vi.fn(),
    isConnected: true,
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
  })),
}));

vi.mock("../hooks/useAudioPlayback", () => ({
  useAudioPlayback: vi.fn(() => ({
    isPlaying: false,
    duration: 0,
    currentTime: 0,
    error: null,
    playAudio: vi.fn(),
    stopAudio: vi.fn(),
    pauseAudio: vi.fn(),
    resumeAudio: vi.fn(),
    getCurrentTime: vi.fn(() => 0),
    queueAudio: vi.fn(),
    clearQueue: vi.fn(),
    queueLength: 0,
  })),
}));

import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useVoiceWebSocket } from "../hooks/useVoiceWebSocket";
import { useAudioPlayback } from "../hooks/useAudioPlayback";

// Default mock values
const defaultWebSocketMock = {
  connectionState: "connected" as const,
  currentStatus: "idle" as const,
  sessionId: "test-session-123",
  metrics: null,
  connect: vi.fn(),
  disconnect: vi.fn(),
  sendAudio: vi.fn(),
  sendCommand: vi.fn(),
  reset: vi.fn(),
  getMetrics: vi.fn(),
  endSession: vi.fn(),
  isConnected: true,
  isListening: false,
  isProcessing: false,
  isSpeaking: false,
};

const defaultRecorderMock = {
  isRecording: false,
  isPaused: false,
  error: null,
  duration: 0,
  startRecording: vi.fn(),
  stopRecording: vi.fn(),
  pauseRecording: vi.fn(),
  resumeRecording: vi.fn(),
  toggleRecording: vi.fn(),
};

const defaultPlaybackMock = {
  isPlaying: false,
  duration: 0,
  currentTime: 0,
  error: null,
  playAudio: vi.fn(),
  stopAudio: vi.fn(),
  pauseAudio: vi.fn(),
  resumeAudio: vi.fn(),
  getCurrentTime: vi.fn(() => 0),
  queueAudio: vi.fn(),
  clearQueue: vi.fn(),
  queueLength: 0,
};

describe("VoiceTutorChat", () => {
  const defaultProps = {
    courseId: "course-123",
    studentId: "student-456",
  };

  beforeEach(() => {
    vi.useFakeTimers();
    // Reset mocks to defaults before each test
    vi.mocked(useVoiceWebSocket).mockReturnValue({ ...defaultWebSocketMock });
    vi.mocked(useAudioRecorder).mockReturnValue({ ...defaultRecorderMock });
    vi.mocked(useAudioPlayback).mockReturnValue({ ...defaultPlaybackMock });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("should render header with title", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Voice Tutor")).toBeInTheDocument();
    });

    it("should show session ID when connected", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      // Session ID is truncated to first 8 chars: "test-ses" + "..."
      expect(screen.getByText(/Session: test-ses/)).toBeInTheDocument();
    });

    it('should show "Connecting..." when no session', () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        connectionState: "connecting",
        sessionId: null,
        isConnected: false,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      // Use getAllByText since there might be multiple "Connecting..." elements
      const connectingElements = screen.getAllByText("Connecting...");
      expect(connectingElements.length).toBeGreaterThan(0);
    });

    it("should show connection status indicator when connected", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      // Check for green dot (connected state in VoiceControls)
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    it("should show disconnected status when not connected", () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        connectionState: "disconnected",
        sessionId: null,
        isConnected: false,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Disconnected")).toBeInTheDocument();
    });

    it("should render VoiceControls", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      // Record button should be present
      expect(
        screen.getByRole("button", { name: /start recording/i }),
      ).toBeInTheDocument();
    });

    it("should render StatusBadge", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Ready")).toBeInTheDocument();
    });
  });

  describe("welcome message", () => {
    it("should show welcome message when no messages and not recording", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(
        screen.getByText("Welcome to Voice Tutoring!"),
      ).toBeInTheDocument();
    });

    it("should show example prompts", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(
        screen.getByText('"Can you explain the main concept?"'),
      ).toBeInTheDocument();
      expect(screen.getByText('"I\'m confused about..."')).toBeInTheDocument();
      expect(screen.getByText('"Give me an example"')).toBeInTheDocument();
    });
  });

  describe("connection lifecycle", () => {
    it("should call connect on mount", () => {
      const connect = vi.fn();
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        connect,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(connect).toHaveBeenCalled();
    });

    it("should call disconnect on unmount", () => {
      const disconnect = vi.fn();
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        disconnect,
      });

      const { unmount } = render(<VoiceTutorChat {...defaultProps} />);

      unmount();

      expect(disconnect).toHaveBeenCalled();
    });

    it("should call onSessionStart callback", () => {
      const onSessionStart = vi.fn();

      vi.mocked(useVoiceWebSocket).mockImplementation((options) => {
        // Trigger onConnect callback
        options.onConnect?.({ sessionId: "new-session", sampleRate: 16000 });

        return { ...defaultWebSocketMock };
      });

      render(
        <VoiceTutorChat {...defaultProps} onSessionStart={onSessionStart} />,
      );

      expect(onSessionStart).toHaveBeenCalledWith("new-session");
    });
  });

  describe("recording controls", () => {
    it("should toggle recording when button is clicked", () => {
      const startRecording = vi.fn();

      vi.mocked(useAudioRecorder).mockReturnValue({
        ...defaultRecorderMock,
        startRecording,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      const recordButton = screen.getByRole("button", {
        name: /start recording/i,
      });
      fireEvent.click(recordButton);

      expect(startRecording).toHaveBeenCalled();
    });

    it("should stop recording when recording and button is clicked", () => {
      const stopRecording = vi.fn();

      vi.mocked(useAudioRecorder).mockReturnValue({
        ...defaultRecorderMock,
        isRecording: true,
        stopRecording,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      const recordButton = screen.getByRole("button", {
        name: /stop recording/i,
      });
      fireEvent.click(recordButton);

      expect(stopRecording).toHaveBeenCalled();
    });

    it("should show recorder error", () => {
      vi.mocked(useAudioRecorder).mockReturnValue({
        ...defaultRecorderMock,
        error: "Microphone permission denied",
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(
        screen.getByText("Microphone permission denied"),
      ).toBeInTheDocument();
    });
  });

  describe("mute controls", () => {
    it("should toggle mute when mute button is clicked", () => {
      const stopAudio = vi.fn();

      vi.mocked(useAudioPlayback).mockReturnValue({
        ...defaultPlaybackMock,
        isPlaying: true,
        stopAudio,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      const muteButton = screen.getByRole("button", { name: /mute/i });
      fireEvent.click(muteButton);

      expect(stopAudio).toHaveBeenCalled();
    });
  });

  describe("reset functionality", () => {
    it("should call reset when reset button is clicked", () => {
      const reset = vi.fn();

      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        reset,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      const resetButton = screen.getByRole("button", { name: /reset/i });
      fireEvent.click(resetButton);

      expect(reset).toHaveBeenCalled();
    });
  });

  describe("status display", () => {
    it("should show listening status", () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        currentStatus: "listening",
        isListening: true,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Listening")).toBeInTheDocument();
    });

    it("should show processing status", () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        currentStatus: "processing",
        isProcessing: true,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Processing")).toBeInTheDocument();
    });

    it("should show speaking status", () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        currentStatus: "speaking",
        isSpeaking: true,
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByText("Speaking")).toBeInTheDocument();
    });
  });

  describe("audio handling", () => {
    it("should send audio chunks when recording", () => {
      const sendAudio = vi.fn();

      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        sendAudio,
      });

      vi.mocked(useAudioRecorder).mockImplementation((options) => {
        // Simulate audio chunk callback
        const chunk = new Float32Array([0.1, 0.2, 0.3]);
        options?.onAudioChunk?.(chunk);

        return {
          ...defaultRecorderMock,
          isRecording: true,
        };
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(sendAudio).toHaveBeenCalled();
    });

    it("should play audio response when not muted", () => {
      const playAudio = vi.fn();

      vi.mocked(useAudioPlayback).mockReturnValue({
        ...defaultPlaybackMock,
        playAudio,
      });

      vi.mocked(useVoiceWebSocket).mockImplementation((options) => {
        // Simulate audio response
        const audioBuffer = new ArrayBuffer(100);
        options.onAudioResponse?.(audioBuffer);

        return { ...defaultWebSocketMock };
      });

      render(<VoiceTutorChat {...defaultProps} />);

      expect(playAudio).toHaveBeenCalled();
    });
  });

  describe("processing indicator", () => {
    it("should show processing dots when processing and no transcription", () => {
      vi.mocked(useVoiceWebSocket).mockReturnValue({
        ...defaultWebSocketMock,
        currentStatus: "processing",
        isProcessing: true,
      });

      const { container } = render(<VoiceTutorChat {...defaultProps} />);

      // Should show bouncing dots
      const dots = container.querySelectorAll(".animate-bounce");
      expect(dots.length).toBeGreaterThan(0);
    });
  });

  describe("accessibility", () => {
    it("should have accessible header", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        "Voice Tutor",
      );
    });

    it("should have accessible control buttons", () => {
      render(<VoiceTutorChat {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /start recording/i }),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /mute/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reset/i }),
      ).toBeInTheDocument();
    });
  });
});
