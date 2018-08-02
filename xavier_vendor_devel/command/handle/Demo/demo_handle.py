#-*- coding: UTF-8 -*-
__author__ = 'Neal'

import re
import time
import command.server.handle_utility as Utility
from ee.common import xavier as Xavier
from ee.common import logger

demo_device={
                        "board":{"id":"board_demo1"},
                        "chip":{"id":"chip_demo1"}
                      }

@Utility.timeout(1)
def hello_handle(params):
    help_info = "hello([index])$\r\n\
    \index=(0,1,2,3), or none\r\n"

    ''' help '''    
    if Utility.is_ask_for_help(params) is True:
        return Utility.handle_done(help_info)

    ''' parameters analysis '''
    params_count = len(params)
    if params_count  > 1:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"param length error") 

    if params_count == 0:
        index = 0
    else:
        index = int(params[0],10)
        if index < 0 or index > 3:
            return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"index param value error")

    result=["Hello Xavier !", "Hello Xavier 1 !", "Hello Xavier 2 !"]
    out_msg=''
    if index >= 3:
        return Utility.handle_done()
    else:
        out_msg = result[index]
        return Utility.handle_done(out_msg)




@Utility.timeout(1)
def hello_read_handle(params):
    help_info = "hello read(<device type>)$\r\n\
    \device type=(board,chip)\r\n"

    ''' help '''    
    if Utility.is_ask_for_help(params) is True:
        return Utility.handle_done(help_info)

    ''' parameters analysis '''
    params_count = len(params)
    if params_count  != 1:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"param length error") 

    #device type
    device_type = params[0]
    global demo_device
    if device_type not in demo_device:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"device type error")

    device_id = demo_device[device_type]["id"]

    #done
    result = Xavier.call('eval',device_id,'read')

    #return msg
    out_msg = result
    return Utility.handle_done(out_msg)


@Utility.timeout(1)
def hello_write_handle(params):
    help_info = "hello write(<device type>, <msg>)$\r\n\
    \tdevice type=(board,chip)$\r\n\
    \tmsg: string"

    ''' help '''    
    if Utility.is_ask_for_help(params) is True:
        return Utility.handle_done(help_info)

    ''' parameters analysis '''
    params_count = len(params)
    if params_count  != 2:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"param length error") 

    #param: device type
    device_type = params[0]
    global demo_device
    if device_type not in demo_device:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_parameter_invalid'],"device type error")

    device_id = demo_device[device_type]["id"]

    #param: msg
    param_msg = str(params[1])
#     logger.error("param_msg %s"  % param_msg)

    #done
    result = Xavier.call('eval',device_id,'write', param_msg)
    if result is False:
        return Utility.handle_error(Utility.handle_errorno['handle_errno_execute_failure'],"execute error") 

    #return msg
    return Utility.handle_done()