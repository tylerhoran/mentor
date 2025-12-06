import { describe, it, expect } from "vitest";
import {
  cn,
  formatDate,
  formatDateTime,
  formatPercentage,
  formatDuration,
} from "./utils";

describe("utils", () => {
  describe("cn", () => {
    it("should merge class names", () => {
      expect(cn("foo", "bar")).toBe("foo bar");
    });

    it("should handle conditional classes", () => {
      expect(cn("foo", false && "bar", "baz")).toBe("foo baz");
    });

    it("should merge tailwind classes correctly", () => {
      expect(cn("px-2", "px-4")).toBe("px-4");
    });

    it("should handle arrays", () => {
      expect(cn(["foo", "bar"])).toBe("foo bar");
    });

    it("should handle objects", () => {
      expect(cn({ foo: true, bar: false, baz: true })).toBe("foo baz");
    });

    it("should handle undefined and null", () => {
      expect(cn("foo", undefined, null, "bar")).toBe("foo bar");
    });

    it("should handle empty input", () => {
      expect(cn()).toBe("");
    });
  });

  describe("formatDate", () => {
    it("should format a date string", () => {
      // Use full ISO string with time to avoid timezone shift issues
      const result = formatDate("2024-01-15T12:00:00");
      expect(result).toContain("Jan");
      expect(result).toContain("2024");
    });

    it("should format a Date object", () => {
      const date = new Date(2024, 5, 20); // June 20, 2024 (month is 0-indexed)
      const result = formatDate(date);
      expect(result).toContain("Jun");
      expect(result).toContain("20");
      expect(result).toContain("2024");
    });

    it("should handle ISO date strings", () => {
      const result = formatDate("2024-12-25T10:30:00Z");
      expect(result).toContain("2024");
    });
  });

  describe("formatDateTime", () => {
    it("should format a date string with time", () => {
      const result = formatDateTime("2024-01-15T14:30:00");
      expect(result).toContain("Jan");
      expect(result).toContain("15");
      expect(result).toContain("2024");
    });

    it("should format a Date object with time", () => {
      const date = new Date("2024-06-20T09:15:00");
      const result = formatDateTime(date);
      expect(result).toContain("Jun");
      expect(result).toContain("20");
      expect(result).toContain("2024");
    });

    it("should include time component", () => {
      const result = formatDateTime("2024-01-15T14:30:00");
      // Should contain some time indicator (format varies by locale)
      expect(result.length).toBeGreaterThan(formatDate("2024-01-15").length);
    });
  });

  describe("formatPercentage", () => {
    it("should format decimal as percentage", () => {
      expect(formatPercentage(0.75)).toBe("75%");
    });

    it("should round to nearest integer", () => {
      expect(formatPercentage(0.756)).toBe("76%");
      expect(formatPercentage(0.754)).toBe("75%");
    });

    it("should handle 0", () => {
      expect(formatPercentage(0)).toBe("0%");
    });

    it("should handle 1 (100%)", () => {
      expect(formatPercentage(1)).toBe("100%");
    });

    it("should handle values over 1", () => {
      expect(formatPercentage(1.5)).toBe("150%");
    });

    it("should handle small decimals", () => {
      expect(formatPercentage(0.01)).toBe("1%");
      expect(formatPercentage(0.001)).toBe("0%");
    });
  });

  describe("formatDuration", () => {
    it("should format minutes only", () => {
      expect(formatDuration(60)).toBe("1m");
      expect(formatDuration(120)).toBe("2m");
      expect(formatDuration(300)).toBe("5m");
    });

    it("should format hours and minutes", () => {
      expect(formatDuration(3600)).toBe("1h 0m");
      expect(formatDuration(3660)).toBe("1h 1m");
      expect(formatDuration(7200)).toBe("2h 0m");
      expect(formatDuration(5400)).toBe("1h 30m");
    });

    it("should handle 0 seconds", () => {
      expect(formatDuration(0)).toBe("0m");
    });

    it("should handle seconds less than a minute", () => {
      expect(formatDuration(30)).toBe("0m");
      expect(formatDuration(59)).toBe("0m");
    });

    it("should handle large durations", () => {
      expect(formatDuration(36000)).toBe("10h 0m");
    });
  });
});
