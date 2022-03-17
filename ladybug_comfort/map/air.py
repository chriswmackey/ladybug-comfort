# coding=utf-8
"""Methods for resolving Air Temperature and Humidity for EnergyPlus output files."""
from __future__ import division

import json

from ladybug.epw import EPW
from ladybug.sql import SQLiteResult
from ladybug.analysisperiod import AnalysisPeriod


def air_map(enclosure_info, sql, epw, analysis_period=None, humidity=False):
    """Get MRT data collections adjusted for shortwave using Radiance .ill files.

    Args:
        enclosure_info: Path to a JSON file containing information about the radiant
            enclosure that sensor points belong to.
        sql: Path to an SQLite file that was generated by EnergyPlus.
            This file must contain hourly or sub-hourly results for zone comfort
            variables.
        epw: An EPW object that will be used to specify data for any sensor outside
            of any enclosure.
        analysis_period: An optional AnalysisPeriod to be applied to all results.
            If None, all data collections will be for the entire run period of
            the sql. (Default: None).
        humidity: Boolean to note whether relative humidity values should be returned
            instead of air temperature. (Default: False)
    """
    # load the enclosure information
    with open(enclosure_info) as json_file:
        enclosure_dict = json.load(json_file)
    zone_order = [zone_id.upper() for zone_id in enclosure_dict['mapper']]
    a_per = analysis_period if analysis_period is not None else AnalysisPeriod()

    # load the indoor values if they are needed
    air_data = []
    if enclosure_dict['has_indoor']:
        sql_obj = SQLiteResult(sql)
        if humidity:
            in_avg_outp, id_key = 'Zone Air Relative Humidity', 'System'
        else:
            in_avg_outp, id_key = 'Zone Mean Air Temperature', 'Zone'
        in_avg_dict = {d.header.metadata[id_key]: d for d in
                       sql_obj.data_collections_by_output_name(in_avg_outp)}
        air_data = [in_avg_dict[z] for z in zone_order]
        if air_data[0].header.analysis_period != a_per:
            air_data = [d.filter_by_analysis_period(a_per) for d in air_data]

    # load the EPW and outdoor values if they are needed
    if enclosure_dict['has_outdoor']:
        epw_obj = EPW(epw)
        out_avg = epw_obj.relative_humidity if humidity \
            else epw_obj.dry_bulb_temperature
        if not a_per.is_annual:
            out_avg = out_avg.filter_by_analysis_period(a_per)
        air_data.append(out_avg)

    # create a base matrix with the same values across all rooms
    air_mtx = []
    for sen_enc in enclosure_dict['sensor_indices']:
        air_mtx.append(air_data[sen_enc]._values)

    # go over the base values to and interpolate across any air boundaries
    for pt_1, int_facs in enclosure_dict['air_bound_proximity'].items():
        zon_i1, zon_i2 = tuple(int_facs[0].keys())
        z_fac1, z_fac2 = tuple(int_facs[0].values())
        dat_1 = (v * z_fac1 for v in air_data[int(zon_i1)])
        dat_2 = (v * z_fac2 for v in air_data[int(zon_i2)])
        dat_comb = tuple(v1 + v2 for v1, v2 in zip(dat_1, dat_2))
        if len(int_facs) > 1:
            for fac in int_facs[1:]:
                zon_i1, zon_i2 = tuple(fac.keys())
                z_fac1, z_fac2 = tuple(fac.values())
                dat_1 = (v * z_fac1 for v in air_data[int(zon_i1)])
                dat_2 = (v * z_fac2 for v in air_data[int(zon_i2)])
                dat_comb_i = (v1 + v2 for v1, v2 in zip(dat_1, dat_2))
                dat_comb = tuple(d1 + d2 for d1, d2 in zip(dat_comb, dat_comb_i))
            fac_len = len(int_facs)
            dat_comb = tuple(d1 / fac_len for d1 in dat_comb)
        air_mtx[int(pt_1)] = dat_comb
    return air_mtx
