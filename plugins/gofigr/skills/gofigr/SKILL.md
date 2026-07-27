---
name: gofigr
description: Write code that publishes figures and data assets to GoFigr (gofigr.io) from Python or R, including Clean Room reproducible functions. Use when the user mentions GoFigr, gofigR, gfconfig, `%load_ext gofigr`, `@reproducible`, "clean room", or asks to publish/capture/version a plot, or to track a data file used by a figure.
when_to_use: Triggers include "publish this figure to GoFigr", "add GoFigr to this notebook", "make this a clean room function", "track this CSV as an asset", "why isn't my figure showing up in GoFigr", and any edit to a file that already imports gofigr or gofigR.
---

# GoFigr

GoFigr versions figures with the code, data, and environment that produced them. Two client libraries: `gofigr` (Python, ≥2.3.3) and `gofigR` (R, ≥2.0.2).

## Route first

| Situation | Read |
|---|---|
| Python — Jupyter, scripts, asset tracking | `${CLAUDE_SKILL_DIR}/references/python.md` |
| R — RMarkdown, scripts, RStudio, asset tracking | `${CLAUDE_SKILL_DIR}/references/r.md` |
| Python `@reproducible` / clean room | `${CLAUDE_SKILL_DIR}/references/cleanroom-python.md` |
| R `reproducible()` / clean room | `${CLAUDE_SKILL_DIR}/references/cleanroom-r.md` |

Read only the file(s) you need. Don't guess at API shapes — the two clients differ in ways that are easy to get wrong (R has no `publisher=` argument; Python has no `packages=` character vector).

## Rules that apply everywhere

**Never hardcode credentials.** Auth comes from `~/.gofigr` (written by the `gfconfig` wizard) or from `GF_API_KEY` / `GF_USERNAME` + `GF_PASSWORD` in the environment. If a user has not configured GoFigr, tell them to run `gfconfig` (Python) or `gofigR::gfconfig()` (R) rather than writing a key into a file.

**R requires an explicit `publish()` call for every figure.** Automatic capture in R is being sunset — it is not reliable. See the R rule below.

**Clean room degrades silently.** Both clients respond to unsupported parameter types, oversized data, or a missing dependency by emitting a *warning* and running the function normally, with no capture. A run that produced no error did not necessarily publish anything. After writing clean room code, tell the user to check for warnings, or verify the revision appeared in the web app.

**Don't invent figure names.** In both clients an unnamed figure is a problem: R publishes it as `"Anonymous Figure"` with a warning. Pass a real name, or use `auto_assign=TRUE`/`auto_assign=True` to let the server assign it by image content.

## The R rule: explicit publish only

Automatic capture in R works by reassigning `plot()` and `print()` in the global environment. It misses figures, double-publishes others, and interacts badly with knitr and with packages that print via their own methods. It is being sunset.

When writing R code, **do not use**:

- `gofigR::enable(auto_publish = TRUE)` — leave it at the default `FALSE`
- `gf_plot()` / `gf_print()` — the same interception machinery under another name
- `publish_base()` — already deprecated in the package; use `publish()`

**Do** call `publish()` once per figure:

```r
p <- ggplot(mtcars, aes(mpg, hp)) + geom_point()
publish(p, figure_name = "MPG vs horsepower")
```

Base graphics go through `publish()` as an expression block:

```r
publish({
  plot(pressure, main = "Pressure vs temperature")
  text(200, 50, "Note the non-linear relationship")
}, data = pressure, figure_name = "Pressure vs temperature")
```

If you are editing R code that already relies on auto-capture, convert it: drop `auto_publish = TRUE`, then add an explicit `publish()` for each figure the code produces. Say what you changed and why — the user may not know the feature is going away.

Python is different: `auto_publish=True` is the default in Jupyter, works well, and should stay on unless the user wants manual control.
