"""
===
EMX
===
EMX simulation interface package for Spectre for TheSyDeKick.

Initially written by Veeti Lahtinen, 2024

"""
import os
import sys
from abc import * 
from thesdk import *

import numpy as np
import subprocess
from datetime import datetime
import shutil

class emx(thesdk):
    """This class is used as instance in momem_simulatormodule property of 
    spice class. Contains simulator dependent definitions.

    Parameters
    ----------
    parent: object, None (mandatory to define). TheSyDeKick parent entity object for this simulator class.

    **kwargs :
       None

    
    """
    def __init__(self, parent=None,**kwargs):
        if parent==None:
            self.print_log(type='F', msg="Parent of simulator module not given")
        else:
            self.parent=parent

    @property 
    def processpath(self):
        ''' 
        String

        Path to the PDK .proc file. Defaults to os.environt["EMX_PROC"], which
        has to be set externally.
        '''
        if not hasattr(self,'_processpath'):
            self._processpath=f'{os.environ["EMX_PROC"]}'
        return self._processpath
    @processpath.setter
    def processpath(self,value):
        self._processpath=value
 
    @property 
    def techlib(self):
        ''' 
        String

        Name of the PDK technology library used for the designs. 
        Defaults to environment variable os.environ["TECHLIB"].
        '''
        if not hasattr(self,'_techlib'):
            self._techlib=f'{os.environ["TECHLIB"]}'
        return self._techlib
    @techlib.setter
    def techlib(self,value):
        self._techlib=value
 
    @property 
    def layermapppath(self):
        ''' 
        String

        Name of the PDK technology library used for the designs. 
        Defaults to environment variable os.environ["LAYERMAP_PATH"].
        '''
        if not hasattr(self,'_layermapppath'):
            self._layermapppath=f'{os.environ["LAYERMAP_PATH"]}'
        return self._layermapppath
    @layermapppath.setter
    def layermapppath(self,value):
        self._layermapppath=value


    @property
    def pin_attribute_num(self):
        '''
        Pin attribute number for the GDS and simulation. Has to be the same
        for the gds and the simulation. 
        '''
        if not hasattr(self,'_pin_attribute_num'):
            self._pin_attribute_num=2
        return self._pin_attribute_num

    @property
    def gdscmd(self):
        '''
        GDS extraction command (used for simulating the design). 

        Can not be set externally, and parsed from other variables:
        libname, cellname, techlib, layermappath, pin_attribute_num
        '''
        if not hasattr(self,'_gdscmd'):
            self._gdscmd=f'cd {os.environ["VIRTUOSO_DIR"]} && strmout -library {self.libname} -strmFile {self.momemsimpath}/{self.result_filenames}.gds \
                    -rundir {os.environ["VIRTUOSO_DIR"]} -topCell {self.cellname} -view layout -techLib {self.techlib} -layermap {self.layermappath} \
                    -logFile {self.momemsimpath}/strmOut.log -summaryFile {self.momemsimpath}/gds_summary.log -verbose -pinAttNum {self.pin_attribute_num}'
        return self._gdscmd

    def generate_gds(self):
        ''' 
        Method to generate the GDS file.
        '''
        self.print_log(type='I',
                msg=f"Running external command {self.gdscmd}")
        subprocess.check_output(self.gdscmd,shell=True)

       
    @property
    def emxcmd(self):
        """String

        Simulation command string to be executed on the command line.
        Automatically generated.
        """
        for sim, val in self.simcmds.Members.items():
            self._emxcmd=f'emx {self.parent.momemsimpath}/{self.parent.result_filenames}.gds \
                    {self.parent.cellname} {self.processpath} --discrete-frequency=0 \
                    --discrete-frequency=1e3 --discrete-frequency=1e6 --accuracy=high \
                    --edge-width={self.edge_width} --thickness={self.thickness} --via-separation={self.via_separation} \
                    --simultaneous-frequencies={self.simultaneous_frequencies} --parallel={self.parallel} --label-depth={self.label_depth}'        
            if self.quasistatic:
                self._emxcmd+=' --quasistatic'
            else:
                self._emxcmd+=' --full-wave'
            if self.recommended_memory:
                self._emxcmd+=' --recommended-memory'
            if self.sim=='sweep':
                if len(self.swpvalues)==0 and any((self.swpstart==None,
                    self.swpstop==None,self.swpstep==None)):
                    self.print_log(type='F',
                            msg=f"Sweep start/stop/step OR sweep values not given to momem_simcmd. Fix and run again.")
                elif len(self.swpvalues)>0:
                    for val in self.swpvalues:
                        self._emxcmd+=f' {val}'
                else:
                    self._emxcmd+=f' --sweep {self.swpstart} {self.swpstop} --sweep-stepsize={self.swpstep}'
            else:
                self.print_log(type='F',
                        msg=f"Invalid simulation type for momem")
            self._emxcmd+=f' --s-impedance={self.impedance} --touchstone --s-file={self.parent.momemsimpath}/{self.result_filenames}.s%np' 
            if len(self.port_map)>0:
                for val in self.port_map:
                    self._emxcmd+=f' -p {val[0]}={val[1]}'
                    self._emxcmd+=f' -i {val[0]}'
            else:
                self.print_log(type='W',
                        msg="Port mapping not given. Are you sure oyu know how your ports are mapped now?")
            if len(self.exclude_ports)>0:
                for val in self.exclude_ports:
                    self._emxcmd+=f' --exclude {val}'
            if len(multid_metals)>0:
                self._emxcmd+=f' --3d='
                for val in self.multid_metals:
                    if val==self.multid_metals[-1]:
                        self._emxcmd+=f'{val}'
                    else:
                        self._emxcmd+=f'{val},'
            else:
                self._emxcmd+=f' --3d=*'
            if len(self.surface_metals)>0:
                self._emxcmd+=f' --surface='
                for val in self.surface_metals:
                    if val==self.surface_metals[-1]:
                        self._emxcmd+=f'{val}'
                    else:
                        self._emxcmd+=f'{val},'
            self._emxcmd+=f' --cadence-pins={self.pin_attribute_num} --log-file={self.parent.momemsimpath}/{self.parent.result_filenames}.log --print-command-line --verbose=1'
        return self._emxcmd

    def execute_emx_simulation(self):
        """Externally called function to execute emx simulation."""
        try:
            self.print_log(type='I',
                    msg=f"Running external command {self.emxcmd}")
            subprocess.check_output(self.emxcmd,shell=True)
        except:
            self.print_log(type='E',
                    msg=traceback.format_exc())
            self.print_log(type='F',
                    msg="Running simulation failed. Have you defined momemsimcmd?")



    def run(self):
        """Externally called function to generate a gds and 
        execute emx simulation."""
        self.generate_gds()
        self.execute_emx_sim()
