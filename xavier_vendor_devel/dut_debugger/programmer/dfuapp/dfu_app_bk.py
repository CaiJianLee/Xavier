#-*- coding: UTF-8 -*-
import sys
import os
import re
import command.server.handle_utility as Utility
from ee.common import xavier as Xavier
from ee.common import logger
from dut_debugger.programmer.dfucommon import dfu_common
#-----from rpc server-----
from dut_debugger.programmer.chipprog.cortexmprog import CortexMProg
from dut_debugger.programmer.chipprog.psoc4prog import Psoc4Prog
from dut_debugger.programmer.chipprog.nrf5xbleprog import Nrf5XProg
from dut_debugger.programmer.chipprog.spiflashprog import SpiFlash
from dut_debugger.programmer.chipprog.stm32prog import Stm32Prog
#-----from python layer-----
from dut_debugger.programmer.chipprog.hearstprog import HearstProg

import time


def _return_to_str(return_from_chip_prog):#[0] true/false,[1] type,[2] return
    ret_str = ""
    if dfu_common.return_type("JSON_STRING") == dfu_common.return_type(return_from_chip_prog[1]):
        ret_str += return_from_chip_prog[2]+"\r\n"
    elif dfu_common.return_type("JSON_BOOLEAN") == dfu_common.return_type(return_from_chip_prog[1]):
        ret_str += "0x%x"%return_from_chip_prog[2]+"\r\n"
    elif dfu_common.return_type("JSON_INTEGER") == dfu_common.return_type(return_from_chip_prog[1]):
        ret_str += "0x%x"%return_from_chip_prog[2]+"\r\n"
    elif dfu_common.return_type("JSON_REAL") == dfu_common.return_type(return_from_chip_prog[1]):
        ret_str += str(return_from_chip_prog[2])+"\r\n"
    elif dfu_common.return_type("JSON_ARRAY") == dfu_common.return_type(return_from_chip_prog[1]):
        idgroup = ""
        for val in return_from_chip_prog[2]:
            # #pring("0x%x"%(val))
            idgroup += "0x%x"%(val)
            idgroup += ","
        ret_str += idgroup[:len(idgroup)-1]+".\r\n"
    elif dfu_common.return_type("NULL") == dfu_common.return_type(return_from_chip_prog[1]):
        ret_str += str(return_from_chip_prog[2])
    else:
        ret_str += "not this return type.\r\n"
    return ret_str


