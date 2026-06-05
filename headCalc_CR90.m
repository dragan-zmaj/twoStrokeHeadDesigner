clearvars
clc

format long

%% Kako nacrtati glavu po ovim merama?
% Nacrtati kruznicu precnika 'pistonCrownDiameter'. 
% Nacrtati pravougaonik 'bore' sirine tako da sredina donje stranice bude u centru kruznice.
% Visinu podici dok ne dodirne kruznicu.
% Isto tako nacrtati pravougaonik 'chamberWidth' sirine.
% Uraditi presek 2 pravougaonika i kruznice. 
% Ostace 2 isecka koji cine squish band.
% Spojiti ta dva isecka pomocnom pravom linijom i iz njenog centra
% konstruisati elipsoid. Njegova sirina treba da bude 'chamberWidth'. A
% njegova poluvisina, tj. od centra elipsoida pa do najvise gornje tacke
% treba da iznosi 'ellipsoidHeight'. Na isti nacin kao sto su crtani
% prethodni pravougaonici, nacrtati treci pravougaonik sirine
% 'sparkPlugDiameter'. Njegovu visinu podici dok ne dodirne elipsoid.
% Uraditi presek treceg pravougaonika i elipsoida.

%% input parameters
bore = 42e-3;
trappedCompressionRatio = 9;
pistonCrownHeight = 1.5e-3;
squishBandAreaRatio = 0.5;
squishBandDistance = 0.5e-3;
exhaustX = 25.7e-3;
sparkPlugVolume = 0;
sparkPlugDiameter = 10e-3;

%% Head Calculation
pistonCrownRadius = (0.25*bore^2 + pistonCrownHeight^2)/2/pistonCrownHeight;
pistonCrownAngle = asin(bore/2/pistonCrownRadius); %ugao izmedju centra i oboda klipa
%pistonCrownAngle*360/2/pi

sparkPlugRadius = sparkPlugDiameter/2;

pistonCrownArea = 2*pi*pistonCrownRadius^2*(1 - cos(pistonCrownAngle));
squishBandArea = squishBandAreaRatio*pistonCrownArea;

%ugao izmedju centra klipa do pocetka squish band-a
squishBandAngle = acos(squishBandArea/pistonCrownRadius^2/2/pi + cos(pistonCrownAngle)); 
squishBandAngleDegree = squishBandAngle*360/2/pi;

if pistonCrownRadius*sin(squishBandAngle) < sparkPlugRadius
    disp('Spark plug diameter too large for given squish band area.');
    disp('You should try either to reduce squish band area or to reduce spark plug diameter');
    return
end


squishBandVolume = (2*pi/3)*((pistonCrownRadius + squishBandDistance)^3 ...
    - pistonCrownRadius^3)*(cos(squishBandAngle) - cos(pistonCrownAngle));

volumeTrappedCyl = 0.25*pi*bore^2*exhaustX;
volumeHead = volumeTrappedCyl/(trappedCompressionRatio - 1);
volumePistonHeadPart = (pistonCrownRadius^3*pi/3)*(2 - 3*(1 + squishBandDistance/pistonCrownRadius)*cos(squishBandAngle)...
    + ((1 + squishBandDistance/pistonCrownRadius)*cos(squishBandAngle))^3);
chamberVolume = volumeHead - squishBandVolume - sparkPlugVolume + volumePistonHeadPart; %sastoji se iz kalote i preostalog korisnog squishBand dela

%% ellipsoidHeight 

% syms chamberVolume pi squishBandAngle pistonCrownRadius sparkPlugDiameter ellipsoidHeight
% A = pistonCrownRadius*sin(squishBandAngle)
% eqn = chamberVolume==A^2*pi*(ellipsoidHeight^2 - sparkPlugDiameter^2*ellipsoidHeight^2/A^2)^0.5 - (ellipsoidHeight^2 - sparkPlugDiameter^2*ellipsoidHeight^2/A^2)^1.5*A^2*pi/3/ellipsoidHeight^2
% sol = solve(eqn, ellipsoidHeight)

ellipsoidHeight = (3*chamberVolume*pistonCrownRadius*sin(squishBandAngle)*(-1/((sparkPlugRadius + pistonCrownRadius*sin(squishBandAngle))*(sparkPlugRadius - pistonCrownRadius*sin(squishBandAngle))))^(1/2))/(pi*sparkPlugRadius^2 + 2*pi*pistonCrownRadius^2*sin(squishBandAngle)^2);
chamberWidth = pistonCrownRadius*sin(squishBandAngle)*2;

chamberHeight = sqrt((ellipsoidHeight^2 - sparkPlugRadius^2*ellipsoidHeight^2/(pistonCrownRadius*sin(squishBandAngle))^2));

%% Output variables 

head = struct;
head.pistonCrownDiameter = 2e3*pistonCrownRadius;
head.chamberWidth = 1e3*chamberWidth;
head.ellipsoidHeight = 1e3*ellipsoidHeight;
head.chamberHeight = 1e3*chamberHeight;

head