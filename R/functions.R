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

# Attempt-weighted totals per league and season (twin of game1lib.season_values).
season_values <- function(values) {
  values %>% group_by(LEAGUE, SEASON) %>%
    summarise(SERIES = n(), G1_M = sum(G1_M), G1_A = sum(G1_A), G1_FGA = sum(G1_FGA),
              REST_M = sum(REST_M), REST_A = sum(REST_A), REST_FGA = sum(REST_FGA), .groups = "drop") %>%
    mutate(G1_PCT = safe_ratio(G1_M, G1_A), REST_PCT = safe_ratio(REST_M, REST_A),
           G1_RATE = safe_ratio(G1_A, G1_FGA), REST_RATE = safe_ratio(REST_A, REST_FGA),
           D_PCT = G1_PCT - REST_PCT, D_RATE = G1_RATE - REST_RATE) %>%
    arrange(LEAGUE, SEASON)
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

# ---- Question 3: stakes and rest (twin of python/stagelib.py) ----

REST_METRICS <- c("CONTRAST_PCT", "CONTRAST_RATE")
STAKE_METRICS <- c("D_PCT", "D2_PCT", "D_RATE")

stages <- function(tg) {
  ts <- tg %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(START = min(as.character(GAME_DATE)), .groups = "drop") %>%
    arrange(LEAGUE, SEASON, TEAM_ID, START) %>%
    group_by(LEAGUE, SEASON, TEAM_ID) %>% mutate(NEXT = lead(SERIES_KEY)) %>% ungroup()
  info <- tg %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>%
    summarise(WINNER_ID = first(WINNER_ID), FINALS = first(FINALS), .groups = "drop")
  nx <- info %>% left_join(ts %>% select(LEAGUE, SEASON, SERIES_KEY, WINNER_ID = TEAM_ID, NEXT),
                           by = c("LEAGUE", "SEASON", "SERIES_KEY", "WINNER_ID"))
  key <- paste(nx$LEAGUE, nx$SEASON, nx$SERIES_KEY)
  nkey <- ifelse(is.na(nx$NEXT), NA, paste(nx$LEAGUE, nx$SEASON, nx$NEXT))
  stage <- ifelse(nx$FINALS, 0L, NA_integer_)
  names(stage) <- key
  for (i in seq_along(key)) {
    todo <- is.na(stage) & !is.na(nkey) & !is.na(stage[nkey])
    todo[is.na(todo)] <- FALSE
    if (!any(todo)) break
    stage[todo] <- stage[nkey[todo]] + 1L
  }
  tibble(LEAGUE = nx$LEAGUE, SEASON = nx$SEASON, SERIES_KEY = nx$SERIES_KEY, STAGE = unname(stage)) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY)
}

stage_mismatches <- function(tg, st) {
  tg %>% filter(!is.na(ROUND)) %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>%
    summarise(ROUND = first(ROUND), .groups = "drop") %>%
    group_by(LEAGUE, SEASON) %>% mutate(MAX_ROUND = max(ROUND)) %>% ungroup() %>%
    left_join(st, by = c("LEAGUE", "SEASON", "SERIES_KEY")) %>%
    filter(!is.na(STAGE), STAGE != MAX_ROUND - ROUND)
}

unexplained_missing_stages <- function(tg, st) {
  with_finals <- tg %>% filter(FINALS) %>% distinct(LEAGUE, SEASON)
  st %>% filter(is.na(STAGE)) %>% inner_join(with_finals, by = c("LEAGUE", "SEASON"))
}

