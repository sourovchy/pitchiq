from pathlib import Path
from string import Template


class PromptLoader:
    def __init__(self, prompt_directory: Path | None = None) -> None:
        self._prompt_directory = prompt_directory or Path(__file__).parents[1] / "prompts"

    def load(self, name: str, **variables: str) -> str:
        prompt_path = self._prompt_directory / f"{name}.md"

        try:
            template = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise RuntimeError(f"Prompt template not found: {name}") from error

        return Template(template).substitute(variables).strip()

