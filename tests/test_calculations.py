"""Minimal unit tests for AstroObject calculations. Run: python -m pytest"""
import os
import sys
import math
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from galaga_lab.Backend.astro_objects import AstroObject 


def make_obj(z=0.1, color=0.0, mag=0.0, exposure_time=1.0):
    obj = AstroObject(ra=150.0, dec=2.0, z=z, exposure_time=exposure_time)
    obj.color = color
    obj.mag = mag
    return obj


def test_get_hue_anchors_and_clip():
    assert make_obj(color=0.3).get_hue() == "rgb(150, 180, 255)"   # blue anchor
    assert make_obj(color=0.9).get_hue() == "rgb(255, 140, 110)"   # red anchor
    assert make_obj(color=-5).get_hue() == "rgb(150, 180, 255)"    # clipped low
    assert make_obj(color=5).get_hue() == "rgb(255, 140, 110)"     # clipped high


def test_get_hue_midpoint():
    # color 0.6 -> c=0.5, components truncated to int
    assert make_obj(color=0.6).get_hue() == "rgb(202, 160, 182)"


def test_peak_brightness_midrange():
    # exposure 1 -> m_lim=25; mag 20 -> (25-20)/10 = 0.5
    assert make_obj(mag=20.0, exposure_time=1.0).peak_brightness() == pytest.approx(0.5)


def test_peak_brightness_clamps():
    assert make_obj(mag=200.0).peak_brightness() == pytest.approx(0.12)   # floor
    assert make_obj(mag=-100.0).peak_brightness() == pytest.approx(1.5)   # ceiling


def test_peak_brightness_exposure_floored():
    # exposure 0 clamps to 1e-3 -> m_lim=19; mag 10 -> 0.9
    assert make_obj(mag=10.0).peak_brightness(exposure_time=0) == pytest.approx(0.9)


def test_distance_modulus_matches_luminosity_distance():
    # identity: mu = 5*log10(d_Mpc) + 25
    obj = make_obj(z=0.4)
    assert obj.distance_modulus() == pytest.approx(5 * math.log10(obj.d) + 25)
