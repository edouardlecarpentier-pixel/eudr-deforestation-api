import requests
import os
from typing import Dict, List, Tuple, Optional
import tempfile
import uuid
from datetime import datetime
import logging
import asyncio
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

logger = logging.getLogger(__name__)

class CopernicusService:
    def __init__(self):
        self.username = os.getenv('COPERNICUS_USERNAME')
        self.password = os.getenv('COPERNICUS_PASSWORD')
        self.api = None
        
        if self.username and self.password:
            try:
                self.api = SentinelAPI(
                    self.username, 
                    self.password, 
                    'https://apihub.copernicus.eu/apihub'
                )
                logger.info("Service Copernicus initialisé avec succès")
            except Exception as e:
                logger.warning(f"Impossible de se connecter à Copernicus: {e}")
                self.api = None
    
    async def get_satellite_image(self, coordinates: List[List[float]], date_range: Tuple[str, str]) -> Dict:
        """
        Récupère une image satellite pour les coordonnées et la période données
        """
        try:
            if not self.api:
                logger.info("Mode démonstration - utilisation d'images simulées")
                return self._get_demo_image(coordinates, date_range)
            
            # Conversion des coordonnées en format WKT
            geojson_polygon = {
                "type": "Polygon",
                "coordinates": [coordinates]
            }
            
            footprint = geojson_to_wkt(geojson_polygon)
            
            # Recherche des produits Sentinel-2
            products = self.api.query(
                footprint,
                date=date_range,
                platformname='Sentinel-2',
                cloudcoverpercentage=(0, 20),
                producttype='S2MSI1C'
            )
            
            if not products:
                logger.warning(f"Aucune image trouvée pour la période {date_range}")
                return self._get_demo_image(coordinates, date_range)
            
            # Sélection du meilleur produit (moins de couverture nuageuse)
            best_product = min(products.items(), 
                             key=lambda x: x[1]['cloudcoverpercentage'])
            
            product_info = best_product[1]
            
            return {
                'url': f"https://scihub.copernicus.eu/dhus/odata/v1/Products('{best_product[0]}')/\$value",
                'date': product_info['beginposition'].strftime('%Y-%m-%d'),
                'cloud_coverage': product_info['cloudcoverpercentage'],
                'resolution': '10m',
                'product_id': best_product[0]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération Copernicus: {str(e)}")
            return self._get_demo_image(coordinates, date_range)
    
    def _get_demo_image(self, coordinates: List[List[float]], date_range: Tuple[str, str]) -> Dict:
        """
        Retourne une image de démonstration
        """
        image_id = str(uuid.uuid4())
        # Calculer le centre des coordonnées pour l'URL
        center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
        
        return {
            'url': f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lon}&zoom=15&size=800x600&maptype=satellite&key=demo",
            'date': date_range[0],
            'cloud_coverage': 5.0,
            'resolution': '10m',
            'product_id': image_id
        }
    
    async def download_image(self, product_id: str, download_path: str) -> str:
        """
        Télécharge une image satellite
        """
        if not self.api:
            raise Exception("Service Copernicus non disponible")
        
        try:
            self.api.download(product_id, download_path)
            return os.path.join(download_path, f"{product_id}.zip")
        except Exception as e:
            logger.error(f"Erreur téléchargement: {e}")
            raise
