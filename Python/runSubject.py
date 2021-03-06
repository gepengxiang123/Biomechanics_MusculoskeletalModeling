"""
----------------------------------------------------------------------
    runSubject.py
----------------------------------------------------------------------
    This class can be used to run all of the OpenSim simulation tools
    in the background.  The program will abort if errors are reached
    in the Scale, IK, or ID steps.  Failed RRA and CMC runs will
    report a message to the user and continue to the next trial.

    Input:
        Subject ID
    Output:
        Simulation results
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2013-08-12
----------------------------------------------------------------------
"""


# ####################################################################
#                                                                    #
#                   Input                                            #
#                                                                    #
# ####################################################################
# Subject ID list
subIDs = ['20130221CONF']
#subIDs = ['20130401AHLM','20121206CONF','20121205CONF','20121204CONF',
#          '20121204APRM','20121110AHRM','20121108AHRM','20121008AHRM',
#          '20120922AHRM','20120920APRM','20120919APLF','20120912AHRF']          
# ####################################################################


# Imports
from datetime import datetime
from runTools import *
from updateFirstLineMOT import updateMOT
from iterateRRAadjustMass import iterateRRA
from rerunCMCadjustTime import rerunCMC


class runSubject:
    """
    A class to run all of the OpenSim simulation steps for a given
    subject from existing Setup files.
    """

    def __init__(self,subID):
        """
        Create an instance of the class from the subject ID and add
        the starting time.
        """
        # Subject ID
        self.subID = subID
        # Starting time
        self.startTime = datetime.now()

    """------------------------------------------------------------"""
    def run(self):
        """
        Main program to run all of the tools for a given subject.
        """
        # Scale
        scaleTool = scale(self.subID)
        scaleTool.run()        
        # IK
        ikTool = ikin(self.subID)
        ikTool.run()        
        # Update first line name in output Scale and IK files for later viewing in GUI.
        updateNames = updateMOT(self.subID)
        updateNames.run()
        # ID
        idTool = idyn(self.subID)
        idTool.run()
        # RRA
        rraTool = rra(self.subID)
        rraTool.run()
        # Adjust model mass based on RRA results and rerun
        iterRRA = iterateRRA(self.subID)
        iterRRA.run()
        # CMC
        cmcTool = cmc(self.subID)
        cmcTool.run()
        # Adjust CMC starting time if simulation crashed and rerun
        reCMC = rerunCMC(self.subID)
        reCMC.run()
        # Display message to user
        d = datetime(1,1,1) + (datetime.now()-self.startTime)
        if d.hour < 1:
            print (self.subID+' is finished -- elapsed time is %d minutes.' %(d.minute))
        else:
            print (self.subID+' is finished -- elapsed time is %d hour(s) and %d minute(s).' %(d.hour, d.minute))
        

"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    # Loop through subject list
    for subID in subIDs:
        # Create instance of class
        runSub = runSubject(subID)
        # Run code
        runSub.run()
