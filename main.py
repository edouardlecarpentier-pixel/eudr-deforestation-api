from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import logging

from services.copernicus_service import CopernicusService
from services.deforestation_analyzer import DeforestationAnalyzer
from services.cache_service import CacheService
from services.notification_service import NotificationService
from models.api_models import (
    GeoJSONRequest, 
    EUDRResponse, 
    SatelliteImageResponse,
    DeforestationReport
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EUDR Deforestation Compliance API",
    description="API pour vérifier la conformité EUDR et détecter la déforestation via Copernicus",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services
copernicus_service = CopernicusService()
deforestation_analyzer = DeforestationAnalyzer()
cache_service = CacheService()
notification_service = NotificationService()

@app.get("/")
async def root():
    return {
        "message": "EUDR Deforestation Compliance API",
        "version": "1.0.0",
        "endpoints": {
            "check_compliance": "/api/v1/eudr/check",
            "get_satellite_images": "/api/v1/satellite/images",
            "analyze_deforestation": "/api/v1/analyze/deforestation"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "copernicus": "connected" if copernicus_service.api else "demo_mode",
            "cache": "connected" if cache_service.redis_client else "disabled",
            "notifications": "configured" if notification_service.smtp_username else "disabled"
        }
    }

@app.post("/api/v1/eudr/check", response_model=EUDRResponse)
async def check_eudr_compliance(request: GeoJSONRequest):
    """
    Vérifie la conformité EUDR pour des coordonnées données
    """
    try:
        # Vérifier le cache d'abord
        cache_key = f"eudr_check_{hash(str(request.geojson['coordinates']))}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info("Résultat récupéré depuis le cache")
            return EUDRResponse(**cached_result)
        
        # Validation des coordonnées
        if not request.geojson or not request.geojson.get('coordinates'):
            raise HTTPException(status_code=400, detail="Coordonnées GeoJSON invalides")
        
        # Récupération des images satellites
        current_image = await copernicus_service.get_satellite_image(
            coordinates=request.geojson['coordinates'],
            date_range=("2023-01-01", "2024-12-31")
        )
        
        historical_image = await copernicus_service.get_satellite_image(
            coordinates=request.geojson['coordinates'],
            date_range=("2019-01-01", "2020-12-31")
        )
        
        # Analyse de déforestation
        analysis_result = await deforestation_analyzer.analyze_change(
            historical_image, current_image, request.geojson['coordinates']
        )
        
        # Détermination de la conformité EUDR
        is_compliant = analysis_result['deforestation_detected'] == False
        
        response_data = {
            "coordinates": request.geojson['coordinates'],
            "is_eudr_compliant": is_compliant,
            "deforestation_detected": analysis_result['deforestation_detected'],
            "analysis_date": datetime.now().isoformat(),
            "confidence_score": analysis_result['confidence_score'],
            "current_image_url": current_image['url'],
            "historical_image_url": historical_image['url'],
            "report": analysis_result['detailed_report']
        }
        
        # Mettre en cache le résultat
        await cache_service.set(cache_key, response_data, ttl=3600)
        
        # Envoyer notification si déforestation détectée
        if analysis_result['deforestation_detected']:
            await notification_service.send_deforestation_alert(
                analysis_result, 
                [os.getenv('ALERT_EMAIL', 'admin@example.com')]
            )
        
        return EUDRResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification EUDR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/api/v1/satellite/images", response_model=SatelliteImageResponse)
async def get_satellite_images(request: GeoJSONRequest):
    """
    Récupère les images satellites pour des coordonnées données
    """
    try:
        current_images = await copernicus_service.get_satellite_image(
            coordinates=request.geojson['coordinates'],
            date_range=("2023-01-01", "2024-12-31")
        )
        
        historical_images = await copernicus_service.get_satellite_image(
            coordinates=request.geojson['coordinates'],
            date_range=("2019-01-01", "2020-12-31")
        )
        
        return SatelliteImageResponse(
            coordinates=request.geojson['coordinates'],
            current_image=current_images,
            historical_image=historical_images,
            retrieved_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des images: {str(e)}")

@app.post("/api/v1/analyze/deforestation", response_model=DeforestationReport)
async def analyze_deforestation(request: GeoJSONRequest):
    """
    Analyse détaillée de déforestation
    """
    try:
        result = await deforestation_analyzer.full_analysis(
            coordinates=request.geojson['coordinates']
        )
        
        return DeforestationReport(**result)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de déforestation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
