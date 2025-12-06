import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Input } from "./input";

describe("Input", () => {
  describe("rendering", () => {
    it("should render an input element", () => {
      render(<Input />);
      expect(screen.getByRole("textbox")).toBeInTheDocument();
    });

    it("should forward ref to input element", () => {
      const ref = { current: null } as React.RefObject<HTMLInputElement>;
      render(<Input ref={ref} />);
      expect(ref.current).toBeInstanceOf(HTMLInputElement);
    });

    it("should pass through additional props", () => {
      render(<Input data-testid="custom-input" />);
      expect(screen.getByTestId("custom-input")).toBeInTheDocument();
    });
  });

  describe("types", () => {
    it("should render text input by default", () => {
      render(<Input />);
      // When no type is specified, input defaults to text (no explicit attribute)
      expect(screen.getByRole("textbox")).toBeInTheDocument();
    });

    it("should render email input", () => {
      render(<Input type="email" />);
      expect(screen.getByRole("textbox")).toHaveAttribute("type", "email");
    });

    it("should render password input", () => {
      render(<Input type="password" />);
      // Password inputs don't have textbox role
      const input = document.querySelector('input[type="password"]');
      expect(input).toBeInTheDocument();
    });

    it("should render number input", () => {
      render(<Input type="number" />);
      expect(screen.getByRole("spinbutton")).toHaveAttribute("type", "number");
    });
  });

  describe("styling", () => {
    it("should apply default styles", () => {
      render(<Input />);
      const input = screen.getByRole("textbox");
      expect(input.className).toContain("h-10");
      expect(input.className).toContain("rounded-md");
      expect(input.className).toContain("border");
    });

    it("should merge custom className", () => {
      render(<Input className="custom-class" />);
      const input = screen.getByRole("textbox");
      expect(input.className).toContain("custom-class");
      expect(input.className).toContain("h-10");
    });

    it("should apply disabled styles", () => {
      render(<Input disabled />);
      const input = screen.getByRole("textbox");
      expect(input).toBeDisabled();
      expect(input.className).toContain("disabled:opacity-50");
    });
  });

  describe("interactions", () => {
    it("should handle value changes", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<Input onChange={onChange} />);
      const input = screen.getByRole("textbox");
      await user.type(input, "hello");
      expect(onChange).toHaveBeenCalled();
    });

    it("should display typed value", async () => {
      const user = userEvent.setup();
      render(<Input />);
      const input = screen.getByRole("textbox");
      await user.type(input, "test value");
      expect(input).toHaveValue("test value");
    });

    it("should handle focus events", async () => {
      const user = userEvent.setup();
      const onFocus = vi.fn();
      render(<Input onFocus={onFocus} />);
      const input = screen.getByRole("textbox");
      await user.click(input);
      expect(onFocus).toHaveBeenCalled();
    });

    it("should handle blur events", async () => {
      const user = userEvent.setup();
      const onBlur = vi.fn();
      render(<Input onBlur={onBlur} />);
      const input = screen.getByRole("textbox");
      await user.click(input);
      await user.tab();
      expect(onBlur).toHaveBeenCalled();
    });

    it("should not allow input when disabled", async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<Input disabled onChange={onChange} />);
      const input = screen.getByRole("textbox");
      await user.type(input, "test");
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe("attributes", () => {
    it("should render with placeholder", () => {
      render(<Input placeholder="Enter text" />);
      expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
    });

    it("should render with initial value", () => {
      render(<Input defaultValue="initial" />);
      expect(screen.getByRole("textbox")).toHaveValue("initial");
    });

    it("should render with name attribute", () => {
      render(<Input name="username" />);
      expect(screen.getByRole("textbox")).toHaveAttribute("name", "username");
    });

    it("should render with required attribute", () => {
      render(<Input required />);
      expect(screen.getByRole("textbox")).toBeRequired();
    });

    it("should render with readonly attribute", () => {
      render(<Input readOnly value="readonly value" />);
      const input = screen.getByRole("textbox");
      expect(input).toHaveAttribute("readonly");
    });
  });
});
