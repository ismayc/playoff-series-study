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

test_that("season totals pool attempts", {
  s <- series_values(load_games())
  s16 <- s %>% mutate(SEASON = 2016, G1_M = 0, G1_A = 0)
  out <- season_values(bind_rows(s, s, s16))
  a <- out %>% filter(SEASON == 2010)
  expect_equal(c(a$SERIES, a$G1_M, a$G1_A, a$G1_FGA), c(2, 10, 40, 160))
  expect_equal(a$G1_PCT, 0.25)
  expect_equal(a$REST_PCT, 14 / 30)
  expect_equal(a$D_RATE, 0.25 - 0.1875)
  b <- out %>% filter(SEASON == 2016)
  expect_true(is.na(b$G1_PCT) && is.na(b$D_PCT))
  expect_equal(b$G1_RATE, 0)
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

# ---- Question 3 (fixture tests/fixtures/stage_games.csv; working in
# tests/python/test_stagelib.py) ----

load_stage <- function() {
  read_csv(file.path(fix, "stage_games.csv"), show_col_types = FALSE,
           col_types = cols(SERIES_KEY = col_character(), GAME_DATE = col_character(),
                            FINALS = col_logical(), .default = col_guess()))
}

test_that("stages", {
  st <- stages(load_stage())
  got <- setNames(st$STAGE, paste(st$SEASON, st$SERIES_KEY))
  expect_equal(unname(got[c("2010 1-3", "2010 1-2", "2010 3-4")]), c(0, 1, 1))
  expect_true(is.na(got[["2011 5-6"]]))
})

test_that("stage checks", {
  tg <- load_stage(); st <- stages(tg)
  expect_equal(nrow(stage_mismatches(tg, st)), 0)
  bad <- tg %>% mutate(ROUND = ifelse(SERIES_KEY == "3-4", 2, ROUND))
  expect_equal(stage_mismatches(bad, st)$SERIES_KEY, "3-4")
  expect_equal(nrow(unexplained_missing_stages(tg, st)), 0)
  broken <- st %>% mutate(STAGE = ifelse(SERIES_KEY == "1-2", NA, STAGE))
  expect_equal(unexplained_missing_stages(tg, broken)$SERIES_KEY, "1-2")
})

test_that("stage follows byes", {
  rows <- list()
  add <- function(key, n, t1, t2, w, fin, day) {
    for (i in seq_len(n)) for (p in list(c(t1, t2), c(t2, t1))) {
      rows[[length(rows) + 1]] <<- tibble(LEAGUE = 10, SEASON = 1999, SERIES_KEY = key, TEAM_ID = p[1], OPP_ID = p[2],
                                          GAME_DATE = sprintf("1999-08-%02d", day + i - 1), WINNER_ID = w, FINALS = fin)
    }
  }
  add("2-3", 1, 2, 3, 2, FALSE, 1); add("1-2", 2, 1, 2, 1, FALSE, 5); add("1-4", 2, 1, 4, 1, TRUE, 20)
  st <- stages(bind_rows(rows))
  expect_equal(setNames(st$STAGE, st$SERIES_KEY)[c("1-4", "1-2", "2-3")], c(`1-4` = 0, `1-2` = 1, `2-3` = 2))
})

test_that("rest values and summary", {
  rv <- rest_values(load_stage())
  r <- function(k) rv[rv$SERIES_KEY == k, ]
  expect_equal(c(r("1-2")$GAP, r("1-3")$GAP, r("3-4")$GAP), c(3, 3, 0))
  a <- (10 / 30 - 12 / 30) - (6 / 20 - 9 / 20)
  expect_equal(r("1-2")$CONTRAST_PCT, a)
  expect_equal(r("1-2")$CONTRAST_RATE, 0 - (20 / 80 - 20 / 90))
  expect_equal(r("1-3")$CONTRAST_PCT, -0.3)
  expect_true(is.na(r("3-4")$CONTRAST_PCT))
  s <- rest_summary(rv)
  row <- s %>% filter(BIN == "3-5", METRIC == "CONTRAST_PCT")
  expect_equal(row$N, 2)
  expect_equal(row$MEAN, (a - 0.3) / 2)
  expect_equal(row$ZERO_GAP_SERIES, 2)
})

test_that("stake summary", {
  sv <- tibble(LEAGUE = 0, STAGE = c(0, 1, 1, NA), D_PCT = c(0.1, 0.2, 0.4, 9), D2_PCT = 0, D_RATE = 0)
  s <- stake_summary(sv)
  expect_equal(sort(unique(s$STAGE)), c(0, 1))
  expect_equal((s %>% filter(STAGE == 1, METRIC == "D_PCT"))$MEAN, 0.3)
})

# ---- Follow-ups 5 to 7; working in tests/python/test_followlib.py ----

follow <- read_csv(file.path(fix, "follow_games.csv"), show_col_types = FALSE,
                   col_types = cols(SERIES_KEY = col_character(), .default = col_guess()))

test_that("outshoot values", {
  ov <- outshoot_values(follow)
  expect_equal(ov$SERIES_KEY, c("1-2", "3-4", "5-6"))
  expect_equal(ov$OUTSHOT, c(TRUE, FALSE, NA))
  expect_equal(ov$SERIES_WIN, c(TRUE, FALSE, TRUE))
  expect_equal(ov$SHOOTER_WON, c(TRUE, TRUE, NA))
  expect_equal(ov$W_PCT, c(0.4, 0.2, 0.3))
})

test_that("outshoot summary", {
  s <- outshoot_summary(outshoot_values(follow))
  get <- function(e) s[s$ESTIMATE == e, ]
  expect_equal(c(get("shooter_wins_series")$N, get("shooter_wins_series")$P), c(2, 1))
  expect_equal(get("shooter_wins_series")$N_DROPPED, 1)
  expect_equal(c(get("g1_winner_outshot")$N, get("g1_winner_outshot")$P), c(1, 1))
  expect_equal(c(get("g1_winner_not_outshot")$N, get("g1_winner_not_outshot")$P), c(1, 0))
  expect_equal(c(get("difference")$P, get("difference")$SE, get("difference")$N_DROPPED), c(1, 0, 1))
})

test_that("proportion interval", {
  p <- proportion_values(c(TRUE, FALSE, TRUE, TRUE, NA))
  expect_equal(c(p$N, p$N_DROPPED, p$P), c(4, 1, 0.75))
  se <- sqrt(0.75 * 0.25 / 4)
  expect_equal(c(p$LO, p$HI), c(0.75 - 1.96 * se, 0.75 + 1.96 * se))
})

test_that("break values and panels", {
  series <- tibble(LEAGUE = c(0, 0), SEASON = c(2010, 2020), SERIES_KEY = c("1-2", "3-4"),
                   D_PCT = c(0.1, 0.3), D2_PCT = 0, D_RATE = 0, D2_RATE = 0)
  dev <- tibble(LEAGUE = c(0, 0, 0), SEASON = c(2010, 2010, 2020), SERIES_KEY = c("1-2", "1-2", "3-4"),
                GAME_NO = c(1, 2, 2), PF100 = c(-2, 2, 5), FTR = c(-0.1, 0.1, 0.2))
  bv <- break_values(series, follow, dev)
  expect_equal(bv$WINS_NEEDED, c(2, 2))
  expect_equal(bv$G1_PF100, c(-2, NA))
  s <- break_summary(bv)
  r20 <- s[s$PANEL == "season_2020" & s$METRIC == "D_PCT", ]
  expect_equal(c(r20$N, r20$MEAN), c(1, 0.3))
  b3 <- s[s$PANEL == "best_of_3" & s$METRIC == "D_PCT", ]
  expect_equal(c(b3$N, b3$MEAN), c(2, 0.2))
  expect_equal(sum(s$PANEL == "best_of_7"), 0)
})

test_that("profile by decade", {
  dev <- tibble(LEAGUE = 0, SEASON = c(1999, 1990, 2001), GAME_NO = 1)
  for (m in PROFILE_METRICS) dev[[m]] <- c(1, 3, 5)
  pd <- profile_decade(dev)
  pd <- pd[pd$METRIC == "PF100", ]
  expect_equal(pd$DECADE, c(1990, 2000))
  expect_equal(pd$N, c(2, 1))
  expect_equal(pd$MEAN, c(2, 5))
})

# ---- Follow-up 8; working in tests/python/test_officiallib.py ----

off_parts <- function() {
  g <- read_csv(file.path(fix, "official_games.csv"), show_col_types = FALSE,
                col_types = cols(SERIES_KEY = col_character(), GAME_ID = col_character(), .default = col_guess()))
  crews <- read_csv(file.path(fix, "official_crews.csv"), show_col_types = FALSE,
                    col_types = cols(GAME_ID = col_character(), OFFICIAL_ID = col_integer()))
  list(dev = g %>% select(-GAME_ID), ids = g %>% select(LEAGUE, SEASON, SERIES_KEY, GAME_NO, GAME_ID), crews = crews)
}
with_low_thresholds <- function(code, other = 1) {
  old <- c(MIN_OTHER_GAMES, MIN_SPLIT_GAMES, MIN_HALF_GAMES)
  MIN_OTHER_GAMES <<- other; MIN_SPLIT_GAMES <<- 1; MIN_HALF_GAMES <<- 1
  on.exit({ MIN_OTHER_GAMES <<- old[1]; MIN_SPLIT_GAMES <<- old[2]; MIN_HALF_GAMES <<- old[3] })
  code
}

test_that("working crews", {
  crews <- tibble(GAME_ID = c(rep("a", 4), rep("b", 4), rep("c", 4), rep("d", 3), rep("e", 4), "f", rep("g", 4)),
                  OFFICIAL_ID = c(1:4, 1:4, 1:4, 1:3, 1:4, NA, 1:4))
  live <- tibble(GAME_ID = c(rep("a", 4), rep("b", 3), rep("d", 3), rep("e", 3), rep("g", 3)),
                 OFFICIAL_ID = c(1L, 2L, 3L, 4L, 1L, 2L, 5L, 1L, 2L, 3L, 1L, 2L, 4L, 1L, 2L, 3L),
                 ASSIGNMENT = c("OFFICIAL1", "OFFICIAL2", "OFFICIAL3", "ALTERNATE", "OFFICIAL1", "OFFICIAL2", "OFFICIAL3",
                                "OFFICIAL1", "OFFICIAL2", "ALTERNATE", "OFFICIAL1", "OFFICIAL2", "ALTERNATE",
                                "OFFICIAL1", "OFFICIAL3", "OFFICIAL2"))
  w <- working_crews(crews, live)
  expect_equal(w$resolved$GAME_ID, c("a", "g"))
  got <- split(w$crews$OFFICIAL_ID, w$crews$GAME_ID)
  expect_equal(got$a, 1:3); expect_equal(got$b, 1:4); expect_equal(got$c, 1:4); expect_equal(got$d, 1:3)
  expect_equal(got$e, 1:4); expect_equal(got$f, NA_integer_); expect_equal(got$g, 1:3)
  expect_equal(names(w$crews), names(crews))
})

test_that("officials coverage and sample", with_low_thresholds({
  p <- off_parts()
  none <- tibble(GAME_ID = character())
  cov <- official_coverage(p$dev, p$ids, p$crews, list(`0` = 2010), none)
  expect_equal(cov$GAMES, c(3, 4)); expect_equal(cov$HARVESTED, c(3, 3)); expect_equal(cov$WITH_CREW, c(3, 2))
  expect_equal(cov$RESOLVED, c(0, 0))
  expect_equal(official_coverage(p$dev, p$ids, p$crews, list(`0` = 2010), tibble(GAME_ID = c("g11", "g31")))$RESOLVED, c(1, 0))
  s <- official_sample(p$dev, p$ids, p$crews)
  expect_equal(s$games$GAME_ID, c("g11", "g12", "g13", "g21", "g22"))
  expect_equal(s$games$RESID, c(-1, -0.5, 0, 1, 0.5))
  expect_equal(nrow(s$link), 15)
  expect_equal(official_game1_profile(s$games)$MEAN, c(-2, 0.5, 3))
}))

test_that("crew tendencies and profile", with_low_thresholds({
  p <- off_parts()
  s <- official_sample(p$dev, p$ids, p$crews)
  cv <- crew_values(s$games, s$link)
  expect_equal(cv$CREW, c(2.5 / 3, 0.75, 0.75, -1.75 / 3, -0.5))
  cp <- crew_profile(cv, p$dev)
  expect_equal(cp$N, c(2, 2, 1))
  expect_equal(cp$MEAN, c(1 / 144, 1 / 144, -1 / 36))
}))

test_that("crew tendency needs other games", with_low_thresholds({
  p <- off_parts()
  s <- official_sample(p$dev, p$ids, p$crews)
  cv <- crew_values(s$games, s$link)
  expect_equal(cv$CREW, c(NA, NA, NA, -0.5, NA))
}, other = 3))

test_that("within official and reliability", with_low_thresholds({
  p <- off_parts()
  s <- official_sample(p$dev, p$ids, p$crews)
  wo <- within_official(s$link)
  expect_equal(wo$OFFICIAL_ID, 1:3)
  expect_equal(wo$D, c(-2.5, -3.5, -4))
  expect_equal(within_summary(wo)$MEAN, -10 / 3)
  h <- official_halves(s$link)
  expect_equal(h$EVEN, c(-0.75, -0.5, -0.5, -0.25))
  r <- official_reliability(h)
  expect_equal(c(r$N, r$R), c(4, -0.5))
  expect_equal(c(r$LO, r$HI), c(tanh(atanh(-0.5) - 1.96), tanh(atanh(-0.5) + 1.96)))
}))

# ---- Follow-up 9; working in tests/python/test_experiencelib.py ----

exp_parts <- function() {
  games <- read_csv(file.path(fix, "profile_games.csv"), show_col_types = FALSE,
                    col_types = cols(SERIES_KEY = col_character(), .default = col_guess())) %>%
    mutate(GAME_ID = paste0("g", GAME_NO))
  players <- read_csv(file.path(fix, "exp_players.csv"), show_col_types = FALSE,
                      col_types = cols(GAME_ID = col_character(), MIN = col_double(), .default = col_guess()))
  logs <- read_csv(file.path(fix, "exp_team_logs.csv"), show_col_types = FALSE,
                   col_types = cols(GAME_ID = col_character(), .default = col_guess()))
  list(games = games, players = players, logs = logs)
}
exp_expected <- c(CONTRAST_PCT = (1 / 4 - 3 / 7) - (1 / 4 - 9 / 57),
                  CONTRAST_RATE = (1 / 4 - 7 / 19) - (1 / 2 - 3 / 10), CONTRAST_PF = -10)

test_that("roster and franchise experience", {
  p <- exp_parts()
  r <- roster_experience(p$players, p$games)
  expect_equal(r$ROSTER_EXP, c(10 / 3, 1.6))
  f <- franchise_experience(p$logs, p$games)
  expect_equal(f$FRAN_EXP, c(6, 3))
})

test_that("team gaps and contrasts", {
  p <- exp_parts()
  g <- team_gaps(p$games)
  expect_equal(g$DPF, c(0, 10))
  for (m in list(list(roster_experience(p$players, p$games), "ROSTER_EXP", 10 / 3 - 1.6),
                 list(franchise_experience(p$logs, p$games), "FRAN_EXP", 3))) {
    cv <- exp_contrasts(g, m[[1]], m[[2]])
    expect_equal(cv$GAP, m[[3]])
    for (k in names(exp_expected)) expect_equal(cv[[k]], unname(exp_expected[k]))
  }
  eq <- tibble(LEAGUE = 0, SEASON = 2010, SERIES_KEY = "1-2", TEAM_ID = c(1, 2), X = 2)
  cv <- exp_contrasts(g, eq, "X")
  expect_equal(cv$GAP, 0)
  expect_true(is.na(cv$CONTRAST_PCT))
})

test_that("experience summary bins", {
  cv <- tibble(LEAGUE = 0, SEASON = 2010, SERIES_KEY = letters[1:5], GAP = c(0, 1, 2, 3, 4),
               CONTRAST_PCT = c(NA, 0.1, 0.2, 0.3, 0.4), CONTRAST_RATE = c(NA, 0, 0, 0, 0),
               CONTRAST_PF = c(NA, 1, 1, 1, 1))
  s <- exp_summary(cv, "roster")
  s <- s[s$METRIC == "CONTRAST_PCT", ]
  expect_equal(s$BIN, c("low", "middle", "high", "any"))
  expect_equal(s$N, c(2, 1, 1, 4))
  expect_equal(c(s$Q1[1], s$Q2[1]), c(2, 3))
  expect_equal(s$EQUAL_SERIES[4], 1)
  expect_equal(s$MEAN[4], 0.25)
})
