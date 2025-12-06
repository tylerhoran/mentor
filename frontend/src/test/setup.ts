import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock localStorage
const localStorageStore: Record<string, string> = {};
const localStorageMock = {
  getItem: vi.fn((key: string) => localStorageStore[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageStore[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete localStorageStore[key];
  }),
  clear: vi.fn(() => {
    Object.keys(localStorageStore).forEach(
      (key) => delete localStorageStore[key],
    );
  }),
  key: vi.fn((index: number) => Object.keys(localStorageStore)[index] || null),
  get length() {
    return Object.keys(localStorageStore).length;
  },
};

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Mock Web Audio API
class MockAudioContext {
  state = "running";
  sampleRate = 16000;
  currentTime = 0;

  createMediaStreamSource = vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  }));

  createScriptProcessor = vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    onaudioprocess: null,
  }));

  createBufferSource = vi.fn(() => ({
    buffer: null,
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    onended: null,
  }));

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  decodeAudioData = vi.fn(async (_buffer: ArrayBuffer) => ({
    duration: 1.0,
    length: 16000,
    sampleRate: 16000,
    numberOfChannels: 1,
    getChannelData: () => new Float32Array(16000),
  }));

  resume = vi.fn(async () => {});
  suspend = vi.fn(async () => {});
  close = vi.fn(async () => {
    this.state = "closed";
  });

  get destination() {
    return {};
  }
}

// @ts-expect-error - mocking global
global.AudioContext = MockAudioContext;

// Mock MediaDevices
const mockMediaStream = {
  getTracks: () => [{ stop: vi.fn() }],
};

Object.defineProperty(navigator, "mediaDevices", {
  value: {
    getUserMedia: vi.fn(async () => mockMediaStream),
  },
  writable: true,
});

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event("open"));
    }, 0);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  });
}

// @ts-expect-error - mocking global
global.WebSocket = MockWebSocket;

// Mock crypto.randomUUID
Object.defineProperty(global, "crypto", {
  value: {
    randomUUID: () => "test-uuid-" + Math.random().toString(36).substr(2, 9),
  },
});

// Mock window.location
Object.defineProperty(window, "location", {
  value: {
    protocol: "http:",
    host: "localhost:3000",
    href: "http://localhost:3000",
  },
  writable: true,
});

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

global.ResizeObserver = MockResizeObserver;

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

global.IntersectionObserver =
  MockIntersectionObserver as unknown as typeof IntersectionObserver;

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();
