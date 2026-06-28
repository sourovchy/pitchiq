import type {
  AnalysisApiResponse,
  AnalysisRequestPayload,
  ApiError,
} from "../types/analysis";

export class AnalysisApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "AnalysisApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const DEFAULT_TIMEOUT_MS = 30_000;

function resolveEndpoint(): string {
  const configuredBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(
    /\/$/,
    "",
  );
  if (configuredBase) {
    return `${configuredBase}/api/analyze`;
  }
  return "/api/analyze";
}

export interface RequestMatchAnalysisOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
}

export async function requestMatchAnalysis(
  payload: AnalysisRequestPayload,
  options: RequestMatchAnalysisOptions = {},
): Promise<AnalysisApiResponse> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const externalSignal = options.signal;

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort("timeout"), timeoutMs);

  const onExternalAbort = () => controller.abort(externalSignal?.reason);
  if (externalSignal) {
    if (externalSignal.aborted) {
      window.clearTimeout(timeoutId);
      controller.abort(externalSignal.reason);
    } else {
      externalSignal.addEventListener("abort", onExternalAbort, { once: true });
    }
  }

  try {
    const response = await fetch(resolveEndpoint(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    const body = (await response.json().catch(() => null)) as
      | AnalysisApiResponse
      | ApiError
      | null;

    if (!response.ok) {
      const apiError = body as ApiError | null;
      const err = apiError?.error;
      throw new AnalysisApiError(
        response.status,
        err?.code ?? "unknown_error",
        err?.message ?? `Request failed with status ${response.status}`,
        err?.details,
      );
    }

    return body as AnalysisApiResponse;
  } catch (error) {
    if (error instanceof AnalysisApiError) {
      throw error;
    }
    if (controller.signal.aborted) {
      if (externalSignal?.aborted) {
        throw new AnalysisApiError(
          0,
          "request_cancelled",
          "The analysis request was cancelled.",
        );
      }
      throw new AnalysisApiError(
        0,
        "request_timeout",
        "The tactical analyst took too long to respond. Please try again.",
      );
    }
    const message =
      error instanceof Error ? error.message : "Network request failed.";
    throw new AnalysisApiError(0, "network_error", message);
  } finally {
    window.clearTimeout(timeoutId);
    if (externalSignal) {
      externalSignal.removeEventListener("abort", onExternalAbort);
    }
  }
}