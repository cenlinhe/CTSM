"""
Run this code by using the following wrapper script:
tools/modify_fsurdat/fsurdat_modifier

The wrapper script includes a full description and instructions.
"""

import logging
import argparse
from configparser import ConfigParser
from ctsm.utils import get_config_value
from ctsm.ctsm_logging import setup_logging_pre_config, add_logging_args, process_logging_args
from ctsm.modify_fsurdat.modify_fsurdat import ModifyFsurdat

logger = logging.getLogger(__name__)

def main ():
    """
    Description
    -----------
    Calls function that modifies an fsurdat (surface dataset)
    """

    # set up logging allowing user control
    setup_logging_pre_config()

    # read the command line argument to obtain the path to the .cfg file
    parser = argparse.ArgumentParser()
    parser.add_argument('cfg_path',
                        help='/path/name.cfg of input file, eg ./modify.cfg')
    add_logging_args(parser)
    args = parser.parse_args()
    process_logging_args(args)
    fsurdat_modifier(args.cfg_path)

def fsurdat_modifier(cfg_path):
    """Implementation of fsurdat_modifier command"""
    # read the .cfg (config) file
    config = ConfigParser()
    config.read(cfg_path)
    section = config.sections()[0]  # name of the first section

    # required: user must set these in the .cfg file
    fsurdat_in = get_config_value(config=config, section=section,
        item='fsurdat_in', file_path=cfg_path)
    fsurdat_out = get_config_value(config=config, section=section,
        item='fsurdat_out', file_path=cfg_path)

    # required but fallback values available for variables omitted
    # entirely from the .cfg file
    idealized = get_config_value(config=config, section=section,
        item='idealized', file_path=cfg_path, convert_to_type=bool)
    zero_nonveg = get_config_value(config=config, section=section,
        item='zero_nonveg', file_path=cfg_path, convert_to_type=bool)

    lnd_lat_1 = get_config_value(config=config, section=section,
        item='lnd_lat_1', file_path=cfg_path, convert_to_type=float)
    lnd_lat_2 = get_config_value(config=config, section=section,
        item='lnd_lat_2', file_path=cfg_path, convert_to_type=float)
    lnd_lon_1 = get_config_value(config=config, section=section,
        item='lnd_lon_1', file_path=cfg_path, convert_to_type=float)
    lnd_lon_2 = get_config_value(config=config, section=section,
        item='lnd_lon_2', file_path=cfg_path, convert_to_type=float)

    landmask_file = get_config_value(config=config, section=section,
        item='landmask_file', file_path=cfg_path, can_be_unset=True)

    # not required: user may set these in the .cfg file
    dom_nat_pft = get_config_value(config=config, section=section,
        item='dom_nat_pft', file_path=cfg_path,
        allowed_values=range(15),  # integers from 0 to 14
        convert_to_type=int, can_be_unset=True)

    lai = get_config_value(config=config, section=section, item='lai',
        file_path=cfg_path, is_list=True,
        convert_to_type=float, can_be_unset=True)
    sai = get_config_value(config=config, section=section, item='sai',
        file_path=cfg_path, is_list=True,
        convert_to_type=float, can_be_unset=True)
    hgt_top = get_config_value(config=config, section=section,
        item='hgt_top', file_path=cfg_path, is_list=True,
        convert_to_type=float, can_be_unset=True)
    hgt_bot = get_config_value(config=config, section=section,
        item='hgt_bot', file_path=cfg_path, is_list=True,
        convert_to_type=float, can_be_unset=True)

    soil_color = get_config_value(config=config, section=section,
        item='soil_color', file_path=cfg_path,
        allowed_values=range(1, 21),  # integers from 1 to 20
        convert_to_type=int, can_be_unset=True)

    std_elev = get_config_value(config=config, section=section,
        item='std_elev', file_path=cfg_path,
        convert_to_type=float, can_be_unset=True)
    max_sat_area = get_config_value(config=config, section=section,
        item='max_sat_area', file_path=cfg_path,
        convert_to_type=float, can_be_unset=True)

    # Create ModifyFsurdat object
    modify_fsurdat = ModifyFsurdat.init_from_file(fsurdat_in,
        lnd_lon_1, lnd_lon_2, lnd_lat_1, lnd_lat_2, landmask_file)

    # ------------------------------
    # modify surface data properties
    # ------------------------------

    # Set fsurdat variables in a rectangle that could be global (default).
    # Note that the land/ocean mask gets specified in the domain file for
    # MCT or the ocean mesh files for NUOPC. Here the user may specify
    # fsurdat variables inside a box but cannot change which points will
    # run as land and which as ocean.
    if idealized:
        modify_fsurdat.set_idealized()  # set 2D variables
        # set 3D and 4D variables pertaining to natural vegetation
        modify_fsurdat.set_dom_nat_pft(dom_nat_pft=0, lai=[], sai=[],
                                       hgt_top=[], hgt_bot=[])

    if dom_nat_pft is not None:  # overwrite "idealized" value
        modify_fsurdat.set_dom_nat_pft(dom_nat_pft=dom_nat_pft,
                                       lai=lai, sai=sai,
                                       hgt_top=hgt_top, hgt_bot=hgt_bot)

    if max_sat_area is not None:  # overwrite "idealized" value
        modify_fsurdat.setvar_lev0('FMAX', max_sat_area)

    if std_elev is not None:  # overwrite "idealized" value
        modify_fsurdat.setvar_lev0('STD_ELEV', std_elev)

    if soil_color is not None:  # overwrite "idealized" value
        modify_fsurdat.setvar_lev0('SOIL_COLOR', soil_color)

    if zero_nonveg:
        modify_fsurdat.zero_nonveg()

    # ----------------------------------------------
    # Output the now modified CTSM surface data file
    # ----------------------------------------------
    modify_fsurdat.write_output(fsurdat_in, fsurdat_out)
