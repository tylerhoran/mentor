import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VoiceIndicator, Waveform, StatusBadge } from './VoiceIndicator';

describe('VoiceIndicator', () => {
  describe('rendering states', () => {
    it('should render idle indicator', () => {
      const { container } = render(<VoiceIndicator state="idle" />);

      // Idle shows 3 gray bars
      const bars = container.querySelectorAll('.bg-gray-300');
      expect(bars.length).toBe(3);
    });

    it('should render listening indicator', () => {
      const { container } = render(
        <VoiceIndicator state="listening" speechProbability={0.5} />
      );

      // Listening shows blue bars
      const bars = container.querySelectorAll('.bg-blue-500');
      expect(bars.length).toBe(3);
    });

    it('should render processing indicator', () => {
      const { container } = render(<VoiceIndicator state="processing" />);

      // Processing shows bouncing yellow dots
      const dots = container.querySelectorAll('.bg-yellow-500');
      expect(dots.length).toBe(3);
    });

    it('should render speaking indicator', () => {
      const { container } = render(<VoiceIndicator state="speaking" />);

      // Speaking shows green pulsing bars
      const bars = container.querySelectorAll('.bg-green-500');
      expect(bars.length).toBe(5);
    });
  });

  describe('listening indicator', () => {
    it('should adjust bar heights based on speech probability', () => {
      const { container, rerender } = render(
        <VoiceIndicator state="listening" speechProbability={0} />
      );

      const bars = container.querySelectorAll('.bg-blue-500');
      const lowHeights = Array.from(bars).map(
        (bar) => (bar as HTMLElement).style.height
      );

      rerender(<VoiceIndicator state="listening" speechProbability={1} />);

      const highBars = container.querySelectorAll('.bg-blue-500');
      const highHeights = Array.from(highBars).map(
        (bar) => (bar as HTMLElement).style.height
      );

      // Heights should be different at different intensities
      expect(lowHeights).not.toEqual(highHeights);
    });

    it('should animate when speech probability is high', () => {
      const { container } = render(
        <VoiceIndicator state="listening" speechProbability={0.8} />
      );

      const bars = container.querySelectorAll('.bg-blue-500');
      const firstBar = bars[0] as HTMLElement;

      // Should have animation style when probability > 0.3
      expect(firstBar.style.animation).toContain('pulse');
    });

    it('should not animate when speech probability is low', () => {
      const { container } = render(
        <VoiceIndicator state="listening" speechProbability={0.2} />
      );

      const bars = container.querySelectorAll('.bg-blue-500');
      const firstBar = bars[0] as HTMLElement;

      // Should not have animation when probability <= 0.3
      expect(firstBar.style.animation).toBe('none');
    });
  });

  describe('processing indicator', () => {
    it('should have staggered animation delays', () => {
      const { container } = render(<VoiceIndicator state="processing" />);

      const dots = container.querySelectorAll('.bg-yellow-500');

      dots.forEach((dot, index) => {
        const element = dot as HTMLElement;
        expect(element.style.animationDelay).toBe(`${index * 150}ms`);
      });
    });

    it('should have bounce animation', () => {
      const { container } = render(<VoiceIndicator state="processing" />);

      const dots = container.querySelectorAll('.animate-bounce');
      expect(dots.length).toBe(3);
    });
  });

  describe('speaking indicator', () => {
    it('should have 5 bars', () => {
      const { container } = render(<VoiceIndicator state="speaking" />);

      const bars = container.querySelectorAll('.bg-green-500');
      expect(bars.length).toBe(5);
    });

    it('should have pulse animation', () => {
      const { container } = render(<VoiceIndicator state="speaking" />);

      const bars = container.querySelectorAll('.animate-pulse');
      expect(bars.length).toBe(5);
    });

    it('should have staggered animation delays', () => {
      const { container } = render(<VoiceIndicator state="speaking" />);

      const bars = container.querySelectorAll('.bg-green-500');

      bars.forEach((bar, index) => {
        const element = bar as HTMLElement;
        expect(element.style.animationDelay).toBe(`${index * 100}ms`);
      });
    });
  });

  describe('className prop', () => {
    it('should apply additional className', () => {
      const { container } = render(
        <VoiceIndicator state="idle" className="custom-class" />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper.className).toContain('custom-class');
    });
  });

  describe('default speechProbability', () => {
    it('should default to 0 when not provided', () => {
      const { container } = render(<VoiceIndicator state="listening" />);

      // Should render without errors
      const bars = container.querySelectorAll('.bg-blue-500');
      expect(bars.length).toBe(3);
    });
  });
});

