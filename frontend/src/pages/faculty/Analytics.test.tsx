import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Analytics from "./Analytics";

// Mock useParams
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ courseId: "course-123" }),
  };
});

// Mock API
vi.mock("../../api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

import { api } from "../../api/client";
const mockApi = api as { get: ReturnType<typeof vi.fn> };

describe("Analytics", () => {
  let queryClient: QueryClient;

  const mockOverview = {
    course_id: "course-123",
    course_name: "Introduction to AI",
    total_students: 45,
    active_students_7d: 32,
    total_interactions: 1250,
    avg_mastery: 0.72,
    concept_stats: [
      {
        concept_id: "c1",
        concept_name: "Neural Networks",
        avg_mastery: 0.85,
        student_count: 45,
        struggling_count: 3,
      },
      {
        concept_id: "c2",
        concept_name: "Deep Learning",
        avg_mastery: 0.55,
        student_count: 40,
        struggling_count: 12,
      },
    ],
    engagement_trend: [
      { date: "2024-01-01", active_students: 20, interactions: 100 },
      { date: "2024-01-08", active_students: 25, interactions: 150 },
    ],
    at_risk_students: [
      {
        student_id: "s1",
        full_name: "John Doe",
        email: "john@example.com",
        risk_factors: ["Low engagement", "Falling behind"],
        last_active: "2024-01-10",
        avg_mastery: 0.35,
      },
    ],
  };

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

  const renderAnalytics = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Analytics />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  describe("loading state", () => {
    it("should show loading spinner while fetching", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {}));
      renderAnalytics();
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("should show message when no data", async () => {
      mockApi.get.mockResolvedValueOnce(null);
      renderAnalytics();
      expect(
        await screen.findByText(/no analytics data available/i),
      ).toBeInTheDocument();
    });
  });

  describe("page structure", () => {
    it("should display page title", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("Class Analytics")).toBeInTheDocument();
    });

    it("should display course name", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("Introduction to AI")).toBeInTheDocument();
    });

    it("should display back to course link", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(
        await screen.findByRole("link", { name: /back to course/i }),
      ).toBeInTheDocument();
    });
  });

  describe("time range selector", () => {
    it("should display time range buttons", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      await screen.findByText("Class Analytics");
      expect(
        screen.getByRole("button", { name: "7 Days" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "30 Days" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "90 Days" }),
      ).toBeInTheDocument();
    });

    it("should update time range when clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValue(mockOverview);
      renderAnalytics();

      await screen.findByText("Class Analytics");
      const sevenDaysBtn = screen.getByRole("button", { name: "7 Days" });
      await user.click(sevenDaysBtn);

      // Should refetch with new range
      expect(mockApi.get).toHaveBeenCalled();
    });
  });

  describe("summary stats", () => {
    it("should display total students", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      const totalStudentsLabels = await screen.findAllByText("Total Students");
      expect(totalStudentsLabels.length).toBeGreaterThan(0);
    });

    it("should display active students", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("Active (7 days)")).toBeInTheDocument();
    });

    it("should display total interactions", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("Total Interactions")).toBeInTheDocument();
    });

    it("should display average mastery", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      const avgMasteryLabels = await screen.findAllByText("Avg Mastery");
      expect(avgMasteryLabels.length).toBeGreaterThan(0);
    });
  });

  describe("engagement trend", () => {
    it("should display engagement trend section", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("Engagement Trend")).toBeInTheDocument();
    });
  });

  describe("at-risk students", () => {
    it("should display at-risk students section", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("At-Risk Students")).toBeInTheDocument();
    });

    it("should display at-risk student names", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(await screen.findByText("John Doe")).toBeInTheDocument();
    });

    it("should display risk factors", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      await screen.findByText("John Doe");
      expect(screen.getByText("Low engagement")).toBeInTheDocument();
      expect(screen.getByText("Falling behind")).toBeInTheDocument();
    });

    it("should show no at-risk students message when empty", async () => {
      mockApi.get.mockResolvedValueOnce({
        ...mockOverview,
        at_risk_students: [],
      });
      renderAnalytics();
      expect(
        await screen.findByText(/no at-risk students identified/i),
      ).toBeInTheDocument();
    });
  });

  describe("concept performance", () => {
    it("should display concept performance section", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      expect(
        await screen.findByText("Concept Performance"),
      ).toBeInTheDocument();
    });

    it("should display concept names", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      await screen.findByText("Concept Performance");
      expect(screen.getByText("Neural Networks")).toBeInTheDocument();
      expect(screen.getByText("Deep Learning")).toBeInTheDocument();
    });

    it("should display struggling counts", async () => {
      mockApi.get.mockResolvedValueOnce(mockOverview);
      renderAnalytics();
      await screen.findByText("Concept Performance");
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("12")).toBeInTheDocument();
    });
  });
});
