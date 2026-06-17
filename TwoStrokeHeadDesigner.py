import math, Part, Sketcher, os, time
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
doc = App.newDocument(filename)

sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))

cnt = 0
idArc =cnt
arc = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,-pistonCrownRadius*math.cos(pistonCrownAngle),0), 
                App.Vector(0,0,1), 
                pistonCrownRadius),
    (math.pi/2 - pistonCrownAngle),
    (math.pi/2 - squishBandAngle)
)
sketch.addGeometry([arc], False)
# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idArc, 3, -2)) #place center of arc on y-axis
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idArc, 1, -1)) #place startpoint of arc on x-axis


# Add a ellipse arc on the left side of the sketch
cnt += 1
idEllipse = cnt
ellipse = Part.Ellipse(
    App.Vector(pistonCrownRadius*math.sin(squishBandAngle),pistonCrownRadius*(math.cos(squishBandAngle) - math.cos(pistonCrownAngle)),0), 
    App.Vector(0,pistonCrownRadius*(math.cos(squishBandAngle) - math.cos(pistonCrownAngle)) + ellipsoidHeight,0), 
    App.Vector(0,pistonCrownRadius*(math.cos(squishBandAngle) - math.cos(pistonCrownAngle)),0), 
)
geometricAngle = math.atan(chamberHeight/sparkPlugRadius)
parametricAngle = math.atan((0.5*chamberWidth * math.sin(geometricAngle))/(ellipsoidHeight * math.cos(geometricAngle)))
arcEllipse = Part.ArcOfEllipse(ellipse, 0, parametricAngle)
sketch.addGeometry([arcEllipse], False)
# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('PointOnObject', idEllipse, 3, -2))
sketch.addConstraint(Sketcher.Constraint('Coincident', idEllipse, 1, idArc, 2))

#doc.recompute()

# Draw a line where spark enters the chamber - ceiling line of the chamber, future hole with thread for spark plug will be cut out here
cnt += 1
idCeilingLine = cnt
y = pistonCrownRadius*(math.cos(squishBandAngle) - math.cos(pistonCrownAngle)) + chamberHeight
line = Part.LineSegment(
    App.Vector(sparkPlugRadius, y, 0),
    App.Vector(0, y, 0)
)
sketch.addGeometry([line], False)
constraintList = []
sketch.addConstraint(Sketcher.Constraint('Coincident', idCeilingLine, 1, idEllipse, 2))
constraintList.append(Sketcher.Constraint('PointOnObject', idCeilingLine, 2, -2))
constraintList.append(Sketcher.Constraint('Horizontal', idCeilingLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)

#doc.recompute()

# Draw vertical line - axis of rotation - it has the length of sparkPlugThreadLength
cnt += 1
idAxisLine = cnt
y1 = pistonCrownRadius*(math.cos(squishBandAngle) - math.cos(pistonCrownAngle)) + chamberHeight
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
#sketch.toggleConstruction(idAxisLine)  # Make it construction geometry
#constraintList.append(Sketcher.Constraint('Vertical', idAxisLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)

#doc.recompute()

# line for spark plug seat
cnt += 1
idSparkPlugSeatLine = cnt
line = Part.LineSegment(
    App.Vector(0, y2, 0),
    App.Vector(sparkPlugSeatDiameter/2, y2, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idAxisLine, 2, idSparkPlugSeatLine, 1))
constraintList.append(Sketcher.Constraint('Horizontal', idSparkPlugSeatLine))

for constraint in constraintList:
    sketch.addConstraint(constraint)

#doc.recompute()

# Outer line 1
cnt += 1
idOuterLine1 = cnt    
y1 = y2
y2 =  outerHeadHeight
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

#doc.recompute()

# Outer Line 2
cnt += 1
idOuterLine2 = cnt
y = outerHeadHeight
x1 = sparkPlugSeatDiameter/2
x2 = outerHeadDiameter/2
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

#doc.recompute()

# Outer Line 3
cnt += 1
idOuterLine3 = cnt
y1 =  outerHeadHeight
x = outerHeadDiameter/2
line = Part.LineSegment(
    App.Vector(x, y1, 0),
    App.Vector(x, 0, 0)
)
sketch.addGeometry([line], False)
constraintList = []
constraintList.append(Sketcher.Constraint('Coincident', idOuterLine2, 2, idOuterLine3, 1))
constraintList.append(Sketcher.Constraint('Vertical', idOuterLine3))

for constraint in constraintList:
    sketch.addConstraint(constraint)

#doc.recompute()

# Outer Line 4
cnt += 1
idOuterLine4 = cnt
x2 = pistonCrownRadius * math.sin(pistonCrownAngle) 
x1 = outerHeadDiameter/2
line = Part.LineSegment(
    App.Vector(x1, 0, 0),
    App.Vector(x2, 0, 0)
)
sketch.addGeometry([line], False)
sketch.addConstraint((Sketcher.Constraint('Coincident', idOuterLine3, 2, idOuterLine4, 1)))
sketch.addConstraint(Sketcher.Constraint('Horizontal', idOuterLine4))
sketch.addConstraint(Sketcher.Constraint('Coincident', idArc, 1, idOuterLine4, 2))



doc.recompute()


# === CREATE REVOLUTION USING PART WORKBENCH ===

# Get the sketch shape
sketchShape = sketch.Shape

wire = max(sketchShape.Wires)

# Revolve around Y-axis (sketch is in XZ plane)
revShape = wire.revolve(
    App.Vector(0, 0, 0),  # Point on axis
    App.Vector(0, 1, 0),  # Direction (Y-axis)
    360.0  # Angle
)

# Create Part object
revolution = doc.addObject('Part::Feature', 'Revolution')
revolution.Shape = revShape
doc.purgeTouched()
doc.recompute()
sketch.Visibility = False
doc.getObject('Revolution').Visibility = True

doc.saveAs(f"{filename}.FCStd")

# Export to STEP file
body = App.ActiveDocument.getObject('Revolution')
Part.export([body], f'{filename}.step')
#print("Test box created and exported as test_box.step")

# === EXPORT TO STL  ===
stl_file = f"{filename}.stl"
try:
    if body and hasattr(body, 'Shape'):
        import Mesh
        mesh_obj = Mesh.Mesh(body.Shape.tessellate(0.1))
        mesh_obj.write(stl_file)
        print(f"[OK] STL file exported: {stl_file}")
except Exception as e:
    print(f"[ERROR] Failed to export STL: {e}")

print("\n=== DONE ===")