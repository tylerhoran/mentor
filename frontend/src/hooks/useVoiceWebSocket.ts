import { useState, useCallback, useRef, useEffect } from 'react';

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
type VoiceStatus = 'idle' | 'listening' | 'processing' | 'speaking' | 'ready';

interface VoiceWebSocketOptions {
  courseId: string;
  studentId?: string;
  sessionId?: string;
  onTranscription?: (text: string) => void;
  onResponse?: (text: string, gamingConfidence?: number) => void;
  onAudioResponse?: (audio: ArrayBuffer) => void;
  onStatusChange?: (status: VoiceStatus, data?: Record<string, unknown>) => void;
  onError?: (error: string) => void;
  onConnect?: (data: { sessionId: string; sampleRate: number }) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

interface SessionMetrics {
  totalInteractions: number;
  totalStudentSpeechMs: number;
  totalTutorSpeechMs: number;
  averageLatencyMs: number;
  speechBalance: number | null;
}

export function useVoiceWebSocket(options: VoiceWebSocketOptions) {
  const {
    courseId,
    studentId,
    sessionId: initialSessionId,
    onTranscription,
    onResponse,
    onAudioResponse,
    onStatusChange,
    onError,
    onConnect,
    autoReconnect = true,
    reconnectDelay = 3000,
  } = options;

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [currentStatus, setCurrentStatus] = useState<VoiceStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null);
  const [metrics, setMetrics] = useState<SessionMetrics | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    clearReconnectTimeout();
    setConnectionState('connecting');
    shouldReconnectRef.current = true;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;

    const params = new URLSearchParams();
    if (studentId) params.set('student_id', studentId);
    if (initialSessionId) params.set('session_id', initialSessionId);

    const wsUrl = `${protocol}//${host}/api/voice/session/${courseId}?${params.toString()}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState('connected');
    };

    ws.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Binary audio data
        const arrayBuffer = await event.data.arrayBuffer();
        onAudioResponse?.(arrayBuffer);
      } else {
        // JSON status message
        try {
          const message = JSON.parse(event.data);
          const status = message.status as VoiceStatus;
          const data = message.data;

          // Update status
          if (['idle', 'listening', 'processing', 'speaking', 'ready'].includes(status)) {
            setCurrentStatus(status);
            onStatusChange?.(status, data);
          }

          // Handle specific message types
          switch (status) {
            case 'ready':
              if (data?.session_id) {
                setSessionId(data.session_id);
                onConnect?.({
                  sessionId: data.session_id,
                  sampleRate: data.sample_rate || 16000
                });
              }
              break;

            case 'transcription':
              if (data?.text) {
                onTranscription?.(data.text);
              }
              break;

            case 'response':
              if (data?.text) {
                onResponse?.(data.text, data.gaming_confidence);
              }
              break;

            case 'metrics':
              if (data) {
                setMetrics({
                  totalInteractions: data.total_interactions,
                  totalStudentSpeechMs: data.total_student_speech_ms,
                  totalTutorSpeechMs: data.total_tutor_speech_ms,
                  averageLatencyMs: data.average_latency_ms,
                  speechBalance: data.speech_balance,
                });
              }
              break;

            case 'error':
              onError?.(data?.message || 'Unknown error');
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      }
    };

    ws.onerror = () => {
      setConnectionState('error');
      onError?.('WebSocket connection error');
    };

    ws.onclose = () => {
      setConnectionState('disconnected');
      setCurrentStatus('idle');
      wsRef.current = null;

      // Auto-reconnect if enabled
      if (autoReconnect && shouldReconnectRef.current) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, reconnectDelay);
      }
    };
  }, [
    courseId,
    studentId,
    initialSessionId,
    onTranscription,
    onResponse,
    onAudioResponse,
    onStatusChange,
    onError,
    onConnect,
    autoReconnect,
    reconnectDelay,
    clearReconnectTimeout
  ]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnectionState('disconnected');
    setCurrentStatus('idle');
  }, [clearReconnectTimeout]);

  const sendAudio = useCallback((audioData: Float32Array) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData.buffer);
    }
  }, []);

  const sendCommand = useCallback((command: string, data?: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command, ...data }));
    }
  }, []);

  const reset = useCallback(() => {
    sendCommand('reset');
  }, [sendCommand]);

  const getMetrics = useCallback(() => {
    sendCommand('get_metrics');
  }, [sendCommand]);

  const endSession = useCallback(() => {
    sendCommand('end');
  }, [sendCommand]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      clearReconnectTimeout();
      wsRef.current?.close();
    };
  }, [clearReconnectTimeout]);

  return {
    connectionState,
    currentStatus,
    sessionId,
    metrics,
    connect,
    disconnect,
    sendAudio,
    sendCommand,
    reset,
    getMetrics,
    endSession,
    isConnected: connectionState === 'connected',
    isListening: currentStatus === 'listening',
    isProcessing: currentStatus === 'processing',
    isSpeaking: currentStatus === 'speaking',
  };
}
