"""
Prompt template loader and renderer.

Loads YAML prompt files from the templates/ directory and provides
variable injection. Each template has multiple versions; the latest
is the default.

Interview talking points:
- Why YAML over JSON? YAML supports multi-line strings without escape
  characters and allows comments. Both matter for prompts, which are
  often long and benefit from inline notes.
- Why double-brace escaping ({{ ... }}) for literal braces? Because we
  use Python's str.format() for variable injection, which treats single
  braces as variables. JSON examples in prompts contain literal braces,
  so they need to be escaped.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class PromptVersion:
    """A single version of a prompt template."""

    version: int
    created: str
    notes: str
    template: str

    def render(self, **variables: str) -> str:
        """Inject variables into the template.

        Uses Python's str.format() — variables are referenced as {name}
        in the template. Use {{name}} for literal braces.
        """
        return self.template.format(**variables)


@dataclass
class Prompt:
    """A named prompt with multiple versions."""

    name: str
    description: str
    variables: list[str]
    versions: list[PromptVersion]

    @property
    def latest(self) -> PromptVersion:
        """The most recent version (highest version number)."""
        return max(self.versions, key=lambda v: v.version)

    def get_version(self, version: int) -> PromptVersion | None:
        """Get a specific version by number."""
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def render(self, version: int | None = None, **variables: str) -> str:
        """Render a prompt with the given variables.

        If version is None, uses the latest version.
        """
        v = self.get_version(version) if version is not None else self.latest
        if v is None:
            raise ValueError(f"Version {version} not found for prompt '{self.name}'")
        return v.render(**variables)


def load_prompt(name: str) -> Prompt:
    """Load a prompt template by name from the templates directory."""
    path = TEMPLATES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f)

    versions = [
        PromptVersion(
            version=v["version"],
            created=str(v.get("created", "")),
            notes=v.get("notes", ""),
            template=v["template"],
        )
        for v in data["versions"]
    ]

    return Prompt(
        name=data["name"],
        description=data.get("description", ""),
        variables=data.get("variables", []),
        versions=versions,
    )


def list_prompts() -> list[str]:
    """List all available prompt names."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted([
        p.stem for p in TEMPLATES_DIR.glob("*.yaml")
    ])
