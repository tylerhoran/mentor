import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { VoiceControls } from './VoiceControls';

describe('VoiceControls', () => {
  const defaultProps = {
    isRecording: false,
    isConnected: true,
    isProcessing: false,
    isSpeaking: false,
    isMuted: false,
    onToggleRecording: vi.fn(),
    onToggleMute: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render main record button', () => {
      render(<VoiceControls {...defaultProps} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton).toBeInTheDocument();
    });

    it('should render mute button', () => {
      render(<VoiceControls {...defaultProps} />);

      const muteButton = screen.getByRole('button', { name: /mute/i });
      expect(muteButton).toBeInTheDocument();
    });

    it('should render reset button when onReset is provided', () => {
      const onReset = vi.fn();
      render(<VoiceControls {...defaultProps} onReset={onReset} />);

      const resetButton = screen.getByRole('button', { name: /reset/i });
      expect(resetButton).toBeInTheDocument();
    });

    it('should not render reset button when onReset is not provided', () => {
      render(<VoiceControls {...defaultProps} />);

      const resetButton = screen.queryByRole('button', { name: /reset/i });
      expect(resetButton).not.toBeInTheDocument();
    });

    it('should show connection status indicator', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  describe('status text', () => {
    it('should show "Tap to speak" when idle', () => {
      render(<VoiceControls {...defaultProps} />);

      expect(screen.getByText('Tap to speak')).toBeInTheDocument();
    });

    it('should show "Connecting..." when disconnected', () => {
      render(<VoiceControls {...defaultProps} isConnected={false} />);

      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });

    it('should show "Listening..." when recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={true} />);

      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });

    it('should show "Processing..." when processing', () => {
      render(<VoiceControls {...defaultProps} isProcessing={true} />);

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should show "Speaking..." when speaking', () => {
      render(<VoiceControls {...defaultProps} isSpeaking={true} />);

      expect(screen.getByText('Speaking...')).toBeInTheDocument();
    });
  });

  describe('connection status', () => {
    it('should show green indicator when connected', () => {
      render(<VoiceControls {...defaultProps} isConnected={true} />);

      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    it('should show red indicator when disconnected', () => {
      render(<VoiceControls {...defaultProps} isConnected={false} />);

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });

  describe('record button', () => {
    it('should call onToggleRecording when clicked', () => {
      const onToggleRecording = vi.fn();
      render(
        <VoiceControls {...defaultProps} onToggleRecording={onToggleRecording} />
      );

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      fireEvent.click(recordButton);

      expect(onToggleRecording).toHaveBeenCalledTimes(1);
    });

    it('should be disabled when not connected', () => {
      render(<VoiceControls {...defaultProps} isConnected={false} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton).toBeDisabled();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<VoiceControls {...defaultProps} disabled={true} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton).toBeDisabled();
    });

    it('should show stop recording label when recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={true} />);

      const recordButton = screen.getByRole('button', {
        name: /stop recording/i,
      });
      expect(recordButton).toBeInTheDocument();
    });

    it('should have pulse animation when recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={true} />);

      const recordButton = screen.getByRole('button', {
        name: /stop recording/i,
      });
      expect(recordButton.className).toContain('animate-pulse');
    });

    it('should have red background when recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={true} />);

      const recordButton = screen.getByRole('button', {
        name: /stop recording/i,
      });
      expect(recordButton.className).toContain('bg-red-500');
    });

    it('should have blue background when not recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={false} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton.className).toContain('bg-blue-500');
    });

    it('should have gray background when disabled', () => {
      render(<VoiceControls {...defaultProps} disabled={true} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton.className).toContain('bg-gray-300');
    });
  });

  describe('mute button', () => {
    it('should call onToggleMute when clicked', () => {
      const onToggleMute = vi.fn();
      render(<VoiceControls {...defaultProps} onToggleMute={onToggleMute} />);

      const muteButton = screen.getByRole('button', { name: /mute/i });
      fireEvent.click(muteButton);

      expect(onToggleMute).toHaveBeenCalledTimes(1);
    });

    it('should show unmute label when muted', () => {
      render(<VoiceControls {...defaultProps} isMuted={true} />);

      const muteButton = screen.getByRole('button', { name: /unmute/i });
      expect(muteButton).toBeInTheDocument();
    });

    it('should have red styling when muted', () => {
      render(<VoiceControls {...defaultProps} isMuted={true} />);

      const muteButton = screen.getByRole('button', { name: /unmute/i });
      expect(muteButton.className).toContain('bg-red-100');
      expect(muteButton.className).toContain('text-red-600');
    });

    it('should have gray styling when not muted', () => {
      render(<VoiceControls {...defaultProps} isMuted={false} />);

      const muteButton = screen.getByRole('button', { name: /mute/i });
      expect(muteButton.className).toContain('bg-gray-100');
      expect(muteButton.className).toContain('text-gray-600');
    });
  });

  describe('reset button', () => {
    it('should call onReset when clicked', () => {
      const onReset = vi.fn();
      render(<VoiceControls {...defaultProps} onReset={onReset} />);

      const resetButton = screen.getByRole('button', { name: /reset/i });
      fireEvent.click(resetButton);

      expect(onReset).toHaveBeenCalledTimes(1);
    });

    it('should have correct tooltip', () => {
      const onReset = vi.fn();
      render(<VoiceControls {...defaultProps} onReset={onReset} />);

      const resetButton = screen.getByRole('button', { name: /reset/i });
      expect(resetButton).toHaveAttribute('title', 'Reset conversation');
    });
  });

  describe('accessibility', () => {
    it('should have proper aria labels on all buttons', () => {
      const onReset = vi.fn();
      render(<VoiceControls {...defaultProps} onReset={onReset} />);

      expect(
        screen.getByRole('button', { name: /start recording/i })
      ).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /mute/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });

    it('should update aria label based on recording state', () => {
      const { rerender } = render(
        <VoiceControls {...defaultProps} isRecording={false} />
      );

      expect(
        screen.getByRole('button', { name: /start recording/i })
      ).toBeInTheDocument();

      rerender(<VoiceControls {...defaultProps} isRecording={true} />);

      expect(
        screen.getByRole('button', { name: /stop recording/i })
      ).toBeInTheDocument();
    });

    it('should have focus ring on record button', () => {
      render(<VoiceControls {...defaultProps} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton.className).toContain('focus:ring');
    });
  });

  describe('visual states', () => {
    it('should scale up when recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={true} />);

      const recordButton = screen.getByRole('button', {
        name: /stop recording/i,
      });
      expect(recordButton.className).toContain('scale-110');
    });

    it('should be normal scale when not recording', () => {
      render(<VoiceControls {...defaultProps} isRecording={false} />);

      const recordButton = screen.getByRole('button', {
        name: /start recording/i,
      });
      expect(recordButton.className).toContain('scale-100');
    });
  });
});
