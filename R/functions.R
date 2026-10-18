# Question 1 definitions from docs/design.md, the R twin of
# python/game1lib.py. Written from the design doc, so a definition both
# readings agree on is one the doc states clearly. tests/R/test_functions.R
# pins these to the same hand-worked fixture as the Python tests.

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
  library(tidyr)
})

Z <- 1.96
NEUTRAL_SEASONS <- c(2020)
SERIES_METRICS <- c("D_PCT", "D2_PCT", "D_RATE", "D2_RATE", "RESID_G1", "RESID_REST")
TEAM_METRICS <- c("TEAM_D_PCT", "TEAM_RESID_G1", "TEAM_RESID_REST")

# num / den, NA unless den > 0.
safe_ratio <- function(num, den) ifelse(!is.na(den) & den > 0, num / den, NA_real_)

sample_games <- function(team_games, coverage) {
  complete <- coverage %>%
    filter(FG3M == 1, FG3A == 1, FGA == 1) %>%
    select(LEAGUE, SEASON)
  team_games %>% inner_join(complete, by = c("LEAGUE", "SEASON")) %>% filter(N_GAMES >= 2)
}

add_expected <- function(games, team_seasons) {
  league <- team_seasons %>% group_by(LEAGUE, SEASON) %>%
    summarise(LG_PCT = safe_ratio(sum(RS_FG3M), sum(RS_FG3A)), .groups = "drop")
  own <- team_seasons %>% transmute(LEAGUE, SEASON, TEAM_ID, OWN_PCT = safe_ratio(RS_FG3M, RS_FG3A))
  allowed <- team_seasons %>%
    transmute(LEAGUE, SEASON, OPP_ID = TEAM_ID, ALLOWED_PCT = safe_ratio(RS_OPP_FG3M, RS_OPP_FG3A))
  games %>%
    left_join(own, by = c("LEAGUE", "SEASON", "TEAM_ID")) %>%
    left_join(allowed, by = c("LEAGUE", "SEASON", "OPP_ID")) %>%
    left_join(league, by = c("LEAGUE", "SEASON")) %>%
    mutate(EXP_PCT = OWN_PCT + ALLOWED_PCT - LG_PCT) %>%
    select(-OWN_PCT, -ALLOWED_PCT, -LG_PCT)
}

# Sums per key group for one segment. EA is NA when any row lacks EXP_PCT.
# Each sum gets its own name in summarise() so no later argument can see a
# column already overwritten (family note: dplyr summarise sequential masking).
segment <- function(games, keys, keep, name) {
  games %>% filter(keep) %>% group_by(across(all_of(keys))) %>%
    summarise(m_ = sum(FG3M), a_ = sum(FG3A), fga_ = sum(FGA),
              ea_ = if (any(is.na(EXP_PCT))) NA_real_ else sum(EXP_PCT * FG3A),
              .groups = "drop") %>%
    rename(!!paste0(name, "_M") := m_, !!paste0(name, "_A") := a_,
           !!paste0(name, "_FGA") := fga_, !!paste0(name, "_EA") := ea_)
}

segment_sums <- function(games, keys) {
  g1 <- segment(games, keys, games$GAME_NO == 1, "G1")
  rest <- segment(games, keys, games$GAME_NO >= 2, "REST")
  g2 <- segment(games, keys, games$GAME_NO == 2, "G2")
  g1 %>% left_join(rest, by = keys) %>% left_join(g2, by = keys)
}

base_metrics <- function(s) {
  s %>% mutate(
    G1_PCT = safe_ratio(G1_M, G1_A), REST_PCT = safe_ratio(REST_M, REST_A), G2_PCT = safe_ratio(G2_M, G2_A),
    G1_RATE = safe_ratio(G1_A, G1_FGA), REST_RATE = safe_ratio(REST_A, REST_FGA),
    G2_RATE = safe_ratio(G2_A, G2_FGA),
    R_G1 = safe_ratio(G1_M - G1_EA, G1_A), R_REST = safe_ratio(REST_M - REST_EA, REST_A))
}

