import React from 'react';

interface VoiceControlsProps {
  isRecording: boolean;
  isConnected: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  isMuted: boolean;
  onToggleRecording: () => void;
  onToggleMute: () => void;
  onReset?: () => void;
  disabled?: boolean;
}

export function VoiceControls({
  isRecording,
  isConnected,
  isProcessing,
  isSpeaking,
  isMuted,
  onToggleRecording,
  onToggleMute,
  onReset,
  disabled = false,
}: VoiceControlsProps) {
  const getRecordButtonColor = () => {
    if (!isConnected || disabled) return 'bg-gray-300';
    if (isRecording) return 'bg-red-500 hover:bg-red-600 animate-pulse';
    return 'bg-blue-500 hover:bg-blue-600';
  };

  const getStatusText = () => {
    if (!isConnected) return 'Connecting...';
    if (isProcessing) return 'Processing...';
    if (isSpeaking) return 'Speaking...';
    if (isRecording) return 'Listening...';
    return 'Tap to speak';
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Main record button */}
      <button
        onClick={onToggleRecording}
        disabled={!isConnected || disabled}
        className={`
          p-6 rounded-full transition-all transform
          ${getRecordButtonColor()}
          ${isRecording ? 'scale-110' : 'scale-100'}
          disabled:cursor-not-allowed
          focus:outline-none focus:ring-4 focus:ring-blue-300
        `}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isRecording ? (
          <MicOffIcon className="w-8 h-8 text-white" />
        ) : (
          <MicIcon className="w-8 h-8 text-white" />
        )}
      </button>

      {/* Status text */}
      <p className="text-sm text-gray-500">{getStatusText()}</p>

      {/* Secondary controls */}
      <div className="flex gap-4">
        {/* Mute button */}
        <button
          onClick={onToggleMute}
          className={`
            p-2 rounded-full transition-colors
            ${isMuted ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}
            hover:bg-gray-200
          `}
          aria-label={isMuted ? 'Unmute' : 'Mute'}
          title={isMuted ? 'Unmute audio' : 'Mute audio'}
        >
          {isMuted ? (
            <VolumeOffIcon className="w-5 h-5" />
          ) : (
            <VolumeIcon className="w-5 h-5" />
          )}
        </button>

        {/* Reset button */}
        {onReset && (
          <button
            onClick={onReset}
            className="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            aria-label="Reset"
            title="Reset conversation"
          >
            <RefreshIcon className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Connection status indicator */}
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className="text-xs text-gray-400">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
}

// Icon components
function MicIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
  );
}

function MicOffIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
    </svg>
  );
}

function VolumeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
    </svg>
  );
}

function VolumeOffIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  );
}
