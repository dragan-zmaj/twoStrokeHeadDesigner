import math, Part, Sketcher
import FreeCAD as App
#import matplotlib.pyplot as plt
from dataclasses import dataclass, asdict

# input data
bore = 42 # diameter of the cylinder
trappedCompressionRatio = 9 # compression ratio until exhaust port opens
pistonCrownHeight = 1.5 # height of the piston spherical dome, other geometries of piston crown are not yet supported
squishBandAreaRatio = 0.5  
squishBandDistance = 0.5 # distance between piston at tdc and head in squish area
exhaustX = 25.7 # distance from cylinder tdc to exhaust port opening
sparkPlugVolume = 0 # volume of the spark plug protruding into the chamber
sparkPlugThreadDiameter = 10 # diameter of the spark plug thread
sparkPlugThreadLength = 19.05 # length of the spark plug thread
sparkPlugSeatDiameter = 20 # diameter of material which has threaded hole for spark plug, this needs to be sufficiently larger than sparkPlugThreadDiameter for thermomechanical reasons
outerHeadDiameter = 46 # head is designed as insert, this is the diameter of the insert, this depends on machining capabilities of original head
outerHeadHeight = 15 # head is designed as insert, this is the height of the insert, this depends on machining capabilities of original head


# PROGRAM STARTS HERE
filename = f"CombustionHead_tCR{int(10*trappedCompressionRatio)}_B{int(bore)}_sqB{int(squishBandAreaRatio*100)}" 

sparkPlugRadius = sparkPlugThreadDiameter / 2
# Piston crown geometry
# IMPORTANT!!!
pistonCrownRadius = (0.25 * bore**2 + pistonCrownHeight**2) / (2 * pistonCrownHeight) 
pistonCrownAngle = math.asin(bore / (2 * pistonCrownRadius))

# Areas
pistonCrownArea = 2 * math.pi * pistonCrownRadius**2 * (1 - math.cos(pistonCrownAngle))
squishBandArea = squishBandAreaRatio * pistonCrownArea

# Squish band angle
squishBandAngle = math.acos(squishBandArea / (pistonCrownRadius**2) / (2 * math.pi) + math.cos(pistonCrownAngle))
squishBandAngleDegree = squishBandAngle * 180 / math.pi

# Check spark plug clearance
if pistonCrownRadius * math.sin(squishBandAngle) < sparkPlugRadius:
    print('Spark plug diameter too large for given squish band area.')
    print('You should try either to reduce squish band area or to reduce spark plug diameter')


# Volumes
squishBandVolume = (2 * math.pi / 3) * (
    (pistonCrownRadius + squishBandDistance)**3 - pistonCrownRadius**3
) * (math.cos(squishBandAngle) - math.cos(pistonCrownAngle))

volumeTrappedCyl = 0.25 * math.pi * bore**2 * exhaustX
volumeHead = volumeTrappedCyl / (trappedCompressionRatio - 1)

volumePistonHeadPart = (pistonCrownRadius**3 * math.pi / 3) * (
    2 - 3 * (1 + squishBandDistance / pistonCrownRadius) * math.cos(squishBandAngle)
    + ((1 + squishBandDistance / pistonCrownRadius) * math.cos(squishBandAngle))**3
)

chamberVolume = volumeHead - squishBandVolume - sparkPlugVolume + volumePistonHeadPart

# Ellipsoid height (converted from your analytical solution)
sinSquish = pistonCrownRadius * math.sin(squishBandAngle)

# Precompute denominator terms for clarity
term1 = math.pi * sparkPlugRadius**2
term2 = 2 * math.pi * pistonCrownRadius**2 * math.sin(squishBandAngle)**2

# The square root term: -1/((a+b)*(a-b)) where a = sparkPlugRadius, b = sinSquish
# This gives 1/(b^2 - a^2) when simplified
sqrt_term = math.sqrt(1 / (sinSquish**2 - sparkPlugRadius**2))

