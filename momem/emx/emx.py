"""
===
EMX
===
Simulation interface package for EMX EM-field
simulator for TheSyDeKick.

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
    def layermappath(self):
        ''' 
        String

        Name of the PDK technology library used for the designs. 
        Defaults to environment variable os.environ["LAYERMAP_PATH"].
        '''
        if not hasattr(self,'_layermappath'):
            self._layermappath=f'{os.environ["LAYERMAP_PATH"]}'
        return self._layermappath
    @layermappath.setter
    def layermappath(self,value):
        self._layermappath=value


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
            self._gdscmd=f'cd {os.environ["VIRTUOSO_DIR"]} && strmout -library {self.parent.libname} -strmFile {self.parent.momemsimpath}/{self.parent.result_filenames}.gds \
                    -rundir {os.environ["VIRTUOSO_DIR"]} -topCell {self.parent.cellname} -view layout -techLib {self.techlib} -layermap {self.layermappath} \
                    -logFile {self.parent.momemsimpath}/strmOut.log -summaryFile {self.parent.momemsimpath}/gds_summary.log -verbose -pinAttNum {self.pin_attribute_num}'
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
        for sim, val in self.parent.simcmd_bundle.Members.items():
            self._emxcmd=f'emx {self.parent.momemsimpath}/{self.parent.result_filenames}.gds {self.parent.cellname} {self.processpath} --discrete-frequency=0 --discrete-frequency=1e3 --discrete-frequency=1e6 --accuracy=high --edge-width={val.edge_width} --thickness={val.thickness} --via-separation={val.via_separation} --simultaneous-frequencies={val.simultaneous_frequencies} --parallel={val.parallel} --label-depth={val.label_depth}'        
            if val.quasistatic:
                self._emxcmd+=' --quasistatic'
            else:
                self._emxcmd+=' --full-wave'
            if val.recommended_memory:
                self._emxcmd+=' --recommended-memory'
            if val.sim=='sweep':
                if len(val.swpvalues)==0 and any((val.swpstart==None,
                    val.swpstop==None,val.swpstep==None)):
                    self.print_log(type='F',
                            msg=f"Sweep start/stop/step OR sweep values not given to momem_simcmd. Fix and run again.")
                elif len(val.swpvalues)>0:
                    for value in val.swpvalues:
                        self._emxcmd+=f' {value}'
                else:
                    self._emxcmd+=f' --sweep {val.swpstart} {val.swpstop} --sweep-stepsize={val.swpstep}'
            else:
                self.print_log(type='F',
                        msg=f"Invalid simulation type for momem")
            self._emxcmd+=f' --s-impedance={val.impedance} --touchstone --s-file={self.parent.momemsimpath}/{self.parent.result_filenames}.s%np' 
            if len(val.port_map)>0:
                for value in val.port_map:
                    self._emxcmd+=f' -p {value[0]}={value[1]}'
                    self._emxcmd+=f' -i {value[0]}'
            else:
                self.print_log(type='W',
                        msg="Port mapping not given. Are you sure oyu know how your ports are mapped now?")
            if len(val.exclude_ports)>0:
                for value in val.exclude_ports:
                    self._emxcmd+=f' --exclude {value}'
            if len(val.multid_metals)>0:
                self._emxcmd+=f' --3d='
                for value in val.multid_metals:
                    if value==val.multid_metals[-1]:
                        self._emxcmd+=f'{value}'
                    else:
                        self._emxcmd+=f'{value},'
            else:
                self._emxcmd+=f' --3d=*'
            if len(val.surface_metals)>0:
                self._emxcmd+=f' --surface='
                for value in val.surface_metals:
                    if value==val.surface_metals[-1]:
                        self._emxcmd+=f'{value}'
                    else:
                        self._emxcmd+=f'{value},'
            self._emxcmd+=f' --cadence-pins={self.pin_attribute_num} --log-file={self.parent.momemsimpath}/{self.parent.result_filenames}.log --print-command-line --verbose=1'
        return self._emxcmd

    def check_environment_variables(self):
        ''' 
        List of all required environment variables. Will raise a KeyError
        if some of them do not exist.

        
        VIRTUOSO_DIR is the path to your virtuoso directory
        TECHLIB is the name of your technology library
        EMX_PROC is path to your process .proc file for EMX
        LAYERMAP_PATH is the path to your PDK layer map.
        '''
        env_vars=[os.environ['VIRTUOSO_DIR'],
                os.environ["EMX_PROC"],
                os.environ["TECHLIB"],
                os.environ["LAYERMAP_PATH"],
                ]

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
                    msg="Running simulation failed.")

    def run(self):
        """Externally called function to generate a gds and 
        execute emx simulation."""
        self.check_environment_variables()
        self.generate_gds()
        self.execute_emx_simulation()
