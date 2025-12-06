import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StudentView from "./StudentView";

// Mock useParams
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ courseId: "course-123", studentId: "student-456" }),
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

describe("StudentView", () => {
  let queryClient: QueryClient;

  const mockStudent = {
    id: "student-456",
    email: "john@example.com",
    full_name: "John Doe",
    enrolled_at: "2024-01-01T00:00:00Z",
    last_active: "2024-01-15T10:00:00Z",
    total_interactions: 150,
    total_time_minutes: 300,
    concept_masteries: [
      {
        concept_id: "c1",
        concept_name: "Neural Networks",
        mastery_level: 0.85,
        attempts: 10,
        last_interaction: "2024-01-15T10:00:00Z",
      },
      {
        concept_id: "c2",
        concept_name: "Deep Learning",
        mastery_level: 0.45,
        attempts: 5,
        last_interaction: "2024-01-14T10:00:00Z",
      },
    ],
    recent_sessions: [
      {
        id: "s1",
        started_at: "2024-01-15T10:00:00Z",
        ended_at: "2024-01-15T10:30:00Z",
        message_count: 20,
        concepts_covered: ["Neural Networks", "Backpropagation"],
      },
    ],
    gaming_flags: [
      {
        id: "f1",
        detected_at: "2024-01-14T10:00:00Z",
        signal_type: "Rapid responses",
        severity: "medium",
        details: "Unusually fast response pattern detected",
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

  const renderStudentView = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <StudentView />
        </BrowserRouter>
      </QueryClientProvider>,
    );
  };

  describe("loading state", () => {
    it("should show loading spinner while fetching", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {}));
      renderStudentView();
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("should show message when student not found", async () => {
      mockApi.get.mockResolvedValueOnce(null);
      renderStudentView();
      expect(await screen.findByText(/student not found/i)).toBeInTheDocument();
    });
  });

  describe("student header", () => {
    it("should display student name", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("John Doe")).toBeInTheDocument();
    });

    it("should display student email", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("john@example.com")).toBeInTheDocument();
    });

    it("should display back to course link", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(
        await screen.findByRole("link", { name: /back to course/i }),
      ).toBeInTheDocument();
    });

    it("should display verification report button", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(
        await screen.findByRole("button", {
          name: /generate verification report/i,
        }),
      ).toBeInTheDocument();
    });
  });

  describe("stats overview", () => {
    it("should display total interactions", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("150")).toBeInTheDocument();
      expect(screen.getByText("Total Interactions")).toBeInTheDocument();
    });

    it("should display minutes engaged", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("300")).toBeInTheDocument();
      expect(screen.getByText("Minutes Engaged")).toBeInTheDocument();
    });

    it("should display concepts mastered count", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      await screen.findByText("John Doe");
      expect(screen.getByText("Concepts Mastered")).toBeInTheDocument();
    });

    it("should display gaming flags count", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      await screen.findByText("John Doe");
      expect(screen.getByText("Gaming Flags")).toBeInTheDocument();
    });
  });

  describe("tabs", () => {
    it("should display all tabs", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      await screen.findByText("John Doe");
      expect(
        screen.getByRole("button", { name: /overview/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /mastery/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /sessions/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /flags/i }),
      ).toBeInTheDocument();
    });

    it("should switch to mastery tab when clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /mastery/i }));
      expect(screen.getByText("Concept Mastery")).toBeInTheDocument();
    });

    it("should switch to sessions tab when clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /sessions/i }));
      expect(screen.getByText("Session History")).toBeInTheDocument();
    });

    it("should switch to flags tab when clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /flags/i }));
      expect(screen.getByText("Gaming Detection Flags")).toBeInTheDocument();
    });
  });

  describe("overview tab", () => {
    it("should display learning progress section", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("Learning Progress")).toBeInTheDocument();
    });

    it("should display concept names", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      await screen.findByText("Learning Progress");
      expect(screen.getByText("Neural Networks")).toBeInTheDocument();
    });

    it("should display recent sessions section", async () => {
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();
      expect(await screen.findByText("Recent Sessions")).toBeInTheDocument();
    });
  });

  describe("mastery tab", () => {
    it("should display all concepts with mastery levels", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /mastery/i }));

      expect(screen.getByText("Neural Networks")).toBeInTheDocument();
      expect(screen.getByText("Deep Learning")).toBeInTheDocument();
      expect(screen.getByText("85%")).toBeInTheDocument();
      expect(screen.getByText("45%")).toBeInTheDocument();
    });

    it("should display attempt counts", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /mastery/i }));

      expect(screen.getByText(/10 attempts/)).toBeInTheDocument();
      expect(screen.getByText(/5 attempts/)).toBeInTheDocument();
    });
  });

  describe("sessions tab", () => {
    it("should display session history", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /sessions/i }));

      expect(screen.getByText(/20 messages/)).toBeInTheDocument();
    });

    it("should display view transcript button", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /sessions/i }));

      expect(
        screen.getByRole("button", { name: /view transcript/i }),
      ).toBeInTheDocument();
    });
  });

  describe("flags tab", () => {
    it("should display gaming flags", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockStudent);
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /flags/i }));

      expect(screen.getByText("Rapid responses")).toBeInTheDocument();
      expect(
        screen.getByText("Unusually fast response pattern detected"),
      ).toBeInTheDocument();
    });

    it("should show no flags message when empty", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce({
        ...mockStudent,
        gaming_flags: [],
      });
      renderStudentView();

      await screen.findByText("John Doe");
      await user.click(screen.getByRole("button", { name: /flags/i }));

      expect(screen.getByText(/no gaming flags detected/i)).toBeInTheDocument();
    });
  });
});