class Programmer():
    def __init__(self,dfu_rpc_node):
        self.prog_instance = None
        self.dfu_rpc_node = dfu_rpc_node
        self.target_address = 0
        self.arch_type = ""
        pass
        
    def list_support_target(self):
        support_chip_architecture = ""
        arch_type = dfu_common.get_chip_arch_type_support(self.dfu_rpc_node)
        for arch_keys in arch_type.keys():
            support_chip_architecture += arch_keys+":"
            chip_type = dfu_common.get_chip_type_support(self.dfu_rpc_node,arch_type[arch_keys])
            for chip_keys in chip_type.keys():
                support_chip_architecture += chip_keys+" "
            support_chip_architecture += "\r\n"
            pass
        #pring(support_chip_architecture)
        return True,support_chip_architecture
        
    def create_target(self,dev_path,what_chip,frequency_hz,sub_type = None):
        ret_str = "\r\n------------------------------------\r\n"
        ret_str += "Operating "
        #traverse
        arch_type = dfu_common.get_chip_arch_type_support(self.dfu_rpc_node)
        for arch_keys in arch_type.keys():
            chip_type = dfu_common.get_chip_type_support(self.dfu_rpc_node,arch_type[arch_keys]) 
            if what_chip in chip_type.keys():
                if arch_keys == "stm32":
                    self.target_address = 0x08000000
                    self.prog_instance = Stm32Prog(self.dfu_rpc_node)
                    # self.prog_instance = Stm32L4xxProg(self.dfu_rpc_node)
                elif arch_keys == "cortexm":
                    self.target_address = 0x00000000
                    if sub_type == "hearst":
                        self.prog_instance = HearstProg(self.dfu_rpc_node)
                    else:
                        self.prog_instance = CortexMProg(self.dfu_rpc_node)
                    
                elif arch_keys == "psoc4":
                    self.target_address = 0x00000000
                    self.prog_instance = Psoc4Prog(self.dfu_rpc_node)
                elif arch_keys == "nrf5xble":
                    self.target_address = 0x00000000
                    self.prog_instance = Nrf5XProg(self.dfu_rpc_node)
                elif arch_keys == "spiflash":
                    self.arch_type = "spiflash"
                    self.target_address = 0x00000000
                    self.prog_instance = SpiFlash(self.dfu_rpc_node)
                else:
                    ret_str += "error ,do not support this device ."
                    return False,ret_str
                ret_str += arch_keys+":"+what_chip+"........\r\n"
                break
        if what_chip not in chip_type.keys():
            ret_str += "error ,do not support this device .\r\n"
            return False,ret_str
            
        
        #create instance
        ret_str += "create target.....\r\n"
        ret = self.prog_instance.create_instance(dev_path,what_chip)#[0] true/false,[1] type,[2] return
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str

        #instance initial
        ret = self.prog_instance.instance_initial(frequency_hz)
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str

        return True,ret_str
    
    def __target_erase_all(self):
        ret_str = "erasing target ....\r\n"
        ret = self.prog_instance.dut_storage_erase_all()
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret_str += "erasing target successfully\r\n"
        return True,ret_str
    
    def __target_programming_only(self,target_file_name,size,target_address = None,file_offset = 0):        
        if target_address == None:
            target_address = self.target_address
        ret_str = "programming target .........\r\n"
        ret = self.prog_instance.dut_storage_infusing(target_file_name,target_address,file_offset,size)
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret_str += "programming target successfully\r\n"
        return True,ret_str
    
    def __target_checkout(self,target_file_name,size,target_address = None,file_offset = 0):
        if target_address == None:
            target_address = self.target_address
        ret_str = "verify target .........\r\n"
        ret = self.prog_instance.dut_storage_checkout(target_file_name,target_address,file_offset,size)
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret_str += "verify target successfully\r\n"
        return True,ret_str
    
    def __target_initial(self):
        ret_str = "initial target ....\r\n"
        ret = self.prog_instance.dut_initial()
        ret_str += _return_to_str(ret)
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
    
    def target_initial(self):
        ret_str = ""
        ret = self.__target_initial()
        ret_str += ret[1]
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
    
    def target_erase_all(self):
        ret_str = ""
        ret = self.__target_initial()
        ret_str += ret[1]
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str

        ret = self.__target_erase_all()
        ret_str += ret[1]
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str

        return True,ret_str
        
    def target_programming(self,target_file_name,size,target_address = None,file_offset = 0):
        if target_address == None:
            target_address = self.target_address
        ret_str = "target file is "+target_file_name+".\r\n"
        ret_str += "target address is "+str(target_address)+".\r\n"
        ret_str += "load file address is "+str(file_offset)+".\r\n"
        ret_str += "load size is %d"%(size)+".\r\n"
        
        ret = self.__target_initial()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.__target_erase_all()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.__target_programming_only(target_file_name,size,target_address,file_offset)
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.__target_checkout(target_file_name,size,target_address,file_offset)
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
            
    def target_programming_only(self,target_file_name,size,target_address = None,file_offset = 0):
        if target_address == None:
            target_address = self.target_address
        ret_str = "target file is "+target_file_name+".\r\n"
        ret_str += "target address is "+str(target_address)+".\r\n"
        ret_str += "load file address is "+str(file_offset)+".\r\n"
        ret_str += "load size is %d"%(size)+".\r\n"
        
        ret = self.__target_initial()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.__target_programming_only(target_file_name,size,target_address,file_offset)
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        if self.arch_type != "spiflash":
            ret = self.__target_checkout(target_file_name,size,target_address,file_offset)
            ret_str += ret[1] 
            if ret[0] == False:
                self.destroy_target()
                return False,ret_str
        else:
            ret_str += "verify target .........\r\n"
            ret_str += "verify target successfully\r\n"
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
        
    def target_checkout(self,target_file_name,size,target_address = None,file_offset = 0):
        if target_address == None:
            target_address = self.target_address
        ret_str = "target file is "+target_file_name+".\r\n"
        ret_str += "target address is "+str(target_address)+".\r\n"
        ret_str += "load file address is "+str(file_offset)+".\r\n"
        ret_str += "load size is %d"%(size)+".\r\n"
                
        ret = self.__target_initial()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.__target_checkout(target_file_name,size,target_address,file_offset)
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.release_target()
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
    
    def read_target_storage(self,target_file_name,read_size,target_address):

        ret_str = "target file is "+target_file_name+".\r\n"
        ret_str += "target address is "+str(target_address)+".\r\n"
        ret_str += "load size is %d"%(size)+".\r\n"
        ret = self.__target_initial()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        
        ret_str += "roading target .........\r\n"        
        ret = self.prog_instance.dut_storage_reading(target_file_name,target_address,read_size)
        ret_str += _return_to_str(ret) 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret_str += "road target done\r\n"
        
        ret = self.release_target()
        ret_str += ret[1] 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        return True,ret_str
        
    def release_target(self):
        ret_str = "release target\r\n"
        ret = self.prog_instance.dut_exit()
        ret_str += _return_to_str(ret) 
        if ret[0] == False:
            self.destroy_target()
            return False,ret_str
        ret_str += "finish target release\r\n"
        return True,ret_str
    
    def destroy_target(self):
        ret_str = "destruct ......\r\n"
        ret = self.prog_instance.destroy_instance()
        if ret[0] == False:
            ret_str += "target destroy error"
            return False,ret_str
        ret_str = "instance destruct ."
        return True,ret_str #ret[1]





