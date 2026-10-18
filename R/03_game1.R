# Question 1, R twin of python/03_game1.py. Writes the same five tables to
# output/r/ for python/04_reconcile.py to compare.
#
#   Rscript R/03_game1.R

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)
source(file.path(here, "functions.R"))

out <- file.path(root, "output", "r")
dir.create(out, showWarnings = FALSE, recursive = TRUE)

tg <- read_csv(file.path(root, "data", "team_games.csv"), guess_max = Inf,
               col_types = cols(LEAGUE = col_integer(), GAME_ID = col_character(), SERIES_KEY = col_character(),
                                HOME = col_logical(), .default = col_guess()))
ts <- read_csv(file.path(root, "data", "team_seasons.csv"), show_col_types = FALSE, guess_max = Inf,
               col_types = cols(LEAGUE = col_integer(), .default = col_guess()))
cov <- read_csv(file.path(root, "output", "coverage.csv"), show_col_types = FALSE,
                col_types = cols(LEAGUE = col_integer(), .default = col_guess()))

games <- add_expected(sample_games(tg, cov), ts)
series <- series_values(games)
team <- team_values(games)
if (nrow(series) == 0 || nrow(team) == 0) stop("empty sample; check data/ and output/coverage.csv")

summary <- bind_rows(summarize_values(series, series_panels(series), SERIES_METRICS),
                     summarize_values(team, TEAM_PANELS, TEAM_METRICS))

write_full <- function(df, name) write_csv(df, file.path(out, name), na = "")
# readr writes doubles with up to 15 significant digits, enough for the
# 1e-9 tolerance in the reconcile.
write_full(series, "game1_series.csv")
write_full(team, "game1_team.csv")
write_full(summary, "game1_summary.csv")
write_full(pooled_values(series), "game1_pooled.csv")
write_full(season_values(series), "game1_season.csv")
cat(sprintf("game1 (R): %d series, %d team-series\n", nrow(series), nrow(team)))
