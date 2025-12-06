import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from "./card";

describe("Card", () => {
  describe("Card component", () => {
    it("should render a div element", () => {
      render(<Card data-testid="card">Content</Card>);
      expect(screen.getByTestId("card")).toBeInTheDocument();
    });

    it("should forward ref to div element", () => {
      const ref = { current: null } as React.RefObject<HTMLDivElement>;
      render(<Card ref={ref}>Content</Card>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it("should apply default styles", () => {
      render(<Card data-testid="card">Content</Card>);
      const card = screen.getByTestId("card");
      expect(card.className).toContain("rounded-lg");
      expect(card.className).toContain("border");
      expect(card.className).toContain("shadow-sm");
    });

    it("should merge custom className", () => {
      render(
        <Card data-testid="card" className="custom-class">
          Content
        </Card>
      );
      const card = screen.getByTestId("card");
      expect(card.className).toContain("custom-class");
      expect(card.className).toContain("rounded-lg");
    });

    it("should pass through additional props", () => {
      render(
        <Card data-testid="card" id="my-card">
          Content
        </Card>
      );
      expect(screen.getByTestId("card")).toHaveAttribute("id", "my-card");
    });
  });

  describe("CardHeader component", () => {
    it("should render children", () => {
      render(<CardHeader>Header Content</CardHeader>);
      expect(screen.getByText("Header Content")).toBeInTheDocument();
    });

    it("should forward ref", () => {
      const ref = { current: null } as React.RefObject<HTMLDivElement>;
      render(<CardHeader ref={ref}>Header</CardHeader>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it("should apply default styles", () => {
      render(<CardHeader data-testid="header">Header</CardHeader>);
      const header = screen.getByTestId("header");
      expect(header.className).toContain("flex");
      expect(header.className).toContain("flex-col");
      expect(header.className).toContain("p-6");
    });

    it("should merge custom className", () => {
      render(
        <CardHeader data-testid="header" className="custom-header">
          Header
        </CardHeader>
      );
      const header = screen.getByTestId("header");
      expect(header.className).toContain("custom-header");
    });
  });

  describe("CardTitle component", () => {
    it("should render as h3 element", () => {
      render(<CardTitle>Title</CardTitle>);
      expect(screen.getByRole("heading", { level: 3 })).toBeInTheDocument();
    });

    it("should forward ref", () => {
      const ref = { current: null } as React.RefObject<HTMLParagraphElement>;
      render(<CardTitle ref={ref}>Title</CardTitle>);
      expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
    });

    it("should apply default styles", () => {
      render(<CardTitle data-testid="title">Title</CardTitle>);
      const title = screen.getByTestId("title");
      expect(title.className).toContain("text-2xl");
      expect(title.className).toContain("font-semibold");
    });

    it("should merge custom className", () => {
      render(
        <CardTitle data-testid="title" className="custom-title">
          Title
        </CardTitle>
      );
      const title = screen.getByTestId("title");
      expect(title.className).toContain("custom-title");
    });
  });

  describe("CardDescription component", () => {
    it("should render as p element", () => {
      render(<CardDescription>Description</CardDescription>);
      expect(screen.getByText("Description").tagName).toBe("P");
    });

    it("should forward ref", () => {
      const ref = { current: null } as React.RefObject<HTMLParagraphElement>;
      render(<CardDescription ref={ref}>Description</CardDescription>);
      expect(ref.current).toBeInstanceOf(HTMLParagraphElement);
    });

    it("should apply default styles", () => {
      render(
        <CardDescription data-testid="desc">Description</CardDescription>
      );
      const desc = screen.getByTestId("desc");
      expect(desc.className).toContain("text-sm");
      expect(desc.className).toContain("text-muted-foreground");
    });

    it("should merge custom className", () => {
      render(
        <CardDescription data-testid="desc" className="custom-desc">
          Description
        </CardDescription>
      );
      const desc = screen.getByTestId("desc");
      expect(desc.className).toContain("custom-desc");
    });
  });

  describe("CardContent component", () => {
    it("should render children", () => {
      render(<CardContent>Card Content</CardContent>);
      expect(screen.getByText("Card Content")).toBeInTheDocument();
    });

    it("should forward ref", () => {
      const ref = { current: null } as React.RefObject<HTMLDivElement>;
      render(<CardContent ref={ref}>Content</CardContent>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it("should apply default styles", () => {
      render(<CardContent data-testid="content">Content</CardContent>);
      const content = screen.getByTestId("content");
      expect(content.className).toContain("p-6");
      expect(content.className).toContain("pt-0");
    });

    it("should merge custom className", () => {
      render(
        <CardContent data-testid="content" className="custom-content">
          Content
        </CardContent>
      );
      const content = screen.getByTestId("content");
      expect(content.className).toContain("custom-content");
    });
  });

  describe("CardFooter component", () => {
    it("should render children", () => {
      render(<CardFooter>Footer Content</CardFooter>);
      expect(screen.getByText("Footer Content")).toBeInTheDocument();
    });

    it("should forward ref", () => {
      const ref = { current: null } as React.RefObject<HTMLDivElement>;
      render(<CardFooter ref={ref}>Footer</CardFooter>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it("should apply default styles", () => {
      render(<CardFooter data-testid="footer">Footer</CardFooter>);
      const footer = screen.getByTestId("footer");
      expect(footer.className).toContain("flex");
      expect(footer.className).toContain("items-center");
      expect(footer.className).toContain("p-6");
      expect(footer.className).toContain("pt-0");
    });

    it("should merge custom className", () => {
      render(
        <CardFooter data-testid="footer" className="custom-footer">
          Footer
        </CardFooter>
      );
      const footer = screen.getByTestId("footer");
      expect(footer.className).toContain("custom-footer");
    });
  });

  describe("Card composition", () => {
    it("should render a complete card structure", () => {
      render(
        <Card data-testid="card">
          <CardHeader>
            <CardTitle>Test Title</CardTitle>
            <CardDescription>Test Description</CardDescription>
          </CardHeader>
          <CardContent>Main content goes here</CardContent>
          <CardFooter>Footer content</CardFooter>
        </Card>
      );

      expect(screen.getByTestId("card")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Test Title" })
      ).toBeInTheDocument();
      expect(screen.getByText("Test Description")).toBeInTheDocument();
      expect(screen.getByText("Main content goes here")).toBeInTheDocument();
      expect(screen.getByText("Footer content")).toBeInTheDocument();
    });
  });
});