rest_values <- function(games) {
  g1 <- games %>% filter(GAME_NO == 1) %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(REST_DAYS = first(REST), M1 = sum(FG3M), A1 = sum(FG3A), F1 = sum(FGA), .groups = "drop")
  rs <- games %>% filter(GAME_NO >= 2) %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(MR = sum(FG3M), AR = sum(FG3A), FR = sum(FGA), .groups = "drop")
  t <- g1 %>% inner_join(rs, by = c("LEAGUE", "SEASON", "SERIES_KEY", "TEAM_ID")) %>%
    mutate(DP = safe_ratio(M1, A1) - safe_ratio(MR, AR), DR = safe_ratio(A1, F1) - safe_ratio(AR, FR)) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, desc(REST_DAYS), TEAM_ID)
  hi <- t %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>% slice(1) %>% ungroup() %>%
    transmute(LEAGUE, SEASON, SERIES_KEY, R_HI = REST_DAYS, DP_HI = DP, DR_HI = DR)
  lo <- t %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>% slice(n()) %>% ungroup() %>%
    transmute(LEAGUE, SEASON, SERIES_KEY, R_LO = REST_DAYS, DP_LO = DP, DR_LO = DR)
  hi %>% inner_join(lo, by = c("LEAGUE", "SEASON", "SERIES_KEY")) %>%
    mutate(GAP = R_HI - R_LO,
           CONTRAST_PCT = ifelse(GAP > 0, DP_HI - DP_LO, NA_real_),
           CONTRAST_RATE = ifelse(GAP > 0, DR_HI - DR_LO, NA_real_)) %>%
    select(LEAGUE, SEASON, SERIES_KEY, GAP, CONTRAST_PCT, CONTRAST_RATE) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY)
}

rest_summary <- function(rv) {
  bins <- list(`1-2` = function(g) g >= 1 & g <= 2, `3-5` = function(g) g >= 3 & g <= 5,
               `6+` = function(g) g >= 6, any = function(g) g >= 1)
  rows <- list()
  for (league in sort(unique(rv$LEAGUE))) {
    lv <- rv[rv$LEAGUE == league, ]
    zero <- sum(lv$GAP == 0)
    for (b in names(bins)) {
      bv <- lv[bins[[b]](lv$GAP), ]
      for (m in REST_METRICS) {
        rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, BIN = b, METRIC = m, ZERO_GAP_SERIES = zero),
                                                describe_values(bv[[m]])))
      }
    }
  }
  bind_rows(rows)
}

stake_summary <- function(sv) {
  rows <- list()
  for (league in sort(unique(sv$LEAGUE))) {
    lv <- sv[sv$LEAGUE == league, ]
    for (s in sort(unique(lv$STAGE[!is.na(lv$STAGE)]))) {
      st <- lv[!is.na(lv$STAGE) & lv$STAGE == s, ]
      for (m in STAKE_METRICS) {
        rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, STAGE = s, METRIC = m), describe_values(st[[m]])))
      }
    }
  }
  bind_rows(rows)
}

# ---- Follow-ups 5 to 7 (twin of python/followlib.py) ----

BREAK_METRICS <- c("D_PCT", "D2_PCT", "D_RATE", "D2_RATE", "G1_PF100", "G1_FTR")
BREAK_PANELS <- list(season_2020 = function(d) d$SEASON == 2020,
                     other_seasons = function(d) d$SEASON != 2020,
                     best_of_3 = function(d) d$WINS_NEEDED == 2,
                     best_of_5 = function(d) d$WINS_NEEDED == 3,
                     best_of_7 = function(d) d$WINS_NEEDED == 4)

# Share of TRUE among non-NA flags, with the Wald 95% interval.
proportion_values <- function(x) {
  kept <- x[!is.na(x)]
  n <- length(kept)
  out <- list(N = n, N_DROPPED = length(x) - n, P = NA_real_, SE = NA_real_, LO = NA_real_, HI = NA_real_)
  if (n == 0) return(out)
  p <- sum(kept) / n
  se <- sqrt(p * (1 - p) / n)
  out$P <- p
  out$SE <- se
  out$LO <- p - Z * se
  out$HI <- p + Z * se
  out
}

outshoot_values <- function(games) {
  keys <- c("LEAGUE", "SEASON", "SERIES_KEY")
  g1 <- games %>% filter(GAME_NO == 1) %>% mutate(PCT = safe_ratio(FG3M, FG3A))
  win <- g1 %>% filter(WL == "W") %>% transmute(LEAGUE, SEASON, SERIES_KEY, G1_WINNER = TEAM_ID, WINNER_ID, W_PCT = PCT)
  lose <- g1 %>% filter(WL == "L") %>% transmute(LEAGUE, SEASON, SERIES_KEY, L_PCT = PCT)
  win %>% inner_join(lose, by = keys) %>%
    mutate(SERIES_WIN = G1_WINNER == WINNER_ID,
           ok = !is.na(W_PCT) & !is.na(L_PCT) & W_PCT != L_PCT,
           OUTSHOT = ifelse(ok, W_PCT > L_PCT, NA),
           SHOOTER_WON = ifelse(ok, OUTSHOT == SERIES_WIN, NA)) %>%
    select(LEAGUE, SEASON, SERIES_KEY, W_PCT, L_PCT, OUTSHOT, SERIES_WIN, SHOOTER_WON) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY)
}

