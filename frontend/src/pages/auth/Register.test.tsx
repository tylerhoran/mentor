import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import Register from "./Register";

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
const mockRegister = vi.fn();
vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    register: mockRegister,
    isLoading: false,
  }),
}));

describe("Register", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderRegister = () => {
    return render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
  };

  describe("rendering", () => {
    it("should render registration form", () => {
      renderRegister();
      expect(
        screen.getByRole("heading", { name: /create an account/i })
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /create account/i })
      ).toBeInTheDocument();
    });

    it("should render link to login page", () => {
      renderRegister();
      const loginLink = screen.getByRole("link", { name: /sign in/i });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute("href", "/login");
    });

    it("should display description text", () => {
      renderRegister();
      expect(
        screen.getByText(/enter your details to get started/i)
      ).toBeInTheDocument();
    });

    it("should render role selection options", () => {
      renderRegister();
      expect(screen.getByLabelText(/student/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/faculty/i)).toBeInTheDocument();
    });
  });

  describe("form validation", () => {
    it("should have required fields", () => {
      renderRegister();
      expect(screen.getByLabelText(/full name/i)).toBeRequired();
      expect(screen.getByLabelText(/email/i)).toBeRequired();
      expect(screen.getByLabelText(/password/i)).toBeRequired();
    });

    it("should have email type on email input", () => {
      renderRegister();
      expect(screen.getByLabelText(/email/i)).toHaveAttribute("type", "email");
    });

    it("should have password type on password input", () => {
      renderRegister();
      expect(screen.getByLabelText(/password/i)).toHaveAttribute(
        "type",
        "password"
      );
    });

    it("should have minimum length on password input", () => {
      renderRegister();
      expect(screen.getByLabelText(/password/i)).toHaveAttribute(
        "minLength",
        "8"
      );
    });
  });

  describe("role selection", () => {
    it("should have student selected by default", () => {
      renderRegister();
      expect(screen.getByLabelText(/student/i)).toBeChecked();
      expect(screen.getByLabelText(/faculty/i)).not.toBeChecked();
    });

    it("should allow selecting faculty role", async () => {
      const user = userEvent.setup();
      renderRegister();

      await user.click(screen.getByLabelText(/faculty/i));
      expect(screen.getByLabelText(/faculty/i)).toBeChecked();
      expect(screen.getByLabelText(/student/i)).not.toBeChecked();
    });

    it("should allow switching back to student role", async () => {
      const user = userEvent.setup();
      renderRegister();

      await user.click(screen.getByLabelText(/faculty/i));
      await user.click(screen.getByLabelText(/student/i));
      expect(screen.getByLabelText(/student/i)).toBeChecked();
    });
  });

  describe("form submission", () => {
    it("should call register with form data on submit", async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValueOnce(undefined);
      renderRegister();

      await user.type(screen.getByLabelText(/full name/i), "John Doe");
      await user.type(screen.getByLabelText(/email/i), "john@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /create account/i }));

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith(
          "john@example.com",
          "password123",
          "John Doe",
          "student"
        );
      });
    });

    it("should register with faculty role when selected", async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValueOnce(undefined);
      renderRegister();

      await user.type(screen.getByLabelText(/full name/i), "Prof. Smith");
      await user.type(screen.getByLabelText(/email/i), "smith@university.edu");
      await user.type(screen.getByLabelText(/password/i), "securepass123");
      await user.click(screen.getByLabelText(/faculty/i));
      await user.click(screen.getByRole("button", { name: /create account/i }));

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith(
          "smith@university.edu",
          "securepass123",
          "Prof. Smith",
          "faculty"
        );
      });
    });

    it("should show success toast and navigate to login on success", async () => {
      const user = userEvent.setup();
      mockRegister.mockResolvedValueOnce(undefined);
      renderRegister();

      await user.type(screen.getByLabelText(/full name/i), "Jane Doe");
      await user.type(screen.getByLabelText(/email/i), "jane@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /create account/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          title: "Registration successful",
          description: "You can now sign in with your credentials",
        });
        expect(mockNavigate).toHaveBeenCalledWith("/login");
      });
    });

    it("should show error toast on registration failure", async () => {
      const user = userEvent.setup();
      mockRegister.mockRejectedValueOnce(new Error("Email already exists"));
      renderRegister();

      await user.type(screen.getByLabelText(/full name/i), "Test User");
      await user.type(screen.getByLabelText(/email/i), "existing@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /create account/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          variant: "destructive",
          title: "Registration failed",
          description: "Email already exists",
        });
      });
    });

    it("should show generic error message for non-Error failures", async () => {
      const user = userEvent.setup();
      mockRegister.mockRejectedValueOnce("Some error");
      renderRegister();

      await user.type(screen.getByLabelText(/full name/i), "Test");
      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "password123");
      await user.click(screen.getByRole("button", { name: /create account/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith({
          variant: "destructive",
          title: "Registration failed",
          description: "Please try again",
        });
      });
    });
  });

  describe("input handling", () => {
    it("should update full name field on input", async () => {
      const user = userEvent.setup();
      renderRegister();
      const nameInput = screen.getByLabelText(/full name/i);

      await user.type(nameInput, "Alice Smith");
      expect(nameInput).toHaveValue("Alice Smith");
    });

    it("should update email field on input", async () => {
      const user = userEvent.setup();
      renderRegister();
      const emailInput = screen.getByLabelText(/email/i);

      await user.type(emailInput, "alice@test.com");
      expect(emailInput).toHaveValue("alice@test.com");
    });

    it("should update password field on input", async () => {
      const user = userEvent.setup();
      renderRegister();
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(passwordInput, "mysecretpass");
      expect(passwordInput).toHaveValue("mysecretpass");
    });
  });
});
