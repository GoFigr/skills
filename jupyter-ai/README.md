# gofigr-jupyter-ai

The **GoFigr Assistant** persona for [jupyter-ai](https://github.com/jupyterlab/jupyter-ai)
v3: Jupyternaut (chat, notebook tools, model picker) extended with GoFigr domain
knowledge, so the assistant can help users publish figures, track assets, and
write clean-room reproducible functions without being told what GoFigr is.

The knowledge is **single-sourced from the Claude skill** in this repo
(`plugins/gofigr/skills/gofigr/`): SKILL.md and its references are embedded as
package data at build time. Update the skill, rebuild, and the persona follows.

Intended deployment: baked into GoFigr managed-compute AMIs, where the AI
gateway environment (`OPENAI_API_BASE` etc.) is already configured. It works in
any jupyter-ai v3 install, though — the persona just adds prompt content.

```bash
pip install ./jupyter-ai   # from the repo root
```

Then select "GoFigr Assistant" in the jupyter-ai chat, or make it the default:

```python
# jupyter_server_config.py / jupyter_lab_config.py
c.PersonaManager.default_persona_id = "jupyter-ai-personas::gofigr_jupyter_ai::GoFigrPersona"
```
