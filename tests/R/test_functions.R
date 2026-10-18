# R/functions.R against the hand-worked fixture in tests/fixtures/. The same
# expected numbers are pinned in tests/python/test_game1lib.py, where the
# working is written out.

fix <- file.path(root, "tests", "fixtures")
load_games <- function(ts_filter = NULL) {
  tg <- read_csv(file.path(fix, "game1_games.csv"), show_col_types = FALSE,
                 col_types = cols(SERIES_KEY = col_character(), HOME = col_logical(), .default = col_guess()))
  ts <- read_csv(file.path(fix, "game1_team_seasons.csv"), show_col_types = FALSE)
  if (!is.null(ts_filter)) ts <- ts[ts$TEAM_ID == ts_filter, ]
  add_expected(tg, ts)
}

test_that("expected 3P%", {
  g <- load_games() %>% filter(GAME_NO == 1) %>% arrange(TEAM_ID)
  expect_equal(g$EXP_PCT, c(0.25, 0.40))
})

test_that("series values", {
  s <- series_values(load_games())
  expect_equal(s$G1_PCT, 0.25)
  expect_equal(s$REST_PCT, 14 / 30)
  expect_equal(s$D_PCT, 0.25 - 14 / 30)
  expect_equal(s$D2_PCT, -0.15)
  expect_equal(s$D_RATE, 0.25 - 0.1875)
  expect_equal(s$D2_RATE, 0)
  expect_equal(s$RESID_G1, (5 - 6.5) / 20)
  expect_equal(s$RESID_REST, (14 - 9) / 30)
  expect_equal(s$DECADE, 2010)
})

test_that("team values", {
  t <- team_values(load_games()) %>% arrange(TEAM_ID)
  expect_equal(t$G1_HOME, c(TRUE, FALSE))
  expect_equal(t$TEAM_D_PCT, c(-0.2, -0.2))
  expect_equal(t$TEAM_RESID_G1, c(0.05, -0.20))
  expect_equal(t$TEAM_RESID_REST, c(0.25, 0))
})

test_that("neutral seasons leave the team split only", {
  g <- load_games() %>% mutate(SEASON = 2020)
  expect_equal(nrow(team_values(g)), 0)
  expect_equal(nrow(series_values(g)), 1)
})

test_that("zero attempts give NA, not zero", {
  g <- load_games() %>%
    mutate(FG3A = ifelse(TEAM_ID == 2 & GAME_NO == 1, 0, FG3A),
           FG3M = ifelse(TEAM_ID == 2 & GAME_NO == 1, 0, FG3M))
  t <- team_values(g) %>% arrange(TEAM_ID)
  expect_true(is.na(t$G1_PCT[2]))
  expect_true(is.na(t$TEAM_D_PCT[2]))
  expect_equal(t$TEAM_D_PCT[1], -0.2)
})

test_that("missing baseline nulls the residual, not the percentage", {
  s <- series_values(load_games(ts_filter = 1))
  expect_true(is.na(s$RESID_G1) && is.na(s$RESID_REST))
  expect_equal(s$D_PCT, 0.25 - 14 / 30)
})

test_that("describe", {
  d <- describe_values(c(1, 2, 3, NA, NaN))
  expect_equal(c(d$N, d$N_DROPPED), c(3, 2))
  expect_equal(d$MEAN, 2)
  expect_equal(d$SD, 1)
  expect_equal(d$SE, 1 / sqrt(3))
  expect_equal(d$LO, 2 - 1.96 / sqrt(3))
  expect_equal(d$HI, 2 + 1.96 / sqrt(3))
  expect_true(is.na(describe_values(numeric(0))$MEAN))
  one <- describe_values(5)
  expect_equal(one$MEAN, 5)
  expect_true(is.na(one$SD) && is.na(one$LO))
})

test_that("sample keeps complete multi-game series", {
  tg <- tibble(LEAGUE = c(0, 0, 0), SEASON = c(1984, 1990, 1990), N_GAMES = c(5, 1, 4))
  cov <- tibble(LEAGUE = c(0, 0), SEASON = c(1984, 1990), FG3M = c(1, 1), FG3A = c(0.16, 1), FGA = c(1, 1))
  got <- sample_games(tg, cov)
  expect_equal(nrow(got), 1)
  expect_equal(got$N_GAMES, 4)
})

