#-*- coding: utf-8 -*-
""" demo board driver.
"""
import copy
import ee.common.utility as Utility
from ee.profile.profile import Profile
from ee.common import logger
from ee.chip.demo_chip import DemoChip

__version__="1.0"
__author__ = "Neal"


class DemoBoard001001(object):
    """Demo board driver

    Public methods:
        --
    """
    def __init__(self,profile):
        self.demo_chip=DemoChip(profile["chip"])

    @staticmethod
    def parse_board_profile(board_profile):
        '''
        Profile:
        {
            #public
            "id":string,
            "partno":"DemoBoard-001-001",

            #private
            "chip":{
                "partno":"DemoChip",
                "id":string
                "init_msg":string
            }
        }
        '''
        board_name = board_profile['id']
        

        boards = Profile.get_boards()
        boards[board_name] = dict()
        boards[board_name]['id'] = board_name
        boards[board_name]['partno'] = board_profile['partno']
        
        boards[board_name]['chip'] = board_profile['chip'].copy() 



    def board_initial(self):
        return True

    def read(self):
        return self.demo_chip.read()

    def write(self,msg):
#         logger.error("msg %s"  % msg)
        return self.demo_chip.write(msg)