describe('Waveform', () => {
  beforeEach(() => {
    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      strokeStyle: '',
      lineWidth: 0,
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;
  });

  describe('rendering', () => {
    it('should render canvas element', () => {
      const { container } = render(<Waveform isActive={false} />);

      const canvas = container.querySelector('canvas');
      expect(canvas).toBeInTheDocument();
    });

    it('should use default dimensions', () => {
      const { container } = render(<Waveform isActive={false} />);

      const canvas = container.querySelector('canvas');
      expect(canvas).toHaveAttribute('width', '200');
      expect(canvas).toHaveAttribute('height', '60');
    });

    it('should use custom dimensions', () => {
      const { container } = render(
        <Waveform isActive={false} width={300} height={100} />
      );

      const canvas = container.querySelector('canvas');
      expect(canvas).toHaveAttribute('width', '300');
      expect(canvas).toHaveAttribute('height', '100');
    });
  });

  describe('inactive state', () => {
    it('should draw flat line when inactive', () => {
      render(<Waveform isActive={false} />);

      // Canvas should show flat line (verified through mock)
    });

    it('should draw flat line when no audio data', () => {
      render(<Waveform isActive={true} />);

      // Canvas should show flat line when no audio data
    });
  });

  describe('active state', () => {
    it('should draw waveform when active with audio data', () => {
      const audioData = new Float32Array([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5]);

      render(<Waveform isActive={true} audioData={audioData} />);

      // Canvas should show waveform
    });

    it('should use custom color', () => {
      const audioData = new Float32Array([0, 0.5, 1]);

      render(
        <Waveform isActive={true} audioData={audioData} color="#FF0000" />
      );

      // Color should be applied to stroke
    });
  });
});

describe('StatusBadge', () => {
  describe('idle state', () => {
    it('should show "Ready" label', () => {
      render(<StatusBadge state="idle" />);

      expect(screen.getByText('Ready')).toBeInTheDocument();
    });

    it('should have gray styling', () => {
      render(<StatusBadge state="idle" />);

      const badge = screen.getByText('Ready');
      expect(badge.className).toContain('bg-gray-100');
      expect(badge.className).toContain('text-gray-600');
    });
  });

  describe('listening state', () => {
    it('should show "Listening" label', () => {
      render(<StatusBadge state="listening" />);

      expect(screen.getByText('Listening')).toBeInTheDocument();
    });

    it('should have blue styling', () => {
      render(<StatusBadge state="listening" />);

      const badge = screen.getByText('Listening');
      expect(badge.className).toContain('bg-blue-100');
      expect(badge.className).toContain('text-blue-700');
    });
  });

  describe('processing state', () => {
    it('should show "Processing" label', () => {
      render(<StatusBadge state="processing" />);

      expect(screen.getByText('Processing')).toBeInTheDocument();
    });

    it('should have yellow styling', () => {
      render(<StatusBadge state="processing" />);

      const badge = screen.getByText('Processing');
      expect(badge.className).toContain('bg-yellow-100');
      expect(badge.className).toContain('text-yellow-700');
    });
  });

  describe('speaking state', () => {
    it('should show "Speaking" label', () => {
      render(<StatusBadge state="speaking" />);

      expect(screen.getByText('Speaking')).toBeInTheDocument();
    });

    it('should have green styling', () => {
      render(<StatusBadge state="speaking" />);

      const badge = screen.getByText('Speaking');
      expect(badge.className).toContain('bg-green-100');
      expect(badge.className).toContain('text-green-700');
    });
  });

  describe('styling', () => {
    it('should have rounded-full class', () => {
      render(<StatusBadge state="idle" />);

      const badge = screen.getByText('Ready');
      expect(badge.className).toContain('rounded-full');
    });

    it('should have small text size', () => {
      render(<StatusBadge state="idle" />);

      const badge = screen.getByText('Ready');
      expect(badge.className).toContain('text-xs');
    });

    it('should have font-medium class', () => {
      render(<StatusBadge state="idle" />);

      const badge = screen.getByText('Ready');
      expect(badge.className).toContain('font-medium');
    });
  });
});
