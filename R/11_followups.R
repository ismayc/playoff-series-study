# Follow-ups 5 to 7, R twin of python/11_followups.py. Writes to output/r/.
#
#   Rscript R/11_followups.R

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
# The R twin's own question 4 game table, so the two pipelines stay separate.
dev <- read_csv(file.path(out, "profile_games.csv"), show_col_types = FALSE, guess_max = Inf,
                col_types = cols(LEAGUE = col_integer(), SERIES_KEY = col_character(), .default = col_guess()))

games <- add_expected(sample_games(tg, cov), ts)
ov <- outshoot_values(games)
bv <- break_values(series_values(games), games, dev)
pd <- profile_decade(dev)
if (nrow(ov) == 0 || nrow(bv) == 0 || nrow(pd) == 0) stop("empty follow-up table")

write_csv(ov, file.path(out, "outshoot_series.csv"), na = "")
write_csv(outshoot_summary(ov), file.path(out, "outshoot_summary.csv"), na = "")
write_csv(bv, file.path(out, "break_series.csv"), na = "")
write_csv(break_summary(bv), file.path(out, "break_summary.csv"), na = "")
write_csv(pd, file.path(out, "profile_decade.csv"), na = "")
cat(sprintf("follow-ups (R): %d series, %d without a Game 1 three-point winner\n", nrow(ov), sum(is.na(ov$OUTSHOT))))
