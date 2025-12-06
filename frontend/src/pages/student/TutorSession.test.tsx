import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import TutorSession from "./TutorSession";

// Mock useParams
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: () => ({ courseId: "course-123" }),
  };
});

// Mock API
const mockStream = vi.fn();
vi.mock("../../api/client", () => ({
  api: {
    get: vi.fn(),
    stream: vi.fn(),
  },
}));

import { api } from "../../api/client";
const mockApi = api as {
  get: ReturnType<typeof vi.fn>;
  stream: ReturnType<typeof vi.fn>;
};

describe("TutorSession", () => {
  let queryClient: QueryClient;

  const mockSession = {
    id: "session-123",
    course_id: "course-123",
    course_name: "Introduction to AI",
    started_at: "2024-01-15T10:00:00Z",
    messages: [],
    current_concept: "Neural Networks",
  };

  const mockSessionWithMessages = {
    ...mockSession,
    messages: [
      {
        id: "msg-1",
        role: "user" as const,
        content: "What is a neural network?",
        timestamp: "2024-01-15T10:00:00Z",
      },
      {
        id: "msg-2",
        role: "assistant" as const,
        content: "A neural network is a computational model...",
        timestamp: "2024-01-15T10:01:00Z",
        pedagogical_move: "explanation",
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

  const renderTutorSession = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <TutorSession />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe("header", () => {
    it("should display course name", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(await screen.findByText("Introduction to AI")).toBeInTheDocument();
    });

    it("should display current concept", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByText(/currently discussing: neural networks/i)
      ).toBeInTheDocument();
    });

    it("should display back link", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      await screen.findByText("Introduction to AI");
      const backLink = screen.getByRole("link", { name: "←" });
      expect(backLink).toHaveAttribute("href", "/student");
    });

    it("should display view progress button", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByRole("button", { name: /view progress/i })
      ).toBeInTheDocument();
    });
  });

  describe("welcome state", () => {
    it("should display welcome message when no messages", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByText(/welcome to your tutoring session/i)
      ).toBeInTheDocument();
    });

    it("should display welcome emoji", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(await screen.findByText("👋")).toBeInTheDocument();
    });

    it("should display helpful description", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByText(/ask me anything about the course material/i)
      ).toBeInTheDocument();
    });

    it("should display quick prompt buttons", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByRole("button", { name: /explain the main concept/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /give me a practice problem/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /review what we covered/i })
      ).toBeInTheDocument();
    });

    it("should populate input when quick prompt clicked", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();

      const promptButton = await screen.findByRole("button", {
        name: /explain the main concept/i,
      });
      await user.click(promptButton);

      const input = screen.getByPlaceholderText(/type your message/i);
      expect(input).toHaveValue("Explain the main concept");
    });
  });

  describe("with existing messages", () => {
    it("should display existing messages", async () => {
      mockApi.get.mockResolvedValueOnce(mockSessionWithMessages);
      renderTutorSession();
      expect(
        await screen.findByText("What is a neural network?")
      ).toBeInTheDocument();
      expect(
        screen.getByText("A neural network is a computational model...")
      ).toBeInTheDocument();
    });

    it("should not show welcome message when messages exist", async () => {
      mockApi.get.mockResolvedValueOnce(mockSessionWithMessages);
      renderTutorSession();
      await screen.findByText("What is a neural network?");
      expect(
        screen.queryByText(/welcome to your tutoring session/i)
      ).not.toBeInTheDocument();
    });

    it("should display pedagogical move indicator", async () => {
      mockApi.get.mockResolvedValueOnce(mockSessionWithMessages);
      renderTutorSession();
      expect(await screen.findByText("explanation")).toBeInTheDocument();
    });
  });

  describe("input form", () => {
    it("should render input field", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByPlaceholderText(/type your message/i)
      ).toBeInTheDocument();
    });

    it("should render send button", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      expect(
        await screen.findByRole("button", { name: /send/i })
      ).toBeInTheDocument();
    });

    it("should disable send button when input is empty", async () => {
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();
      const sendButton = await screen.findByRole("button", { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it("should enable send button when input has text", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();

      const input = await screen.findByPlaceholderText(/type your message/i);
      await user.type(input, "Hello");

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).not.toBeDisabled();
    });

    it("should update input value on type", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      renderTutorSession();

      const input = await screen.findByPlaceholderText(/type your message/i);
      await user.type(input, "Test message");
      expect(input).toHaveValue("Test message");
    });
  });

  describe("message submission", () => {
    it("should add user message to chat on submit", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      mockApi.stream.mockImplementation(
        async (_url: string, _data: unknown, callback: (chunk: string) => void) => {
          callback("This is the response");
        }
      );
      renderTutorSession();

      const input = await screen.findByPlaceholderText(/type your message/i);
      await user.type(input, "Hello AI");
      await user.click(screen.getByRole("button", { name: /send/i }));

      await waitFor(() => {
        expect(screen.getByText("Hello AI")).toBeInTheDocument();
      });
    });

    it("should clear input after submit", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      mockApi.stream.mockImplementation(async () => {});
      renderTutorSession();

      const input = await screen.findByPlaceholderText(/type your message/i);
      await user.type(input, "Hello AI");
      await user.click(screen.getByRole("button", { name: /send/i }));

      await waitFor(() => {
        expect(input).toHaveValue("");
      });
    });

    it("should call stream API with correct parameters", async () => {
      const user = userEvent.setup();
      mockApi.get.mockResolvedValueOnce(mockSession);
      mockApi.stream.mockImplementation(async () => {});
      renderTutorSession();

      const input = await screen.findByPlaceholderText(/type your message/i);
      await user.type(input, "Explain AI");
      await user.click(screen.getByRole("button", { name: /send/i }));

      await waitFor(() => {
        expect(mockApi.stream).toHaveBeenCalledWith(
          "/tutor/message/course-123",
          { message: "Explain AI" },
          expect.any(Function)
        );
      });
    });
  });

  describe("mastery update toast", () => {
    it("should display mastery update when present", async () => {
      mockApi.get.mockResolvedValueOnce({
        ...mockSession,
        mastery_update: {
          concept: "Neural Networks",
          previous: 0.5,
          current: 0.7,
        },
      });
      renderTutorSession();
      expect(await screen.findByText("Mastery Updated!")).toBeInTheDocument();
      expect(screen.getByText(/neural networks: 50% → 70%/i)).toBeInTheDocument();
    });
  });
});
