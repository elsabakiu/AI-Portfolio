import { describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useDashboardActions } from "./useDashboardActions";

const toastSuccess = vi.fn();
const toastError = vi.fn();

vi.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => toastSuccess(...args),
    error: (...args: unknown[]) => toastError(...args),
  },
}));

describe("useDashboardActions", () => {
  it("calls stream and emits success toast", async () => {
    const startStream = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useDashboardActions(startStream));

    await act(async () => {
      await result.current.runAnalysis();
    });

    expect(startStream).toHaveBeenCalledWith({ skipSynthesis: true });
    expect(toastSuccess).toHaveBeenCalled();
  });

  it("emits error toast and rethrows", async () => {
    const startStream = vi.fn().mockRejectedValue(new Error("boom"));
    const { result } = renderHook(() => useDashboardActions(startStream));

    await expect(result.current.runAnalysis()).rejects.toThrow("boom");
    expect(toastError).toHaveBeenCalled();
  });
});
