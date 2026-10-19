# Follow-up 9, R twin of python/14_experience.py. Writes to output/r/.
# Reads data/player_games.csv and data/team_playoff_games.csv, which
# python/14_experience.py flattens from the raw logs; run that first.
#
#   Rscript R/14_experience.R

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
cov <- read_csv(file.path(root, "output", "coverage.csv"), show_col_types = FALSE,
                col_types = cols(LEAGUE = col_integer(), .default = col_guess()))
players <- read_csv(file.path(root, "data", "player_games.csv"), show_col_types = FALSE,
                    col_types = cols(GAME_ID = col_character(), TEAM_ID = col_double(), PLAYER_ID = col_double(),
                                     MIN = col_double(), LEAGUE = col_integer(), SEASON = col_integer()))
teams <- read_csv(file.path(root, "data", "team_playoff_games.csv"), show_col_types = FALSE,
                  col_types = cols(GAME_ID = col_character(), TEAM_ID = col_double(),
                                   LEAGUE = col_integer(), SEASON = col_integer()))
if (nrow(players) == 0) stop("no player logs")

games <- sample_games(tg, cov)
seasons <- teams %>% distinct(LEAGUE, SEASON)
exp <- roster_experience(players, games) %>%
  full_join(franchise_experience(teams, games), by = EXP_TEAM_KEYS)
gaps <- team_gaps(games)
team <- gaps %>% left_join(exp, by = EXP_TEAM_KEYS) %>% arrange(LEAGUE, SEASON, SERIES_KEY, TEAM_ID)
series <- list(); summaries <- list()
for (m in c("roster", "franchise")) {
  col <- if (m == "roster") "ROSTER_EXP" else "FRAN_EXP"
  e <- exp %>% select(all_of(EXP_TEAM_KEYS), all_of(col)) %>% filter(!is.na(.data[[col]]))
  cv <- exp_contrasts(gaps, e, col)
  series[[m]] <- cv %>% mutate(MEASURE = m)
  summaries[[m]] <- exp_summary(cv, m)
}

write_csv(exp_coverage(players, seasons), file.path(out, "experience_coverage.csv"), na = "")
write_csv(team, file.path(out, "experience_team.csv"), na = "")
write_csv(bind_rows(series) %>% select(MEASURE, LEAGUE, SEASON, SERIES_KEY, GAP, all_of(EXP_CONTRASTS)),
          file.path(out, "experience_series.csv"), na = "")
write_csv(bind_rows(summaries), file.path(out, "experience_summary.csv"), na = "")
cat(sprintf("experience (R): %d team-series\n", nrow(team)))
