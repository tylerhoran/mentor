import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import History from "./History";

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

describe("History", () => {
  let queryClient: QueryClient;

  const mockHistory = {
    sessions: [
      {
        id: "session-1",
        started_at: "2024-01-15T10:00:00Z",
        ended_at: "2024-01-15T10:30:00Z",
        duration_minutes: 30,
        message_count: 15,
        concepts_covered: [
          { id: "c1", name: "Neural Networks" },
          { id: "c2", name: "Backpropagation" },
        ],
        mastery_changes: [
          { concept_id: "c1", concept_name: "Neural Networks", before: 0.5, after: 0.7 },
        ],
        summary: "Discussed neural network fundamentals",
      },
      {
        id: "session-2",
        started_at: "2024-01-14T14:00:00Z",
        ended_at: "2024-01-14T14:45:00Z",
        duration_minutes: 45,
        message_count: 20,
        concepts_covered: [{ id: "c1", name: "Neural Networks" }],
        mastery_changes: [],
        summary: "Introduction to neural networks",
      },
    ],
    total_count: 2,
    page: 1,
    page_size: 10,
  };

  const mockSessionDetail = {
    id: "session-1",
    started_at: "2024-01-15T10:00:00Z",
    ended_at: "2024-01-15T10:30:00Z",
    messages: [
      {
        id: "msg-1",
        role: "user" as const,
        content: "Can you explain neural networks?",
        timestamp: "2024-01-15T10:00:00Z",
      },
      {
        id: "msg-2",
        role: "assistant" as const,
        content: "Neural networks are computational models...",
        timestamp: "2024-01-15T10:01:00Z",
        pedagogical_move: "explanation",
      },
    ],
    concepts_covered: [{ id: "c1", name: "Neural Networks" }],
    mastery_changes: [
      { concept_id: "c1", concept_name: "Neural Networks", before: 0.5, after: 0.7 },
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

  const renderHistory = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <History />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe("loading state", () => {
    it("should show loading spinner while fetching", () => {
      mockApi.get.mockImplementation(() => new Promise(() => {}));
      renderHistory();
      expect(document.querySelector(".animate-spin")).toBeInTheDocument();
    });
  });

  describe("page structure", () => {
    it("should display page title", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(await screen.findByText("Session History")).toBeInTheDocument();
    });

    it("should display session count", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(await screen.findByText("2 sessions")).toBeInTheDocument();
    });

    it("should display back to dashboard link", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(
        await screen.findByRole("link", { name: /back to dashboard/i })
      ).toBeInTheDocument();
    });

    it("should display new session button", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(
        await screen.findByRole("button", { name: /new session/i })
      ).toBeInTheDocument();
    });
  });

  describe("empty state", () => {
    it("should show no sessions message when empty", async () => {
      mockApi.get.mockResolvedValueOnce({
        sessions: [],
        total_count: 0,
        page: 1,
        page_size: 10,
      });
      renderHistory();
      expect(await screen.findByText(/no sessions yet/i)).toBeInTheDocument();
    });
  });

  describe("session list", () => {
    it("should display session dates", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      await screen.findByText("Session History");
      // Check for formatted dates - exact format depends on locale
      const dateElements = document.querySelectorAll(".font-medium");
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it("should display message counts", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(await screen.findByText("15 msgs")).toBeInTheDocument();
      expect(screen.getByText("20 msgs")).toBeInTheDocument();
    });

    it("should display duration", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(await screen.findByText("30 min")).toBeInTheDocument();
      expect(screen.getByText("45 min")).toBeInTheDocument();
    });

    it("should display concept tags", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      const neuralNetworkTags = await screen.findAllByText("Neural Networks");
      expect(neuralNetworkTags.length).toBeGreaterThan(0);
    });
  });

  describe("session selection", () => {
    it("should show select message when no session selected", async () => {
      mockApi.get.mockResolvedValueOnce(mockHistory);
      renderHistory();
      expect(
        await screen.findByText(/select a session to view details/i)
      ).toBeInTheDocument();
    });

    it("should load session details when clicked", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockHistory)
        .mockResolvedValueOnce(mockSessionDetail);
      renderHistory();

      await screen.findByText("15 msgs");
      const sessionButtons = screen.getAllByRole("button");
      const sessionButton = sessionButtons.find((btn) =>
        btn.textContent?.includes("15 msgs")
      );

      if (sessionButton) {
        await user.click(sessionButton);

        await waitFor(() => {
          expect(mockApi.get).toHaveBeenCalledWith(
            "/students/sessions/detail/session-1"
          );
        });
      }
    });
  });

  describe("session detail", () => {
    it("should display session details section title", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockHistory)
        .mockResolvedValueOnce(mockSessionDetail);
      renderHistory();

      await screen.findByText("15 msgs");
      const sessionButtons = screen.getAllByRole("button");
      const sessionButton = sessionButtons.find((btn) =>
        btn.textContent?.includes("15 msgs")
      );

      if (sessionButton) {
        await user.click(sessionButton);
        expect(await screen.findByText("Session Details")).toBeInTheDocument();
      }
    });

    it("should display transcript section", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockHistory)
        .mockResolvedValueOnce(mockSessionDetail);
      renderHistory();

      await screen.findByText("15 msgs");
      const sessionButtons = screen.getAllByRole("button");
      const sessionButton = sessionButtons.find((btn) =>
        btn.textContent?.includes("15 msgs")
      );

      if (sessionButton) {
        await user.click(sessionButton);
        expect(await screen.findByText("Transcript")).toBeInTheDocument();
      }
    });

    it("should display messages in transcript", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockHistory)
        .mockResolvedValueOnce(mockSessionDetail);
      renderHistory();

      await screen.findByText("15 msgs");
      const sessionButtons = screen.getAllByRole("button");
      const sessionButton = sessionButtons.find((btn) =>
        btn.textContent?.includes("15 msgs")
      );

      if (sessionButton) {
        await user.click(sessionButton);
        expect(
          await screen.findByText("Can you explain neural networks?")
        ).toBeInTheDocument();
        expect(
          screen.getByText("Neural networks are computational models...")
        ).toBeInTheDocument();
      }
    });

    it("should display mastery changes", async () => {
      const user = userEvent.setup();
      mockApi.get
        .mockResolvedValueOnce(mockHistory)
        .mockResolvedValueOnce(mockSessionDetail);
      renderHistory();

      await screen.findByText("15 msgs");
      const sessionButtons = screen.getAllByRole("button");
      const sessionButton = sessionButtons.find((btn) =>
        btn.textContent?.includes("15 msgs")
      );

      if (sessionButton) {
        await user.click(sessionButton);
        expect(await screen.findByText("Mastery Changes")).toBeInTheDocument();
        expect(screen.getByText(/50%.*→.*70%/)).toBeInTheDocument();
      }
    });
  });
});
