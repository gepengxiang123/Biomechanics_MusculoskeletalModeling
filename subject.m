classdef subject < handle
    % SUBJECT - A class to store all modeling simulations for a subject.
    %
    %
    
    % Created by Megan Schroeder
    % Last Modified 2014-01-13
    
    
    %% Properties
    % Properties for the subject class
    
    properties (SetAccess = private)
        SubID           % Subject ID
        A_Walk_01       % Walking simulations
        A_Walk_02
        A_Walk_03
        A_Walk_04
        A_Walk_05
        U_Walk_01
        U_Walk_02
        U_Walk_03
        U_Walk_04
        U_Walk_05
        A_SD2F_01       % Stair descent to floor simulations
        A_SD2F_02
        A_SD2F_03
        A_SD2F_04
        A_SD2F_05
        U_SD2F_01
        U_SD2F_02
        U_SD2F_03
        U_SD2F_04
        U_SD2F_05
        A_SD2S_01       % Stair descent to step simulations
        A_SD2S_02
        A_SD2S_03
        A_SD2S_04
        A_SD2S_05
        U_SD2S_01
        U_SD2S_02
        U_SD2S_03
        U_SD2S_04
        U_SD2S_05
        Cycles          % Cycles (individual trials)
        Summary         % Subject summary (mean, standard deviation)
    end
    properties (Hidden = true, SetAccess = private)
        SubDir          % Directory where files are stored
        MaxIsometric    % Maximum isometric muscle force
    end
    
    
    %% Methods
    % Methods for the subject class
    
    methods
        % *****************************************************************
        %       Constructor Method
        % *****************************************************************
        function obj = subject(subID)
            % SUBJECT - Construct instance of class
            %
            
            % Subject ID
            obj.SubID = subID;
            % Subject directory
            obj.SubDir = OpenSim.getSubjectDir(subID);            
            % Identify simulation names
            allProps = properties(obj);
            simNames = allProps(2:end-2);
            % Preallocate and do a parallel loop
            tempData = cell(length(simNames),1);
            parfor i = 1:length(simNames)
                % Create simulation object
                tempData{i} = OpenSim.simulation(subID,simNames{i});                
            end
            % Assign properties
            for i = 1:length(simNames)
                obj.(simNames{i}) = tempData{i};
            end
            % Isometric muscle forces            
            muscles = obj.(simNames{1}).Muscles;
            muscleLegs = cell(size(muscles));
            for i = 1:length(muscles)
                muscleLegs{i} = [muscles{i},'_r'];
            end
            maxForces = cell(1,length(muscles));
            maxForces = dataset({maxForces,muscles{:}});
            % Parse xml
            modelFile = [obj.SubDir,filesep,obj.SubID,'.osim'];
            domNode = xmlread(modelFile);            
            maxIsoNodeList = domNode.getElementsByTagName('max_isometric_force');
            for i = 1:maxIsoNodeList.getLength
                if any(strcmp(maxIsoNodeList.item(i-1).getParentNode.getAttribute('name'),muscleLegs))
                    musc = char(maxIsoNodeList.item(i-1).getParentNode.getAttribute('name'));
                    maxForces.(musc(1:end-2)) = str2double(char(maxIsoNodeList.item(i-1).getFirstChild.getData));
                end
            end
            obj.MaxIsometric = maxForces;
            % Add normalized muscle forces property to individual simulations
            for i = 1:length(simNames)
                muscles = obj.(simNames{i}).Muscles;
                for j = 1:length(muscles)
                    obj.(simNames{i}).NormMuscleForces.(muscles{j}) = obj.(simNames{i}).MuscleForces.(muscles{j})./obj.MaxIsometric.(muscles{j}).*100;
                end
            end
            % -------------------------------------------------------------
            %       Cycles
            % -------------------------------------------------------------
            cstruct = struct();
            sims = properties(obj);
            checkSim = @(x) isa(obj.(x{1}),'OpenSim.simulation');
            sims(~arrayfun(checkSim,sims)) = [];
            % Loop through all simulations
            for i = 1:length(sims)
                cycleName = sims{i}(1:end-3);
                if ~isfield(cstruct,cycleName)
                    % Create field
                    cstruct.(cycleName) = struct();
                    % EMG
                    cstruct.(cycleName).EMG = obj.(sims{i}).MuscleEMG;
                    % Muscle Forces (normalized to max)
                    cstruct.(cycleName).Forces = obj.(sims{i}).NormMuscleForces;
                    % Simulation Name
                    cstruct.(cycleName).Simulations = {sims{i}};
                % If the fieldname already exists, need to append existing to new
                else
                    % EMG
                    oldEMG = cstruct.(cycleName).EMG;
                    newEMG = obj.(sims{i}).MuscleEMG;
                    emgprops = newEMG.Properties.VarNames;
                    for m = 1:length(emgprops)
                        newEMG.(emgprops{m}) = [oldEMG.(emgprops{m}) newEMG.(emgprops{m})];
                    end
                    cstruct.(cycleName).EMG = newEMG;
                    % Muscle Forces
                    oldForces = cstruct.(cycleName).Forces;
                    newForces = obj.(sims{i}).NormMuscleForces;
                    forceprops = newForces.Properties.VarNames;
                    for m = 1:length(forceprops)
                        newForces.(forceprops{m}) = [oldForces.(forceprops{m}) newForces.(forceprops{m})];
                    end
                    cstruct.(cycleName).Forces = newForces;
                    % Simulation Name
                    oldNames = cstruct.(cycleName).Simulations;
                    cstruct.(cycleName).Simulations = [oldNames; {sims{i}}];
                end
            end
            % Convert structure to dataset
            nrows = length(fieldnames(cstruct));
            varnames = {'Simulations','EMG','Forces'};
            cdata = cell(nrows,length(varnames));
            cdataset = dataset({cdata,varnames{:}});
            obsnames = fieldnames(cstruct);
            for i = 1:length(obsnames)
                for j = 1:length(varnames)
                    cdataset{i,j} = cstruct.(obsnames{i}).(varnames{j});
                end
            end           
            cdataset = set(cdataset,'ObsNames',obsnames);
            % Assign Property
            obj.Cycles = cdataset;
            % -------------------------------------------------------------
            %       Averages & Standard Deviation
            % -------------------------------------------------------------
            % Set up struct
            sumStruct = struct();
            varnames = {'EMG','Forces'};
            obsnames = get(cdataset,'ObsNames');
            nrows = size(cdataset,1);
            adata = cell(nrows,length(varnames));
            sdata = cell(nrows,length(varnames));
            adataset = dataset({adata,varnames{:}});
            sdataset = dataset({sdata,varnames{:}});
            % Calculate averages
            for i = 1:length(obsnames)
                % EMG
                adataset{i,'EMG'} = OpenSim.getDatasetMean(obsnames{i},cdataset{i,'EMG'},2);
                sdataset{i,'EMG'} = OpenSim.getDatasetStdDev(obsnames{i},cdataset{i,'EMG'});
                % Forces
                adataset{i,'Forces'} = OpenSim.getDatasetMean(obsnames{i},cdataset{i,'Forces'},2);
                sdataset{i,'Forces'} = OpenSim.getDatasetStdDev(obsnames{i},cdataset{i,'Forces'});
            end
            adataset = set(adataset,'ObsNames',obsnames);
            sdataset = set(sdataset,'ObsNames',obsnames);
            % Add to struct
            sumStruct.Mean = adataset;
            sumStruct.StdDev = sdataset;    
            % Assign Property
            obj.Summary = sumStruct;            
        end
        % *****************************************************************
        %       Plotting Methods
        % *****************************************************************
        function varargout = plotMuscleForces(obj,varargin)
            % PLOTMUSCLEFORCES - Compare involved leg vs. uninvolved leg for a given cycle
            %
            
            % Parse inputs
            p = inputParser;
            checkObj = @(x) isa(x,'OpenSim.subject');            
            validCycles = {'Walk','SD2F','SD2S'};
            defaultCycle = 'Walk';
            checkCycle = @(x) any(validatestring(x,validCycles));
            subProps = properties(obj);
            simObj = obj.(subProps{2});
            validMuscles = [simObj.Muscles,{'All','Quads','Hamstrings','Gastrocs'}];
            defaultMuscle = 'All';
            checkMuscle = @(x) any(validatestring(x,validMuscles));
            defaultFigHandle = figure('NumberTitle','off','Visible','off');
            defaultAxesHandles = axes('Parent',defaultFigHandle);
            p.addRequired('obj',checkObj);            
            p.addOptional('Cycle',defaultCycle,checkCycle)            
            p.addOptional('Muscle',defaultMuscle,checkMuscle);
            p.addOptional('fig_handle',defaultFigHandle);
            p.addOptional('axes_handles',defaultAxesHandles);
            p.parse(obj,varargin{:});
            % Shortcut references to input arguments
            fig_handle = p.Results.fig_handle;
            if ~isempty(p.UsingDefaults)          
                set(fig_handle,'Name',['Group Muscle Forces (',p.Results.Muscle,') for ',p.Results.Cycle,' Cycle - Uninvovled vs. Involved'],'Visible','on');
                [axes_handles,mNames] = OpenSim.getAxesAndMuscles(simObj,p.Results.Muscle);
            else
                axes_handles = p.Results.axes_handles;
                [~,mNames] = OpenSim.getAxesAndMuscles(simObj,p.Results.Muscle);
            end
            % Plot
            figure(fig_handle);
            for j = 1:length(mNames)
                set(fig_handle,'CurrentAxes',axes_handles(j));
                XplotMuscleForces(obj,p.Results.Cycle,mNames{j});
            end
            % Legend
            lStruct = struct;
            axesH = get(axes_handles(1),'Children');
            lStruct.axesHandles = axesH;
            if isa(obj,'OpenSim.controlGroup')
                lStruct.names = {'Left'; 'Right'};
            else
                lStruct.names = {'Uninvolved'; 'ACLR'};
            end
            % Return (to GUI)
            if nargout == 1
                varargout{1} = lStruct;
            end
            % -------------------------------------------------------------
            %   Subfunction
            % -------------------------------------------------------------
            function XplotMuscleForces(obj,Cycle,Muscle)
                % XPLOTMUSCLEFORCES - Worker function to plot muscle forces for a specific cycle and muscle
                %
               
                ColorA = [1 0 0.6];
                ColorU = [0 0.5 1];                
                % Plot
                % X vector
                x = (0:100)';
                % Mean
                plot(x,obj.Summary.Mean{['U_',Cycle],'Forces'}.(Muscle),'Color',ColorU,'LineWidth',3); hold on;
                plot(x,obj.Summary.Mean{['A_',Cycle],'Forces'}.(Muscle),'Color',ColorA,'LineWidth',3);
                % Standard Deviation
                plusSDU = obj.Summary.Mean{['U_',Cycle],'Forces'}.(Muscle)+obj.Summary.StdDev{['U_',Cycle],'Forces'}.(Muscle);
                minusSDU = obj.Summary.Mean{['U_',Cycle],'Forces'}.(Muscle)-obj.Summary.StdDev{['U_',Cycle],'Forces'}.(Muscle);
                xx = [x' fliplr(x')];
                yy = [plusSDU' fliplr(minusSDU')];
                hFill = fill(xx,yy,ColorU);
                set(hFill,'EdgeColor','none');
                alpha(0.25);
                plusSDA = obj.Summary.Mean{['A_',Cycle],'Forces'}.(Muscle)+obj.Summary.StdDev{['A_',Cycle],'Forces'}.(Muscle);
                minusSDA = obj.Summary.Mean{['A_',Cycle],'Forces'}.(Muscle)-obj.Summary.StdDev{['A_',Cycle],'Forces'}.(Muscle);
                xx = [x' fliplr(x')];
                yy = [plusSDA' fliplr(minusSDA')];
                hFill = fill(xx,yy,ColorA);
                set(hFill,'EdgeColor','none');
                alpha(0.25);
                % Reverse children order (so mean is on top and shaded region is in back)
                set(gca,'Children',flipud(get(gca,'Children')));
                % Axes properties
                set(gca,'box','off');
                % Set axes limits
                xlim([0 100]);
                ydefault = get(gca,'YLim');
                ylim([0 ydefault(2)]);
                % Labels
                title(upper(Muscle),'FontWeight','bold');
                xlabel({'% Cycle',''});
                ylabel('% Max Isometric Force');
            end
        end
    end
    
end
