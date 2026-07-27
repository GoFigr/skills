# GoFigr — R

Package: `gofigR`. Verified against 2.0.2.

```r
install.packages("gofigR")            # or:
devtools::install_github("gofigr/gofigR")
```

## Configuration

One-time, interactive. Writes `~/.gofigr`:

```r
library(gofigR)
gfconfig()
```

Or environment variables: `GF_API_KEY`, or `GF_USERNAME` + `GF_PASSWORD`; plus optional `GF_WORKSPACE`, `GF_URL`.

Never write an API key into a source file.

## Setup

In a knitr setup chunk, a script, or at the RStudio prompt:

```r
library(gofigR)
gofigR::enable(workspace_name = "Analytics",
               analysis_name  = "Penguins")
```

`analysis_name` defaults to the basename of the source file when it can be detected. The analysis and workspace are created if missing (`create_analysis` / `create_workspace`, both `TRUE` by default).

Selected `enable()` parameters:

| Parameter | Default | Notes |
|---|---|---|
| `auto_publish` | `FALSE` | **leave it at `FALSE`** — see below |
| `workspace_name` / `workspace` | from `~/.gofigr` | name, or API ID |
| `analysis_name` / `analysis_api_id` | source file name | |
| `watermark` | `QR_WATERMARK` | or `LINK_WATERMARK`, `NO_WATERMARK` |
| `show` | `"watermark"` | `"original"` or `"hide"`; affects display only, not what is published |
| `auto_assign` | from config | AI assigns revisions to figures by image content; requires AI enabled server-side |
| `verbose`, `debug` | `FALSE` | |

## Publishing — always explicit

**Automatic capture in R is being sunset.** It works by reassigning `plot()` and `print()` in the global environment, and it is not reliable. Do not use `enable(auto_publish = TRUE)`, `gf_plot()`, `gf_print()`, or the deprecated `publish_base()`.

Every figure gets its own `publish()` call.

### Grid graphics (ggplot2, lattice, ComplexHeatmap)

```r
p <- ggplot(mtcars, aes(mpg, hp)) + geom_point()
publish(p, figure_name = "MPG vs horsepower")
```

The pipe works too:

```r
hm <- Heatmap(matrix(rnorm(100), nrow = 10))
hm %>% publish("Correlation heatmap")
```

### Base graphics

Pass the plotting expression as a block. GoFigr converts base output to grid graphics behind the scenes.

```r
publish({
  plot(pressure, main = "Pressure vs temperature")
  text(200, 50, "Note the non-linear relationship")
}, data = pressure, figure_name = "Pressure vs temperature")
```

The optional `data` argument attaches a dataset to the figure; it is stored as `.RDS` under the revision's files.

### publish() parameters

| Parameter | Default | Notes |
|---|---|---|
| `plot_obj` | — | plot object or a `{ ... }` expression |
| `figure_name` | inferred from the plot title | see the naming warning below |
| `data` | `NULL` | saved with the revision as `.RDS` |
| `metadata` | execution context | named list |
| `image_formats` | `c("eps")` | PNG is always produced |
| `show` | `TRUE` | display the figure after publishing |
| `width`, `height`, `units`, `dpi` | current device / `"in"` / ggsave default | |
| `auto_assign` | session default from `enable()` | per-call override |

Returns the revision object.

**Naming.** With `auto_assign = FALSE` (the default), a figure with no `figure_name` and no inferable title is published as `"Anonymous Figure"` with a warning. Always pass `figure_name`, unless the session uses `auto_assign = TRUE`.

## Asset tracking

`gofigR` exports reader wrappers that checksum and upload the file, then link it to every figure published afterwards. They mask the base/readr functions of the same name when the package is attached, and pass `...` straight through:

`read.csv`, `read.csv2`, `read_csv`, `read_csv2`, `read_tsv`, `read_delim`, `read.xlsx`

```r
df <- gofigR::read.csv("data/penguins.csv")
```

To sync without reading, use `sync_file()`, which returns the path so it composes with any reader:

```r
sync_file("data/reference.fasta")
dat <- readRDS(sync_file("data/model.rds"))
```

Because these wrappers shadow common base functions, prefer the namespaced form `gofigR::read.csv(...)` in code you are writing for someone else.

## RMarkdown / knitr

````markdown
```{r setup, include=FALSE}
library(gofigR)
library(ggplot2)
gofigR::enable(workspace_name = "Scratchpad",
               analysis_name  = "Penguin report")
```

```{r flipper_hist, fig.width=8, fig.height=6}
p <- ggplot(penguins, aes(flipper_length_mm)) + geom_histogram(bins = 20)
publish(p, figure_name = "Flipper length distribution")
```
````

The chunk's code is captured with the revision automatically.

## Shiny

Replace `plotOutput` + `renderPlot` with `gfPlot` + `gfPlotServer` to give users a publish button:

```r
ui <- fluidPage(
  sliderInput("bins", "Number of bins:", min = 1, max = 50, value = 30),
  gfPlot("distPlot")
)

server <- function(input, output) {
  gfPlotServer("distPlot", {
    hist(faithful$eruptions, breaks = input$bins)
  })
}
```

## Gotchas

**Never call `publish()` from a forked child process** — inside `parallel::mclapply`, `future::plan(multicore)`, and similar. Forks inherit the short ID counter, producing duplicate IDs and server-side conflicts, and graphics devices do not survive forks. Use a socket cluster (`future::plan(multisession)`) or publish from the parent.

**`enable()` must run before any `publish()` call.** Without it, `publish()` warns and returns `NULL` rather than erroring.

**Converting existing auto-capture code.** Drop `auto_publish = TRUE`, then add one `publish()` per figure the script produces. Base-graphics figures need their plotting calls wrapped in `publish({ ... })`, which usually means moving code, not just adding a line.
