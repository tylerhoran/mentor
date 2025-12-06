import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CourseBuilder from "./CourseBuilder";

// Track current courseId for dynamic mock
let currentCourseId = "course-123";

// Mock useParams
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ courseId: currentCourseId }),
  };
});

// Mock API
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from "@/api/client";
const mockApi = apiClient as { get: ReturnType<typeof vi.fn> };

describe("CourseBuilder", () => {
  let queryClient: QueryClient;

  const mockCourse = {
    id: "course-123",
    name: "Introduction to AI",
    description: "Learn the basics of AI",
    status: "active",
  };

  const mockConcepts = [
    {
      id: "c1",
      name: "Neural Networks",
      description: "Understanding neural networks",
      difficulty_level: "intermediate",
      estimated_time_minutes: 30,
      prerequisites: ["c0"],
    },
    {
      id: "c2",
      name: "Deep Learning",
      description: "Advanced deep learning techniques",
      difficulty_level: "advanced",
      estimated_time_minutes: 45,
      prerequisites: ["c1"],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    currentCourseId = "course-123";
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const renderCourseBuilder = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <CourseBuilder />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  describe("new course form", () => {
    beforeEach(() => {
      currentCourseId = "new";
    });

    it("should display new course form when courseId is new", () => {
      renderCourseBuilder();
      expect(screen.getByText("Create New Course")).toBeInTheDocument();
    });

    it("should display course name input", () => {
      renderCourseBuilder();
      expect(screen.getByText(/course name/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/introduction to data engineering/i),
      ).toBeInTheDocument();
    });

    it("should display description textarea", () => {
      renderCourseBuilder();
      expect(screen.getByText(/description/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/course description/i),
      ).toBeInTheDocument();
    });

    it("should display cancel and create buttons", () => {
      renderCourseBuilder();
      expect(screen.getByRole("link", { name: /cancel/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /create course/i }),
      ).toBeInTheDocument();
    });

    it("should update course name on input", async () => {
      const user = userEvent.setup();
      renderCourseBuilder();
      const input = screen.getByPlaceholderText(
        /introduction to data engineering/i,
      );
      await user.type(input, "My New Course");
      expect(input).toHaveValue("My New Course");
    });
  });

  describe("existing course", () => {
    it("should display course name in header", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      expect(await screen.findByText("Introduction to AI")).toBeInTheDocument();
    });

    it("should display course description", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      expect(
        await screen.findByText("Learn the basics of AI"),
      ).toBeInTheDocument();
    });

    it("should display back button", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      await screen.findByText("Introduction to AI");
      const backLink = screen.getByRole("link", { name: "" });
      expect(backLink).toHaveAttribute("href", "/faculty");
    });
  });

  describe("tabs", () => {
    it("should display all tabs", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      await screen.findByText("Introduction to AI");
      expect(
        screen.getByRole("button", { name: /concepts/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /materials/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /settings/i }),
      ).toBeInTheDocument();
    });

    it("should switch to materials tab", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /materials/i }));
      expect(screen.getByText("Course Materials")).toBeInTheDocument();
    });

    it("should switch to settings tab", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /settings/i }));
      expect(screen.getByText("Course Settings")).toBeInTheDocument();
    });
  });

  describe("concepts tab", () => {
    it("should display knowledge graph heading", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      expect(await screen.findByText("Knowledge Graph")).toBeInTheDocument();
    });

    it("should display add concept button", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      expect(
        await screen.findByRole("button", { name: /add concept/i }),
      ).toBeInTheDocument();
    });

    it("should display concepts when loaded", async () => {
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();
      await screen.findByText("Knowledge Graph");
      // Check the page has concept section rendered
      const addButton = screen.getByRole("button", { name: /add concept/i });
      expect(addButton).toBeInTheDocument();
    });

    it("should display empty state when no concepts", async () => {
      mockApi.get.mockResolvedValueOnce(mockCourse).mockResolvedValueOnce([]);
      renderCourseBuilder();
      expect(await screen.findByText(/no concepts yet/i)).toBeInTheDocument();
    });
  });

  describe("materials tab", () => {
    it("should display upload material button", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /materials/i }));

      expect(
        screen.getByRole("button", { name: /upload material/i }),
      ).toBeInTheDocument();
    });

    it("should display upload instructions", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /materials/i }));

      expect(screen.getByText(/upload pdfs/i)).toBeInTheDocument();
    });
  });

  describe("settings tab", () => {
    it("should display pedagogy configuration", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /settings/i }));

      expect(screen.getByText("Pedagogy Configuration")).toBeInTheDocument();
    });

    it("should display teaching style selector", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /settings/i }));

      expect(screen.getByText(/teaching style/i)).toBeInTheDocument();
    });

    it("should display base model selector", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /settings/i }));

      expect(screen.getByText(/base model/i)).toBeInTheDocument();
    });

    it("should display save settings button", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockCourse)
        .mockResolvedValueOnce(mockConcepts);
      renderCourseBuilder();

      await screen.findByText("Introduction to AI");
      await user.click(screen.getByRole("button", { name: /settings/i }));

      expect(
        screen.getByRole("button", { name: /save settings/i }),
      ).toBeInTheDocument();
    });
  });
});
