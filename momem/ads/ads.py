"""
===
ADS
===
ADS simulation interface package for Spectre for TheSyDeKick.

Initially written by Veeti Lahtinen and Kaisa Ryynänen, 2021

"""
import os
import sys
from abc import * 
from thesdk import *
from momem.ads.citi_to_touchstone import citi_to_touchstone as ctt

import numpy as np
import subprocess
from datetime import datetime
import shutil

class ads(thesdk):
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
    def emsetupsrcpath(self):
        """String

        Path to the emSetup source of the virtuoso entity ('VIRTUOSO_DIR/<libname>/<name>/emSetup').

        ADS specific parameter
        """
        if not hasattr(self,'_emsetupsrcpath'):
            self._emsetupsrcpath = self.sourcelibpath+'/'+self.parent.cellname+'/emSetup'
        return self._emsetupsrcpath 

    @property
    def sourcelibpath(self):
        """String

        Path to the virtuoso entity ('VIRTUOSO_DIR/<libname>').

        Not to be set externally.
        """
        if not hasattr(self,'_sourcelibpath'):
            self._sourcelibpath = os.environ['VIRTUOSO_DIR']+'/'+self.parent.libname
        return self._sourcelibpath


    @property
    def aelpath(self):
        """String

        Path to the AEL file that is used to create the 
        simulation input files. Can not be set extrenally.
        """
        if not hasattr(self,'_aelpath'):
            self._aelpath = self.parent.momemsimpath+'/init.ael'
        return self._aelpath

    @property
    def adscmd(self):
        """String

        Simulation command string to be executed on the command line.
        Automatically generated.
        """
        if not hasattr(self,'_adscmd'):
            adssimcmd = "adsMomWrapper -O -3D --objMode=RF proj proj"
            self._adscmd = f'cd {self.parent.momemsimpath} && {self.ads_submission} {adssimcmd}'
        return self._adscmd

    def set_simulation_options(self, **kwargs):
        """ Automatically called function to set the simulation settings

        When changing settings
        """
        for name, val in self.parent.simcmd_bundle.Members.items():
            if val.TL_mesh_cells > 0:
                # Enable TL mesh
                TL_mesh_enable = True
            else:
                TL_mesh_enable = False

            
            if len(val.swpvalues)>0:
                self.print_log(type='F',
                        msg=f"Sweep values not supported for ADS. Give sweepstop and step instead.")
            elif any((val.swpstop==None,val.swpstep==None)):
                self.print_log(type='F',
                        msg=f"Sweep stop and step values not given to momem_simcmd. Fix and run again.")
            stop_freq=val.swpstop
            step_freq=val.swpstep

            # Calculate number of simulation points
            freq_points = int(np.round(stop_freq / step_freq) + 1)

            if stop_freq != -1 and step_freq != -1:
                VIRTUOSO_DIR = os.environ["VIRTUOSO_DIR"]
                cmd=f'sed -i -e "s/22222/{stop_freq}/g" \
                        -e "s#1212#{step_freq}#g" \
                        -e "s#<ptsFreq>19</ptsFreq>#<ptsFreq>{freq_points}</ptsFreq>#g" \
                        -e "s#<EdgeMeshEnabled>True</EdgeMeshEnabled>#<EdgeMeshEnabled>{val.edge_mesh}</EdgeMeshEnabled>#g" \
                        -e "s#44444#{val.TL_mesh_cells}#g" \
                        -e "s#<TLMeshEnabled>True</TLMeshEnabled>#<TLMeshEnabled>{TL_mesh_enable}</TLMeshEnabled>#g" \
                        -e "s#33333#{val.mesh_cells}#g" \
                        -e "s#CELL_placeholder#{self.parent.cellname}#g" \
                        -e "s#WORKSPACE_placeholder_lib#{self.parent.libname}#g" \
                        -e "s#WORKSPACE_placeholder#{self.parent.momemsimpath}#g" \
                         "{self.emsetupsrcpath}/emStateFile.xml"'
                self.print_log(type='I', msg="Running external command %s" %(cmd) )
                subprocess.check_output(cmd,shell=True)


    def configure_environment(self):
        ''' 
        Create the files and configure the environment for the
        simulator. Implements the original functionality
        from the configure script of ads_template.
        '''
        link_oa_design_path=f'{self.parent.entitypath}/link_oa_design.sh'
        if not os.path.exists(link_oa_design_path):
            self.print_log(type='F',
                msg=f"You need link_oa_design script. See momem_template!")
        else:
            cmd=f'{link_oa_design_path} -l {os.environ["VIRTUOSO_DIR"]}/{self.parent.libname} -t {os.environ["ADSSUBSTRATEFILE"]} -w {self.parent.momemsimpath}'
            self.print_log(type='I', msg="Running external command %s" %(cmd) )
            subprocess.check_output(cmd,shell=True)
        if not os.path.exists(self.emsetupsrcpath):
            os.mkdir(self.emsetupsrcpath)
        master_tag_path=f'{self.emsetupsrcpath}/master.tag'
        self.print_log(type='I',
            msg=f"Creating {master_tag_path} file")
        if not os.path.exists(master_tag_path):
            with open(master_tag_path, 'w') as f:
                f.write("-- Master.tag File, Rev:1.0\n")
                f.write("eesof_em_setup.file")
        eesof_em_setup=f'{self.emsetupsrcpath}/eesof_em_setup.file'
        self.print_log(type='I',
            msg=f"Creating {eesof_em_setup} file")
        if not os.path.exists(eesof_em_setup):
            with open(eesof_em_setup, 'w') as f:
                f.write("# Ensuring Version Control does not get an empty file. #\n")
                f.write("# My magic number is 156.                              #")
        em_state_file_path=f'{self.emsetupsrcpath}/emStateFile.xml'
        self.print_log(type='I',
            msg=f"Copying {os.environ['EMSTATEFILE']} to {em_state_file_path}.")
        shutil.copy(os.environ["EMSTATEFILE"],em_state_file_path)
        ads_data_path=f'{self.parent.momemsimpath}/data'
        if not os.path.exists(ads_data_path):
            self.print_log(type='I',
                msg=f"Creating {ads_data_path} directory.")
            os.mkdir(ads_data_path)
        if not os.path.exists(self.aelpath):
            self.print_log(type='I',
                msg=f"Creating the AEL file to generate simulation input files to {self.aelpath}")
            with open(self.aelpath, 'w') as f:
                f.write('de_open_workspace("{self.parent.momemsimpath}"); // Open correct folder\n')
                f.write('dex_em_writeSimulationFiles("{self.parent.libname}","{self.parent.cellname}","emSetup","simulation"); // Generate simulation input files\n')
                f.write('de_exit(); // Close ADS\n')

    def check_environment_variables(self):
        ''' 
        List of all required environment variables. Will raise a KeyError
        if some of them do not exist.
        '''
        env_vars=[os.environ['VIRTUOSO_DIR'],
                os.environ["ADSSUBSTRATEFILE"],
                os.environ['EMSTATEFILE'],
                ]

    def generate_input_files(self):
        """ Automatically called function to generate the input/configuration files using AEL """
        if not os.path.exists(self.aelpath):
            self.print_log(type='E',msg=f'The {self.aelpath} file does not exist.')
        cmd = f'cd {self.parent.momemsimpath} && ads -nw -m init.ael' 
        self.print_log(type='I', msg="Running external command %s" %(cmd) )
        subprocess.check_output(cmd,shell=True)

    def execute_ads_sim(self):
        """Automatically called function to execute ADS momentum simulation."""
        self.print_log(type='I', msg="Running external command %s" %(self.adscmd) )
        os.system(self.adscmd)

    def run(self):
        """Externally called function to execute ads simulation."""
        self.check_environment_variables()
        self.configure_environment()
        self.set_simulation_options()
        self.generate_input_files()
        self.execute_ads_sim()
        self.converter = ctt()
        self.converter.input_file = f'{self.parent.momemsimpath}/proj.cti'
        self.converter.output_file = f'{self.parent.momemsimpath}/{self.parent.result_filename}'
        self.converter.generate_contents()
