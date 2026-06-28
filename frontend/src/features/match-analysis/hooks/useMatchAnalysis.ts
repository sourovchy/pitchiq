import { useCallback, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  AnalysisApiError,
  requestMatchAnalysis,
} from "../../../services/analysisService";
import type {
  AnalysisApiResponse,
  AnalysisRequestPayload,
} from "../../../types/analysis";

const REQUEST_TIMEOUT_MS = 30_000;

export function useMatchAnalysis() {
  const abortRef = useRef<AbortController | null>(null);

  const mutation = useMutation<AnalysisApiResponse, AnalysisApiError, AnalysisRequestPayload>({
    mutationFn: (payload) => {
      // Use the active controller if submit already wired one; otherwise mint
      // a fresh one so unmount/reset can still cancel an in-flight request.
      const controller = abortRef.current ?? new AbortController();
      if (!abortRef.current) {
        abortRef.current = controller;
      }
      return requestMatchAnalysis(payload, {
        timeoutMs: REQUEST_TIMEOUT_MS,
        signal: controller.signal,
      });
    },
  });

  const submit = useCallback(
    (payload: AnalysisRequestPayload) => {
      abortRef.current?.abort("superseded");
      abortRef.current = new AbortController();
      mutation.mutate(payload);
    },
    [mutation],
  );

  useEffect(() => {
    return () => {
      abortRef.current?.abort("unmount");
    };
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort("reset");
    abortRef.current = null;
    mutation.reset();
  }, [mutation]);

  return {
    submit,
    reset,
    data: mutation.data,
    error: mutation.error,
    isError: mutation.isError,
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
  };
}