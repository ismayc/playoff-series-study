# Question 4, R twin of python/06_profiles.py. Writes to output/r/.
#
#   Rscript R/06_profiles.R

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)
source(file.path(here, "functions.R"))

out <- file.path(root, "output", "r")
dir.create(out, showWarnings = FALSE, recursive = TRUE)

tg <- read_csv(file.path(root, "data", "team_games.csv"), guess_max = Inf, show_col_types = FALSE,
               col_types = cols(LEAGUE = col_integer(), GAME_ID = col_character(), SERIES_KEY = col_character(),
                                HOME = col_logical(), .default = col_guess()))
cov <- read_csv(file.path(root, "output", "coverage.csv"), show_col_types = FALSE,
                col_types = cols(LEAGUE = col_integer(), .default = col_guess()))

tm <- team_game_metrics(profile_sample(tg, cov))
if (nrow(tm) == 0) stop("empty sample")
dev <- game_deviations(tm)
state <- series_state(tm)

write_csv(dev, file.path(out, "profile_games.csv"), na = "")
write_csv(profile_summary(dev), file.path(out, "profile_summary.csv"), na = "")
write_csv(state_summary(state), file.path(out, "profile_state.csv"), na = "")
cat(sprintf("profiles (R): %d games, %d games with a series leader\n", nrow(dev), nrow(state$games)))
