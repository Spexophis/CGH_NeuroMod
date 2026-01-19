# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import ctypes
from ctypes import c_int32, c_uint8, c_uint32, c_double, c_char, POINTER, create_string_buffer

from cgh_neuromod import logger


class HamamatsuSLM:

    def __init__(self, lib_path=None, logg=None):
        self.logg = logg or logger.setup_logging()
        if lib_path is not None:
            self.lib = ctypes.CDLL(lib_path)
            self._bind_functions()
        else:
            self.logg.error("No lib path specified")

    def _bind_functions(self):
        # Open_Dev
        self.lib.Open_Dev.argtypes = [POINTER(c_uint8), c_int32]
        self.lib.Open_Dev.restype = c_int32

        # Close_Dev
        self.lib.Close_Dev.argtypes = [POINTER(c_uint8), c_int32]
        self.lib.Close_Dev.restype = c_int32

        # Check_HeadSerial
        self.lib.Check_HeadSerial.argtypes = [c_uint8, POINTER(c_char), c_int32]
        self.lib.Check_HeadSerial.restype = c_int32

        # Write_FMemArray
        self.lib.Write_FMemArray.argtypes = [
            c_uint8, POINTER(c_uint8), c_int32, c_uint32, c_uint32, c_uint32
        ]
        self.lib.Write_FMemArray.restype = c_int32

        # Check_Temp
        self.lib.Check_Temp.argtypes = [c_uint8, POINTER(c_double), POINTER(c_double)]
        self.lib.Check_Temp.restype = c_int32

        # Mode_Select
        self.lib.Mode_Select.argtypes = [c_uint8, c_uint8]
        self.lib.Mode_Select.restype = c_int32

        # Mode_Check
        self.lib.Mode_Check.argtypes = [c_uint8, POINTER(c_uint32)]
        self.lib.Mode_Check.restype = c_int32

    def open(self, bid_list):
        size = len(bid_list)
        arr = (c_uint8 * size)(*bid_list)
        return self.lib.Open_Dev(arr, size)

    def close(self, bid_list):
        size = len(bid_list)
        arr = (c_uint8 * size)(*bid_list)
        return self.lib.Close_Dev(arr, size) == 1

    def get_serial(self, bid, char_size=11):
        buf = create_string_buffer(char_size)
        result = self.lib.Check_HeadSerial(bid, buf, char_size)
        if result == 1:
            return buf.value.decode("ascii", errors="ignore")
        return None

    def write_fmem_array(self, bid, array, xpix=1272, ypix=1024, slot_no=0):
        array_size = xpix * ypix
        if len(array) != array_size:
            raise ValueError(
                f"Array length {len(array)} does not match expected size {array_size} ({xpix}x{ypix})"
            )
        c_array = (c_uint8 * array_size)(*array)
        result = self.lib.Write_FMemArray(bid, c_array, array_size, xpix, ypix, slot_no)
        return result == 1

    def check_temp(self, bid):
        head_temp = c_double()
        cb_temp = c_double()
        result = self.lib.Check_Temp(bid, ctypes.byref(head_temp), ctypes.byref(cb_temp))
        if result == 1:
            return head_temp.value, cb_temp.value
        return None

    def mode_select(self, bid, mode):
        """
        Set operation mode.

        Parameters
        ----------
        bid : int
        mode : int (0 = DVI, 1 = USB/Trigger)

        Returns
        -------
        bool
        """
        result = self.lib.Mode_Select(bid, mode)
        return result == 1

    def mode_check(self, bid):
        """
        Get current operation mode.

        Returns
        -------
        int or None
            0 = DVI, 1 = USB/Trigger, None = failed
        """
        mode = c_uint32()
        result = self.lib.Mode_Check(bid, ctypes.byref(mode))
        if result == 1:
            return mode.value
        return None
