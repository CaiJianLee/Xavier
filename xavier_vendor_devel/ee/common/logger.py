import logging
import logging.handlers
import os
import sys
import random
import time
import inspect
import datetime
import re
import threading
import fcntl
import select
import ctypes
from functools import wraps
from ee.common import utility

mutex = threading.Lock()
libsys = ctypes.CDLL("libc.so.6")
READ_ONLY = (select.EPOLLIN | select.EPOLLHUP | select.EPOLLPRI | select.EPOLLERR)
READ_WRITE = (READ_ONLY | select.EPOLLOUT)

(r,w) = os.pipe()
pipe_w = os.fdopen(w, "w")
pipe_r = os.fdopen(r, "r")

MAX_SIZE = 1024 * 1024 * 10

CRITICAL = logging.CRITICAL
ERROR    = logging.ERROR
WARNING  = logging.WARNING
INFO     = logging.INFO
DEBUG    = logging.DEBUG
NOTSET   = logging.NOTSET

loc_lev = {'CRITICAL':CRITICAL, 'ERROR':ERROR, 'WARNING':WARNING, 'INFO':INFO, 'DEBUG':DEBUG}
thread_local = threading.local()
log_object = {}

class ScreenPrintLog(threading.Thread):
    def __init__(self, file_name):
        super(ScreenPrintLog, self).__init__()
        self.file_name = file_name
        self.local_name = (file_name.split(".log")[0]).upper()

    def run(self):
        thread_local.file = self.file_name
        thread_local.name = self.local_name
        epoll = select.epoll()
        epoll.register(pipe_r.fileno(), READ_ONLY)
        while True:
            try:
                events = epoll.poll()
            except IOError:
                continue
            for fileno, event in events:
                try:
                    if (event & (select.POLLIN | select.POLLPRI)) :
                        self._screen_log()
                except Exception as e:
                    pass
        return True

    def _screen_log(self):
        while True:
            try:
                log_str = pipe_r.readline().strip()
                if log_str:
                    warning(log_str)
            except Exception:
                break
            log_str = ""
        return None


class SmartGiantLog():
    def __init__(self, file_name):
        self.file = file_name
        self.name = (file_name.split(".log")[0]).upper()
        self.logger = None
        self.local_level = None
        self.local_env = None
        self.log_path = None
        self.log_server = None
        self.log_count = None
        self.handle = None

    def create_log_handle(self):
        self.logger = logging.getLogger(self.name)
        format = logging.Formatter('%(asctime)-12s%(message)s', '[%Y-%m-%d %H:%M:%S]',)

        self.log_path = utility.get_log_path()
        if (False == os.path.exists(self.log_path)):
            os.system("mkdir %s -p >/dev/null"%(self.log_path))

        self.log_count = self._get_log_count(self.file)
        self.handle = logging.handlers.RotatingFileHandler("%s/%s"%(self.log_path, self.file), maxBytes = MAX_SIZE, backupCount = 10)
        self.handle.setFormatter(format)
        self.handle.setLevel(NOTSET)
        self.logger.addHandler(self.handle)
        self.local_level = WARNING
        self.logger.setLevel(self.local_level)
        self.local_env = "XAVIER_LOG_" + self.name
        self.log_server = ScreenPrintLog(self.file)
        self.log_server.setDaemon(True)
        self.log_server.start()

    def reset_log_handle(self):
        self.logger.removeHandler(self.handle)
        format = logging.Formatter('%(asctime)-12s%(message)s', '[%Y-%m-%d %H:%M:%S]',)
        self.handle = logging.FileHandler("%s/%s"%(self.log_path, self.file))
        self.handle.setFormatter(format)
        self.handle.setLevel(NOTSET)
        self.logger.addHandler(self.handle)

    def _dump_log(self):
        file = "%s/%s.10"%(self.log_path, self.file)
        if False == os.path.exists(file):
            return None
        back_path = self.log_path + "/back"
        if False == os.path.exists(back_path):
            os.system("mkdir %s -p >/dev/null"%(back_path))
        if self.log_count > 9:
            self.log_count = 0
        back_file = "%s/%s.*"%(back_path, self.file)
        tar_name = "%s/%s%02d.tar.gz"%(back_path, self.name.lower(), self.log_count)
        os.system("rm -f %s >/dev/null"%(back_file))
        os.system("rm -f %s >/dev/null"%(tar_name))
        os.system("mv %s/%s.* %s/ >/dev/null"%(self.log_path, self.file, back_path))
        os.system("tar -cvzf %s %s/%s.*>/dev/null"%(tar_name, back_path, self.file))
        os.system("rm -f %s >/dev/null"%(back_file))
        self.log_count += 1
        return None

    def _get_env_value(self):
        try:
            return (os.environ.get(self.local_env)).upper()
        except Exception:
            return ""

    def _get_log_level(self, env_value):
        for i in range(0, len(env_value)):
            try:
                return loc_lev[env_value[i]]
            except Exception:
                pass
        return self.local_level

    def set_path(self, path):
        if False == os.path.exists(path):
            os.system("mkdir %s -p >/dev/null"%(path))
        self.log_path = path
        self.reset_log_handle()

    def _get_log_count(self, file_name):
        last_time = 0
        last_count = 0
        back_path = self.log_path + "/back"
        if False == os.path.exists(back_path):
            os.system("mkdir %s -p >/dev/null"%(back_path))
            return 0

        for i in range(0, 10):
            name = ("%s/%s%02d.tar.gz"%(back_path, self.name.lower(), i))
            if False == os.path.exists(name):
                return i
            _time = os.path.getmtime(name)
            if last_time < _time:
                last_time = _time
                last_count = i
        return last_count + 1


