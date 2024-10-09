'''
======================
EMX simulation command
======================

Class for EMX simulation commands

Initially written by Veeti Lahtinen

'''
import os
import sys
from abc import * 
from thesdk import *
from thesdk.iofile import iofile
import numpy as np
import pandas as pd
import pdb

class momem_simcmd(thesdk):
    '''
    Class to provide simulation command parameters to momem testbench.
    When instantiated in the parent class, this class automatically
    attaches spice_simcmd objects to simcmd_bundle -bundle in testbench.
    
    Attributes
    ----------
    parent : object 
        The parent object initializing the spice_simcmd instance. Default None.
    sim : 'sweep'
        Simulation type. Currently 'sweep' only supported
    impedance : int
        Set the port reference impedance when printing S-parameters (default 50 ohm).
    swpstart : float, optional
        Sweep start value. Give either this, swpstop and swpstep or the swpvalues
    swpstop : float, optional
        Sweep stop value. Give either this, swpstart and swpstep or the swpvalues
    swpstep : float, optional
        Sweep step value. Give either this, swpstop and swpstart or the swpvalues
    swpvalues : float, optional
        List of sweep values. Give either this OR swpstart,swpstop and swpstep.
    edge_width : int
        Set edge width in microns. Default 1 micron
    thickness : int
        Set metal thickness in microns. Default 1 micron
    via_separation : int
        Set the value in microns where array of vias is merged into one via. Default
        0.5 microns, but if you don't want to merge, specify 0.
    port_map : list
        Currently only supported in EMX! List of port maps. List of lists,
        e.g. [[P001, IN], [P002, OUT]].
        Attaches a voltage source to each of the pins and ground plane, and includes
        the respective ports.
    exclude_ports : list
        Currently only supported in EMX! List of ports you don't want to solve.
    3d_metals : list
        Currently only supported in EMX! List of layers that you want to use the 
        3D models for. Default: All
    recommended_memory : bool
        Applies for EMX only! Allow EMX to do discretization and interaction computation
        steps and determine a recommended amount of memory and set memory limit to
        the recommendation. 
        Default True.
    label_depth : int
        Applies for EMX only! Default 0 means that EMX oonly considers labels in the
        top-level structure. If label_depth is 1, it looks for substructures of the
        top level as well.
    simultaneous_frequencies : int
        Applies for EMX only! Allows EMX to solve up to specified number of frequencies
        in parallel. Default 0, means that EMX can do as many simultaneous frequencies as it
        profitably can, subject to processor and memory availabiliity.
    parallel : int
        Applies for EMX only! Default 0 means that EMX willl use up to maximum number of CPUs
        allowed for single license. Value -1 will request as many CPUs as there are on the
        machine, possibly requiring multiple licences.
    quasistatic : bool
        Applies for EMX only! Typically in IC applications retardation effects are small,
        thus this option can be used to tell EMX that a quasistatic model is sufficient
        for calculating the interactions between elements.
        Makes simulations faster and use less memory.
        Default True, if False, full wave model is used. 
    edge_mesh : bool
        Applies for ADS only! Enable edge mesh? 
        Default: True.
    mesh_cells : int
        Applies for ADS only! Number of mesh cells per fstop wavelenght.
        Default: 30.
    TL_mesh_cells : int
        Applies for ADS only! Transmission line mesh density. Cells per line width
        Default: 0.

    Examples
    --------
    Simple sweep from 0 to 100 GHz with 1GHz steps and default edge_width, thickness and via_separation:: 

        _=momem_simcmd(self,sim='sweep',impedance=50,
                swpstart=0,swpstop=100e9,swpstep=1e9,
                port_map=self.port_map)

    '''

    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,parent,**kwargs):
        try:
            self.parent = parent
            self.sim = kwargs.get('sim','sweep')
            self.impedance = kwargs.get('impedance',50)
            self.swpstart = kwargs.get('swpstart',None)
            self.swpstop = kwargs.get('swpstop',None)
            self.swpstep = kwargs.get('swpstep',None)
            self.swpvalues = kwargs.get('swpvalues',[]) if type(kwargs.get('swpvalues', [])) == list else [kwargs.get('swpvalues')]
            self.edge_width = kwargs.get('edge_width',1)
            self.thickness = kwargs.get('thickness',1)
            self.via_separation = kwargs.get('via_separation',0.5)
            self.edge_mesh = kwargs.get('edge_mesh',True)
            self.mesh_cells = kwargs.get('mesh_cells',30)
            self.TL_mesh_cells = kwargs.get('TL_mesh_cells',0)
            self.thickness = kwargs.get('thickness',1)
            self.port_map = kwargs.get('port_map',[]) if type(kwargs.get('port_map', [])) == list else [kwargs.get('port_map')]
            self.exclude_ports = kwargs.get('exclude_ports',[]) if type(kwargs.get('exclude_ports', [])) == list else [kwargs.get('exclude_ports')]
            self.multid_metals = kwargs.get('3d_metals',[]) if type(kwargs.get('3d_metals', [])) == list else [kwargs.get('3d_metals')]
            self.recommended_memory = kwargs.get('recommended_memory',True)
            self.label_depth = kwargs.get('label_depth',0)
            self.simultaneous_frequencies = kwargs.get('simultaneous_frequencies',0)
            self.parallel = kwargs.get('parallel',0)
            self.quasistatic = kwargs.get('quasistatic',True)
        except:
            self.print_log(type='E',msg=traceback.format_exc())
            self.print_log(type='F', msg="Simulation command definition failed.")

        if hasattr(self.parent,'simcmd_bundle'):
            self.parent.simcmd_bundle.new(name=self.sim,val=self)

