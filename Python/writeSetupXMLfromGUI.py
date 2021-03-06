"""
----------------------------------------------------------------------
    writeSetupXMLfromGUI.py
----------------------------------------------------------------------
    This program can be executed from the OpenSim GUI to export all of
    the necessary Setup (*.xml) files for a given subject.  Generic
    model files are based on the input generic model name.

    Input arguments:
        subIDs (list)
        genericModelName (string -- gait2392, Arnold2010, 
                          Arnold2010_MillardEquilibrium, 
                          Arnold2010_MillardAcceleration)
    Output:
        Setup XML files
        External Loads XML files
----------------------------------------------------------------------
    Created by Megan Schroeder
    Last Modified 2014-01-11
----------------------------------------------------------------------
"""


# ####################################################################
#                                                                    #
#                   Inputs                                           #
#                                                                    #
# ####################################################################
# Generic model to use
genericModelName = 'Arnold2010_MillardEquilibrium'
# Subject ID
#subIDs = ['20130221CONF']
subIDs = ['20121204APRM','20121204CONF','20121205CONM','20121206CONF']
#subIDs = ['20130401CONM','20130401AHLM','20130207APRM','20121205CONF',
#          '20121110AHRM','20121108AHRM','20121008AHRM','20120922AHRM',
#          '20120920APRM','20120919APLF','20120912AHRF']
#subIDs = ['20110622CONM','20110706APRF','20110927CONM','20111025APRM',
#          '20111130AHLM','20120306AHRF','20120306CONF','20120313AHLM',
#          '20120403AHLF']
# ####################################################################


# Imports
import os
import glob
import math
from xml.dom.minidom import parse