outshoot_summary <- function(ov) {
  rows <- list()
  for (league in sort(unique(ov$LEAGUE))) {
    lv <- ov[ov$LEAGUE == league, ]
    dropped <- sum(is.na(lv$OUTSHOT))
    shooter <- proportion_values(lv$SHOOTER_WON)
    yes <- proportion_values(lv$SERIES_WIN[!is.na(lv$OUTSHOT) & lv$OUTSHOT])
    no <- proportion_values(lv$SERIES_WIN[!is.na(lv$OUTSHOT) & !lv$OUTSHOT])
    yes$N_DROPPED <- dropped
    no$N_DROPPED <- dropped
    diff <- list(N = yes$N + no$N, N_DROPPED = dropped, P = NA_real_, SE = NA_real_, LO = NA_real_, HI = NA_real_)
    if (yes$N > 0 && no$N > 0) {
      diff$P <- yes$P - no$P
      diff$SE <- sqrt(yes$SE^2 + no$SE^2)
      diff$LO <- diff$P - Z * diff$SE
      diff$HI <- diff$P + Z * diff$SE
    }
    for (e in list(list("shooter_wins_series", shooter), list("g1_winner_outshot", yes),
                   list("g1_winner_not_outshot", no), list("difference", diff))) {
      rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, ESTIMATE = e[[1]]), e[[2]]))
    }
  }
  bind_rows(rows)
}

break_values <- function(series, games, dev) {
  keys <- c("LEAGUE", "SEASON", "SERIES_KEY")
  wins <- games %>% distinct(LEAGUE, SEASON, SERIES_KEY, WINS_NEEDED)
  g1 <- dev %>% filter(GAME_NO == 1) %>% transmute(LEAGUE, SEASON, SERIES_KEY, G1_PF100 = PF100, G1_FTR = FTR)
  series %>% select(LEAGUE, SEASON, SERIES_KEY, D_PCT, D2_PCT, D_RATE, D2_RATE) %>%
    left_join(wins, by = keys) %>% left_join(g1, by = keys) %>% arrange(LEAGUE, SEASON, SERIES_KEY)
}

break_summary <- function(bv) summarize_values(bv, BREAK_PANELS, BREAK_METRICS)

profile_decade <- function(dev) {
  d <- dev %>% mutate(DECADE = (SEASON %/% 10) * 10)
  rows <- list()
  for (league in sort(unique(d$LEAGUE))) {
    lv <- d[d$LEAGUE == league, ]
    for (dec in sort(unique(lv$DECADE))) {
      dv <- lv[lv$DECADE == dec, ]
      for (g in sort(unique(dv$GAME_NO))) {
        gv <- dv[dv$GAME_NO == g, ]
        for (m in PROFILE_METRICS) {
          rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, DECADE = dec, GAME_NO = g, METRIC = m),
                                                  describe_values(gv[[m]])))
        }
      }
    }
  }
  bind_rows(rows)
}

# ---- Follow-up 8: fouls and the officials (twin of python/officiallib.py) ----

CREW_SIZE <- 3
MIN_OTHER_GAMES <- 5
MIN_SPLIT_GAMES <- 3
MIN_HALF_GAMES <- 10
OFF_GAME_KEYS <- c("LEAGUE", "SEASON", "SERIES_KEY", "GAME_NO")
OFF_SERIES_KEYS <- c("LEAGUE", "SEASON", "SERIES_KEY")

official_game_ids <- function(team_games) {
  team_games %>% distinct(LEAGUE, SEASON, SERIES_KEY, GAME_NO, GAME_ID) %>% arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO)
}

