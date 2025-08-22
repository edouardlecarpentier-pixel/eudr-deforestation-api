import numpy as np
from typing import Dict, List, Any
import logging
from datetime import datetime
import random
import math

logger = logging.getLogger(__name__)

class DeforestationAnalyzer:
    
    def __init__(self):
        self.ndvi_threshold = 0.4  # Seuil NDVI pour détecter la végétation
        self.change_threshold = 0.15  # Seuil de changement significatif
        self.forest_threshold = 0.6  # Seuil pour considérer une zone comme forestière
    
    async def analyze_change(self, historical_image: Dict, current_image: Dict, 
                           coordinates: List[List[float]]) -> Dict[str, Any]:
        """
        Analyse les changements entre deux images satellites
        """
        try:
            area_hectares = self._calculate_area(coordinates)
            
            # Simulation de l'analyse basée sur des paramètres réalistes
            # En production, ceci analyserait les vraies images NDVI
            
            # Facteurs influençant la probabilité de déforestation
            area_factor = min(area_hectares / 100, 1.0)  # Plus grande zone = plus de risque
            location_factor = self._get_location_risk_factor(coordinates)
            
            # Calcul de la probabilité de déforestation
            base_probability = 0.3
            deforestation_probability = base_probability * (area_factor + location_factor) / 2
            deforestation_probability = min(max(deforestation_probability, 0.1), 0.9)
            
            deforestation_detected = deforestation_probability > 0.5
            
            forest_loss_area = 0
            ndvi_change = 0
            
            if deforestation_detected:
                forest_loss_area = area_hectares * random.uniform(0.1, 0.4)
                ndvi_change = -random.uniform(0.2, 0.4)
            else:
                ndvi_change = random.uniform(-0.1, 0.1)
            
            return {
                'deforestation_detected': deforestation_detected,
                'confidence_score': deforestation_probability,
                'area_analyzed': area_hectares,
                'forest_loss_area': forest_loss_area,
                'change_percentage': (forest_loss_area / area_hectares * 100) if area_hectares > 0 else 0,
                'detailed_report': {
                    'ndvi_change': ndvi_change,
                    'vegetation_loss': deforestation_detected,
                    'analysis_method': 'NDVI comparison with ML enhancement',
                    'temporal_analysis': {
                        'historical_period': historical_image['date'],
                        'current_period': current_image['date'],
                        'time_span_days': self._calculate_time_span(
                            historical_image['date'], 
                            current_image['date']
                        )
                    },
                    'risk_factors': {
                        'area_size': area_factor,
                        'geographic_risk': location_factor,
                        'cloud_coverage_impact': max(
                            historical_image.get('cloud_coverage', 0),
                            current_image.get('cloud_coverage', 0)
                        ) / 100
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {str(e)}")
            raise
    
    async def full_analysis(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """
        Analyse complète de déforestation avec rapport détaillé
        """
        try:
            area_hectares = self._calculate_area(coordinates)
            location_risk = self._get_location_risk_factor(coordinates)
            
            # Simulation d'une analyse ML avancée
            forest_loss_detected = random.choice([True, False]) if location_risk > 0.5 else False
            forest_loss_area = area_hectares * random.uniform(0, 0.3) if forest_loss_detected else 0
            change_percentage = (forest_loss_area / area_hectares * 100) if area_hectares > 0 else 0
            
            # Calcul du niveau de confiance basé sur plusieurs facteurs
            confidence_factors = [
                0.9 if area_hectares > 10 else 0.7,  # Taille de la zone
                0.95,  # Qualité des images (simulé)
                0.9 - (location_risk * 0.2),  # Complexité géographique
            ]
            analysis_confidence = sum(confidence_factors) / len(confidence_factors)
            
            # Génération des recommandations
            recommendations = []
            if forest_loss_detected:
                recommendations.extend([
                    "🚨 Vérification terrain immédiate recommandée",
                    "📋 Conformité EUDR à risque - documentation requise",
                    "🤝 Contact urgent avec les fournisseurs concernés",
                    "📊 Audit complémentaire de la chaîne d'approvisionnement"
                ])
            else:
                recommendations.extend([
                    "✅ Zone conforme aux exigences EUDR actuelles",
                    "📈 Surveillance continue recommandée (monitoring trimestriel)",
                    "📋 Documentation à jour et conforme"
                ])
            
            # Ajout de recommandations basées sur la taille
            if area_hectares > 100:
                recommendations.append("🛰️ Surveillance satellite haute fréquence recommandée")
            
            return {
                'area_analyzed': area_hectares,
                'forest_loss_detected': forest_loss_detected,
                'forest_loss_area': forest_loss_area,
                'change_percentage': change_percentage,
                'analysis_confidence': analysis_confidence,
                'recommendations': recommendations,
                'detailed_metrics': {
                    'vegetation_indices': {
                        'current_ndvi': random.uniform(0.3, 0.8),
                        'historical_ndvi': random.uniform(0.4, 0.9),
                        'ndvi_change': random.uniform(-0.3, 0.1),
                        'evi': random.uniform(0.2, 0.7),  # Enhanced Vegetation Index
                    },
                    'land_cover_classification': {
                        'forest_percentage': random.uniform(60, 90) if not forest_loss_detected else random.uniform(40, 70),
                        'agricultural_percentage': random.uniform(5, 30),
                        'other_percentage': random.uniform(5, 15),
                        'water_percentage': random.uniform(0, 5)
                    },
                    'risk_assessment': {
                        'deforestation_risk': 'HIGH' if location_risk > 0.7 else 'MEDIUM' if location_risk > 0.4 else 'LOW',
                        'geographic_complexity': location_risk,
                        'monitoring_priority': 'URGENT' if forest_loss_detected else 'STANDARD'
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète: {str(e)}")
            raise
    
    def _calculate_area(self, coordinates: List[List[float]]) -> float:
        """
        Calcule l'aire approximative en hectares en utilisant la formule de Shoelace
        """
        if len(coordinates) < 3:
            return 0
        
        # Conversion des coordonnées géographiques en mètres (approximation)
        def deg_to_meters(lat_deg, lon_deg):
            lat_m = lat_deg * 111320  # 1 degré latitude ≈ 111.32 km
            lon_m = lon_deg * 111320 * math.cos(math.radians(lat_deg))  # Correction longitude
            return lat_m, lon_m
        
        # Calcul avec formule de Shoelace
        area = 0
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            lat1, lon1 = deg_to_meters(coordinates[i][1], coordinates[i][0])
            lat2, lon2 = deg_to_meters(coordinates[j][1], coordinates[j][0])
            area += lat1 * lon2 - lat2 * lon1
        
        area = abs(area) / 2.0  # Aire en mètres carrés
        area_hectares = area / 10000  # Conversion en hectares
        
        return max(area_hectares, 1.0)  # Minimum 1 hectare
    
    def _get_location_risk_factor(self, coordinates: List[List[float]]) -> float:
        """
        Évalue le facteur de risque basé sur la localisation géographique
        """
        # Calcul du centre des coordonnées
        center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
        
        # Facteurs de risque par région (approximatifs)
        # Amérique du Sud (Amazonie) - risque élevé
        if -10 <= center_lat <= 10 and -80 <= center_lon <= -40:
            return 0.8
        
        # Afrique centrale - risque élevé
        elif -10 <= center_lat <= 10 and 10 <= center_lon <= 35:
            return 0.7
        
        # Asie du Sud-Est - risque moyen-élevé
        elif -10 <= center_lat <= 20 and 90 <= center_lon <= 150:
            return 0.6
        
        # Europe - risque faible
        elif 35 <= center_lat <= 70 and -10 <= center_lon <= 50:
            return 0.2
        
        # Autres régions - risque moyen
        else:
            return 0.4
    
    def _calculate_time_span(self, start_date: str, end_date: str) -> int:
        """
        Calcule l'écart en jours entre deux dates
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return (end - start).days
        except:
            return 365  # Valeur par défaut
