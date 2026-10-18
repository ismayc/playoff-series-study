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
