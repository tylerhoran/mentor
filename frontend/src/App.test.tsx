import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";

// Track auth state
let mockAuthState = {
  user: null as { id: string; email: string; role: string; full_name: string } | null,
  isAuthenticated: false,
};

// Mock auth store
vi.mock("./stores/auth", () => ({
  useAuthStore: () => mockAuthState,
}));

// Mock all page components to simplify testing
vi.mock("./pages/auth/Login", () => ({
  default: () => <div data-testid="login-page">Login Page</div>,
}));

vi.mock("./pages/auth/Register", () => ({
  default: () => <div data-testid="register-page">Register Page</div>,
}));

vi.mock("./pages/faculty/Dashboard", () => ({
  default: () => <div data-testid="faculty-dashboard">Faculty Dashboard</div>,
}));

vi.mock("./pages/faculty/CourseBuilder", () => ({
  default: () => <div data-testid="course-builder">Course Builder</div>,
}));

vi.mock("./pages/faculty/StudentView", () => ({
  default: () => <div data-testid="student-view">Student View</div>,
}));

vi.mock("./pages/faculty/Analytics", () => ({
  default: () => <div data-testid="analytics">Analytics</div>,
}));

vi.mock("./pages/student/TutorSession", () => ({
  default: () => <div data-testid="tutor-session">Tutor Session</div>,
}));

vi.mock("./pages/student/Progress", () => ({
  default: () => <div data-testid="student-progress">Student Progress</div>,
}));

vi.mock("./pages/student/History", () => ({
  default: () => <div data-testid="student-history">Student History</div>,
}));

vi.mock("./components/ui/toaster", () => ({
  Toaster: () => <div data-testid="toaster">Toaster</div>,
}));

describe("App", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthState = {
      user: null,
      isAuthenticated: false,
    };
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const renderApp = (initialRoute = "/") => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  describe("unauthenticated routes", () => {
    it("should render login page at /login", () => {
      renderApp("/login");
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });

    it("should render register page at /register", () => {
      renderApp("/register");
      expect(screen.getByTestId("register-page")).toBeInTheDocument();
    });

    it("should redirect to login from root when not authenticated", () => {
      renderApp("/");
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  describe("protected routes - unauthenticated", () => {
    it("should redirect to login when accessing faculty dashboard", () => {
      renderApp("/faculty");
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });

    it("should redirect to login when accessing tutor session", () => {
      renderApp("/tutor/course-123");
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });

    it("should redirect to login when accessing student progress", () => {
      renderApp("/progress");
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  describe("faculty routes", () => {
    beforeEach(() => {
      mockAuthState = {
        user: {
          id: "1",
          email: "prof@university.edu",
          role: "faculty",
          full_name: "Prof. Smith",
        },
        isAuthenticated: true,
      };
    });

    it("should render faculty dashboard at /faculty", () => {
      renderApp("/faculty");
      expect(screen.getByTestId("faculty-dashboard")).toBeInTheDocument();
    });

    it("should render course builder at /faculty/course/:courseId", () => {
      renderApp("/faculty/course/course-123");
      expect(screen.getByTestId("course-builder")).toBeInTheDocument();
    });

    it("should render analytics at /faculty/course/:courseId/analytics", () => {
      renderApp("/faculty/course/course-123/analytics");
      expect(screen.getByTestId("analytics")).toBeInTheDocument();
    });

    it("should render student view at /faculty/course/:courseId/student/:studentId", () => {
      renderApp("/faculty/course/course-123/student/student-456");
      expect(screen.getByTestId("student-view")).toBeInTheDocument();
    });

    it("should redirect faculty to /faculty from root", () => {
      renderApp("/");
      expect(screen.getByTestId("faculty-dashboard")).toBeInTheDocument();
    });

    it("should redirect faculty away from student-only routes", () => {
      renderApp("/tutor/course-123");
      // Faculty should be redirected since they don't have student role
      expect(screen.queryByTestId("tutor-session")).not.toBeInTheDocument();
    });
  });

  describe("admin routes", () => {
    beforeEach(() => {
      mockAuthState = {
        user: {
          id: "1",
          email: "admin@university.edu",
          role: "admin",
          full_name: "Admin User",
        },
        isAuthenticated: true,
      };
    });

    it("should allow admin to access faculty dashboard", () => {
      renderApp("/faculty");
      expect(screen.getByTestId("faculty-dashboard")).toBeInTheDocument();
    });

    it("should allow admin to access course builder", () => {
      renderApp("/faculty/course/course-123");
      expect(screen.getByTestId("course-builder")).toBeInTheDocument();
    });

    it("should redirect admin to /faculty from root", () => {
      renderApp("/");
      expect(screen.getByTestId("faculty-dashboard")).toBeInTheDocument();
    });
  });

  describe("student routes", () => {
    beforeEach(() => {
      mockAuthState = {
        user: {
          id: "1",
          email: "student@university.edu",
          role: "student",
          full_name: "John Student",
        },
        isAuthenticated: true,
      };
    });

    it("should render tutor session at /tutor/:courseId", () => {
      renderApp("/tutor/course-123");
      expect(screen.getByTestId("tutor-session")).toBeInTheDocument();
    });

    it("should render student progress at /progress", () => {
      renderApp("/progress");
      expect(screen.getByTestId("student-progress")).toBeInTheDocument();
    });

    it("should render student history at /history", () => {
      renderApp("/history");
      expect(screen.getByTestId("student-history")).toBeInTheDocument();
    });

    it("should redirect student to /progress from root", () => {
      renderApp("/");
      expect(screen.getByTestId("student-progress")).toBeInTheDocument();
    });

    it("should redirect student away from faculty routes", () => {
      renderApp("/faculty");
      // Student should be redirected since they don't have faculty role
      expect(screen.queryByTestId("faculty-dashboard")).not.toBeInTheDocument();
    });
  });

  describe("toaster", () => {
    it("should render toaster component", () => {
      renderApp("/login");
      expect(screen.getByTestId("toaster")).toBeInTheDocument();
    });
  });
});
