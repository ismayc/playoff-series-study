# Question 3, R twin of python/08_stakes_rest.py. Writes to output/r/.
#
#   Rscript R/08_stakes_rest.R

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)
source(file.path(here, "functions.R"))

out <- file.path(root, "output", "r")
dir.create(out, showWarnings = FALSE, recursive = TRUE)

tg <- read_csv(file.path(root, "data", "team_games.csv"), guess_max = Inf, show_col_types = FALSE,
               col_types = cols(LEAGUE = col_integer(), GAME_ID = col_character(), SERIES_KEY = col_character(),
                                GAME_DATE = col_character(), HOME = col_logical(), FINALS = col_logical(),
                                .default = col_guess()))
ts <- read_csv(file.path(root, "data", "team_seasons.csv"), show_col_types = FALSE, guess_max = Inf,
               col_types = cols(LEAGUE = col_integer(), .default = col_guess()))
cov <- read_csv(file.path(root, "output", "coverage.csv"), show_col_types = FALSE,
                col_types = cols(LEAGUE = col_integer(), .default = col_guess()))

st <- stages(tg)
if (nrow(stage_mismatches(tg, st)) > 0) stop("stage disagrees with the encoded round")
if (nrow(unexplained_missing_stages(tg, st)) > 0) stop("series without a stage in a season with a Finals")

games <- add_expected(sample_games(tg, cov), ts)
sv <- series_values(games) %>% left_join(st, by = c("LEAGUE", "SEASON", "SERIES_KEY"))
rv <- rest_values(games)

write_csv(st, file.path(out, "series_stage.csv"), na = "")
write_csv(stake_summary(sv), file.path(out, "stakes_summary.csv"), na = "")
write_csv(rv, file.path(out, "rest_series.csv"), na = "")
write_csv(rest_summary(rv), file.path(out, "rest_summary.csv"), na = "")
cat(sprintf("stakes and rest (R): %d series staged, %d zero-gap series\n", sum(!is.na(st$STAGE)), sum(rv$GAP == 0)))