class setupXML:
    """
    A class containing attributes and methods associated with writing
    setup XML files from the OpenSim API. A subject ID and generic
    model name are required to create an instance based on this class.
    """

    def __init__(self,subID,genericModelName):
        """
        Method to create an instance of the setupXML class. Attributes
        include the subject ID, generic model name, subject directory,
        and generic file directory.
        """
        self.subID = subID
        self.genericModelName = genericModelName
        nuDir = getScriptsDir()
        while os.path.basename(nuDir) != 'Northwestern-RIC':
            nuDir = os.path.dirname(nuDir)
        self.subDir = os.path.join(nuDir,'Modeling','OpenSim','Subjects',subID)+'\\'
        self.genDir = os.path.dirname(os.path.dirname(self.subDir[0:-2]))+'\\GenericFiles\\'

    """------------------------------------------------------------"""
    def readPersonalInfoXML(self):
        """
        Reads personal information xml file and adds attriubutes
        associated with the subject's mass, height, and the marker set
        used during the experiment.
        """
        persInfoXML = glob.glob(self.subDir+'*__PersonalInformation.xml')[0]
        dom = parse(persInfoXML)
        self.mass = float(dom.getElementsByTagName('mass')[0].firstChild.nodeValue)
        self.height = float(dom.getElementsByTagName('height')[0].firstChild.nodeValue)
        self.markerSet = dom.getElementsByTagName('markerSet')[0].firstChild.nodeValue

    """------------------------------------------------------------"""
    def createSetupXML_Scale(self):
        """
        Write setup file for scale step.
        """
        # Static TRC filename
        trcFileName = self.subID+'_0_StaticPose.trc'
        # Create MarkerData object to read starting and ending times from TRC file
        markerData = modeling.MarkerData(self.subDir+trcFileName)
        timeRange = modeling.ArrayDouble()
        timeRange.setitem(0,markerData.getStartFrameTime())
        timeRange.setitem(1,markerData.getLastFrameTime())
        # Create ScaleTool object
        scaleTool = modeling.ScaleTool(self.genDir+'ScaleTool.xml')
        scaleTool.setName(self.subID)
        # Modify top-level properties
        scaleTool.setPathToSubject(self.subDir)
        scaleTool.setSubjectMass(self.mass)
        scaleTool.setSubjectHeight(self.height)
        # Update GenericModelMaker
        scaleTool.getGenericModelMaker().setModelFileName(self.genDir+self.genericModelName+'.osim')
        scaleTool.getGenericModelMaker().setMarkerSetFileName(self.genDir+self.genericModelName.split('_')[0]+'_'+self.markerSet+'_Scale_MarkerSet.xml')
        # Update ModelScaler
        scaleTool.getModelScaler().setApply(True)
        scaleOrder = modeling.ArrayStr()
        scaleOrder.setitem(0,'measurements')
        scaleTool.getModelScaler().setScalingOrder(scaleOrder)
        scaleTool.getModelScaler().getMeasurementSet().assign(modeling.MeasurementSet().makeObjectFromFile(self.genDir+self.genericModelName.split('_')[0]+'_'+self.markerSet+'_Scale_MeasurementSet.xml'))
        scaleTool.getModelScaler().setMarkerFileName(self.subDir+trcFileName)
        scaleTool.getModelScaler().setTimeRange(timeRange)
        scaleTool.getModelScaler().setPreserveMassDist(True)
        scaleTool.getModelScaler().setOutputModelFileName(self.subDir+'TempScaled.osim')
        scaleTool.getModelScaler().setOutputScaleFileName(self.subDir+trcFileName.replace('.trc','_ScaleSet.xml'))
        # Update MarkerPlacer
        scaleTool.getMarkerPlacer().setApply(True)
        scaleTool.getMarkerPlacer().getIKTaskSet().assign(modeling.IKTaskSet(self.genDir+self.genericModelName.split('_')[0]+'_'+self.markerSet+'_Scale_IKTaskSet.xml'))
        scaleTool.getMarkerPlacer().setStaticPoseFileName(self.subDir+trcFileName)
        scaleTool.getMarkerPlacer().setTimeRange(timeRange)
        scaleTool.getMarkerPlacer().setOutputMotionFileName(self.subDir+trcFileName.replace('.trc','_Scale.mot'))
        scaleTool.getMarkerPlacer().setOutputModelFileName(self.subDir+self.subID+'.osim')
        scaleTool.getMarkerPlacer().setOutputMarkerFileName('')
        # Write changes to XML setup file
        scaleTool.print(self.subDir+trcFileName.replace('.trc','__Setup_Scale.xml'))

    """------------------------------------------------------------"""
    def createSetupXML_IK(self):
        """
        Write setup files for IK step.
        """
        # Create InverseKinematicsTool object
        ikTool = modeling.InverseKinematicsTool(self.genDir+'InverseKinematicsTool.xml')
        # Dynamic TRC filenames
        trcFilePathList = glob.glob(self.subDir+self.subID+'_*_*_*.trc')
        # Loop through TRC files
        for trcFilePath in trcFilePathList:
            # TRC filename
            trcFileName = os.path.basename(trcFilePath)
            # Name of tool
            ikTool.setName(os.path.splitext(trcFileName)[0])
            # <IKTaskSet>
            ikTool.getIKTaskSet().assign(modeling.IKTaskSet(self.genDir+self.genericModelName.split('_')[0]+'_'+self.markerSet+'_IK_IKTaskSet.xml'))
            # <marker_file>
            ikTool.setMarkerDataFileName(trcFilePath)
            # <coordinate_file>
            ikTool.setCoordinateFileName('')
            # Create MarkerData object to read starting and ending times from TRC file
            markerData = modeling.MarkerData(trcFilePath)
            # <time_range>
            ikTool.setStartTime(markerData.getStartFrameTime())
            ikTool.setEndTime(markerData.getLastFrameTime())
            # <output_motion_file>
            ikTool.setOutputMotionFileName(trcFilePath.replace('.trc','_IK.mot'))
            # Write changes to XML setup file
            xmlSetupFilePath = trcFilePath.replace('.trc','__Setup_IK.xml')
            ikTool.print(xmlSetupFilePath)
            #
            # **** Temporary fix for setting model name using XML parsing ****
            dom = parse(xmlSetupFilePath)
            dom.getElementsByTagName('model_file')[0].firstChild.nodeValue = self.subDir+self.subID+'.osim'
            xmlstring = dom.toxml('UTF-8')
            xmlFile = open(xmlSetupFilePath,'w')
            xmlFile.write(xmlstring)
            xmlFile.close()

    """------------------------------------------------------------"""
    def createExternalLoadsXML(self):
        """
        Write XML file specifying external loads from GRF.mot file.
        """
        # Create ExternalLoads object
        extLoads = modeling.ExternalLoads()
        extLoads.assign(modeling.ExternalLoads().makeObjectFromFile(self.genDir+'ExternalLoads.xml'))
        # Dynamic TRC filenames
        trcFilePathList = glob.glob(self.subDir+self.subID+'_*_*_*.trc')
        # Loop through TRC files
        for trcFilePath in trcFilePathList:
            # TRC filename
            trcFileName = os.path.basename(trcFilePath)
            # Name of object
            extLoads.setName(os.path.splitext(trcFileName)[0])
            # <datafile>
            extLoads.setDataFileName(trcFilePath.replace('.trc','_GRF.mot'))
            # <external_loads_model_kinematics_file>
            extLoads.setExternalLoadsModelKinematicsFileName(trcFilePath.replace('.trc','_IK.mot'))
            # <lowpass_cutoff_frequency_for_load_kinematics>
            extLoads.setLowpassCutoffFrequencyForLoadKinematics(6)
            # Write changes to XML file
            extLoads.print(trcFilePath.replace('.trc','_ExternalLoads.xml'))

    """------------------------------------------------------------"""
    def createSetupXML_ID(self):
        """
        Write setup files for ID step.
        """
        # Create InverseDynamicsTool object
        idTool = modeling.InverseDynamicsTool(self.genDir+'InverseDynamicsTool.xml')
        # <forces_to_exclude>
        excludedForces = modeling.ArrayStr()
        excludedForces.setitem(0,'muscles')
        idTool.setExcludedForces(excludedForces)
        # <lowpass_cutoff_frequency_for_coordinates>
        idTool.setLowpassCutoffFrequency(6)
        # Dynamic TRC filenames
        trcFilePathList = glob.glob(self.subDir+self.subID+'_*_*_*.trc')
        # Loop through TRC files
        for trcFilePath in trcFilePathList:
            # TRC filename
            trcFileName = os.path.basename(trcFilePath)
            # Name of tool
            idTool.setName(os.path.splitext(trcFileName)[0])
            # Create Storage object to read starting and ending times from MOT file
            motData = modeling.Storage(trcFilePath.replace('.trc','_GRF.mot'))
            # <time_range>
            idTool.setStartTime(motData.getFirstTime())
            idTool.setEndTime(motData.getLastTime())
            # <external_loads_file>
            idTool.setExternalLoadsFileName(trcFilePath.replace('.trc','_ExternalLoads.xml'))
            # <coordinates_file>
            idTool.setCoordinatesFileName(trcFilePath.replace('.trc','_IK.mot'))
            # <output_gen_force_file>
            idTool.setOutputGenForceFileName(trcFileName.replace('.trc','_ID.sto'))
            # Write changes to XML setup file
            xmlSetupFilePath = trcFilePath.replace('.trc','__Setup_ID.xml')
            idTool.print(xmlSetupFilePath)
            #
            # **** Temporary fix for setting model name using XML parsing ****
            dom = parse(xmlSetupFilePath)
            for i in range(len(dom.getElementsByTagName('model_file'))):
                dom.getElementsByTagName('model_file')[i].firstChild.nodeValue = self.subDir+self.subID+'.osim'
            xmlstring = dom.toxml('UTF-8')
            xmlFile = open(xmlSetupFilePath,'w')
            xmlFile.write(xmlstring)
            xmlFile.close()

    """------------------------------------------------------------"""
    def createSetupXML_RRA(self):
        """
        Write setup files for RRA step.
        """
        # Create RRATool object
        rraTool = modeling.RRATool(self.genDir+'RRATool.xml')
        # <model_file>
        rraTool.setModelFilename(self.subDir+self.subID+'.osim')
        # <replace_force_set>
        rraTool.setReplaceForceSet(True)
        # <force_set_files>
        forceSetFiles = modeling.ArrayStr()
        forceSetFiles.setitem(0,self.genDir+self.genericModelName.split('_')[0]+'_ForceSet.xml')
        rraTool.setForceSetFiles(forceSetFiles)
        # <results_directory>
        rraTool.setResultsDir(self.subDir)
        # <output_precision>
        rraTool.setOutputPrecision(20)
        # <solve_for_equilibrium_for_auxiliary_states>
        rraTool.setSolveForEquilibrium(True)
        # <task_set_file>
        rraTool.setTaskSetFileName(self.genDir+self.genericModelName.split('_')[0]+'_CMCTaskSet.xml')
        # <lowpass_cutoff_frequency>
        rraTool.setLowpassCutoffFrequency(6)
        # <adjust_com_to_reduce_residuals>
        rraTool.setAdjustCOMToReduceResiduals(True)
        # <adjusted_com_body>
        rraTool.setAdjustedCOMBody('torso')
        # Dynamic TRC filenames
        trcFilePathList = glob.glob(self.subDir+self.subID+'_*_*_*.trc')
        # Loop through TRC files
        for trcFilePath in trcFilePathList:
            # TRC filename
            trcFileName = os.path.basename(trcFilePath)
            # Name of tool
            rraTool.setName(os.path.splitext(trcFileName)[0]+'_RRA')
            # Create Storage object to read starting and ending times from MOT file
            motData = modeling.Storage(trcFilePath.replace('.trc','_GRF.mot'))
            # <initial_time>
            rraTool.setInitialTime(math.ceil(motData.getFirstTime()*1000)/1000)
            # <final_time>
            rraTool.setFinalTime(math.floor(motData.getLastTime()*1000)/1000)
            # <external_loads_file>
            rraTool.setExternalLoadsFileName(trcFilePath.replace('.trc','_ExternalLoads.xml'))
            # <desired_kinematics_file>
            rraTool.setDesiredKinematicsFileName(trcFilePath.replace('.trc','_IK.mot'))
            # <output_model_file>
            rraTool.setOutputModelFileName(trcFilePath.replace('.trc','__AdjustedCOM.osim'))
            # Write changes to XML file
            rraTool.print(trcFilePath.replace('.trc','__Setup_RRA.xml'))

    """------------------------------------------------------------"""
    def createSetupXML_CMC(self):
        """
        Write setup files for CMC step.
        """
        # Create CMCTool object
        cmcTool = modeling.CMCTool(self.genDir+'CMCTool.xml')
        # <force_set_files>
        forceSetFiles = modeling.ArrayStr()
        forceSetFiles.setitem(0,self.genDir+self.genericModelName.split('_')[0]+'_ForceSet.xml')
        cmcTool.setForceSetFiles(forceSetFiles)
        # <results_directory>
        cmcTool.setResultsDir(self.subDir)
        # <output_precision>
        cmcTool.setOutputPrecision(20)
        # <maximum_number_of_integrator_steps>
        cmcTool.setMaximumNumberOfSteps(30000)
        # <maximum_integrator_step_size>
        cmcTool.setMaxDT(0.0001)
        # <integrator_error_tolerance>
        cmcTool.setErrorTolerance(1e-006)
        # <task_set_file>
        cmcTool.setTaskSetFileName(self.genDir+self.genericModelName.split('_')[0]+'_CMCTaskSet.xml')
        # <lowpass_cutoff_frequency>
        cmcTool.setLowpassCutoffFrequency(-1)
        # <use_fast_optimization_target>
        if self.genericModelName == 'gait2392':
            cmcTool.setUseFastTarget(True)
        else:
            cmcTool.setUseFastTarget(False)
        # Dynamic TRC filenames
        trcFilePathList = glob.glob(self.subDir+self.subID+'_*_*_*.trc')
        # Loop through TRC files
        for trcFilePath in trcFilePathList:
            # TRC filename
            trcFileName = os.path.basename(trcFilePath)
            # Name of tool
            cmcTool.setName(os.path.splitext(trcFileName)[0]+'_CMC')
            # <model_file>
            cmcTool.setModelFilename(trcFilePath.replace('.trc','.osim'))
            # Create Storage object to read starting and ending times from MOT file
            motData = modeling.Storage(trcFilePath.replace('.trc','_GRF.mot'))
            # <initial_time>
            cmcTool.setInitialTime(math.ceil(motData.getFirstTime()*1000)/1000)
            # <final_time>
            cmcTool.setFinalTime(math.floor(motData.getLastTime()*1000)/1000)
            # <external_loads_file>
            cmcTool.setExternalLoadsFileName(trcFilePath.replace('.trc','_ExternalLoads.xml'))
            # <desired_kinematics_file>
            cmcTool.setDesiredKinematicsFileName(trcFilePath.replace('.trc','_RRA_Kinematics_q.sto'))
            # Write changes to XML file
            cmcTool.print(trcFilePath.replace('.trc','__Setup_CMC.xml'))

    """------------------------------------------------------------"""
    def run(self):
        """
        The main program invoked to call the other subfunctions.
        """
        # Get subject specific information from file
        self.readPersonalInfoXML()
        # Create the setup file used to run the scale step
        self.createSetupXML_Scale()
        # Create the setup file(s) used to run the IK step
        self.createSetupXML_IK()
        # Create the external loads file(s) used for all kinetic analyses
        self.createExternalLoadsXML()
        # Create the setup file(s) used to run the ID step
        self.createSetupXML_ID()
        # Create the setup file(s) used to run the RRA step
        self.createSetupXML_RRA()
        # Create the setup file(s) used to run the CMC step
        self.createSetupXML_CMC()


"""*******************************************************************
*                                                                    *
*                   Script Execution                                 *
*                                                                    *
*******************************************************************"""
if __name__ == '__main__':
    # Loop through subject list
    for subID in subIDs:
        # Create instance of class
        setXML = setupXML(subID,genericModelName)
        # Run code
        setXML.run()