#IMPORTANT!!!
ellipsoidHeight = (3 * chamberVolume * sinSquish * sqrt_term) / (term1 + term2) 

# IMPORTANT!!!
chamberWidth = 2 * sinSquish 
# IMPORTANT!!!
chamberHeight = math.sqrt(
    ellipsoidHeight**2 - (sparkPlugRadius**2 * ellipsoidHeight**2) / (pistonCrownRadius * math.sin(squishBandAngle))**2
)


# Create document and body
#doc = App.newDocument(f"CombustionHead_tCR{int(10*trappedCompressionRatio)}_B{int(bore)}_sqB{int(squishBandAreaRatio*100)}")
doc = App.newDocument()
body = doc.addObject("PartDesign::Body", "Body")

# Create sketch on XZ plane
sketch = body.newObject("Sketcher::SketchObject", "Sketch")
sketch.AttachmentSupport = (doc.getObject("Origin"), ["XZ_Plane"])
sketch.MapMode = "FlatFace"


# Add an squish band arc on the right side of the sketch
cnt = 0
idArc1 =cnt
arc1 = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), pistonCrownRadius),
    (math.pi/2 - pistonCrownAngle),
    (math.pi/2 - squishBandAngle)
)
sketch.addGeometry([arc1], False)
# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idArc1, 3, -2))


# Add a squish band arc on the left side of the sketch
cnt += 1
idArc2 = cnt
arc2 = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), pistonCrownRadius),
    (math.pi/2 + squishBandAngle),
    (math.pi/2 + pistonCrownAngle)
)
sketch.addGeometry([arc2], False)
# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idArc2, 3, -2))


# Add an ellipse representing the combustion chamber cross-section without spark plug cutout
cnt += 1
idEllipse = cnt
ellipse = Part.Ellipse(
    App.Vector(pistonCrownRadius*math.sin(squishBandAngle),pistonCrownRadius*math.cos(squishBandAngle),0), 
    App.Vector(0,pistonCrownRadius*math.cos(squishBandAngle) + ellipsoidHeight,0), 
    App.Vector(0,pistonCrownRadius*math.cos(squishBandAngle),0), 
)
sketch.addGeometry([ellipse], False)
sketch.exposeInternalGeometry(2)
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idEllipse, 3, -2))


# Cut out lower part of the ellipse
y = pistonCrownRadius * math.cos(squishBandAngle) - chamberHeight
x = chamberWidth * math.sqrt(1 - (chamberHeight/ellipsoidHeight)**2)
sketch.trim(2, App.Vector(-x, y, 0))
sketch.trim(2, App.Vector(x, y, 0))


