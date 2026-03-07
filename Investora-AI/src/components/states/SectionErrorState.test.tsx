import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SectionErrorState } from "./SectionErrorState";

describe("SectionErrorState", () => {
  it("renders label and fires retry callback", () => {
    const onRetry = vi.fn();
    render(<SectionErrorState label="Failed to load" onRetry={onRetry} />);

    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
