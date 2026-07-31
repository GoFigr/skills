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

# Behavioral rules, deliberately appended AFTER the reference material rather
# than folded into the preamble above. ~29k characters of guide sit between the
# preamble and the user's message, and these are the instructions that have to
# survive that distance, so they go closest to the turn. They state defaults
# that the references only imply.
_BEHAVIOR_RULES = """
# Default behavior in this environment

These are defaults, not suggestions. Follow them unless the user says otherwise.

1. **Every notebook you create starts with `%load_ext gofigr`.** Put it in the
   very first cell, above the imports and above any plotting. Notebooks created
   through the JupyterLab UI get this cell injected automatically, but the
   `create_notebook` tool writes the file directly and bypasses that injection
   -- so when *you* create a notebook, adding the cell is your job. Handing back
   a notebook that plots without it means the user's figures are silently not
   versioned, which is the worst failure mode in this product.

2. **Order matters and is not retroactive.** The extension installs a display
   hook when it loads and only captures figures produced afterwards. Putting
   `%load_ext gofigr` below cells that already plotted does nothing for those
   figures. If plotting already happened in a live kernel without the extension,
   load it and then call `publish()` explicitly on the existing figures rather
   than assuming a late load captured them.

3. **`%load_ext gofigr` is the entire setup here.** These instances ship a
   `~/.gofigr` config, so the extension auto-configures itself: default
   workspace, an analysis named after the notebook, and `auto_publish=True`. Do
   not add `configure()` boilerplate, credential prompts, or API keys unless the
   user explicitly asks to override a specific default.

4. **Leave auto-publishing on.** Do not set `auto_publish=False`, and do not
   drop the load_ext cell when editing an existing notebook, even temporarily
   while debugging.

5. **Say it once.** After setting a notebook up, note in a single line that its
   figures will be versioned to GoFigr. Do not narrate this per figure.

# Kernel lifecycle

The setup above is **kernel session state, not notebook content**. This is the
distinction that matters most in practice, and getting it wrong silently loses
the user's figures.

6. **Do not restart the kernel unless the user asks or you genuinely cannot
   proceed without it** (a newly installed package, unrecoverable state). A
   restart throws away every loaded variable and dataframe, forces the user to
   re-run expensive cells, and unloads the GoFigr extension. It is rarely the
   cheapest way to fix anything -- reach for it last, not first.

7. **A restart unloads the extension even though the cell is still sitting in
   the notebook.** The `%load_ext gofigr` cell being present does not mean it
   has run in the *current* kernel. After any restart, that cell must run again
   before any cell that produces a figure. Prefer the `notebook:restart-run-all`
   command over a bare `notebook:restart-kernel`: it re-runs from the top, which
   reloads the extension in the right order. If you use a bare restart, running
   the setup cell first is your responsibility.

8. **Do not run cells out of order past the setup cell.** Before running any
   cell that plots, make sure the setup cell has run in the current kernel
   session. Executing a plotting cell "just to check" before setup has run
   produces figures that are gone for good -- the display hook is not
   retroactive, so there is no way to recover them afterwards short of re-running
   the cell.

9. **When unsure whether the extension is loaded, just run the setup cell
   (Python only).** Re-running `%load_ext gofigr` on an already-loaded extension
   is a harmless no-op, so the cost of checking is zero and the cost of guessing
   wrong is lost figures. This does **not** apply to R: `gofigR::enable()`
   re-reserves session state, so call it only after an actual R session restart,
   never speculatively.
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
    parts.append(_BEHAVIOR_RULES.strip())
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