series_values <- function(games) {
  keys <- c("LEAGUE", "SEASON", "SERIES_KEY")
  segment_sums(games, keys) %>% base_metrics() %>%
    mutate(D_PCT = G1_PCT - REST_PCT, D2_PCT = G1_PCT - G2_PCT,
           D_RATE = G1_RATE - REST_RATE, D2_RATE = G1_RATE - G2_RATE,
           RESID_G1 = R_G1, RESID_REST = R_REST, DECADE = (SEASON %/% 10) * 10) %>%
    select(-R_G1, -R_REST) %>% arrange(LEAGUE, SEASON, SERIES_KEY)
}

team_values <- function(games) {
  keys <- c("LEAGUE", "SEASON", "SERIES_KEY", "TEAM_ID")
  g <- games %>% filter(!(SEASON %in% NEUTRAL_SEASONS))
  home <- g %>% filter(GAME_NO == 1) %>% transmute(LEAGUE, SEASON, SERIES_KEY, TEAM_ID, G1_HOME = HOME)
  segment_sums(g, keys) %>% base_metrics() %>%
    mutate(TEAM_D_PCT = G1_PCT - REST_PCT, TEAM_RESID_G1 = R_G1, TEAM_RESID_REST = R_REST) %>%
    select(-R_G1, -R_REST) %>% inner_join(home, by = keys) %>% arrange(across(all_of(keys)))
}

describe_values <- function(x) {
  kept <- x[!is.na(x)]
  n <- length(kept)
  out <- list(N = n, N_DROPPED = length(x) - n, MEAN = NA_real_, SD = NA_real_,
              SE = NA_real_, LO = NA_real_, HI = NA_real_)
  if (n == 0) return(out)
  out$MEAN <- mean(kept)
  if (n < 2) return(out)
  out$SD <- sd(kept)
  out$SE <- out$SD / sqrt(n)
  out$LO <- out$MEAN - Z * out$SE
  out$HI <- out$MEAN + Z * out$SE
  out
}

# panels: named list of functions from a data frame to a logical vector.
summarize_values <- function(values, panels, metrics) {
  rows <- list()
  for (league in sort(unique(values$LEAGUE))) {
    lv <- values[values$LEAGUE == league, ]
    for (panel in names(panels)) {
      pv <- lv[panels[[panel]](lv), ]
      if (nrow(pv) == 0) next
      for (m in metrics) {
        rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, PANEL = panel, METRIC = m),
                                                describe_values(pv[[m]])))
      }
    }
  }
  bind_rows(rows)
}

series_panels <- function(values) {
  panels <- list(all = function(d) rep(TRUE, nrow(d)))
  for (dec in sort(unique(values$DECADE))) {
    local({
      d0 <- dec
      panels[[paste0(d0, "s")]] <<- function(d) d$DECADE == d0
    })
  }
  panels
}

TEAM_PANELS <- list(home = function(d) d$G1_HOME, road = function(d) !d$G1_HOME)

pooled_values <- function(values) {
  values %>% group_by(LEAGUE) %>%
    summarise(SERIES = n(), G1_M = sum(G1_M), G1_A = sum(G1_A),
              REST_M = sum(REST_M), REST_A = sum(REST_A), .groups = "drop") %>%
    mutate(G1_PCT = G1_M / G1_A, REST_PCT = REST_M / REST_A, D_PCT = G1_PCT - REST_PCT) %>%
    arrange(LEAGUE)
}

# ---- Question 4: per-game profiles (twin of python/profilelib.py) ----

PROFILE_NEEDED <- c("FGA", "FTA", "OREB", "DREB", "TOV", "PF", "AST", "FGM", "FG3A", "MIN")
PROFILE_METRICS <- c("PF100", "TOV100", "ORTG", "FTR", "AST_RATE", "OREB_PCT", "PACE", "FG3A_RATE", "FG3_PCT")

profile_sample <- function(team_games, coverage) {
  ok <- Reduce(`&`, lapply(PROFILE_NEEDED, function(c) coverage[[c]] == 1))
  complete <- coverage[ok, c("LEAGUE", "SEASON")]
  team_games %>% inner_join(complete, by = c("LEAGUE", "SEASON")) %>% filter(N_GAMES >= 2)
}

