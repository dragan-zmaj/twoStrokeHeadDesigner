import FreeCAD, Part, Sketcher
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, asdict

# input data
bore = 42
trappedCompressionRatio = 9
pistonCrownHeight = 1.5
squishBandAreaRatio = 0.5
squishBandDistance = 0.5
exhaustX = 25.7
sparkPlugVolume = 0
sparkPlugDiameter = 10

# 
sparkPlugRadius = sparkPlugDiameter / 2

# Piston crown geometry
# IMPORTANT!!!
pistonCrownRadius = (0.25 * bore**2 + pistonCrownHeight**2) / (2 * pistonCrownHeight) 
pistonCrownAngle = np.arcsin(bore / (2 * pistonCrownRadius))

# Areas
pistonCrownArea = 2 * np.pi * pistonCrownRadius**2 * (1 - np.cos(pistonCrownAngle))
squishBandArea = squishBandAreaRatio * pistonCrownArea

# Squish band angle
squishBandAngle = np.arccos(squishBandArea / (pistonCrownRadius**2) / (2 * np.pi) + np.cos(pistonCrownAngle))
squishBandAngleDegree = squishBandAngle * 180 / np.pi

# Check spark plug clearance
if pistonCrownRadius * np.sin(squishBandAngle) < sparkPlugRadius:
    print('Spark plug diameter too large for given squish band area.')
    print('You should try either to reduce squish band area or to reduce spark plug diameter')


# Volumes
squishBandVolume = (2 * np.pi / 3) * (
    (pistonCrownRadius + squishBandDistance)**3 - pistonCrownRadius**3
) * (np.cos(squishBandAngle) - np.cos(pistonCrownAngle))

volumeTrappedCyl = 0.25 * np.pi * bore**2 * exhaustX
volumeHead = volumeTrappedCyl / (trappedCompressionRatio - 1)

volumePistonHeadPart = (pistonCrownRadius**3 * np.pi / 3) * (
    2 - 3 * (1 + squishBandDistance / pistonCrownRadius) * np.cos(squishBandAngle)
    + ((1 + squishBandDistance / pistonCrownRadius) * np.cos(squishBandAngle))**3
)

chamberVolume = volumeHead - squishBandVolume - sparkPlugVolume + volumePistonHeadPart

# Ellipsoid height (converted from your analytical solution)
sinSquish = pistonCrownRadius * np.sin(squishBandAngle)

# Precompute denominator terms for clarity
term1 = np.pi * sparkPlugRadius**2
term2 = 2 * np.pi * pistonCrownRadius**2 * np.sin(squishBandAngle)**2

# The square root term: -1/((a+b)*(a-b)) where a = sparkPlugRadius, b = sinSquish
# This gives 1/(b^2 - a^2) when simplified
sqrt_term = np.sqrt(1 / (sinSquish**2 - sparkPlugRadius**2))

#IMPORTANT!!!
ellipsoidHeight = (3 * chamberVolume * sinSquish * sqrt_term) / (term1 + term2) 

# IMPORTANT!!!
chamberWidth = 2 * sinSquish 
# IMPORTANT!!!
chamberHeight = np.sqrt(
    ellipsoidHeight**2 - (sparkPlugRadius**2 * ellipsoidHeight**2) / (pistonCrownRadius * np.sin(squishBandAngle))**2
)


# Create document and body
#doc = App.newDocument(f"CombustionHead_tCR{int(10*trappedCompressionRatio)}_B{int(bore)}_sqB{int(squishBandAreaRatio*100)}",)
doc = App.newDocument()
body = doc.addObject("PartDesign::Body", "Body")

# Create sketch on XZ plane
sketch = body.newObject("Sketcher::SketchObject", "Sketch")
sketch.AttachmentSupport = (doc.getObject("Origin"), ["XZ_Plane"])
sketch.MapMode = "FlatFace"

# Add an squish band arc on the right side of the sketch
arc1 = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), pistonCrownRadius),
    (np.pi/2 - pistonCrownAngle),
    (np.pi/2 - squishBandAngle)
)
sketch.addGeometry([arc1], False)

# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))

# Add a squish band arc on the left side of the sketch
arc2 = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), pistonCrownRadius),
    (np.pi/2 + squishBandAngle),
    (np.pi/2 + pistonCrownAngle)
)
sketch.addGeometry([arc2], False)
# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('Coincident', 1, 3, -1, 1))


# Add an ellipse representing the combustion chamber cross-section without spark plug cutout
ellipse = Part.Ellipse(
    App.Vector(pistonCrownRadius*np.sin(squishBandAngle),pistonCrownRadius*np.cos(squishBandAngle),0), 
    App.Vector(0,pistonCrownRadius*np.cos(squishBandAngle) + ellipsoidHeight,0), 
    App.Vector(0,pistonCrownRadius*np.cos(squishBandAngle),0), 
)
sketch.addGeometry([ellipse], False)
sketch.exposeInternalGeometry(2)
sketch.addConstraint(Sketcher.Constraint('PointOnObject', 2, 3, -2))

# Cut out lower part of the ellipse
y = pistonCrownRadius * np.cos(squishBandAngle) - chamberHeight
x = chamberWidth * np.sqrt(1 - (chamberHeight/ellipsoidHeight)**2)
sketch.trim(2, App.Vector(-x, y, 0))
sketch.trim(2, App.Vector(x, y, 0))
del x, y

doc.recompute()

# Export to STEP file
Part.export([box], "test_box.step")
print("Test box created and exported as test_box.step")