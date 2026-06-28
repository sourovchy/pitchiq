import { useState } from "react";

import { useMatchAnalysis } from "./hooks/useMatchAnalysis";
import { AnalysisErrorState } from "./components/AnalysisErrorState";
import { AnalysisLoadingState } from "./components/AnalysisLoadingState";
import { MatchAnalysisForm } from "./components/MatchAnalysisForm";
import { MatchAnalysisResults } from "./components/MatchAnalysisResults";
import type { AnalysisRequestPayload } from "../../types/analysis";

export function MatchAnalysisPage() {
  const analysis = useMatchAnalysis();
  const [lastRequest, setLastRequest] = useState<AnalysisRequestPayload | null>(null);

  function handleSubmit(payload: AnalysisRequestPayload) {
    setLastRequest(payload);
    analysis.submit(payload);
  }

  function handleRetry() {
    if (lastRequest) {
      analysis.submit(lastRequest);
    }
  }

  const showResults = analysis.isSuccess ? analysis.data : null;

  return (
    <main className="mx-auto max-w-6xl px-6 pt-10 pb-16 lg:px-8 lg:pt-16 lg:pb-24" aria-label="Tactical match analysis">
      <header className="mb-10 max-w-3xl">
        <p className="text-[10px] font-semibold tracking-[0.24em] text-pitch uppercase">
          Tactical match analysis
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          A pre-match brief in seconds.
        </h1>
        <p className="mt-4 text-base text-white/60 sm:text-lg">
          Pick any two national teams. <span className="font-semibold text-white">PitchIQ</span> reasons about formations,
          structural strengths, key duels, and how the game is likely to flow
          — then returns a structured JSON brief rendered into this dashboard.
        </p>
      </header>

      <MatchAnalysisForm onSubmit={handleSubmit} isLoading={analysis.isPending} />

      <div className="mt-8">
        {analysis.isPending ? (
          <AnalysisLoadingState
            homeTeam={lastRequest?.homeTeam ?? ""}
            awayTeam={lastRequest?.awayTeam ?? ""}
          />
        ) : analysis.isError && analysis.error ? (
          <AnalysisErrorState
            error={analysis.error}
            onRetry={lastRequest ? handleRetry : undefined}
          />
        ) : null}
      </div>

      {showResults ? (
        <div className="mt-10">
          <MatchAnalysisResults
            analysis={showResults.data}
            model={showResults.model}
          />
        </div>
      ) : null}
    </main>
  );
}