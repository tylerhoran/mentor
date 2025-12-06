import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Mock window.location
const mockLocation = { href: "" };
vi.stubGlobal("window", { location: mockLocation });

// Mock localStorage
let store: Record<string, string> = {};
const localStorageMock = {
  getItem: vi.fn((key: string) => store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete store[key];
  }),
  clear: vi.fn(() => {
    store = {};
  }),
};
vi.stubGlobal("localStorage", localStorageMock);

// We need to dynamically import to get the module after mocks are set
const getApiClient = async () => {
  const module = await import("./client");
  return module.apiClient;
};

describe("ApiClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    store = {};
    mockLocation.href = "";
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("setToken", () => {
    it("should store token in localStorage", async () => {
      const apiClient = await getApiClient();
      apiClient.setToken("test-token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "access_token",
        "test-token",
      );
    });

    it("should remove token from localStorage when null", async () => {
      const apiClient = await getApiClient();
      apiClient.setToken(null);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("access_token");
    });
  });

  describe("get", () => {
    it("should make GET request", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: "test" }),
      });

      const result = await apiClient.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        expect.objectContaining({ method: "GET" }),
      );
      expect(result).toEqual({ data: "test" });
    });

    it("should include query params", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      await apiClient.get("/test", { foo: "bar", baz: "qux" });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/test\?.*foo=bar/),
        expect.anything(),
      );
    });

    it("should include Authorization header when token is set", async () => {
      const apiClient = await getApiClient();
      apiClient.setToken("my-token");
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      await apiClient.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer my-token",
          }),
        }),
      );
    });
  });

  describe("post", () => {
    it("should make POST request with JSON body", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });

      const result = await apiClient.post("/test", { name: "test" });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ name: "test" }),
        }),
      );
      expect(result).toEqual({ success: true });
    });

    it("should handle POST without body", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      await apiClient.post("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          method: "POST",
          body: undefined,
        }),
      );
    });
  });

  describe("patch", () => {
    it("should make PATCH request", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ updated: true }),
      });

      const result = await apiClient.patch("/test/1", { name: "updated" });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/1"),
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ name: "updated" }),
        }),
      );
      expect(result).toEqual({ updated: true });
    });
  });

  describe("delete", () => {
    it("should make DELETE request", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ deleted: true }),
      });

      const result = await apiClient.delete("/test/1");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/1"),
        expect.objectContaining({ method: "DELETE" }),
      );
      expect(result).toEqual({ deleted: true });
    });
  });

  describe("error handling", () => {
    it("should throw error on non-ok response", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: "Bad request" }),
      });

      await expect(apiClient.get("/test")).rejects.toThrow("Bad request");
    });

    it("should redirect to login on 401", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" }),
      });

      await expect(apiClient.get("/test")).rejects.toThrow();
      expect(mockLocation.href).toBe("/login");
    });

    it("should clear token on 401", async () => {
      const apiClient = await getApiClient();
      apiClient.setToken("old-token");
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" }),
      });

      await expect(apiClient.get("/test")).rejects.toThrow();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("access_token");
    });

    it("should handle json parse errors", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error("Invalid JSON");
        },
      });

      await expect(apiClient.get("/test")).rejects.toThrow("Request failed");
    });
  });

  describe("204 No Content", () => {
    it("should return empty object for 204 responses", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const result = await apiClient.delete("/test/1");
      expect(result).toEqual({});
    });
  });

  describe("uploadFile", () => {
    it("should upload file with FormData", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ fileId: "123" }),
      });

      const file = new File(["content"], "test.txt", { type: "text/plain" });
      const result = await apiClient.uploadFile("/upload", file);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/upload"),
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        }),
      );
      expect(result).toEqual({ fileId: "123" });
    });

    it("should include additional data in FormData", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      const file = new File(["content"], "test.txt", { type: "text/plain" });
      await apiClient.uploadFile("/upload", file, { folder: "docs" });

      const call = mockFetch.mock.calls[0];
      const formData = call[1].body as FormData;
      expect(formData.get("folder")).toBe("docs");
    });

    it("should throw on upload error", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: "File too large" }),
      });

      const file = new File(["content"], "test.txt", { type: "text/plain" });
      await expect(apiClient.uploadFile("/upload", file)).rejects.toThrow(
        "File too large",
      );
    });
  });

  describe("streamPost", () => {
    it("should yield streamed data chunks", async () => {
      const apiClient = await getApiClient();
      const encoder = new TextEncoder();
      const chunks = [
        encoder.encode("data: chunk1\n"),
        encoder.encode("data: chunk2\n"),
        encoder.encode("data: [DONE]\n"),
      ];

      let chunkIndex = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          if (chunkIndex < chunks.length) {
            return { done: false, value: chunks[chunkIndex++] };
          }
          return { done: true, value: undefined };
        }),
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const results: string[] = [];
      for await (const chunk of apiClient.streamPost("/stream", {
        message: "test",
      })) {
        results.push(chunk);
      }

      expect(results).toEqual(["chunk1", "chunk2"]);
    });

    it("should throw on stream error", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const generator = apiClient.streamPost("/stream", {});
      await expect(generator.next()).rejects.toThrow("Stream request failed");
    });

    it("should throw if no response body", async () => {
      const apiClient = await getApiClient();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: null,
      });

      const generator = apiClient.streamPost("/stream", {});
      await expect(generator.next()).rejects.toThrow("No response body");
    });
  });
});
