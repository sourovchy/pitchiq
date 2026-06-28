from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int


class GeminiConfigurationError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="gemini_not_configured",
            message="The tactical analysis service is not configured.",
            status_code=503,
        )


class GeminiProviderError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="gemini_unavailable",
            message="The tactical analysis provider is temporarily unavailable.",
            status_code=502,
        )


class AnalysisGenerationError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="invalid_analysis_response",
            message="The model could not produce a valid tactical analysis.",
            status_code=502,
        )

