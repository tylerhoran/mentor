import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useVoiceWebSocket } from '../hooks/useVoiceWebSocket';
import { useAudioPlayback } from '../hooks/useAudioPlayback';
import { VoiceControls } from './VoiceControls';
import { VoiceIndicator, StatusBadge } from './VoiceIndicator';

interface Message {
  id: string;
  role: 'student' | 'tutor';
  text: string;
  timestamp: Date;
  gamingConfidence?: number;
}

interface VoiceTutorChatProps {
  courseId: string;
  studentId?: string;
  onSessionStart?: (sessionId: string) => void;
  onSessionEnd?: () => void;
}

export function VoiceTutorChat({
  courseId,
  studentId,
  onSessionStart,
  onSessionEnd,
}: VoiceTutorChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState('');
  const [speechProbability, setSpeechProbability] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { playAudio, stopAudio, isPlaying } = useAudioPlayback({
    onPlayEnd: () => {
      // Ready for next input after TTS finishes
    },
  });

  // WebSocket connection
  const {
    connectionState,
    currentStatus,
    sessionId,
    connect,
    disconnect,
    sendAudio,
    reset,
    isConnected,
    isListening,
    isProcessing,
    isSpeaking,
  } = useVoiceWebSocket({
    courseId,
    studentId,
    onConnect: ({ sessionId }) => {
      onSessionStart?.(sessionId);
    },
    onTranscription: (text) => {
      setCurrentTranscription(text);
    },
    onResponse: (text, gamingConfidence) => {
      // Add tutor message
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'tutor',
        text,
        timestamp: new Date(),
        gamingConfidence,
      }]);
    },
    onAudioResponse: async (audio) => {
      if (!isMuted) {
        await playAudio(audio);
      }
    },
    onStatusChange: (status, data) => {
      if (status === 'listening' && data?.speech_probability !== undefined) {
        setSpeechProbability(data.speech_probability as number);
      }
    },
    onError: (error) => {
      console.error('Voice error:', error);
    },
  });

  // Audio recorder
  const {
    isRecording,
    startRecording,
    stopRecording,
    error: recorderError,
  } = useAudioRecorder({
    sampleRate: 16000,
    onAudioChunk: (chunk) => {
      sendAudio(chunk);
    },
    onError: (error) => {
      console.error('Recorder error:', error);
    },
  });

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
      onSessionEnd?.();
    };
  }, [connect, disconnect, onSessionEnd]);

  // Add student message when transcription is complete
  useEffect(() => {
    if (currentStatus === 'processing' && currentTranscription) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'student',
        text: currentTranscription,
        timestamp: new Date(),
      }]);
      setCurrentTranscription('');
    }
  }, [currentStatus, currentTranscription]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentTranscription]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const toggleMute = useCallback(() => {
    if (isMuted) {
      setIsMuted(false);
    } else {
      stopAudio();
      setIsMuted(true);
    }
  }, [isMuted, stopAudio]);

  const handleReset = useCallback(() => {
    reset();
    setMessages([]);
    setCurrentTranscription('');
  }, [reset]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between p-4 bg-white border-b shadow-sm">
        <div className="flex items-center gap-3">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <div>
            <h1 className="font-semibold text-gray-900">Voice Tutor</h1>
            <p className="text-xs text-gray-500">
              {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : 'Connecting...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <StatusBadge state={currentStatus as 'idle' | 'listening' | 'processing' | 'speaking'} />
          <VoiceIndicator
            state={currentStatus as 'idle' | 'listening' | 'processing' | 'speaking'}
            speechProbability={speechProbability}
          />
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && !isRecording && (
            <WelcomeMessage />
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Live transcription */}
          {currentTranscription && (
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-lg p-3 bg-blue-400 text-white opacity-80">
                <p className="text-sm">{currentTranscription}</p>
                <span className="inline-block w-1 h-4 bg-white animate-pulse ml-1" />
              </div>
            </div>
          )}

          {/* Processing indicator */}
          {isProcessing && !currentTranscription && (
            <div className="flex justify-start">
              <div className="rounded-lg p-4 bg-white border shadow-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Controls */}
      <div className="p-6 bg-white border-t shadow-lg">
        <VoiceControls
          isRecording={isRecording}
          isConnected={isConnected}
          isProcessing={isProcessing}
          isSpeaking={isSpeaking || isPlaying}
          isMuted={isMuted}
          onToggleRecording={toggleRecording}
          onToggleMute={toggleMute}
          onReset={handleReset}
        />

        {recorderError && (
          <p className="text-center text-sm text-red-500 mt-2">{recorderError}</p>
        )}
      </div>
    </div>
  );
}

function WelcomeMessage() {
  return (
    <div className="text-center py-12">
      <div className="text-5xl mb-4">🎓</div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Welcome to Voice Tutoring!
      </h2>
      <p className="text-gray-500 max-w-md mx-auto mb-6">
        Speak naturally to ask questions or discuss concepts.
        I'll guide you through the material using Socratic dialogue.
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {[
          'Can you explain the main concept?',
          'I\'m confused about...',
          'Give me an example',
        ].map((prompt) => (
          <span
            key={prompt}
            className="px-3 py-2 bg-gray-100 border rounded-lg text-sm text-gray-600"
          >
            "{prompt}"
          </span>
        ))}
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isStudent = message.role === 'student';

  return (
    <div className={`flex ${isStudent ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isStudent
            ? 'bg-blue-500 text-white'
            : 'bg-white border shadow-sm text-gray-900'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        <div className={`flex items-center justify-between mt-1 ${
          isStudent ? 'text-blue-100' : 'text-gray-400'
        }`}>
          <span className="text-xs">
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
          {message.gamingConfidence !== undefined && message.gamingConfidence > 0.5 && (
            <span className="text-xs text-yellow-500" title="Gaming detected">
              ⚠️
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
