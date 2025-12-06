import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { create } from "zustand";

// Mock the API client
const mockPost = vi.fn();
const mockGet = vi.fn();
const mockSetToken = vi.fn();

vi.mock("../api/client", () => ({
  apiClient: {
    post: (...args: unknown[]) => mockPost(...args),
    get: (...args: unknown[]) => mockGet(...args),
    setToken: (...args: unknown[]) => mockSetToken(...args),
  },
}));

// Create a non-persisted version for testing
interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "faculty" | "student" | "admin" | "researcher";
  institution_id: string | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
    role: string,
  ) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

// Import apiClient after mock is set up
import { apiClient } from "../api/client";

// Create a test store without persist middleware
const createTestStore = () =>
  create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,

    login: async (email: string, password: string) => {
      set({ isLoading: true });
      try {
        const response = await apiClient.post<{
          access_token: string;
          refresh_token: string;
        }>("/auth/login", { email, password });

        apiClient.setToken(response.access_token);
        localStorage.setItem("refresh_token", response.refresh_token);

        const user = await apiClient.get<User>("/auth/me");
        set({ user, isAuthenticated: true, isLoading: false });
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },

    register: async (
      email: string,
      password: string,
      fullName: string,
      role: string,
    ) => {
      set({ isLoading: true });
      try {
        await apiClient.post("/auth/register", {
          email,
          password,
          full_name: fullName,
          role,
        });
        set({ isLoading: false });
      } catch (error) {
        set({ isLoading: false });
        throw error;
      }
    },

    logout: () => {
      apiClient.setToken(null);
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false });
    },

    fetchUser: async () => {
      try {
        const user = await apiClient.get<User>("/auth/me");
        set({ user, isAuthenticated: true });
      } catch {
        set({ user: null, isAuthenticated: false });
      }
    },
  }));

describe("useAuthStore", () => {
  let useTestAuthStore: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage items individually since jsdom may not support clear()
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("access_token");
    useTestAuthStore = createTestStore();
  });

  describe("initial state", () => {
    it("should have null user initially", () => {
      const { result } = renderHook(() => useTestAuthStore());
      expect(result.current.user).toBeNull();
    });

    it("should not be authenticated initially", () => {
      const { result } = renderHook(() => useTestAuthStore());
      expect(result.current.isAuthenticated).toBe(false);
    });

    it("should not be loading initially", () => {
      const { result } = renderHook(() => useTestAuthStore());
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("login", () => {
    const mockUser = {
      id: "user-123",
      email: "test@example.com",
      full_name: "Test User",
      role: "student" as const,
      institution_id: null,
    };

    it("should login successfully", async () => {
      mockPost.mockResolvedValueOnce({
        access_token: "test-access-token",
        refresh_token: "test-refresh-token",
      });
      mockGet.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(mockSetToken).toHaveBeenCalledWith("test-access-token");
    });

    it("should throw error on login failure", async () => {
      mockPost.mockRejectedValueOnce(new Error("Invalid credentials"));

      const { result } = renderHook(() => useTestAuthStore());

      await expect(
        act(async () => {
          await result.current.login("test@example.com", "wrongpassword");
        }),
      ).rejects.toThrow("Invalid credentials");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it("should store refresh token in localStorage", async () => {
      mockPost.mockResolvedValueOnce({
        access_token: "test-access-token",
        refresh_token: "test-refresh-token",
      });
      mockGet.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(localStorage.getItem("refresh_token")).toBe("test-refresh-token");
    });

    it("should set loading state during login", async () => {
      let resolvePost: (value: unknown) => void;
      mockPost.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolvePost = resolve;
          }),
      );

      const { result } = renderHook(() => useTestAuthStore());

      // Start login but don't await
      let loginPromise: Promise<void>;
      act(() => {
        loginPromise = result.current.login("test@example.com", "password123");
      });

      // Should be loading
      expect(result.current.isLoading).toBe(true);

      // Complete the login
      await act(async () => {
        resolvePost!({
          access_token: "token",
          refresh_token: "refresh",
        });
        mockGet.mockResolvedValueOnce(mockUser);
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("register", () => {
    it("should register successfully", async () => {
      mockPost.mockResolvedValueOnce({});

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.register(
          "new@example.com",
          "password123",
          "New User",
          "student",
        );
      });

      expect(mockPost).toHaveBeenCalledWith("/auth/register", {
        email: "new@example.com",
        password: "password123",
        full_name: "New User",
        role: "student",
      });
      expect(result.current.isLoading).toBe(false);
    });

    it("should throw error on registration failure", async () => {
      mockPost.mockRejectedValueOnce(new Error("Email already registered"));

      const { result } = renderHook(() => useTestAuthStore());

      await expect(
        act(async () => {
          await result.current.register(
            "existing@example.com",
            "password123",
            "User",
            "student",
          );
        }),
      ).rejects.toThrow("Email already registered");

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("logout", () => {
    it("should clear user and authentication state", async () => {
      // Set up authenticated state first via login
      mockPost.mockResolvedValueOnce({
        access_token: "token",
        refresh_token: "refresh",
      });
      mockGet.mockResolvedValueOnce({
        id: "user-123",
        email: "test@example.com",
        full_name: "Test User",
        role: "student",
        institution_id: null,
      });

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(result.current.isAuthenticated).toBe(true);

      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it("should clear token from API client", () => {
      const { result } = renderHook(() => useTestAuthStore());

      act(() => {
        result.current.logout();
      });

      expect(mockSetToken).toHaveBeenCalledWith(null);
    });

    it("should remove refresh token from localStorage", () => {
      localStorage.setItem("refresh_token", "some-token");

      const { result } = renderHook(() => useTestAuthStore());

      act(() => {
        result.current.logout();
      });

      expect(localStorage.getItem("refresh_token")).toBeNull();
    });
  });

  describe("fetchUser", () => {
    it("should fetch and set user", async () => {
      const mockUser = {
        id: "user-123",
        email: "test@example.com",
        full_name: "Test User",
        role: "student" as const,
        institution_id: null,
      };
      mockGet.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.fetchUser();
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it("should clear auth state on fetch failure", async () => {
      // Set up authenticated state first
      mockPost.mockResolvedValueOnce({
        access_token: "token",
        refresh_token: "refresh",
      });
      mockGet.mockResolvedValueOnce({
        id: "1",
        email: "test@example.com",
        full_name: null,
        role: "student",
        institution_id: null,
      });

      const { result } = renderHook(() => useTestAuthStore());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(result.current.isAuthenticated).toBe(true);

      // Now fetch should fail
      mockGet.mockRejectedValueOnce(new Error("Unauthorized"));

      await act(async () => {
        await result.current.fetchUser();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});
