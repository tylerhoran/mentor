import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button, buttonVariants } from "./button";

describe("Button", () => {
  describe("rendering", () => {
    it("should render a button element", () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole("button")).toBeInTheDocument();
      expect(screen.getByText("Click me")).toBeInTheDocument();
    });

    it("should forward ref to button element", () => {
      const ref = { current: null } as React.RefObject<HTMLButtonElement>;
      render(<Button ref={ref}>Button</Button>);
      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });

    it("should pass through additional props", () => {
      render(<Button data-testid="custom-button">Button</Button>);
      expect(screen.getByTestId("custom-button")).toBeInTheDocument();
    });
  });

  describe("variants", () => {
    it("should apply default variant classes", () => {
      render(<Button>Default</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("bg-primary");
    });

    it("should apply destructive variant classes", () => {
      render(<Button variant="destructive">Destructive</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("bg-destructive");
    });

    it("should apply outline variant classes", () => {
      render(<Button variant="outline">Outline</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("border");
      expect(button.className).toContain("bg-background");
    });

    it("should apply secondary variant classes", () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("bg-secondary");
    });

    it("should apply ghost variant classes", () => {
      render(<Button variant="ghost">Ghost</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("hover:bg-accent");
    });

    it("should apply link variant classes", () => {
      render(<Button variant="link">Link</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("underline-offset-4");
    });
  });

  describe("sizes", () => {
    it("should apply default size classes", () => {
      render(<Button>Default Size</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("h-10");
      expect(button.className).toContain("px-4");
    });

    it("should apply small size classes", () => {
      render(<Button size="sm">Small</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("h-9");
      expect(button.className).toContain("px-3");
    });

    it("should apply large size classes", () => {
      render(<Button size="lg">Large</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("h-11");
      expect(button.className).toContain("px-8");
    });

    it("should apply icon size classes", () => {
      render(<Button size="icon">Icon</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("h-10");
      expect(button.className).toContain("w-10");
    });
  });

  describe("asChild", () => {
    it("should render as a slot when asChild is true", () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      );
      const link = screen.getByRole("link");
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", "/test");
    });
  });

  describe("interactions", () => {
    it("should handle click events", async () => {
      const user = userEvent.setup();
      let clicked = false;
      render(<Button onClick={() => (clicked = true)}>Click me</Button>);
      await user.click(screen.getByRole("button"));
      expect(clicked).toBe(true);
    });

    it("should not fire click when disabled", async () => {
      const user = userEvent.setup();
      let clicked = false;
      render(
        <Button disabled onClick={() => (clicked = true)}>
          Disabled
        </Button>
      );
      await user.click(screen.getByRole("button"));
      expect(clicked).toBe(false);
    });

    it("should apply disabled styles", () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button.className).toContain("disabled:opacity-50");
    });
  });

  describe("custom className", () => {
    it("should merge custom className with variant classes", () => {
      render(<Button className="custom-class">Button</Button>);
      const button = screen.getByRole("button");
      expect(button.className).toContain("custom-class");
      expect(button.className).toContain("bg-primary");
    });
  });

  describe("buttonVariants", () => {
    it("should generate correct classes for default variant and size", () => {
      const classes = buttonVariants();
      expect(classes).toContain("bg-primary");
      expect(classes).toContain("h-10");
    });

    it("should generate correct classes for specified variant and size", () => {
      const classes = buttonVariants({ variant: "destructive", size: "lg" });
      expect(classes).toContain("bg-destructive");
      expect(classes).toContain("h-11");
    });
  });
});
