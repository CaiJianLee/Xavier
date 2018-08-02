#-*- coding: UTF-8 -*-
"""
demo chip driver
"""
from __future__ import division
from ee.common import logger
import ee.common.utility as Utility
from ee.profile.profile import Profile

__version__="1.0"
__author__ = "Neal"


class DemoChip(object):
    """Demo chip driver

    Public methods:
        --
    """
    def __init__(self,profile):
        """
        Profile:
        {
            #public
            "id":string,
            "partno":"DemoChip",

            #private
            "init_msg":string
        }
        """
        self._msg = profile["init_msg"]
        self._initial_msg = None

    @staticmethod
    def parse_chip_profile(chip_profile, board_name):
        """
        Profile:
        {
            #public
            "id":string,
            "partno":"DemoChip",

            #private
            "init_msg":string
        }
        """
        logger.error("chip_profile %s, board_name %s"  % (chip_profile, board_name))
        
        chip_name = chip_profile['id']

        chips = Profile.get_chips()
        chips[chip_name] = dict()

        chips[chip_name]["init_msg"] = chip_profile["init_msg"]
        chips[chip_name]['partno'] = chip_profile['partno']

        logger.error("chips = %s" % chips)

    def read(self):
        """ read init_msg
        Args:
            none
            
        Returns:
            string
        """
        return self._msg;

    def write(self, msg):
        """ write init_msg
        Args:
            msg: string

        Returns:
            bool: True | False, True for success, False for failed.
        """
        
        self._msg = msg
        return True

    def initial(self,msg):
        slef._initial_msg = msg
        return True
    
    
    
    
    
    
    