test_that("summaries and pooled totals", {
  s <- series_values(load_games())
  out <- summarize_values(s, series_panels(s), SERIES_METRICS)
  expect_setequal(unique(out$PANEL), c("all", "2010s"))
  row <- out %>% filter(PANEL == "all", METRIC == "D_PCT")
  expect_equal(row$N, 1)
  expect_equal(row$MEAN, 0.25 - 14 / 30)
  expect_true(is.na(row$SD))
  p <- pooled_values(s)
  expect_equal(c(p$G1_M, p$G1_A, p$REST_M, p$REST_A), c(5, 20, 14, 30))
})

# ---- Question 4 (fixture tests/fixtures/profile_games.csv; working in
# tests/python/test_profilelib.py) ----

load_tm <- function() {
  team_game_metrics(read_csv(file.path(fix, "profile_games.csv"), show_col_types = FALSE,
                             col_types = cols(SERIES_KEY = col_character(), .default = col_guess())))
}

test_that("profile rates", {
  a <- load_tm() %>% filter(TEAM_ID == 1) %>% arrange(GAME_NO)
  expect_equal(a$P, c(90, 100, 110))
  expect_equal(a$PF100, c(20, 20, 20))
  expect_equal(a$PACE, c(90, 100, 110 * 48 / 53))
  expect_equal(a$OREB_PCT, rep(0.25, 3))
  expect_equal(a$FTR, c(25 / 80, 25 / 90, 25 / 100))
  expect_equal(a$ORTG, c(100 * 100 / 90, 100, 100 * 100 / 110))
  expect_equal(a$TOV100, c(10, 9, 900 / 110))
})

test_that("game deviations", {
  d <- game_deviations(load_tm()) %>% arrange(GAME_NO)
  expect_equal(d$PF100, c(10 / 3, -5 / 3, -5 / 3))
  pace <- c(90, 100, 110 * 48 / 53)
  expect_equal(d$PACE, pace - mean(pace))
  a <- c(0.25, 1 / 3, 0.4); b <- c(0.5, 0.3, 0.3)
  expect_equal(d$FG3A_RATE, ((a - mean(a)) + (b - mean(b))) / 2)
})

test_that("a blank team drops from the game mean", {
  tm <- load_tm() %>% mutate(FG3_PCT = ifelse(TEAM_ID == 2 & GAME_NO == 3, NA, FG3_PCT))
  d <- game_deviations(tm) %>% arrange(GAME_NO)
  a <- c(5 / 20, 10 / 30, 20 / 40); b <- c(10 / 40, 9 / 27)
  expect_equal(d$FG3_PCT[3], a[3] - mean(a))
  expect_equal(d$FG3_PCT[1], ((a[1] - mean(a)) + (b[1] - mean(b))) / 2)
})

test_that("profile panels", {
  p <- profile_summary(game_deviations(load_tm()))
  expect_setequal(unique(p$PANEL), c("all", "full_length"))
  row <- p %>% filter(PANEL == "all", GAME_NO == 1, METRIC == "PF100")
  expect_equal(row$N, 1)
  expect_equal(row$MEAN, 10 / 3)
  short <- game_deviations(load_tm()) %>% mutate(WINS_NEEDED = 4)
  expect_equal(unique(profile_summary(short)$PANEL), "all")
})

test_that("series state", {
  s <- series_state(load_tm())
  expect_equal(nrow(s$games), 1)
  expect_equal(s$games$GAME_NO, 2)
  a <- c(0.25, 1 / 3, 0.4); b <- c(0.5, 0.3, 0.3)
  expect_equal(s$games$TRAIL_MINUS_LEAD, (b[2] - mean(b)) - (a[2] - mean(a)))
  ss <- state_summary(s)
  expect_equal(ss$TIED_GAMES, 1)
  expect_equal(ss$N, 1)
})

test_that("profile sample needs every count", {
  tg <- tibble(LEAGUE = c(0, 0), SEASON = c(1984, 1985), N_GAMES = c(4, 4))
  cov <- tibble(LEAGUE = c(0, 0), SEASON = c(1984, 1985))
  for (c in PROFILE_NEEDED) cov[[c]] <- c(1, 1)
  cov$TOV <- c(0.16, 1)
  expect_equal(profile_sample(tg, cov)$SEASON, 1985)
})
