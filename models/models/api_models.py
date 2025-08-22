from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class GeoJSONRequest(BaseModel):
    geojson: Dict[str, Any]
    analysis_type: Optional[str] = "deforestation"
    
class SatelliteImage(BaseModel):
    url: str
    date: str
    cloud_coverage: float
    resolution: str
    product_id: Optional[str] = None
    
class EUDRResponse(BaseModel):
    coordinates: List[List[float]]
    is_eudr_compliant: bool
    deforestation_detected: bool
    analysis_date: str
    confidence_score: float
    current_image_url: str
    historical_image_url: str
    report: Dict[str, Any]

class SatelliteImageResponse(BaseModel):
    coordinates: List[List[float]]
    current_image: SatelliteImage
    historical_image: SatelliteImage
    retrieved_at: str

class DeforestationReport(BaseModel):
    area_analyzed: float  # en hectares
    forest_loss_detected: bool
    forest_loss_area: float  # en hectares
    change_percentage: float
    analysis_confidence: float
    recommendations: List[str]
    detailed_metrics: Dict[str, Any]

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
