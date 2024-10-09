"""
===============================================
Method of Momentum EM field simulator interface
===============================================

Method of Momemntum (MOM)simulation interface package for The System Development Kit 

Provides utilities to import EM field simulation  modules to python environment and
automatically generate testbenches for the most common simulation cases.

Initially written by Veeti Lahtinen and Kaisa Ryynänen, 2021

Notes for developers
--------------------

There are now two ways to provide simulator dependent structures that are
(most of the time) followed:

    1. Simulator dependent *properties* are defined in packages 
    <simulator>/<simulator>.py that are used as `momem_simulator` instance
    in this momem class inside *momem_simulator* property. Properties and 
    attributed of instance of *this class* (i.e. all TheSyDeKick Entitites)
    are made visible to momem_simulators through passing the *self* as *parent* 
    argument in instance creation. Properties defined inside 
    *momem_simulator* are accessed and set through corresponding properties of
    this class.

    2. This is an interface package, generic momem simulation 
    related methods should be provided in *momem_methods* module.


"""

import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))

from thesdk import *
from momem.ads.ads import ads
from momem.emx.emx import emx
from momem.momem_simcmd import momem_simcmd as momem_simcmd

import numpy as np
import subprocess
from datetime import datetime
import shutil
import skrf as rf

class momem(thesdk,metaclass=abc.ABCMeta):
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
    def libname(self):
        '''String
        
        Sourcelib name. Currently defaults to <entityname>

        Can (and should) be set externally, if the libname name is different than <entityname>.
        '''
        if not hasattr(self, '_libname'):
            self._libname = self.name
        return self._libname
    @libname.setter
    def libname(self,value):
        self._libname=value

    @property
    def cellname(self):
        '''String
        
        Top cell name that will be simulated.

        Can (and should) be set externally, 
        if the cellname name is different than <entityname>.
        '''
        if not hasattr(self, '_cellname'):
            self._cellname = self.name
        return self._cellname
    @cellname.setter
    def cellname(self,value):
        self._cellname=value

    @property
    def result_filenames(self):
        '''
        String

        Name of the files to be saved in to the simulation directory.

        Not to be set externally, and is tb_<name>
        '''
        if not hasattr(self,'_result_filenames'):
            self._result_filenames=f'tb_{self.name}'
        return self._result_filenames

    @property
    def preserve_momemfiles(self):  
        """True | False (default)

        If True, do not delete file IO files after simulations. Useful for
        debugging the file IO
        """
        if hasattr(self,'_preserve_momemfiles'):
            return self._preserve_momemfiles
        else:
            self._preserve_momemfiles=False
        return self._preserve_momemfiles
    @preserve_momemfiles.setter
    def preserve_momemfiles(self,value):
        self._preserve_momemfiles=value

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
    def interactive_momem(self):
        """ True | False (default)
        
        Launch simulator in interactive mode, which means that the simulation
        progress is displayed on the screen. """

        if hasattr(self,'_interactive_momem'):
            return self._interactive_momem
        else:
            self._interactive_momem=False
        return self._interactive_momem
    @interactive_momem.setter
    def interactive_momem(self,value):
        self._interactive_momem=value

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
    def momem_submission(self):
        """
        Defines momem submission prefix from thesdk.GLOBALS['LSFSUBMISSION']
        for LSF submissions.

        Usually something like 'bsub -K' and 'bsub -I'.
        """
        if not hasattr(self, '_momem_submission'):
            try:
                if not self.has_lsf:
                    self.print_log(type='I', msg='LSF not configured. Running locally')
                    self._momem_submission=''
                else:
                    if self.interactive_momem:
                        if not self.distributed_run:
                            self._momem_submission = thesdk.GLOBALS['LSFINTERACTIVE'] + ' '
                        else: # Spectre LSF doesn't support interactive queues
                            self.print_log(type='W', msg='Cannot run in interactive mode if distributed mode is on!')
                            self._momem_submission = thesdk.GLOBALS['LSFSUBMISSION'] + ' -o %s/bsublog.txt ' % (self.momemsimpath)
                    else:
                        self._momem_submission = thesdk.GLOBALS['LSFSUBMISSION'] + ' -o %s/bsublog.txt ' % (self.momemsimpath)
            except:
                self.print_log(type='W',msg='Error while defining momem submission command. Running locally.')
                self._momem_submission=''

        return self._momem_submission
    @momem_submission.setter
    def momem_submission(self,value):
        self._momem_submission=value

    @property
    def momemsrcpath(self):
        """String

        Path to the momem source of the entity ('./momem').
        """
        self._momemsrcpath  =  self.entitypath + '/momem'
        if not (os.path.exists(self._momemsrcpath)):
            self.print_log(type='E',msg='The %s source entity folder does not exist. Run configure!' % self._momemsrcpath)
        return self._momemsrcpath

    @property
    def momemsimpath(self):
        """String

        Simulation path. (self.simpath)
        """
        if not hasattr(self,'_momemsimpath'):
            self._momemsimpath = self.simpath
            if os.path.exists(self._momemsimpath):
                self.print_log(type='I',msg=f"Overwriting {self._momemsimpath}")
                targetpath=f'{self._momemsimpath}'
                self.print_log(type='I',
                        msg=f"Deleting {targetpath}")
                shutil.rmtree(targetpath)
            self.print_log(type="I",
                    msg=f"Creating {self._momemsimpath}")
            os.makedirs(self._momemsimpath)
        return self._momemsimpath

    def cleanup_momemsimpath(self):
        """ Method to clean up files from momemsimpath.

        Leaves just the S-parameter file
        """
        if os.path.exists(self.momemsimpath):
            self.print_log(type='I',
                    msg=f"Cleaning up {self.momemsimpath}")
            for target in os.listdir(self.momemsimpath):
                # If some regex guru wants to find a better method
                # please implement, do this for now.
                filename, file_extension = os.path.splitext(target)
                # Remove everything except the S-parameter file
                if not (file_extension[-1]=='p' and 's' in file_extension):
                    targetpath=f'{self.momemsimpath}/{target}'
                    self.print_log(type='I',msg=f"Deleting {targetpath}")
                    os.system(f'rm -f {targetpath}')

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
    def si_prefix_mult(self):
        """dict : Dictionary mapping SI-prefixes to multipliers.
        """
        if hasattr(self, '_si_prefix_mult'):
            return self._si_prefix_mult
        else:
            self._si_prefix_mult = {
                    'E':1e18,
                    'P':1e15,
                    'T':1e12,
                    'G':1e9,
                    'M':1e6,
                    'k':1e3,
                    'm':1e-3,
                    'u':1e-6,
                    'n':1e-9,
                    'p':1e-12,
                    'f':1e-15,
                    'a':1e-18,
                    }
        return self._si_prefix_mult
   
    @property
    def simcmd_bundle(self):
        """ Bundle : A thesdk.Bundle containing `momem_simcmd` objects. The `momem_simcmd`
        objects are automatically added to this Bundle, nothing should be
        manually added.

        """
        if not hasattr(self,'_simcmd_bundle'):
            self._simcmd_bundle=Bundle()
        return self._simcmd_bundle
    @simcmd_bundle.setter
    def simcmd_bundle(self,value):
        self._simcmd_bundle=value

    @property
    def momem_simulator(self): 
        """The simulator specific operation is defined with an instance of 
        simulator specific class. Properties and methods return values from that class.

        :type: ads
        :type: emx

        """
        if not hasattr(self,'_momem_simulator'):
            if self.model == 'emx':
                self._momem_simulator=emx(parent=self)
            elif self.model == 'ads':
                self._momem_simulator=ads(parent=self)
            else:
                self.print_log(type='F', msg=f'Unsupported simulator: {self.model}')
        return self._momem_simulator
   
    def read_simulation_results(self):
        '''
        Automatically reads the Touchstone file
        the simulator outputs and extracts the results to
        self.extracts.Members["net"].
        '''
        try:
            filename=glob.glob(f"{self.momemsimpath}/{self.result_filenames}.s*p")[0]
            self.print_log(type='I',
                    msg=f"Reading simulation results from {filename}.")
            self.extracts.Members['net']=rf.Network(filename)
            self.print_log(type='I',
                    msg=f"Saveed results to self.extracts.Members['net'].")
        except:
            self.print_log(type='W',msg=traceback.format_exc())
            self.print_log(type='W',msg=f'Something went wrong while reading simulation results from {filename}.')
            filepath=self.momemsimpath.split(self.runname)[0]
            self.print_log(type='F',
                    msg=f"Available results: {os.listdir(filepath)}")

    def run_momem(self):
        """Externally called function to execute simulation."""
        if self.load_state=='':
            self.momem_simulator.run()
        self.read_simulation_results()
        if not self.preserve_momemfiles:
            self.cleanup_momemsimpath()