official_coverage <- function(dev, ids, crews, first) {
  keep <- rep(FALSE, nrow(dev))
  for (lg in names(first)) keep <- keep | (dev$LEAGUE == as.integer(lg) & dev$SEASON >= first[[lg]])
  n <- crews %>% group_by(GAME_ID) %>% summarise(N_OFF = n_distinct(OFFICIAL_ID[!is.na(OFFICIAL_ID)]), .groups = "drop")
  dev[keep, OFF_GAME_KEYS] %>% left_join(ids, by = OFF_GAME_KEYS) %>% left_join(n, by = "GAME_ID") %>%
    group_by(LEAGUE, SEASON) %>%
    summarise(GAMES = n(), HARVESTED = sum(!is.na(N_OFF)), WITH_CREW = sum(!is.na(N_OFF) & N_OFF == CREW_SIZE),
              .groups = "drop") %>%
    arrange(LEAGUE, SEASON)
}

official_sample <- function(dev, ids, crews) {
  c <- crews %>% filter(!is.na(OFFICIAL_ID)) %>% distinct()
  full <- c %>% count(GAME_ID, name = "N_OFF") %>% filter(N_OFF == CREW_SIZE)
  games <- dev %>% select(all_of(OFF_GAME_KEYS), PF100) %>% inner_join(ids, by = OFF_GAME_KEYS) %>%
    semi_join(full, by = "GAME_ID") %>% filter(!is.na(PF100)) %>%
    group_by(LEAGUE, GAME_NO) %>% mutate(RESID = PF100 - mean(PF100)) %>% ungroup() %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO)
  link <- c %>% inner_join(games %>% select(GAME_ID, all_of(OFF_GAME_KEYS), PF100, RESID), by = "GAME_ID") %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO, OFFICIAL_ID)
  list(games = games, link = link)
}

official_game1_profile <- function(games) {
  rows <- list()
  for (league in sort(unique(games$LEAGUE))) {
    lv <- games[games$LEAGUE == league, ]
    for (g in sort(unique(lv$GAME_NO))) {
      rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, PART = "pf100", GAME_NO = g),
                                              describe_values(lv$PF100[lv$GAME_NO == g])))
    }
  }
  bind_rows(rows)
}

crew_values <- function(games, link) {
  tot <- link %>% group_by(LEAGUE, OFFICIAL_ID) %>% summarise(T_SUM = sum(RESID), T_N = n(), .groups = "drop")
  own <- link %>% group_by(LEAGUE, SEASON, SERIES_KEY, OFFICIAL_ID) %>%
    summarise(S_SUM = sum(RESID), S_N = n(), .groups = "drop")
  tend <- own %>% inner_join(tot, by = c("LEAGUE", "OFFICIAL_ID")) %>%
    mutate(OTHER_N = T_N - S_N, TEND = ifelse(OTHER_N >= MIN_OTHER_GAMES, (T_SUM - S_SUM) / OTHER_N, NA_real_)) %>%
    select(LEAGUE, SEASON, SERIES_KEY, OFFICIAL_ID, TEND)
  crew <- link %>% select(all_of(OFF_GAME_KEYS), OFFICIAL_ID) %>%
    inner_join(tend, by = c(OFF_SERIES_KEYS, "OFFICIAL_ID")) %>%
    group_by(LEAGUE, SEASON, SERIES_KEY, GAME_NO) %>% summarise(CREW = mean_or_na(TEND), .groups = "drop")
  games %>% select(all_of(OFF_GAME_KEYS)) %>% left_join(crew, by = OFF_GAME_KEYS) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, GAME_NO)
}

crew_profile <- function(cv, dev) {
  want <- dev %>% count(LEAGUE, SEASON, SERIES_KEY, name = "WANT")
  have <- cv %>% filter(!is.na(CREW)) %>% count(LEAGUE, SEASON, SERIES_KEY, name = "HAVE")
  ok <- want %>% inner_join(have, by = OFF_SERIES_KEYS) %>% filter(WANT == HAVE) %>% select(all_of(OFF_SERIES_KEYS))
  d <- cv %>% inner_join(ok, by = OFF_SERIES_KEYS) %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>%
    mutate(CREW_DEV = CREW - mean(CREW)) %>% ungroup()
  rows <- list()
  for (league in sort(unique(d$LEAGUE))) {
    lv <- d[d$LEAGUE == league, ]
    for (g in sort(unique(lv$GAME_NO))) {
      rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, PART = "crew", GAME_NO = g),
                                              describe_values(lv$CREW_DEV[lv$GAME_NO == g])))
    }
  }
  bind_rows(rows)
}

