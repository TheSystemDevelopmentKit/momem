"""
===================
ADS Interface class
===================

ADS Momentum simulation interface package for The System Development Kit 

Provides utilities to import ads modules to python environment and
automatically generate testbenches for the most common simulation cases.

Initially written by Veeti Lahtinen and Kaisa Ryynänen, 2021

"""

import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))

from thesdk import *
from ads.citi_to_touchstone import citi_to_touchstone as ctt

import numpy as np
import subprocess
from datetime import datetime
import shutil

class ads(thesdk,metaclass=abc.ABCMeta):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    #These need to be converted to abstact properties
    def __init__(self): 
        pass

    @property
    def name(self):
        """String

        Name of the module.
        """
        if not hasattr(self, '_name'):
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def sourcelib(self):
        '''String
        
        Sourcelib name. Currently defaults to nameofthemodule_generated, which is a BAG assumption

        Can (and should) be set externally, if the sourcelib name is different than <entityname>_generated.
        '''
        if not hasattr(self, '_sourcelib'):
            # TODO: make this non-BAG assumption
            # Bag assumption
            self._sourcelib = self.name+'_generated'
        return self._sourcelib
    @sourcelib.setter
    def sourcelib(self,value):
        self._sourcelib=value

    @property
    def sourcelibpath(self):
        """String

        Path to the virtuoso entity ('VIRTUOSO_DIR/<sourcelib>').
        """
        if not hasattr(self,'_sourcelibpath'):
            self._sourcelibpath = os.environ['VIRTUOSO_DIR']+'/'+self.sourcelib
        return self._sourcelibpath

    @property
    def emsetupsrcpath(self):
        """String

        Path to the emSetup source of the virtuoso entity ('VIRTUOSO_DIR/<sourcelib>/<name>/emSetup').
        """
        if not hasattr(self,'_emsetupsrcpath'):
            self._emsetupsrcpath = self.sourcelibpath+'/'+self.name+'/emSetup'
        return self._emsetupsrcpath 

    @property
    def preserve_adsfiles(self):  
        """True | False (default)

        If True, do not delete file IO files (proj) after simulations. Useful for
        debugging the file IO"""
        if hasattr(self,'_preserve_adsfiles'):
            return self._preserve_adsfiles
        else:
            self._preserve_adsfiles=False
        return self._preserve_adsfiles
    @preserve_adsfiles.setter
    def preserve_adsfiles(self,value):
        self._preserve_adsfiles=value

    @property
    def distributed_run(self):
        """ Boolean (default False)

            If True, distributes simulations 
            into the LSF cluster. The number of subprocesses launched is
            set by self.num_processes.
        """
        if hasattr(self, '_distributed_run'):
            return self._distributed_run
        else:
            self._distributed_run=False
        return self.distributed_run
    @distributed_run.setter
    def distributed_run(self, value):
        self._distributed_run=value

    @property
    def num_processes(self):
        """ integer

            Maximum number of spawned child processes for distributed runs.
        """
        if hasattr(self, '_num_processes'):
            return self._num_processes
        else:
            self._num_processes=10
        return self.num_processes
    @num_processes.setter
    def num_processes(self, value):
        self._num_processes=int(value)

    @property
    def interactive_ads(self):
        """ True | False (default)
        
        Launch simulator in interactive mode, which means that the simulation
        progress is displayed on the screen. """

        if hasattr(self,'_interactive_ads'):
            return self._interactive_ads
        else:
            self._interactive_ads=False
        return self._interactive_ads
    @interactive_ads.setter
    def interactive_ads(self,value):
        self._interactive_ads=value

    @property 
    def has_lsf(self):
        """
        Returs True if LSF submissions are properly defined. Default False
        """
        if ( not thesdk.GLOBALS['LSFINTERACTIVE'] == '' ) and (not thesdk.GLOBALS['LSFINTERACTIVE'] == ''):
            self._has_lsf = True
        else:
            self._has_lsf = False
        return self._has_lsf

    @property 
    def ads_submission(self):
        """
        Defines ads submission prefix from thesdk.GLOBALS['LSFSUBMISSION']
        for LSF submissions.

        Usually something like 'bsub -K' and 'bsub -I'.
        """
        if not hasattr(self, '_ads_submission'):
            try:
                if not self.has_lsf:
                    self.print_log(type='I', msg='LSF not configured. Running locally')
                    self._ads_submission=''
                else:
                    if self.interactive_ads:
                        if not self.distributed_run:
                            self._ads_submission = thesdk.GLOBALS['LSFINTERACTIVE'] + ' '
                        else: # Spectre LSF doesn't support interactive queues
                            self.print_log(type='W', msg='Cannot run in interactive mode if distributed mode is on!')
                            self._ads_submission = thesdk.GLOBALS['LSFSUBMISSION'] + ' -o %s/bsublog.txt ' % (self.adssimpath)
                    else:
                        self._ads_submission = thesdk.GLOBALS['LSFSUBMISSION'] + ' -o %s/bsublog.txt ' % (self.adssimpath)
            except:
                self.print_log(type='W',msg='Error while defining ads submission command. Running locally.')
                self._ads_submission=''

        return self._ads_submission
    @ads_submission.setter
    def ads_submission(self,value):
        self._ads_submission=value

    @property
    def adssrcpath(self):
        """String

        Path to the ads source of the entity ('./ads').
        """
        self._adssrcpath  =  self.entitypath + '/ads'
        if not (os.path.exists(self._adssrcpath)):
            self.print_log(type='E',msg='The %s source entity folder does not exist. Run configure!' % self._adssrcpath)
        return self._adssrcpath

    @property
    def adssrc(self):
        ''' String
        
        Path to the input/configuration files generated ('./ads/simulation')

        Automatically created by init.ael upon running the AEL program.
        '''
        if not hasattr(self, '_adssrc'):
            self._adssrc  =  self.entitypath + '/ads/simulation'
        return self._adssrc
    @adssrc.deleter
    def adssrc(self):
        if not self.preserve_adsfiles:
            try:
                shutil.rmtree(self.adssrc)
                self.print_log(type='I',msg='Removing %s.' % self.adssrc)
            except:
                self.print_log(type='W',msg='Could not remove %s.' % self.adssrc)

    @property
    def adssimpath(self):
        """String

        Simulation path. (./Simulations/adssim/<runname>)
        """
        self._adssimpath = self.entitypath+'/Simulations/adssim/'+self.runname
        try:
            if not (os.path.exists(self._adssimpath)):
                os.makedirs(self._adssimpath)
                self.print_log(type='I',msg='Creating %s.' % self._adssimpath)
        except:
            self.print_log(type='E',msg='Failed to create %s.' % self._adssimpath)
        return self._adssimpath

    @property
    def sparam_filename(self):
        '''String
        
        Changes the S-parameter output file name. Defaults to proj<i>, where i corresponds to
        the simulation repetition. E.g 0 -> first simulation, 1 -> 2nd. etc.

        Should be given without the file type extension, because touchstone .sNp format
        extension depends on the number of ports in the layout. This is automatically generated
        by citi_to_touchstone.
        '''
        if not hasattr(self, '_sparam_filename'):
            self._sparam_filename = 'proj0'
        return self._sparam_filename
    @sparam_filename.setter
    def sparam_filename(self,value):
        self._sparam_filename = value


    @property
    def adscmd(self):
        """String

        ADS Momentum simulation command string to be executed on the command line.
        Automatically generated.
        """
        #if not hasattr(self,'_adscmd'):
        adssimcmd = "adsMomWrapper -O -3D --objMode=RF proj proj"
        # Check if the filename already exists:
        # If it does, name the new generated file as proj<i>
        i = 0 
        files = os.listdir(self.adssimpath+'/')
        files_no_ext = [file.split('.')[0] for file in files]
        while self.sparam_filename in files_no_ext:
            self.sparam_filename = f'proj{i}'
            i+=1
        self._adscmd = f'cd {self.adssrc} && {self.ads_submission} {adssimcmd}'
        return self._adscmd
    # Just to give the freedom to set this if needed
    @adscmd.setter
    def adscmd(self,value):
        self._adscmd=value

    @property
    def runname(self):
        """String 
        
        Automatically generated name for the simulation. 
        
        Formatted as timestamp_randomtag, i.e. '20201002103638_tmpdbw11nr4'.
        Can be overridden by assigning self.runname = 'myname'."""
        if hasattr(self,'_runname'):
            return self._runname
        else:
            self._runname='%s_%s' % \
                    (datetime.now().strftime('%Y%m%d%H%M%S'),os.path.basename(tempfile.mkstemp()[1]))
        return self._runname
    @runname.setter
    def runname(self,value):
        self._runname=value

    @property
    def fstop(self):
        """ Integer or float

        Maximum frequency of the simulation. """

        if not hasattr(self, '_fstop'):
            self._fstop = -1
        return self._fstop
    @fstop.setter
    def fstop(self, value):
        self._fstop = value

    @property
    def fstep(self):
        """ Integer or float

        Frequency step for the simulation. """

        if not hasattr(self, '_fstep'):
            self._fstep = -1
        return self._fstep
    @fstep.setter
    def fstep(self, value):
        self._fstep = value

    @property
    def fstop_unit(self):
        """ String

        Frequency unit for fstop """

        if not hasattr(self, '_fstop_unit'):
            self._fstop_unit = "Hz"
        return self._fstop_unit
    @fstop_unit.setter
    def fstop_unit(self, value):
        self._fstop_unit = value

    @property
    def fstep_unit(self):
        """ String

        Frequency unit for fstep """

        if not hasattr(self, '_fstep_unit'):
            self._fstep_unit = "Hz"
        return self._fstep_unit
    @fstep_unit.setter
    def fstep_unit(self, value):
        self._fstep_unit = value

    @property
    def edge_mesh_enable(self):
        """ Boolean (True or False)

        Enables edge mesh """

        if not hasattr(self, '_edge_mesh_enable'):
            self._edge_mesh_enable = False
        return self._edge_mesh_enable
    @edge_mesh_enable.setter
    def edge_mesh_enable(self, value):
        self._edge_mesh_enable = value

    @property
    def mesh_cells(self):
        """ Integer

        Defines the mesh density. Cells per fstop wavelength """

        if not hasattr(self, '_mesh_cells'):
            self._mesh_cells = 20
        return self._mesh_cells
    @mesh_cells.setter
    def mesh_cells(self, value):
        self._mesh_cells = value

    @property
    def TL_mesh_cells(self):
        """ Integer

        Defines the transmission line mesh density. Cells per line width """

        if not hasattr(self, '_TL_mesh_cells'):
            self._TL_mesh_cells = 0
        return self._TL_mesh_cells
    @TL_mesh_cells.setter
    def TL_mesh_cells(self, value):
        self._TL_mesh_cells = value

    def set_simulation_options(self, **kwargs):
        """ Automatically called function to set the simulation settings

        When changing settings, always run ./configure first.
        """
        
        if self.TL_mesh_cells != 0:
            # Enable TL mesh
            TL_mesh_enable = True
        else:
            TL_mesh_enable = False

        stop_freq = self.fstop
        step_freq = self.fstep
        stop_freq_unit = self.fstop_unit.lower()
        if stop_freq_unit == 'khz':
            stop_freq = stop_freq * 10e+2
        elif stop_freq_unit == 'mhz':
            stop_freq = stop_freq * 10e+5
        elif stop_freq_unit == 'ghz':
            stop_freq = stop_freq * 10e+8
        
        step_freq_unit = self.fstep_unit.lower()
        if step_freq_unit == 'khz':
            step_freq = step_freq * 10e+2
        elif step_freq_unit == 'mhz':
            step_freq = step_freq * 10e+5
        elif step_freq_unit == 'ghz':
            step_freq = step_freq * 10e+8

        # Calculate number of simulation points
        freq_points = int(np.round(stop_freq / step_freq) + 1)

        if os.path.exists(self.emsetupsrcpath):
            if stop_freq != -1 and step_freq != -1:
                VIRTUOSO_DIR = os.environ["VIRTUOSO_DIR"]

                os.system(f'sed -i -e "s/22222/{stop_freq}/g" \
                -e "s#1212#{step_freq}#g" \
                -e "s#<ptsFreq>19</ptsFreq>#<ptsFreq>{freq_points}</ptsFreq>#g" \
                -e "s#<EdgeMeshEnabled>True</EdgeMeshEnabled>#<EdgeMeshEnabled>{self.edge_mesh_enable}</EdgeMeshEnabled>#g" \
                -e "s#44444#{self.TL_mesh_cells}#g" \
                -e "s#<TLMeshEnabled>True</TLMeshEnabled>#<TLMeshEnabled>{TL_mesh_enable}</TLMeshEnabled>#g" \
                -e "s#33333#{self.mesh_cells}#g" \
                 "{self.emsetupsrcpath}/emStateFile.xml"')
        else:
            self.print_log(type = "E", msg = f"{self.emsetupsrcpath} folder does not exist, run configure")


    def generate_input_files(self):
        """ Automatically called function to generate the input/configuration files using AEL """
        aelpath = self.adssrcpath+'/init.ael'
        if not os.path.exists(aelpath):
            self.print_log(type='E',msg=f'The {aelpath} file does not exist. Run configure!')
        cmd = f'cd {self.adssrcpath} && ads -nw -m init.ael' 
        self.print_log(type='I', msg="Running external command %s" %(cmd) )
        subprocess.check_output(cmd,shell=True)

    def execute_ads_sim(self):
        """Automatically called function to execute ADS momentum simulation."""
        self.print_log(type='I', msg="Running external command %s" %(self.adscmd) )
        os.system(self.adscmd)

    def run_ads(self):
        """Externally called function to execute ads simulation."""
        self.set_simulation_options()
        self.generate_input_files()
        self.execute_ads_sim()
        self.converter = ctt()
        self.converter.input_file = f'{self.adssrc}/proj.cti'
        self.converter.output_file = f'{self.adssimpath}/{self.sparam_filename}'
        self.converter.generate_contents()
        del self.adssrc
