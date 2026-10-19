"""officiallib against tests/fixtures/official_games.csv and
official_crews.csv (same expected numbers in tests/R/test_functions.R).
Thresholds are lowered to 1 so four officials can exercise every rule.

Worked by hand. PF100 deviations: 1-2 (2010) -3, 0, 3; 3-4 (2011) -1, 1;
5-6 (2011) has a two-official Game 1 and an unharvested Game 2, so it drops.
  Means by game number: G1 -2, G2 0.5, G3 3, so RESID is
  1-2: -1, -0.5, 0; 3-4: 1, 0.5.
  Officials 1 to 4 (A to D): A 1-2 G1 G2, 3-4 G1 G2; B 1-2 G1 G2 G3, 3-4 G1;
  C 1-2 G1 G3, 3-4 G1 G2; D 1-2 G2 G3, 3-4 G2.
8b tendencies (other series only): for 1-2, A .75, B 1, C .75, D .5;
  for 3-4, A -.75, B -.5, C -.5, D -.25.
  CREW: 1-2 G1 2.5/3, G2 .75, G3 .75; 3-4 G1 -1.75/3, G2 -.5.
  CREW_DEV: 1-2 1/18, -1/36, -1/36; 3-4 -1/24, 1/24.
  Profile: G1 1/144, G2 1/144, G3 -1/36.
8c: A -2 - .5 = -2.5; B -2 - 1.5 = -3.5; C -2 - 2 = -4; D has no Game 1.
8d: EVEN (2010) A -.75, B -.5, C -.5, D -.25; ODD (2011) .75, 1, .75, .5; r = -0.5.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import polars as pl
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))
import officiallib as ol  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


@pytest.fixture(autouse=True)
def low_thresholds(monkeypatch):
    for name in ("MIN_OTHER_GAMES", "MIN_SPLIT_GAMES", "MIN_HALF_GAMES"):
        monkeypatch.setattr(ol, name, 1)


@pytest.fixture
def parts():
    g = pl.read_csv(FIX / "official_games.csv", schema_overrides={"SERIES_KEY": pl.Utf8})
    crews = pl.read_csv(FIX / "official_crews.csv")
    dev, ids = g.drop("GAME_ID"), g.select(*ol.GAME_KEYS, "GAME_ID")
    return dev, ids, crews


def test_flatten(tmp_path):
    (tmp_path / "g1.json").write_text(json.dumps([{"personId": 7}, {"personId": 8}]))
    (tmp_path / "g2.json").write_text("[]")
    f = ol.flatten_officials(tmp_path)
    assert f.rows() == [("g1", 7), ("g1", 8), ("g2", None)]


def test_coverage(parts):
    dev, ids, crews = parts
    cov = ol.coverage(dev, ids, crews, {0: 2010})
    assert cov.select("SEASON", "GAMES", "HARVESTED", "WITH_CREW").rows() == [(2010, 3, 3, 3), (2011, 4, 3, 2)]
    assert ol.coverage(dev, ids, crews, {0: 2011})["SEASON"].to_list() == [2011]


def test_sample_and_resid(parts):
    games, link = ol.sample(*parts)
    assert games["GAME_ID"].to_list() == ["g11", "g12", "g13", "g21", "g22"]
    assert games["RESID"].to_list() == pytest.approx([-1, -0.5, 0, 1, 0.5])
    assert link.height == 15 and 5 not in link["OFFICIAL_ID"].to_list()


def test_game1_profile(parts):
    games, _ = ol.sample(*parts)
    p = ol.game1_profile(games)
    assert p["GAME_NO"].to_list() == [1, 2, 3]
    assert p["MEAN"].to_list() == pytest.approx([-2, 0.5, 3])


def test_crew(parts):
    dev = parts[0]
    games, link = ol.sample(*parts)
    cv = ol.crew_values(games, link)
    assert cv["CREW"].to_list() == pytest.approx([2.5 / 3, 0.75, 0.75, -1.75 / 3, -0.5])
    p = ol.crew_profile(cv, dev)
    assert p["N"].to_list() == [2, 2, 1]
    assert p["MEAN"].to_list() == pytest.approx([1 / 144, 1 / 144, -1 / 36])


def test_crew_tendency_needs_other_games(parts, monkeypatch):
    monkeypatch.setattr(ol, "MIN_OTHER_GAMES", 3)  # only B (3 games in 1-2) qualifies, for 3-4
    games, link = ol.sample(*parts)
    cv = ol.crew_values(games, link)
    assert cv["CREW"].to_list()[:3] == [None, None, None]
    assert cv["CREW"].to_list()[3] == pytest.approx(-0.5)
    assert cv["CREW"].to_list()[4] is None


def test_within_official(parts):
    _, link = ol.sample(*parts)
    wo = ol.within_official(link)
    assert wo["OFFICIAL_ID"].to_list() == [1, 2, 3]
    assert wo["D"].to_list() == pytest.approx([-2.5, -3.5, -4])
    assert ol.within_summary(wo)["MEAN"].to_list() == pytest.approx([-10 / 3])


def test_reliability(parts):
    _, link = ol.sample(*parts)
    h = ol.halves(link)
    assert h["EVEN"].to_list() == pytest.approx([-0.75, -0.5, -0.5, -0.25])
    assert h["ODD"].to_list() == pytest.approx([0.75, 1, 0.75, 0.5])
    r = ol.reliability(h).row(0, named=True)
    assert (r["N"], r["R"]) == (4, pytest.approx(-0.5))
    z = math.atanh(-0.5)
    assert r["LO"] == pytest.approx(math.tanh(z - 1.96)) and r["HI"] == pytest.approx(math.tanh(z + 1.96))


def test_pearson_degenerate():
    assert ol.pearson([1.0], [2.0]) is None
    assert ol.pearson([1.0, 1.0], [2.0, 3.0]) is None