within_official <- function(link) {
  link %>% group_by(LEAGUE, OFFICIAL_ID) %>%
    summarise(N_G1 = sum(GAME_NO == 1), N_LATER = sum(GAME_NO >= 2),
              G1 = mean_or_na(PF100[GAME_NO == 1]), LATER = mean_or_na(PF100[GAME_NO >= 2]), .groups = "drop") %>%
    filter(N_G1 >= MIN_SPLIT_GAMES, N_LATER >= MIN_SPLIT_GAMES) %>%
    mutate(D = G1 - LATER) %>% arrange(LEAGUE, OFFICIAL_ID)
}

within_summary <- function(wo) {
  bind_rows(lapply(sort(unique(wo$LEAGUE)), function(lg)
    as_tibble(c(list(LEAGUE = lg), describe_values(wo$D[wo$LEAGUE == lg])))))
}

official_halves <- function(link) {
  link %>% group_by(LEAGUE, OFFICIAL_ID) %>%
    summarise(N_EVEN = sum(SEASON %% 2 == 0), N_ODD = sum(SEASON %% 2 == 1),
              EVEN = mean_or_na(RESID[SEASON %% 2 == 0]), ODD = mean_or_na(RESID[SEASON %% 2 == 1]),
              .groups = "drop") %>%
    filter(N_EVEN >= MIN_HALF_GAMES, N_ODD >= MIN_HALF_GAMES) %>% arrange(LEAGUE, OFFICIAL_ID)
}

official_reliability <- function(h) {
  bind_rows(lapply(sort(unique(h$LEAGUE)), function(lg) {
    lv <- h[h$LEAGUE == lg, ]
    n <- nrow(lv)
    r <- if (n >= 2 && sd(lv$EVEN) > 0 && sd(lv$ODD) > 0) cor(lv$EVEN, lv$ODD) else NA_real_
    lo <- hi <- NA_real_
    if (!is.na(r) && n > 3 && abs(r) < 1) {
      se <- 1 / sqrt(n - 3)
      lo <- tanh(atanh(r) - Z * se)
      hi <- tanh(atanh(r) + Z * se)
    }
    tibble(LEAGUE = lg, N = n, R = r, LO = lo, HI = hi)
  }))
}

# ---- Follow-up 9: experienced vs inexperienced (twin of python/experiencelib.py) ----

EXP_TEAM_KEYS <- c("LEAGUE", "SEASON", "SERIES_KEY", "TEAM_ID")
EXP_CONTRASTS <- c("CONTRAST_PCT", "CONTRAST_RATE", "CONTRAST_PF")
FRANCHISE_SEASONS <- 3

roster_experience <- function(players, games) {
  per_season <- players %>% group_by(LEAGUE, PLAYER_ID, SEASON) %>%
    summarise(N = n_distinct(GAME_ID), .groups = "drop") %>% arrange(LEAGUE, PLAYER_ID, SEASON) %>%
    group_by(LEAGUE, PLAYER_ID) %>% mutate(PRIOR = cumsum(N) - N) %>% ungroup()
  ids <- games %>% distinct(LEAGUE, SEASON, SERIES_KEY, GAME_ID)
  players %>% inner_join(ids, by = c("LEAGUE", "SEASON", "GAME_ID")) %>%
    group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID, PLAYER_ID) %>%
    summarise(MIN = sum(ifelse(is.na(MIN), 0, MIN)), .groups = "drop") %>%
    inner_join(per_season %>% select(LEAGUE, PLAYER_ID, SEASON, PRIOR), by = c("LEAGUE", "PLAYER_ID", "SEASON")) %>%
    group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(ROSTER_EXP = safe_ratio(sum(MIN * PRIOR), sum(MIN)), .groups = "drop") %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, TEAM_ID)
}