def print_log_decorator(fn):
    @wraps(fn)
    def wraps_wrapper(msg, *args, **kwargs):
        try:
            value = log_object[thread_local.name]._get_env_value()
            if value:
                env_value = value.split(":")
                now_level = log_object[thread_local.name]._get_log_level(env_value)
                if log_object[thread_local.name].local_level != now_level:
                    log_object[thread_local.name].logger.setLevel(now_level)
                if ("TRACE" in env_value):
                    frame = sys._getframe(1)
                    fn(str(frame.f_code))
            result = fn(msg, *args, **kwargs)
            log_object[thread_local.name]._dump_log()
            return result
        except Exception as e:
            pass

    return wraps_wrapper

def init(file_name):
    thread_local.name = (file_name.split(".log")[0]).upper()
    mutex.acquire(1)
    try:
        type(log_object[thread_local.name])
        mutex.release()
        return None
    except Exception:
        pass
    try:
        log_object[thread_local.name] = SmartGiantLog(file_name)
    except Exception as e:
        mutex.release()
        return
    mutex.release()
    log_object[thread_local.name].create_log_handle()
    return None

@print_log_decorator
def boot(msg, *args, **kwargs):
    try:
        msg = "[LWP:%d]"%(libsys.syscall(224)) + "[BOOT ]" + str(msg)
        log_object[thread_local.name].logger.critical(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

@print_log_decorator
def info(msg, *args, **kwargs):
    try:
        msg = "[LWP:%d]"%(libsys.syscall(224)) + "[INFO ]" + str(msg)
        log_object[thread_local.name].logger.info(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

@print_log_decorator
def warning(msg, *args, **kwargs):
    try:
        msg = "[LWP:%d]"%(libsys.syscall(224)) + "[WARN ]" + str(msg)
        log_object[thread_local.name].logger.warning(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

@print_log_decorator
def error(msg, *args, **kwargs):
    try:
        msg = "[LWP:%d]"%(libsys.syscall(224)) + "[ERROR]" + str(msg)
        log_object[thread_local.name].logger.error(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

@print_log_decorator
def critical(msg, *args, **kwargs):
    try:
        msg =  "[LWP:%d]"%(libsys.syscall(224)) + str(msg)
        log_object[thread_local.name].logger.critical(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

@print_log_decorator
def debug(msg, *args, **kwargs):
    try:
        msg = "[LWP:%d]"%(libsys.syscall(224)) + "[DEBUG]" + str(msg)
        log_object[thread_local.name].logger.debug(msg, *args, **kwargs)
    except Exception as e:
        pass
    return None

def setLevel(level):
    try:
        if (True == isinstance(level, int)):
            log_object[thread_local.name].local_level = level
        else:
            log_object[thread_local.name].local_level = loc_lev[level.upper()]
        log_object[thread_local.name].logger.setLevel(log_object[thread_local.name].local_level)
    except Exception:
            pass
    return None

def setLogPath(path):
    if (True == isinstance(path, str)):
        try:
            log_object[thread_local.name].set_path(path)
        except Exception:
            pass

def print_list2hex(data):
    if isinstance(data, list):
        out_data = '['
        for x in data:
            if isinstance(x, int):
                out_data += '%#x, '%x
            elif isinstance(x, list):
                out_data += '%s, '%print_list2hex(x)
            else:
                out_data += '%s, '%x
        out_data = out_data[:-2] + ']'
    else:
        out_data = data
    return out_data