# Draw a line where spark enters the chamber
cnt += 1
idCeilingLine = cnt
y = pistonCrownRadius * math.cos(squishBandAngle) + ellipsoidHeight*math.sqrt(1 - (sparkPlugRadius/chamberWidth)**2)
line = Part.LineSegment(
    App.Vector(-sparkPlugRadius, y, 0),
    App.Vector(sparkPlugRadius, y, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('PointOnObject', idCeilingLine, 1, idEllipse))
constraintList.append(Sketcher.Constraint('PointOnObject', idCeilingLine, 2, idEllipse))
constraintList.append(Sketcher.Constraint('Horizontal', idCeilingLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)


# Trim the ellipse above the spark plug line
y = pistonCrownRadius * math.cos(squishBandAngle) + ellipsoidHeight
sketch.trim(idEllipse, App.Vector(0, y, 0))

sketch.delGeometries([idArc2, (cnt+1)])

idEllipse -= 1
idCeilingLine -= 1

# Draw vertical line - axis of rotation - it has the length of sparkPlugThreadLength
cnt = max([idArc1, idEllipse, idCeilingLine]) + 1
idAxisLine = cnt
y1 = pistonCrownRadius * math.cos(squishBandAngle) + ellipsoidHeight*math.sqrt(1 - (sparkPlugRadius/chamberWidth)**2)
y2 = y1 + sparkPlugThreadLength
line = Part.LineSegment(
    App.Vector(0, y1, 0),
    App.Vector(0, y2, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('PointOnObject', idAxisLine, 1, idCeilingLine))
constraintList.append(Sketcher.Constraint('PointOnObject', idAxisLine, 1, -2))
constraintList.append(Sketcher.Constraint('PointOnObject', idAxisLine, 2, -2))
#constraintList.append(Sketcher.Constraint('Vertical', idAxisLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)

# trim ceiling line to axis line
sketch.trim(idCeilingLine, App.Vector(-sparkPlugRadius/2, y1, 0))

# line for spark plug seat
cnt += 1
idSparkPlugSeatLine = cnt
y = pistonCrownRadius * math.cos(squishBandAngle) + ellipsoidHeight*math.sqrt(1 - (sparkPlugRadius/chamberWidth)**2)
x1 = 0
x2 = sparkPlugSeatDiameter/2
line = Part.LineSegment(
    App.Vector(x1, y, 0),
    App.Vector(x2, y, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idAxisLine, 2, idSparkPlugSeatLine, 1))
constraintList.append(Sketcher.Constraint('Horizontal', idSparkPlugSeatLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)

# Outer line 1
cnt += 1
idOuterLine1 = cnt    
y2 = pistonCrownRadius * math.cos(pistonCrownAngle) + outerHeadHeight
y1 = pistonCrownRadius * math.cos(pistonCrownAngle) + ellipsoidHeight + sparkPlugThreadLength
x = sparkPlugSeatDiameter/2
line = Part.LineSegment(
    App.Vector(x, y1, 0),
    App.Vector(x, y2, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idSparkPlugSeatLine, 2, idOuterLine1, 1))
constraintList.append(Sketcher.Constraint('Vertical', idOuterLine1))

for constraint in constraintList:
    sketch.addConstraint(constraint)

# Outer Line 2
cnt += 1
idOuterLine2 = cnt
y = pistonCrownRadius * math.cos(pistonCrownAngle) + outerHeadHeight
x2 = outerHeadDiameter/2
x1 = sparkPlugSeatDiameter/2
line = Part.LineSegment(
    App.Vector(x1, y, 0),
    App.Vector(x2, y, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idOuterLine1, 2, idOuterLine2, 1))
constraintList.append(Sketcher.Constraint('Horizontal', idOuterLine2))

for constraint in constraintList:
    sketch.addConstraint(constraint)

# Outer Line 3
cnt += 1
idOuterLine3 = cnt
y2 = pistonCrownRadius * math.cos(pistonCrownAngle)
y1 = pistonCrownRadius * math.cos(pistonCrownAngle) + outerHeadHeight
x = outerHeadDiameter/2
line = Part.LineSegment(
    App.Vector(x, y1, 0),
    App.Vector(x, y2, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idOuterLine2, 2, idOuterLine3, 1))
constraintList.append(Sketcher.Constraint('Vertical', idOuterLine3))

for constraint in constraintList:
    sketch.addConstraint(constraint)

cnt += 1
idOuterLine4 = cnt
x2 = pistonCrownRadius * math.sin(pistonCrownAngle) 
y = pistonCrownRadius * math.cos(pistonCrownAngle) 
x1 = outerHeadDiameter/2
line = Part.LineSegment(
    App.Vector(x1, y, 0),
    App.Vector(x2, y, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idOuterLine3, 2, idOuterLine4, 1))
constraintList.append(Sketcher.Constraint('Horizontal', idOuterLine4))
constraintList.append(Sketcher.Constraint('Coincident', idArc1, 1, idOuterLine4, 2))

for constraint in constraintList:
    sketch.addConstraint(constraint)


doc.recompute()





'''
# Export to STEP file
Part.export([box], "test_box.step")
print("Test box created and exported as test_box.step")
'''