franchise_experience <- function(team_logs, games) {
  per <- team_logs %>% group_by(LEAGUE, TEAM_ID, SEASON) %>% summarise(N = n_distinct(GAME_ID), .groups = "drop")
  teams <- games %>% distinct(LEAGUE, SEASON, SERIES_KEY, TEAM_ID)
  bind_rows(lapply(seq_len(FRANCHISE_SEASONS), function(k)
    teams %>% left_join(per %>% mutate(SEASON = SEASON + k), by = c("LEAGUE", "TEAM_ID", "SEASON")) %>%
      mutate(N = ifelse(is.na(N), 0, N)))) %>%
    group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>% summarise(FRAN_EXP = as.numeric(sum(N)), .groups = "drop") %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, TEAM_ID)
}

team_gaps <- function(games) {
  tm <- team_game_metrics(games)
  g1 <- tm %>% filter(GAME_NO == 1) %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(M1 = sum(FG3M), A1 = sum(FG3A), F1 = sum(FGA), PF1 = mean_or_na(PF100), .groups = "drop")
  rest <- tm %>% filter(GAME_NO >= 2) %>% group_by(LEAGUE, SEASON, SERIES_KEY, TEAM_ID) %>%
    summarise(MR = sum(FG3M), AR = sum(FG3A), FR = sum(FGA), PFR = mean_or_na(PF100), .groups = "drop")
  g1 %>% inner_join(rest, by = EXP_TEAM_KEYS) %>%
    transmute(LEAGUE, SEASON, SERIES_KEY, TEAM_ID,
              DP = safe_ratio(M1, A1) - safe_ratio(MR, AR), DR = safe_ratio(A1, F1) - safe_ratio(AR, FR),
              DPF = PF1 - PFR) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, TEAM_ID)
}

exp_contrasts <- function(gaps, exp, col) {
  t <- gaps %>% inner_join(exp, by = EXP_TEAM_KEYS) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY, desc(.data[[col]]), TEAM_ID)
  hi <- t %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>% slice(1) %>% ungroup()
  lo <- t %>% group_by(LEAGUE, SEASON, SERIES_KEY) %>% slice(n()) %>% ungroup()
  hi %>% inner_join(lo, by = c("LEAGUE", "SEASON", "SERIES_KEY"), suffix = c("", "_LO")) %>%
    mutate(GAP = .data[[col]] - .data[[paste0(col, "_LO")]], ok = GAP > 0,
           CONTRAST_PCT = ifelse(ok, DP - DP_LO, NA_real_),
           CONTRAST_RATE = ifelse(ok, DR - DR_LO, NA_real_),
           CONTRAST_PF = ifelse(ok, DPF - DPF_LO, NA_real_)) %>%
    select(LEAGUE, SEASON, SERIES_KEY, GAP, all_of(EXP_CONTRASTS)) %>%
    arrange(LEAGUE, SEASON, SERIES_KEY)
}

exp_summary <- function(cv, measure) {
  rows <- list()
  for (league in sort(unique(cv$LEAGUE))) {
    lv <- cv[cv$LEAGUE == league, ]
    pos <- lv[!is.na(lv$GAP) & lv$GAP > 0, ]
    equal <- sum(!is.na(lv$GAP) & lv$GAP == 0)
    q <- unname(quantile(pos$GAP, c(1 / 3, 2 / 3), type = 7))
    bins <- list(low = pos$GAP <= q[1], middle = pos$GAP > q[1] & pos$GAP <= q[2],
                 high = pos$GAP > q[2], any = rep(TRUE, nrow(pos)))
    for (b in names(bins)) {
      bv <- pos[bins[[b]], ]
      for (m in EXP_CONTRASTS) {
        rows[[length(rows) + 1]] <- as_tibble(c(list(LEAGUE = league, MEASURE = measure, BIN = b, METRIC = m,
                                                     Q1 = q[1], Q2 = q[2], EQUAL_SERIES = equal),
                                                describe_values(bv[[m]])))
      }
    }
  }
  bind_rows(rows)
}

exp_coverage <- function(players, seasons) {
  n <- players %>% count(LEAGUE, SEASON, name = "PLAYER_ROWS")
  seasons %>% left_join(n, by = c("LEAGUE", "SEASON")) %>%
    mutate(PLAYER_ROWS = ifelse(is.na(PLAYER_ROWS), 0L, PLAYER_ROWS)) %>% arrange(LEAGUE, SEASON)
}
