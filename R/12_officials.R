# Follow-up 8, R twin of python/12_officials.py. Writes to output/r/.
# Reads data/game_officials.csv and data/live_officials.csv, which
# python/12_officials.py flattens from the raw harvest and the cached
# liveData box scores; run that first.
#
#   Rscript R/12_officials.R

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)
source(file.path(here, "functions.R"))

out <- file.path(root, "output", "r")
dir.create(out, showWarnings = FALSE, recursive = TRUE)
# Season (year it ends) of the first officials season; python/10_harvest_officials.py FIRST_SEASON.
FIRST_SEASON <- list(`0` = 2001, `10` = 2003)

tg <- read_csv(file.path(root, "data", "team_games.csv"), guess_max = Inf, show_col_types = FALSE,
               col_types = cols(LEAGUE = col_integer(), GAME_ID = col_character(), SERIES_KEY = col_character(),
                                GAME_DATE = col_character(), HOME = col_logical(), FINALS = col_logical(),
                                .default = col_guess()))
crews <- read_csv(file.path(root, "data", "game_officials.csv"), show_col_types = FALSE,
                  col_types = cols(GAME_ID = col_character(), OFFICIAL_ID = col_integer()))
dev <- read_csv(file.path(out, "profile_games.csv"), show_col_types = FALSE, guess_max = Inf,
                col_types = cols(LEAGUE = col_integer(), SERIES_KEY = col_character(), .default = col_guess()))
live <- read_csv(file.path(root, "data", "live_officials.csv"), show_col_types = FALSE,
                 col_types = cols(GAME_ID = col_character(), OFFICIAL_ID = col_integer(), ASSIGNMENT = col_character()))
if (nrow(crews) == 0) stop("no harvested officials")
if (nrow(live) == 0) stop("no liveData officials")
wc <- working_crews(crews, live)
crews <- wc$crews

ids <- official_game_ids(tg)
s <- official_sample(dev, ids, crews)
if (nrow(s$games) == 0) stop("no question 4 game lists three officials")
cv <- crew_values(s$games, s$link)
wo <- within_official(s$link)
h <- official_halves(s$link)

write_csv(official_coverage(dev, ids, crews, FIRST_SEASON, wc$resolved), file.path(out, "officials_coverage.csv"), na = "")
write_csv(bind_rows(official_game1_profile(s$games), crew_profile(cv, dev)), file.path(out, "officials_profile.csv"), na = "")
write_csv(within_summary(wo), file.path(out, "officials_within.csv"), na = "")
write_csv(official_reliability(h), file.path(out, "officials_reliability.csv"), na = "")
write_csv(cv, file.path(out, "officials_crew_games.csv"), na = "")
write_csv(wo, file.path(out, "officials_people.csv"), na = "")
write_csv(h, file.path(out, "officials_halves.csv"), na = "")
cat(sprintf("officials (R): %d games with a crew of three (%d resolved by liveData), %d officials\n",
            nrow(s$games), nrow(wc$resolved), n_distinct(s$link$OFFICIAL_ID)))
