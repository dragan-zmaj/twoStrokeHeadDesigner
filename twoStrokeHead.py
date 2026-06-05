import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, asdict

@dataclass
class headDimensions:
    pistonCrownDiameter: float
    chamberWidth: float
    ellipsoidHeight: float
    chamberHeight: float

def calcHead(
    bore: float = 42e-3,
    trappedCompressionRatio: float = 9,
    pistonCrownHeight: float = 1.5e-3,
    squishBandAreaRatio: float = 0.5,
    squishBandDistance: float = 0.5e-3,
    exhaustX: float = 25.7e-3,
    sparkPlugVolume: float = 0,
    sparkPlugDiameter: float = 10e-3
) -> headDimensions:
    """
    Calculate combustion head geometry for two-stroke engines.
    
    All dimensions in meters (SI units).
    """
    
    sparkPlugRadius = sparkPlugDiameter / 2
    
    # Piston crown geometry
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
        return None
    
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
    
    ellipsoidHeight = (3 * chamberVolume * sinSquish * sqrt_term) / (term1 + term2)
    
    chamberWidth = 2 * sinSquish
    chamberHeight = np.sqrt(
        ellipsoidHeight**2 - (sparkPlugRadius**2 * ellipsoidHeight**2) / (pistonCrownRadius * np.sin(squishBandAngle))**2
    )
    
    # Convert to mm for output
    return headDimensions(
        pistonCrownDiameter=2e3 * pistonCrownRadius,
        chamberWidth=1e3 * chamberWidth,
        ellipsoidHeight=1e3 * ellipsoidHeight,
        chamberHeight=1e3 * chamberHeight
    )


if __name__ == "__main__":
    # Run with default parameters (matching your MATLAB example)
    result = calcHead()
    
    if result:
        print("\n=== Combustion Head Dimensions ===")
        print(f"Piston Crown Diameter: {result.pistonCrownDiameter:.3f} mm")
        print(f"Chamber Width:          {result.chamberWidth:.3f} mm")
        print(f"Ellipsoid Height:       {result.ellipsoidHeight:.3f} mm")
        print(f"Chamber Height:         {result.chamberHeight:.3f} mm")