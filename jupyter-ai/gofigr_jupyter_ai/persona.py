"""GoFigr Assistant: Jupyternaut extended with GoFigr domain knowledge.

Subclasses JupyternautPersona, so it inherits the chat plumbing, notebook
tools, model picker, and model resolution unchanged; the only additions are
the identity (name/avatar/description) and a knowledge block appended to the
system prompt. The knowledge is the Claude skill's SKILL.md + references,
embedded as package data at build time (see pyproject.toml force-include) so
the two stay single-sourced.
"""
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jupyter_ai_jupyternaut.jupyternaut.jupyternaut import JupyternautPersona
from jupyter_ai_persona_manager.base_persona import PersonaDefaults

# Order matters: SKILL.md routes; the references follow inline in the same
# order its routing table lists them.
_KNOWLEDGE_FILES = [
    "SKILL.md",
    "references/python.md",
    "references/r.md",
    "references/cleanroom-python.md",
    "references/cleanroom-r.md",
]

_KNOWLEDGE_PREAMBLE = """
<gofigr_knowledge>
You are running inside GoFigr managed compute. GoFigr (gofigr.io) is a
reproducibility engine that versions figures together with the code, data, and
environment that produced them; users here publish figures from notebooks with
the `gofigr` (Python) and `gofigR` (R) clients. The usage guide below is
authoritative -- prefer it over prior knowledge. Its routing table refers to
reference files; those references are included inline right after the guide,
as sections titled "Reference: <name>".
"""

# The GoFigr mark, copied verbatim from gofigr-python
# (gofigr/resources/logo_small.png) -- the same logo the notebook widgets
# show, so the chat avatar matches the rest of the product. Refresh this copy
# if the brand mark changes.
_AVATAR_FILENAME = "logo.png"


@lru_cache(maxsize=1)
def _gofigr_knowledge() -> str:
    """Assemble the knowledge block from embedded skill content (cached)."""
    root = files("gofigr_jupyter_ai") / "knowledge"
    parts = [_KNOWLEDGE_PREAMBLE.strip()]
    for rel_path in _KNOWLEDGE_FILES:
        text = (root / rel_path).read_text(encoding="utf-8")
        if rel_path == "SKILL.md":
            text = _strip_frontmatter(text)
        else:
            parts.append(f"# Reference: {rel_path}")
        parts.append(text.strip())
    parts.append("</gofigr_knowledge>")
    return "\n\n".join(parts)


def _strip_frontmatter(text: str) -> str:
    """Drop the leading YAML frontmatter block (--- ... ---) if present."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + len("\n---"):].lstrip()
    return text


class GoFigrPersona(JupyternautPersona):
    """Jupyternaut + GoFigr domain knowledge."""

    @property
    def defaults(self) -> PersonaDefaults:
        return PersonaDefaults(
            name="GoFigr Assistant",
            avatar_path=str(files("gofigr_jupyter_ai") / _AVATAR_FILENAME),
            description=(
                "Data analysis assistant that knows GoFigr: publishing figures, "
                "tracking assets, and clean-room reproducible functions."
            ),
            system_prompt="...",  # unused; assembled in get_system_prompt (as in Jupyternaut)
        )

    def get_system_prompt(self, model_id: str, message: Any) -> str:
        base = super().get_system_prompt(model_id=model_id, message=message)
        return f"{base}\n\n{_gofigr_knowledge()}"
