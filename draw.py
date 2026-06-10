import FreeCAD, Part, Sketcher

# Create document and body
doc = App.newDocument("CombustionHead")
body = doc.addObject("PartDesign::Body", "Body")

# Create sketch on XZ plane
sketch = body.newObject("Sketcher::SketchObject", "Sketch")
sketch.AttachmentSupport = (doc.getObject("Origin"), ["XZ_Plane"])
sketch.MapMode = "FlatFace"

# Add an arc (center at origin, radius 55.289mm, from 43° to 62.4°)
import math
radius = 55.289
startAngle = 0.751862   # about 43°
endAngle = 1.090050     # about 62.4°

arc = Part.ArcOfCircle(
    Part.Circle(App.Vector(0,0,0), App.Vector(0,0,1), radius),
    startAngle,
    endAngle
)
sketch.addGeometry([arc], False)

# Constrain arc endpoint to origin
sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))

doc.recompute()