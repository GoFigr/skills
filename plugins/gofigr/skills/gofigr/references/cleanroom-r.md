# Clean Room — R

`reproducible()` runs a function in a clean environment containing only its declared parameters, the exports of the packages you list, base R, and `publish()`. GoFigr captures the source, parameters, data frames, environment, and output.

The R API differs from Python's in three ways worth memorizing:

1. Parameters are declared as **function defaults** using `slider()` / `dropdown()` / `checkbox()` / `text_input()` / `static()` — there are no `*Param` classes.
2. Packages are declared with a `packages` argument. Nothing is available by default beyond base R.
3. There is **no `publisher` argument**. `publish()` is always injected, and the session set up by `gofigR::enable()` decides where the figure goes.

## The isolation rule

The function body cannot see anything from the global environment. Everything arrives as a parameter or comes from a package named in `packages`.

```r
# WRONG — `my_data` is a global, dplyr is never declared
reproducible(
  function(bins = 20L) {
    d <- my_data %>% filter(mass > 3500)
    ggplot(d, aes(flipper)) + geom_histogram(bins = bins)
  },
  packages = c("ggplot2")
)

# RIGHT
reproducible(
  function(data = static(penguins), threshold = slider(3500, min = 2000, max = 6000)) {
    d <- dplyr::filter(data, mass > threshold)
    p <- ggplot(d, aes(flipper)) + geom_histogram()
    publish(p, figure_name = "Flipper histogram")
  },
  packages = c("ggplot2", "dplyr")
)
```

## Basic use

```r
library(gofigR)
library(ggplot2)

gofigR::enable(workspace_name = "Analytics", analysis_name = "Penguins")

reproducible(
  function(data = static(iris)) {
    p <- ggplot(data, aes(Sepal.Length, Petal.Length, color = Species)) + geom_point()
    publish(p, figure_name = "Iris Scatter")
  },
  packages = c("ggplot2")
)
```

## reproducible()

```r
reproducible(fn,
             packages    = character(0),
             imports     = list(),
             name        = NULL,
             interactive = FALSE,
             viewer      = NULL)
```

| Parameter | Notes |
|---|---|
| `fn` | function whose formals use the parameter constructors below |
| `packages` | character vector, or named list to pin versions: `list(ggplot2 = "3.5.0")`. Unnamed vectors resolve installed versions automatically |
| `imports` | named list mapping aliases to packages, e.g. `list(plt = "ggplot2")`, recorded in the manifest for parity with the Python client |
| `name` | display name in the web app; without it the function is anonymous |
| `interactive` | launches a Shiny gadget with parameter widgets |
| `viewer` | `shiny::paneViewer()`, `shiny::browserViewer()`, or `shiny::dialogViewer(...)`. Defaults to a dialog, or the RStudio Viewer when available |

Returns whatever the function body returns — typically the result of `publish()`.

## Parameter constructors

```r
bins      = slider(20L, min = 5L,  max = 50L, step = 5L)     # integer slider
alpha     = slider(0.7, min = 0.1, max = 1.0, step = 0.05)   # numeric slider
species   = dropdown("Adelie", choices = c("Adelie", "Chinstrap", "Gentoo"))
show_grid = checkbox(TRUE)
title     = text_input("Flipper Length Distribution")
data      = static(penguins)
```

Pass an integer literal (`20L`) for an integer slider — the gadget preserves the type when feeding the value back to the function.

`static()` renders no widget. Use it for data frames and anything else you want captured but not edited. Plain defaults are wrapped in `static()` automatically, so `data = iris` and `data = static(iris)` are equivalent.

## Interactive mode

```r
reproducible(
  function(
      point_size  = slider(2, min = 0.5, max = 5, step = 0.5),
      color_by    = dropdown("Species", choices = c("Species", "Sepal.Width", "Petal.Width")),
      show_smooth = checkbox(FALSE),
      data        = static(iris)
    ) {
      p <- ggplot(data, aes(Sepal.Length, Petal.Length, color = .data[[color_by]])) +
        geom_point(size = point_size) +
        theme_minimal()
      if (show_smooth) p <- p + geom_smooth(method = "lm", se = FALSE)
      publish(p, figure_name = "Iris Scatter")
    },
    packages    = c("ggplot2"),
    interactive = TRUE
)
```

While the gadget is open, `publish()` is a no-op preview. Clicking **Publish** re-runs the function with the real `publish()` and shows a link plus QR code to the new revision.

Interactive mode needs a live interactive R session. Under knitr or in a non-interactive script it is skipped silently and the function runs once with its default parameter values — which is the correct behavior for knitting, but means an `interactive = TRUE` example in an `.Rmd` will not error to tell you it was downgraded.

## Requirements and silent fallbacks

Clean room does not raise on these — it warns and runs the function as a plain function with no capture. Check warnings before reporting success.

| Trigger | Behavior |
|---|---|
| `nanoparquet` not installed | warns, runs without clean room metadata |
| Unsupported parameter type | warns, runs without clean room metadata |
| Total data frame size over 100 MB (`object.size()`) | warns, runs without clean room metadata |

Install the parquet dependency once:

```r
install.packages("nanoparquet")
```

Serializable parameter types: atomic values (numeric, integer, logical, character), data frames, and nested lists of those. Anything else — S4 objects, environments, functions, model fits — falls back.

## Other behaviors

**Data frames are copied.** They round-trip through Parquet before the function sees them, so the clean room version matches what is stored.

**Other parameters round-trip through JSON.** Atomic values pass through `jsonlite`, so the function sees exactly what will be persisted in the manifest.

**Source extraction** uses `body(fn)`. Functions written inline as the first argument work directly; programmatically constructed functions work as long as `body(fn)` returns a valid expression.

## In RMarkdown

````markdown
```{r setup, include=FALSE}
library(gofigR)
library(ggplot2)
gofigR::enable(workspace_name = "Scratchpad", analysis_name = "Clean room in R")
```

```{r iris_scatter, fig.width=8, fig.height=6}
reproducible(
  function(point_size = slider(2, min = 0.5, max = 5, step = 0.5),
           data       = static(iris)) {
    p <- ggplot(data, aes(Sepal.Length, Petal.Length, color = Species)) +
      geom_point(size = point_size) +
      theme_minimal()
    publish(p, figure_name = "Iris Scatter")
  },
  packages = c("ggplot2")
)
```
````

The chunk renders the figure inline, captures clean room metadata, and publishes a revision from a single call.
