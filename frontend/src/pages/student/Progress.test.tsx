import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Progress from "./Progress";

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

describe("Progress", () => {
  let queryClient: QueryClient;

  const mockProgress = {
    course_id: "course-123",
    course_name: "Introduction to AI",
    overall_mastery: 0.75,
    total_time_minutes: 120,
    total_interactions: 45,
    concepts: [
      {
        id: "c1",
        name: "Neural Networks",
        description: "Understanding neural networks",
        mastery_level: 0.85,
        attempts: 10,
        last_practiced: "2024-01-15T10:00:00Z",
        prerequisites_met: true,
        is_unlocked: true,
      },
      {
        id: "c2",
        name: "Deep Learning",
        description: "Advanced deep learning techniques",
        mastery_level: 0.45,
        attempts: 5,
        last_practiced: null,
        prerequisites_met: false,
        is_unlocked: false,
      },
    ],
    learning_trajectory: [
      { date: "2024-01-01", mastery: 0.2, concepts_practiced: 1 },
      { date: "2024-01-08", mastery: 0.5, concepts_practiced: 2 },
      { date: "2024-01-15", mastery: 0.75, concepts_practiced: 3 },
    ],
    strengths: ["Pattern Recognition", "Data Analysis"],
    areas_for_improvement: ["Mathematical Foundations"],
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

  const renderProgress = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Progress />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe("loading state", () => {
    it("should show loading spinner while fetching", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {}));
      renderProgress();
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("should show message when no progress data", async () => {
      mockApi.get.mockResolvedValueOnce(null);
      renderProgress();
      expect(
        await screen.findByText(/progress data not available/i)
      ).toBeInTheDocument();
    });
  });

  describe("with progress data", () => {
    it("should display page title", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("My Progress")).toBeInTheDocument();
    });

    it("should display course name", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Introduction to AI")).toBeInTheDocument();
    });

    it("should display overall mastery percentage", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("75%")).toBeInTheDocument();
    });

    it("should display total time spent", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("120")).toBeInTheDocument();
      expect(screen.getByText("Minutes Learning")).toBeInTheDocument();
    });

    it("should display total interactions", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("45")).toBeInTheDocument();
      expect(screen.getByText("Interactions")).toBeInTheDocument();
    });

    it("should display continue learning button", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(
        await screen.findByRole("button", { name: /continue learning/i })
      ).toBeInTheDocument();
    });

    it("should display back to dashboard link", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(
        await screen.findByRole("link", { name: /back to dashboard/i })
      ).toBeInTheDocument();
    });
  });

  describe("concepts display", () => {
    it("should display concept names", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Neural Networks")).toBeInTheDocument();
      expect(screen.getByText("Deep Learning")).toBeInTheDocument();
    });

    it("should display concept descriptions", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(
        await screen.findByText("Understanding neural networks")
      ).toBeInTheDocument();
    });

    it("should show mastery labels", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      await screen.findByText("Neural Networks");
      expect(screen.getByText("Mastered")).toBeInTheDocument();
      expect(screen.getByText("Developing")).toBeInTheDocument();
    });

    it("should show locked indicator for locked concepts", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Locked")).toBeInTheDocument();
    });

    it("should display attempt counts", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("10 attempts")).toBeInTheDocument();
      expect(screen.getByText("5 attempts")).toBeInTheDocument();
    });
  });

  describe("insights section", () => {
    it("should display strengths", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Strengths")).toBeInTheDocument();
      expect(screen.getByText("Pattern Recognition")).toBeInTheDocument();
      expect(screen.getByText("Data Analysis")).toBeInTheDocument();
    });

    it("should display areas for improvement", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Focus Areas")).toBeInTheDocument();
      expect(screen.getByText("Mathematical Foundations")).toBeInTheDocument();
    });
  });

  describe("learning trajectory", () => {
    it("should display learning trajectory section", async () => {
      mockApi.get.mockResolvedValueOnce(mockProgress);
      renderProgress();
      expect(await screen.findByText("Learning Trajectory")).toBeInTheDocument();
    });
  });
});
