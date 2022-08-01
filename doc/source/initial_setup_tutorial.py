"""
======================
Initial setup tutorial
======================
Tutorial for initially setting up the simulation interface. 
This has to be done once for the process node, in order to get
all the correct configurations done.

Initially written by Veeti Lahtinen 2022. 

The emStateFile.xml required for the simulations and setting the simulation settings
is a process dependent file, which is difficult to manually change.
Therefore the following steps are introduced with figures to set the default values
such that the implemented script may easily set the stateFile to correspond to correct values.

1.  Open GUI, create a new workspace called "WORKSPACE_placeholder"
2.  Name the library to "WORKSPACE_placeholder_lib" (this should be default from workspace name)
3.  Create a new layout in the workspace, and name it "CELL_placeholder",
    and select your process dependent substrate. This may require adding some technology files to
    the workspace, similar to normally setting up a library in ADS. This step may also be performed
    in Virtuoso, by naming the workspace, library and cell as instructed earlier and adding the library
    in ADS GUI.
4.  Open the emSetup view from the layout view. 
5.  In the first view ("MOM uW" or "MOM RF"), change EM Simulator option
    to "Momentum RF", as shown in Figure x
6.  In "Substrate view", select your process' substrate
7.  In "Frequency plan" view, set Type: "Linear", Fstart: "11111", Fstop: "22222",
    Step: "1212" as shown in Figure y
8.  In "Options" view, go to mesh and in "Mesh density", select "Cells/Wavelength" and set it to "33333".
    Enable "Edge mesh", with the option "Auto-determine edge width".
    Enable "Transmission line mesh", and set it to "44444". The view is shown in Figure z
9.  Save the EM Setup view. 
10. Move the generated emStateFile.xml (should be 
    ./WORKSPACE_placeholder/WORKSPACE_placeholder_lib/CELL_placeholder/emSetup/emStateFile.xml) 
    to this ads folder to ./adsfiles/emStateFile.template
11. Add line "EMSTATEFILE=${THESDKHOME}/Entities/ads/adsfiles/emStateFile.template"
    to configure in TheSyDeKick project root, and run "./configure".


"""
