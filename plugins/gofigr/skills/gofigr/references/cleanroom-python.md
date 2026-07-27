# Clean Room — Python

`@reproducible` turns a function into a self-contained, reproducible unit. The function sees only its own parameters, the packages it declares, and builtins — nothing from the surrounding notebook. When it runs, GoFigr captures the source, parameters, DataFrames, environment, and output.

## The isolation rule

This is the constraint that breaks generated code most often:

**The function body cannot reference notebook globals, module-level variables, or imports made outside it.** Everything it needs arrives as a parameter or comes from a declared package. Write the function as if it lived in an empty file.

```python
# WRONG — `penguins` and `THRESHOLD` are notebook globals
@reproducible
def bad(bins: int = 20):
    filtered = penguins[penguins.body_mass_g > THRESHOLD]
    sns.histplot(filtered, x="flipper_length_mm", bins=bins)

# RIGHT — everything comes in through the signature
@reproducible
def good(data, threshold: int = 3500, bins: int = 20):
    filtered = data[data.body_mass_g > threshold]
    sns.histplot(filtered, x="flipper_length_mm", bins=bins)

good(penguins)
```

`sns` is fine in both: it is a default package (see below).

## Basic use

In Jupyter, `%load_ext gofigr` injects `reproducible` and every `*Param` class:

```python
%load_ext gofigr
import seaborn as sns

penguins = sns.load_dataset("penguins")

@reproducible
def flipper_histogram(data, bins: int = 20):
    sns.histplot(data=data, x="flipper_length_mm", bins=bins)

flipper_histogram(penguins)
```

With `auto_publish=True` (the default), the figure publishes on its own.

## Parameter widgets

Add `interactive=True` to render controls above the figure; changing one re-runs the function.

```python
from typing import Literal

@reproducible(interactive=True)
def flipper_distribution(
    data,
    bins: int    = SliderParam(20, min=5, max=100, step=5),
    alpha: float = SliderParam(0.7, min=0.1, max=1.0, step=0.05),
    species: str = DropdownParam("Adelie", choices=["Adelie", "Chinstrap", "Gentoo"]),
    show_kde: Literal["yes", "no", "auto"] = "yes",
    show_grid: bool = True,
    title: str   = "Flipper Length Distribution",
):
    filtered = data[data["species"] == species]
    kde = True if show_kde == "yes" else (False if show_kde == "no" else None)
    ax = sns.histplot(data=filtered, x="flipper_length_mm", bins=bins, alpha=alpha, kde=kde)
    ax.set_title(title)
    if show_grid:
        ax.grid(True, alpha=0.3)

flipper_distribution(penguins)
```

### Inference vs. explicit Param classes

| Default | Widget |
|---|---|
| `int` / `float` | slider |
| `bool` | checkbox |
| `str` | text input |
| `Literal[...]` type hint | dropdown |
| `pd.DataFrame` | static (read-only) |

Explicit classes: `SliderParam(default, min=, max=, step=)`, `DropdownParam(default, choices=[...])`, `CheckboxParam(default)`, `TextParam(default)`, `StaticParam(default)`.

Omitted slider bounds are resolved automatically: min `0`; max `max(value * 2, 100)` for ints and `max(value * 2, 1.0)` for floats; step `1` for ints, `0.1` for floats. Set them explicitly when the auto range would be nonsense for the variable.

### interactive=True requires anywidget

```bash
pip install anywidget
```

JupyterLab needs a full restart (not just the kernel) plus a hard browser reload. Classic Notebook (<7) also needs the nbextension enabled:

```bash
jupyter nbextension install --py anywidget --sys-prefix
jupyter nbextension enable  --py anywidget --sys-prefix
```

If widgets still don't render:

```python
from gofigr.reproducible import check_anywidget_health
check_anywidget_health()
```

Outside Jupyter, `interactive=True` warns and runs non-interactively.

## Packages

Defaults available inside every clean room: `pd` (pandas), `np` (numpy), `plt` (matplotlib.pyplot), `sns` (seaborn).

```python
@reproducible(packages={"gg": "plotnine"})                       # merged with defaults
@reproducible(packages={"pd": "pandas"}, merge_packages=False)   # replaces defaults
```

Session-wide:

```python
from gofigr.reproducible import set_default_packages, reset_default_packages
set_default_packages({"gg": "plotnine"})
set_default_packages({"pd": "pandas", "gg": "plotnine"}, merge=False)
reset_default_packages()
```

## Publishing

With `auto_publish=True` in Jupyter, nothing extra is needed.

For explicit control — and always in scripts — pass a publisher and call `publish()` inside the body. `publish()` is injected into the clean room globals automatically:

```python
from gofigr.publisher import Publisher

pub = Publisher(workspace="Analytics", analysis="Penguins")

@reproducible(publisher=pub)
def flipper_histogram(data, bins: int = 20):
    sns.histplot(data=data, x="flipper_length_mm", bins=bins)
    publish(plt.gcf(), target="Flipper Histogram")

flipper_histogram(penguins)
```

Each revision stores the function body, a JSON manifest (parameter types, widget config, imports, package versions), DataFrame parameters as Parquet, and a flag marking it a Clean Room revision.

## Scripts

```python
from gofigr.publisher import Publisher
from gofigr.reproducible import reproducible, SliderParam
import matplotlib.pyplot as plt
import seaborn as sns

penguins = sns.load_dataset("penguins")
pub = Publisher(workspace="Analytics", analysis="Penguins")

@reproducible(publisher=pub)
def flipper_histogram(data, bins: int = SliderParam(20, min=5, max=100, step=5)):
    sns.histplot(data=data, x="flipper_length_mm", bins=bins)
    publish(plt.gcf(), target="Flipper Histogram")

flipper_histogram(penguins)
```

Differences from Jupyter: no name injection (import explicitly), no auto-publish (pass `publisher=`), `interactive=True` ignored.

## Silent fallbacks

Clean room does not raise on these — it warns and runs the function as a plain function, capturing nothing. Check warnings before reporting success.

| Trigger | Behavior |
|---|---|
| Unsupported parameter type — custom objects, numpy arrays, lambdas | warns, runs without clean room |
| Total DataFrame size over 100 MB (`memory_usage(deep=True)`) | warns, runs without clean room |
| `interactive=True` outside Jupyter | warns, runs non-interactively |

## Other behaviors

**DataFrames are copied.** DataFrame arguments round-trip through Parquet, so the function receives a deserialized copy. Mutating it does not affect the caller's object, and dtypes that don't survive Parquet won't survive here.

**`plt.show()` is automatic.** If matplotlib figures exist after the body runs, it is called for you.

**Source must be importable.** The body is extracted with `inspect.getsource`. Functions built by `exec` are not supported.

**Return values.** Returned normally in non-interactive mode; `None` in interactive mode, where output goes to the widget.

**Nesting.** Each call gets its own context; the innermost wins for `publish()`. The context resets when the function returns or raises.
