# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 10:14:16 2019

@author: cwhanse
"""

import numpy as np
import pandas as pd

import pytest
from pandas.util.testing import assert_series_equal
from numpy.testing import assert_allclose

from pvlib import iam as _iam
from conftest import needs_numpy_1_10, requires_scipy


@needs_numpy_1_10
def test_ashrae():
    thetas = np.array([-90., -67.5, -45., -22.5, 0., 22.5, 45., 67.5, 89., 90.,
                       np.nan])
    expected = np.array([0, 0.9193437, 0.97928932, 0.99588039, 1., 0.99588039,
                         0.97928932, 0.9193437, 0, 0, np.nan])
    iam = _iam.ashrae(thetas, .05)
    assert_allclose(iam, expected, equal_nan=True)
    iam_series = _iam.ashrae(pd.Series(thetas))
    assert_series_equal(iam_series, pd.Series(expected))


@needs_numpy_1_10
def test_ashrae_scalar():
    thetas = -45.
    iam = _iam.ashrae(thetas, .05)
    expected = 0.97928932
    assert_allclose(iam, expected, equal_nan=True)
    thetas = np.nan
    iam = _iam.ashrae(thetas, .05)
    expected = np.nan
    assert_allclose(iam, expected, equal_nan=True)


@needs_numpy_1_10
def test_physical():
    aoi = np.array([-90., -67.5, -45., -22.5, 0., 22.5, 45., 67.5, 90.,
                    np.nan])
    expected = np.array([0, 0.8893998, 0.98797788, 0.99926198, 1, 0.99926198,
                         0.98797788, 0.8893998, 0, np.nan])
    iam = _iam.physical(aoi, 1.526, 0.002, 4)
    assert_allclose(iam, expected, equal_nan=True)

    # GitHub issue 397
    aoi = pd.Series(aoi)
    iam = _iam.physical(aoi, 1.526, 0.002, 4)
    expected = pd.Series(expected)
    assert_series_equal(iam, expected)


@needs_numpy_1_10
def test_physical_scalar():
    aoi = -45.
    iam = _iam.physical(aoi, 1.526, 0.002, 4)
    expected = 0.98797788
    assert_allclose(iam, expected, equal_nan=True)
    aoi = np.nan
    iam = _iam.physical(aoi, 1.526, 0.002, 4)
    expected = np.nan
    assert_allclose(iam, expected, equal_nan=True)


def test_martin_ruiz():

    aoi = 45.
    a_r = 0.16
    expected = 0.98986965

    # will fail if default values change
    iam = _iam.martin_ruiz(aoi)
    assert_allclose(iam, expected)
    # will fail if parameter names change
    iam = _iam.martin_ruiz(aoi=aoi, a_r=a_r)
    assert_allclose(iam, expected)

    a_r = 0.18
    aoi = [-100, -60, 0, 60, 100, np.nan, np.inf]
    expected = [0.0, 0.9414631, 1.0, 0.9414631, 0.0, np.nan, 0.0]

    # check out of range of inputs as list
    iam = _iam.martin_ruiz(aoi, a_r)
    assert_allclose(iam, expected, equal_nan=True)

    # check out of range of inputs as array
    iam = _iam.martin_ruiz(np.array(aoi), a_r)
    assert_allclose(iam, expected, equal_nan=True)

    # check out of range of inputs as Series
    aoi = pd.Series(aoi)
    expected = pd.Series(expected)
    iam = _iam.martin_ruiz(aoi, a_r)
    assert_series_equal(iam, expected)

    # check exception clause
    with pytest.raises(RuntimeError):
        _iam.martin_ruiz(0.0, a_r=0.0)


@requires_scipy
def test_iam_interp():

    aoi_meas = [0.0, 45.0, 65.0, 75.0]
    iam_meas = [1.0,  0.9,  0.8,  0.6]

    # simple default linear method
    aoi = 55.0
    expected = 0.85
    iam = _iam.interp(aoi, aoi_meas, iam_meas)
    assert_allclose(iam, expected)

    # simple non-default method
    aoi = 55.0
    expected = 0.8878062
    iam = _iam.interp(aoi, aoi_meas, iam_meas, method='cubic')
    assert_allclose(iam, expected)

    # check with all reference values
    aoi = aoi_meas
    expected = iam_meas
    iam = _iam.interp(aoi, aoi_meas, iam_meas)
    assert_allclose(iam, expected)

    # check normalization and Series
    aoi = pd.Series(aoi)
    expected = pd.Series(expected)
    iam_mult = np.multiply(0.9, iam_meas)
    iam = _iam.interp(aoi, aoi_meas, iam_mult, normalize=True)
    assert_series_equal(iam, expected)

    # check beyond reference values
    aoi = [-45, 0, 45, 85, 90, 95, 100, 105, 110]
    expected = [0.9, 1.0, 0.9, 0.4, 0.3, 0.2, 0.1, 0.0, 0.0]
    iam = _iam.interp(aoi, aoi_meas, iam_meas)
    assert_allclose(iam, expected)

    # check exception clause
    with pytest.raises(ValueError):
        _iam.interp(0.0, [0], [1])

    # check exception clause
    with pytest.raises(ValueError):
        _iam.interp(0.0, [0, 90], [1, -1])


@pytest.mark.parametrize('aoi,expected', [
    (45, 0.9975036250000002),
    (np.array([[-30, 30, 100, np.nan]]),
     np.array([[0, 1.007572, 0, np.nan]])),
    (pd.Series([80]), pd.Series([0.597472]))
])
def test_sapm(sapm_module_params, aoi, expected):

    out = _iam.sapm(aoi, sapm_module_params)

    if isinstance(aoi, pd.Series):
        assert_series_equal(out, expected, check_less_precise=4)
    else:
        assert_allclose(out, expected, atol=1e-4)


def test_sapm_limits():
    module_parameters = {'B0': 5, 'B1': 0, 'B2': 0, 'B3': 0, 'B4': 0, 'B5': 0}
    assert _iam.sapm(1, module_parameters) == 5

    module_parameters = {'B0': 5, 'B1': 0, 'B2': 0, 'B3': 0, 'B4': 0, 'B5': 0}
    assert _iam.sapm(1, module_parameters, upper=1) == 1

    module_parameters = {'B0': -5, 'B1': 0, 'B2': 0, 'B3': 0, 'B4': 0, 'B5': 0}
    assert _iam.sapm(1, module_parameters) == 0