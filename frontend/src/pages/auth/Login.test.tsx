import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Login from "./Login";

// Mock navigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock toast
const mockToast = vi.fn();
vi.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({ toast: mockToast }),
}));

// Mock auth store
const mockLogin = vi.fn();
vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    login: mockLogin,
    isLoading: false,
  }),
}));

describe("Login", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
  };

  describe("rendering", () => {
    it("should render login form", () => {
      renderLogin();
      expect(
        screen.getByRole("heading", { name: /welcome to mentor/i })
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    it("should render link to register page", () => {
      renderLogin();
      const registerLink = screen.getByRole("link", { name: /register/i });
      expect(registerLink).toBeInTheDocument();
      expect(registerLink).toHaveAttribute("href", "/register");
    });

    it("should display description text", () => {
      renderLogin();
      expect(
        screen.getByText(/sign in to your account to continue/i)
      ).toBeInTheDocument();
    });
  });

  describe("form validation", () => {
    it("should have required fields", () => {
      renderLogin();
      expect(screen.getByLabelText(/email/i)).toBeRequired();
      expect(screen.getByLabelText(/password/i)).toBeRequired();
    });

    it("should have email type on email input", () => {
      renderLogin();
      expect(screen.getByLabelText(/email/i)).toHaveAttribute("type", "email");
    });

    it("should have password type on password input", () => {
      renderLogin();
      expect(screen.getByLabelText(/password/i)).toHaveAttribute(
        "type",
        "password"
      );
    });
  });

  describe("form submission", () => {
    it("should call login with email and password on submit", async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValueOnce(undefined);
      renderLogin();

      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /sign in/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith("test@example.com", "password123");
      });
    });

    it("should navigate to home on successful login", async () => {
      const user = userEvent.setup();
      mockLogin.mockResolvedValueOnce(undefined);
      renderLogin();

      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /sign in/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/");
      });
    });

    it("should show error toast on login failure", async () => {
      const user = userEvent.setup();
      mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"));
      renderLogin();

      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "wrongpassword");
      await user.click(screen.getByRole("button", { name: /sign in/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          variant: "destructive",
          title: "Login failed",
          description: "Invalid credentials",
        });
      });
    });

    it("should show generic error message for non-Error failures", async () => {
      const user = userEvent.setup();
      mockLogin.mockRejectedValueOnce("Some error");
      renderLogin();

      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "password");
      await user.click(screen.getByRole("button", { name: /sign in/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          variant: "destructive",
          title: "Login failed",
          description: "Invalid credentials",
        });
      });
    });
  });

  describe("input handling", () => {
    it("should update email field on input", async () => {
      const user = userEvent.setup();
      renderLogin();
      const emailInput = screen.getByLabelText(/email/i);

      await user.type(emailInput, "user@test.com");
      expect(emailInput).toHaveValue("user@test.com");
    });

    it("should update password field on input", async () => {
      const user = userEvent.setup();
      renderLogin();
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(passwordInput, "secret123");
      expect(passwordInput).toHaveValue("secret123");
    });
  });
});
