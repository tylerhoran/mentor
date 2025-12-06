import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentDashboard from "./Dashboard";

// Mock auth store
vi.mock("../../stores/auth", () => ({
  useAuthStore: () => ({
    user: { id: "1", full_name: "John Doe", email: "john@example.com" },
  }),
}));

// Mock API
vi.mock("../../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

// Import api after mock
import { api } from "../../api/client";
const mockApi = api as { get: ReturnType<typeof vi.fn> };

describe("StudentDashboard", () => {
  let queryClient: QueryClient;

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
          <StudentDashboard />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  describe("rendering", () => {
    it("should render welcome message with user name", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByText(/welcome back, john/i),
      ).toBeInTheDocument();
    });

    it("should render subtitle", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByText(/continue your learning journey/i),
      ).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("should show loading spinner while fetching courses", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves
      renderDashboard();
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("should show no courses message when empty", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(await screen.findByText(/no courses yet/i)).toBeInTheDocument();
    });

    it("should show enrollment code button when no courses", async () => {
      mockApi.get.mockResolvedValueOnce([]);
      renderDashboard();
      expect(
        await screen.findByRole("button", { name: /enter enrollment code/i }),
      ).toBeInTheDocument();
    });
  });

  describe("with courses", () => {
    const mockCourses = [
      {
        id: "course-1",
        name: "Introduction to AI",
        code: "CS101",
        instructor_name: "Prof. Smith",
        enrolled_at: "2024-01-01",
        overall_mastery: 0.75,
        concepts_mastered: 3,
        total_concepts: 4,
        last_session: "2024-01-15T10:00:00Z",
      },
      {
        id: "course-2",
        name: "Data Structures",
        code: "CS201",
        instructor_name: "Prof. Johnson",
        enrolled_at: "2024-01-02",
        overall_mastery: 0.5,
        concepts_mastered: 2,
        total_concepts: 4,
        last_session: null,
      },
    ];

    it("should display course list", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      const aiCourses = await screen.findAllByText("Introduction to AI");
      expect(aiCourses.length).toBeGreaterThan(0);
      const dsCourses = screen.getAllByText("Data Structures");
      expect(dsCourses.length).toBeGreaterThan(0);
    });

    it("should display course codes and instructors", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findAllByText("Introduction to AI");
      const cs101Elements = screen.getAllByText(/CS101/);
      expect(cs101Elements.length).toBeGreaterThan(0);
      expect(screen.getByText(/Prof. Smith/)).toBeInTheDocument();
    });

    it("should display mastery progress", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findAllByText("Introduction to AI");
      expect(screen.getByText("75%")).toBeInTheDocument();
      expect(screen.getByText("3/4 concepts")).toBeInTheDocument();
    });

    it("should display action buttons for each course", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findAllByText("Introduction to AI");
      const progressButtons = screen.getAllByRole("button", {
        name: /progress/i,
      });
      const historyButtons = screen.getAllByRole("button", {
        name: /history/i,
      });
      const learnButtons = screen.getAllByRole("button", { name: /learn/i });
      expect(progressButtons.length).toBeGreaterThan(0);
      expect(historyButtons.length).toBeGreaterThan(0);
      expect(learnButtons.length).toBeGreaterThan(0);
    });

    it("should display My Courses section", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      expect(await screen.findByText("My Courses")).toBeInTheDocument();
    });

    it("should display recent activity section", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      expect(await screen.findByText("Recent Activity")).toBeInTheDocument();
    });

    it("should show continue link for courses with last session", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourses);
      renderDashboard();
      await screen.findAllByText("Introduction to AI");
      const continueLinks = screen.getAllByText("Continue");
      expect(continueLinks.length).toBeGreaterThan(0);
    });
  });

  describe("mastery colors", () => {
    it("should show green for high mastery (80%+)", async () => {
      mockApi.get.mockResolvedValueOnce([
        {
          id: "1",
          name: "High Mastery Course",
          code: "C1",
          instructor_name: "Prof",
          enrolled_at: "2024-01-01",
          overall_mastery: 0.85,
          concepts_mastered: 4,
          total_concepts: 4,
          last_session: null,
        },
      ]);
      renderDashboard();
      await screen.findAllByText("High Mastery Course");
      const progressBars = document.querySelectorAll(".bg-green-500");
      expect(progressBars.length).toBeGreaterThan(0);
    });

    it("should show yellow for medium mastery (60-80%)", async () => {
      mockApi.get.mockResolvedValueOnce([
        {
          id: "1",
          name: "Medium Mastery Course",
          code: "C1",
          instructor_name: "Prof",
          enrolled_at: "2024-01-01",
          overall_mastery: 0.65,
          concepts_mastered: 3,
          total_concepts: 4,
          last_session: null,
        },
      ]);
      renderDashboard();
      await screen.findAllByText("Medium Mastery Course");
      const progressBars = document.querySelectorAll(".bg-yellow-500");
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });
});
