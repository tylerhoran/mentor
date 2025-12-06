import React from 'react';

type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

interface VoiceIndicatorProps {
  state: VoiceState;
  speechProbability?: number;
  className?: string;
}

export function VoiceIndicator({
  state,
  speechProbability = 0,
  className = ''
}: VoiceIndicatorProps) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      {state === 'idle' && <IdleIndicator />}
      {state === 'listening' && <ListeningIndicator intensity={speechProbability} />}
      {state === 'processing' && <ProcessingIndicator />}
      {state === 'speaking' && <SpeakingIndicator />}
    </div>
  );
}

function IdleIndicator() {
  return (
    <div className="flex items-center gap-1">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="w-1 h-4 bg-gray-300 rounded-full"
        />
      ))}
    </div>
  );
}

interface ListeningIndicatorProps {
  intensity: number;
}

function ListeningIndicator({ intensity }: ListeningIndicatorProps) {
  // Scale heights based on intensity (0-1)
  const heights = [
    4 + intensity * 12,
    6 + intensity * 14,
    4 + intensity * 12,
  ];

  return (
    <div className="flex items-center gap-1">
      {heights.map((height, i) => (
        <div
          key={i}
          className="w-1 bg-blue-500 rounded-full transition-all duration-100"
          style={{
            height: `${height}px`,
            animation: intensity > 0.3 ? `pulse 0.5s ease-in-out ${i * 0.1}s infinite` : 'none'
          }}
        />
      ))}
    </div>
  );
}

function ProcessingIndicator() {
  return (
    <div className="flex items-center gap-1">
      {[...Array(3)].map((_, i) => (
        <div
          key={i}
          className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}

function SpeakingIndicator() {
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-green-500 rounded-full animate-pulse"
          style={{
            height: `${8 + Math.sin(i * 0.8) * 8}px`,
            animationDelay: `${i * 100}ms`
          }}
        />
      ))}
    </div>
  );
}

// Waveform visualization component
interface WaveformProps {
  audioData?: Float32Array;
  isActive: boolean;
  color?: string;
  width?: number;
  height?: number;
}

export function Waveform({
  audioData,
  isActive,
  color = '#3B82F6',
  width = 200,
  height = 60,
}: WaveformProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    if (!isActive || !audioData || audioData.length === 0) {
      // Draw flat line
      ctx.beginPath();
      ctx.strokeStyle = '#E5E7EB';
      ctx.lineWidth = 2;
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
      return;
    }

    // Draw waveform
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    const sliceWidth = width / audioData.length;
    let x = 0;

    for (let i = 0; i < audioData.length; i++) {
      const v = audioData[i];
      const y = (v * height / 2) + height / 2;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.stroke();
  }, [audioData, isActive, color, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="rounded"
    />
  );
}

// Compact status badge
interface StatusBadgeProps {
  state: VoiceState;
}

export function StatusBadge({ state }: StatusBadgeProps) {
  const getConfig = () => {
    switch (state) {
      case 'listening':
        return { color: 'bg-blue-100 text-blue-700', label: 'Listening' };
      case 'processing':
        return { color: 'bg-yellow-100 text-yellow-700', label: 'Processing' };
      case 'speaking':
        return { color: 'bg-green-100 text-green-700', label: 'Speaking' };
      default:
        return { color: 'bg-gray-100 text-gray-600', label: 'Ready' };
    }
  };

  const { color, label } = getConfig();

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}