team_game_metrics <- function(games) {
  games %>% mutate(
    P = ((FGA + 0.44 * FTA - OREB + TOV) + (OPP_FGA + 0.44 * OPP_FTA - OPP_OREB + OPP_TOV)) / 2,
    REG = ifelse(LEAGUE == 0, 48, 40),
    PF100 = safe_ratio(100 * PF, P), TOV100 = safe_ratio(100 * TOV, P), ORTG = safe_ratio(100 * PTS, P),
    FTR = safe_ratio(FTA, FGA), AST_RATE = safe_ratio(AST, FGM),
    OREB_PCT = safe_ratio(OREB, OREB + OPP_DREB),
    PACE = safe_ratio(P * REG, MIN / 5),
    FG3A_RATE = safe_ratio(FG3A, FGA), FG3_PCT = safe_ratio(FG3M, FG3A)) %>%
    select(-REG)
}

# mean() of an all-NA vector with na.rm is NaN; the design wants blank.
mean_or_na <- function(x) if (all(is.na(x))) NA_real_ else mean(x, na.rm = TRUE)

game_deviations <- function(tm) {
  tm %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    mutate(across(all_of(PROFILE_METRICS), ~ .x - mean_or_na(.x))) %>%
    group_by(LEAGUE, SEASON, SERIES_KEY, GAME_NO) %>%
    summarise(N_GAMES = first(N_GAMES), WINS_NEEDED = first(WINS_NEEDED),
              across(all_of(PROFILE_METRICS), mean_or_na), .groups = "drop") %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO)
}

profile_summary <- function(dev) {
  panels <- list(all = function(d) rep(TRUE, nrow(d)),
                 full_length = function(d) d$N_GAMES == 2 * d$WINS_NEEDED - 1)
  rows <- list()
  for (league in sort(unique(dev$LEAGUE))) {
    for (panel in names(panels)) {
      lv <- dev[dev$LEAGUE == league, ]
      pv <- lv[panels[[panel]](lv), ]
      for (g in sort(unique(pv$GAME_NO))) {
        gv <- pv[pv$GAME_NO == g, ]
        for (m in PROFILE_METRICS) {
          rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, PANEL = panel, GAME_NO = g, METRIC = m),
                                                  describe_values(gv[[m]])))
        }
      }
    }
  }
  bind_rows(rows)
}

series_state <- function(tm) {
  t <- tm %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>% arrange(GAME_NO, .by_group = TRUE) %>%
    mutate(DEV = FG3A_RATE - mean_or_na(FG3A_RATE),
           WINS_BEFORE = cumsum(WL == "W") - (WL == "W")) %>% ungroup()
  opp <- t %>% transmute(LEAGUE, SEASON, SERIES_KEY, GAME_NO, OPP_ID = TEAM_ID,
                         OPP_WINS_BEFORE = WINS_BEFORE, OPP_DEV = DEV)
  j <- t %>% filter(GAME_NO >= 2) %>%
    inner_join(opp, by = c("LEAGUE", "SEASON", "SERIES_KEY", "GAME_NO", "OPP_ID"))
  games <- j %>% filter(WINS_BEFORE < OPP_WINS_BEFORE) %>%
    transmute(LEAGUE, SEASON, SERIES_KEY, GAME_NO, TRAIL_MINUS_LEAD = DEV - OPP_DEV) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO)
  tied <- j %>% filter(WINS_BEFORE == OPP_WINS_BEFORE, TEAM_ID < OPP_ID) %>% count(LEAGUE, name = "TIED_GAMES")
  list(games = games, tied = tied)
}

state_summary <- function(state) {
  bind_rows(lapply(sort(unique(state$games$LEAGUE)), function(league) {
    v <- state$games$TRAIL_MINUS_LEAD[state$games$LEAGUE == league]
    tied <- state$tied$TIED_GAMES[state$tied$LEAGUE == league]
    as_tibble(c(list(LEAGUE = league, TIED_GAMES = if (length(tied)) tied else 0L), describe_values(v)))
  }))
}
