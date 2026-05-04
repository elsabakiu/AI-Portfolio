// @vitest-environment happy-dom

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReviewPage } from "./ReviewPage";

vi.mock("../instrument", () => ({
  Sentry: {
    setTag: vi.fn(),
    setContext: vi.fn(),
    withScope: (callback: (scope: unknown) => void) =>
      callback({
        setTag: vi.fn(),
        setLevel: vi.fn(),
        setContext: vi.fn(),
      }),
    captureException: vi.fn(),
  },
}));

vi.mock("../lib/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    code: string;

    constructor(status: number, payload: { code: string; message: string }) {
      super(payload.message);
      this.name = "ApiError";
      this.status = status;
      this.code = payload.code;
    }
  },
  getDraft: vi.fn(),
  extractInspection: vi.fn(),
  saveDraft: vi.fn(),
  sendToInfraCloud: vi.fn(),
}));

const api = await import("../lib/api");

function renderReviewPage() {
  return render(
    <MemoryRouter initialEntries={["/review/14401"]}>
      <Routes>
        <Route path="/review/:id" element={<ReviewPage />} />
      </Routes>
    </MemoryRouter>
  );
}

function mockFetchSequence(...responses: Array<Partial<Response> & { json?: () => Promise<unknown>; blob?: () => Promise<Blob> }>) {
  const fetchMock = vi.fn();

  for (const response of responses) {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({}),
      blob: async () => new Blob(["audio"], { type: "audio/wav" }),
      ...response,
    });
  }

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("ReviewPage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("restores a saved draft without rerunning extraction", async () => {
    mockFetchSequence({
      json: async () => ({
        ID: 14401,
        Status: "Suspicion",
        Material: "Beton | Stahlbeton",
      }),
    });

    vi.mocked(api.getDraft).mockResolvedValue({
      suspicion_id: 14401,
      proposal: {
        ID: 14401,
        Status: "Damage",
        Material: "Beton | Stahlbeton",
      },
      savedAt: "2026-03-23T10:30:00.000Z",
      workflow_run_id: "workflow-run-1",
      transcript: "Laengsriss bestaetigt.",
    });

    renderReviewPage();

    expect(await screen.findByText("Saved draft restored")).toBeInTheDocument();
    expect(screen.getByText(/review state resumed/i)).toBeInTheDocument();
    expect(screen.getByText("Damage")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Transcript" })).toBeInTheDocument();
    expect(screen.getByText(/Laengsriss bestaetigt\./i)).toBeInTheDocument();
  });

  it("shows extraction errors to the reviewer", async () => {
    mockFetchSequence(
      {
        json: async () => ({
          ID: 14401,
          Status: "Suspicion",
          Material: "Beton | Stahlbeton",
        }),
      },
      {
        ok: false,
        status: 500,
      }
    );

    vi.mocked(api.getDraft).mockRejectedValue(new api.ApiError(404, {
      code: "DRAFT_NOT_FOUND",
      message: "Draft not found.",
    }));

    renderReviewPage();

    await screen.findByText("Run Extraction");
    await userEvent.click(screen.getByRole("button", { name: "Run Extraction" }));

    expect(await screen.findByText("Extraction failed")).toBeInTheDocument();
    expect(screen.getByText("Failed to load the sample audio.")).toBeInTheDocument();
  });

  it("lets reviewers correct invalid extracted values before saving", async () => {
    mockFetchSequence(
      {
        json: async () => ({
          ID: 14401,
          Status: "Suspicion",
          Material: "Beton | Stahlbeton",
        }),
      },
      {
        blob: async () => new Blob(["audio"], { type: "audio/wav" }),
      }
    );

    vi.mocked(api.getDraft).mockRejectedValue(new api.ApiError(404, {
      code: "DRAFT_NOT_FOUND",
      message: "Draft not found.",
    }));
    vi.mocked(api.extractInspection).mockResolvedValue({
      suspicion_id: "14401",
      intent: "VALIDATE_DAMAGE",
      confidence: {},
      simulated_infracloud_payload: {
        ID: 14401,
        Status: "Damage",
        Class: "9",
      },
    });
    vi.mocked(api.saveDraft).mockResolvedValue({
      savedAt: "2026-03-23T10:30:00.000Z",
    });

    renderReviewPage();

    await userEvent.click(await screen.findByRole("button", { name: "Run Extraction" }));

    expect(await screen.findByText(/Fix 1 invalid field/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "9" }));
    const select = await screen.findByRole("combobox");
    await userEvent.selectOptions(select, "2");

    await waitFor(() =>
      expect(screen.queryByText(/Fix 1 invalid field/i)).not.toBeInTheDocument()
    );

    const saveButton = screen.getByRole("button", { name: "Save" });
    expect(saveButton).toBeEnabled();

    await userEvent.click(saveButton);

    await waitFor(() => expect(api.saveDraft).toHaveBeenCalled());
    expect(screen.getByText("Draft saved.")).toBeInTheDocument();
  });

  it("keeps send disabled until approval and then enables submission", async () => {
    mockFetchSequence(
      {
        json: async () => ({
          ID: 14401,
          Status: "Suspicion",
          Material: "Beton | Stahlbeton",
        }),
      },
      {
        blob: async () => new Blob(["audio"], { type: "audio/wav" }),
      }
    );

    vi.mocked(api.getDraft).mockRejectedValue(new api.ApiError(404, {
      code: "DRAFT_NOT_FOUND",
      message: "Draft not found.",
    }));
    vi.mocked(api.extractInspection).mockResolvedValue({
      suspicion_id: "14401",
      intent: "VALIDATE_DAMAGE",
      confidence: {},
      simulated_infracloud_payload: {
        ID: 14401,
        Status: "Damage",
        Class: "2",
      },
    });
    vi.mocked(api.saveDraft).mockResolvedValue({
      savedAt: "2026-03-23T10:30:00.000Z",
    });
    vi.mocked(api.sendToInfraCloud).mockResolvedValue({
      sentAt: "2026-03-23T11:00:00.000Z",
      mode: "mock-send",
    });

    renderReviewPage();

    await userEvent.click(await screen.findByRole("button", { name: "Run Extraction" }));

    const sendButton = await screen.findByRole("button", { name: "Send to InfraCloud" });
    expect(sendButton).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(screen.getByRole("button", { name: "Send to InfraCloud" })).toBeEnabled());

    await userEvent.click(screen.getByRole("button", { name: "Send to InfraCloud" }));

    await waitFor(() => expect(api.sendToInfraCloud).toHaveBeenCalled());
  });

  it("renders the transcript above the updated fields section", async () => {
    mockFetchSequence(
      {
        json: async () => ({
          ID: 14401,
          Status: "Suspicion",
          Material: "Beton | Stahlbeton",
        }),
      },
      {
        blob: async () => new Blob(["audio"], { type: "audio/wav" }),
      }
    );

    vi.mocked(api.getDraft).mockRejectedValue(new api.ApiError(404, {
      code: "DRAFT_NOT_FOUND",
      message: "Draft not found.",
    }));
    vi.mocked(api.extractInspection).mockResolvedValue({
      suspicion_id: "14401",
      intent: "VALIDATE_DAMAGE",
      transcript: "Leichte Korrosion am Gelander.",
      confidence: {},
      simulated_infracloud_payload: {
        ID: 14401,
        Status: "Damage",
        Class: "2",
      },
    });

    renderReviewPage();

    await userEvent.click(await screen.findByRole("button", { name: "Run Extraction" }));

    const transcriptHeading = await screen.findByRole("heading", { name: "Transcript" });
    const updatedFieldsHeading = await screen.findByRole("heading", { name: "Updated Fields" });

    const order = transcriptHeading.compareDocumentPosition(updatedFieldsHeading);
    expect(order & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
