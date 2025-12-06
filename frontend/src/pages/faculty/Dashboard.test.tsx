import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import FacultyDashboard from "./Dashboard";

// Mock auth store
const mockLogout = vi.fn();
vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    user: { id: "1", email: "prof@university.edu", full_name: "Prof. Smith" },
    logout: mockLogout,
  }),
}));

// Mock API
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from "@/api/client";
const mockApi = apiClient as { get: ReturnType<typeof vi.fn> };

describe("FacultyDashboard", () => {
  let queryClient: QueryClient;

  const mockCourses = [
    {
      id: "course-1",
      name: "Introduction to AI",
      description: "Learn the basics of AI",
      status: "active",
    },
    {
      id: "course-2",
      name: "Data Structures",
      description: "Fundamental data structures",
      status: "draft",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const renderDashboard = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <FacultyDashboard />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe("header", () => {
    it("should display app title", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(await screen.findByText("Mentor")).toBeInTheDocument();
    });

    it("should display user email", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByText("prof@university.edu")
      ).toBeInTheDocument();
    });

    it("should display sign out button", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByRole("button", { name: /sign out/i })
      ).toBeInTheDocument();
    });

    it("should call logout when sign out clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();

      const signOutBtn = await screen.findByRole("button", {
        name: /sign out/i,
      });
      await user.click(signOutBtn);
      expect(mockLogout).toHaveBeenCalled();
    });
  });

  describe("page content", () => {
    it("should display Your Courses heading", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(await screen.findByText("Your Courses")).toBeInTheDocument();
    });

    it("should display New Course button", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByRole("link", { name: /new course/i })
      ).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("should show skeleton cards while loading", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {}));
      renderDashboard();
      const skeletonCards = document.querySelectorAll(".animate-pulse");
      expect(skeletonCards.length).toBeGreaterThan(0);
    });
  });

  describe("empty state", () => {
    it("should show no courses message", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(await screen.findByText(/no courses yet/i)).toBeInTheDocument();
    });

    it("should show create course button in empty state", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByRole("link", { name: /create course/i })
      ).toBeInTheDocument();
    });
  });

  describe("with courses", () => {
    it("should display course names", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      expect(await screen.findByText("Introduction to AI")).toBeInTheDocument();
      expect(screen.getByText("Data Structures")).toBeInTheDocument();
    });

    it("should display course descriptions", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findByText("Introduction to AI");
      expect(screen.getByText("Learn the basics of AI")).toBeInTheDocument();
    });

    it("should display course status badges", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findByText("Introduction to AI");
      expect(screen.getByText("active")).toBeInTheDocument();
      expect(screen.getByText("draft")).toBeInTheDocument();
    });

    it("should display Edit button for each course", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findByText("Introduction to AI");
      const editButtons = screen.getAllByRole("link", { name: /edit/i });
      expect(editButtons.length).toBe(2);
    });

    it("should display Analytics button for each course", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findByText("Introduction to AI");
      const analyticsButtons = screen.getAllByRole("link", {
        name: /analytics/i,
      });
      expect(analyticsButtons.length).toBe(2);
    });
  });
});
