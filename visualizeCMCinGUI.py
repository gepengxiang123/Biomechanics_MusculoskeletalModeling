"""
----------------------------------------------------------------------
    visualizeCMCinGUI.py
----------------------------------------------------------------------
    This class can be used within the OpenSim GUI to visually observe
    the 'states' result from a CMC simulation (selected at runtime).
    
    Input:
        None (interactive selection of trial)
    Output:
        visualization in GUI
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2013-07-16
----------------------------------------------------------------------
"""


class visualizeCMC:
    """
    A class containing attributes and methods associated with 
    previewing an adjusted COM / mass properties model, and associated
    CMC states in the GUI.
    """
    
    def cleanUp(self):
        """
        Cleans up the current state of the GUI by closing any open
        models and motion files.
        """
        # Close any open models
        openModels = getAllModels()
        if len(openModels):
            for model in openModels:
                setCurrentModel(model)
                performAction("FileClose")
        # Wait        
        time.sleep(1)

    """------------------------------------------------------------"""
    def selectTrial(self):
        """
        Displays a dialog box listing all of the trc files in a given
        directory. Care should be taken to ensure that the directory
        corresponds to the chosen subject ID.
        """
        # Select interactively
        self.trcFilePath = utils.FileUtils.getInstance().browseForFilename('.trc','Select the file to preview',1)

    """------------------------------------------------------------"""
    def loadAdjustedModel(self):
        """
        Loads the adjusted COM model for the chosen trial into the
        GUI.
        """
        # Load model in GUI
        addModel(self.trcFilePath.replace('.trc','.osim'))

    """------------------------------------------------------------"""
    def loadCMCMotion(self):
        """
        Loads the CMC motion into the adjusted model.
        """
        # Load motion file to current model
        loadMotion(self.trcFilePath.replace('.trc','_CMC_states.sto'))

    """------------------------------------------------------------"""
    def run(self):
        """
        Main program invoked via script execution.
        """
        # Close any open models
        self.cleanUp()
        # Dynamically select file to preview
        self.selectTrial()        
        # Add adjusted COM (RRA/CMC) model
        self.loadAdjustedModel()
        # Load CMC motion to model
        self.loadCMCMotion()


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# Imports
import os
import time 
import org.opensim.utils as utils

"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    # Create instance of class
    visCMC = visualizeCMC()
    # Run code
    visCMC.run()
