"""
Space Data Loader - Enhanced space exploration data ingestion
Integrates multiple space data sources for comprehensive knowledge base
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Generator
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from ..core.config import config
    from ..core.retrievers import Document
except ImportError:
    # Fallback for when running independently
    class Document:
        def __init__(self, content: str, metadata: dict):
            self.content = content
            self.metadata = metadata
    
    class MockConfig:
        def get(self, key, default=None):
            return default
    
    config = MockConfig()

logger = logging.getLogger(__name__)


class SpaceDataLoader:
    """Enhanced space data loader with multiple API integrations"""
    
    def __init__(self):
        self.config = config
        self.nasa_api_key = config.get('data_sources.nasa_api_key', 'DEMO_KEY')
        self.base_urls = {
            'nasa_apod': 'https://api.nasa.gov/planetary/apod',
            'nasa_images': 'https://images-api.nasa.gov',
            'nasa_techport': 'https://api.nasa.gov/techport/api',
            'nasa_mars_weather': 'https://api.nasa.gov/insight_weather',
            'iss_position': 'http://api.open-notify.org/iss-now.json',
            'spacex_launches': 'https://api.spacexdata.com/v4/launches',
            'spacex_rockets': 'https://api.spacexdata.com/v4/rockets',
            'neo_watch': 'https://api.nasa.gov/neo/rest/v1/feed',
            'exoplanets': 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync'
        }
        
        # Data categories for organization
        self.data_categories = {
            "astronomical_objects": {
                "description": "Planets, moons, asteroids, comets, and other celestial bodies",
                "sources": ["neo_watch", "exoplanets", "nasa_images"]
            },
            "space_missions": {
                "description": "Past, current, and planned space missions",
                "sources": ["nasa_techport", "spacex_launches"]
            },
            "spacecraft_technology": {
                "description": "Rockets, satellites, instruments, and propulsion systems",
                "sources": ["spacex_rockets", "nasa_techport"]
            },
            "real_time_data": {
                "description": "Current space conditions and tracking data",
                "sources": ["iss_position", "nasa_mars_weather"]
            },
            "educational_content": {
                "description": "Space education and outreach materials",
                "sources": ["nasa_apod", "nasa_images"]
            }
        }
        
        self.processed_documents = 0
        self.failed_requests = 0
    
    async def load_comprehensive_space_data(self) -> Dict[str, Any]:
        """Load comprehensive space data from multiple sources"""
        
        logger.info("🚀 Starting comprehensive space data loading...")
        
        # Create tasks for parallel data loading
        tasks = [
            self._load_nasa_apod_data(),
            self._load_nasa_missions_data(),
            self._load_spacex_data(),
            self._load_celestial_bodies_data(),
            self._load_real_time_space_data(),
            self._load_exoplanet_data(),
            self._load_space_technology_data()
        ]
        
        # Execute all loading tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all documents
        all_documents = []
        successful_sources = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Data source {i} failed: {result}")
                self.failed_requests += 1
            else:
                all_documents.extend(result)
                successful_sources.append(i)
        
        logger.info(f"✅ Loaded {len(all_documents)} documents from {len(successful_sources)} sources")
        
        return {
            "success": True,
            "total_documents": len(all_documents),
            "documents": all_documents,
            "successful_sources": len(successful_sources),
            "failed_requests": self.failed_requests,
            "categories": list(self.data_categories.keys())
        }
    
    async def _load_nasa_apod_data(self) -> List[Document]:
        """Load NASA Astronomy Picture of the Day data (simulated)"""
        documents = []
        
        try:
            # Simulated APOD data for demo
            apod_samples = [
                {
                    "title": "NGC 6302: The Butterfly Nebula",
                    "date": "2025-01-20",
                    "explanation": "The bright clusters and nebulae of planet Earth's night sky are often named for flowers or insects. Though its wingspan covers over 3 light-years, NGC 6302 is no exception. With an estimated surface temperature of about 36,000 degrees C, the dying central star of this particular planetary nebula has become exceptionally hot.",
                    "url": "https://apod.nasa.gov/apod/image/2501/ngc6302_hst_3400.jpg",
                    "media_type": "image",
                    "copyright": "NASA, ESA, Hubble"
                },
                {
                    "title": "The Pleiades Star Cluster",
                    "date": "2025-01-19", 
                    "explanation": "Perhaps the most famous star cluster on the sky, the bright stars of the Pleiades can be seen without binoculars from even the depths of a light-polluted city. Also known as the Seven Sisters and M45, the Pleiades is one of the brightest and closest open clusters.",
                    "url": "https://apod.nasa.gov/apod/image/2501/pleiades_ward_2400.jpg",
                    "media_type": "image",
                    "copyright": "NASA"
                },
                {
                    "title": "Earth's Aurora from the International Space Station",
                    "date": "2025-01-18",
                    "explanation": "Spectacular aurora displays were captured by astronauts aboard the International Space Station as Earth rotated below. These ethereal curtains of light result from collisions between energetic particles from the Sun and molecules in Earth's atmosphere.",
                    "url": "https://apod.nasa.gov/apod/image/2501/aurora_iss_4800.jpg",
                    "media_type": "image",
                    "copyright": "NASA, ISS Expedition"
                }
            ]
            
            for item in apod_samples:
                content = f"""
Title: {item.get('title', 'Unknown')}
Date: {item.get('date', 'Unknown')}
Explanation: {item.get('explanation', 'No explanation available')}
Image URL: {item.get('url', 'No image')}
Copyright: {item.get('copyright', 'NASA')}
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "educational_content",
                        "source": "nasa_apod",
                        "type": "astronomy_image",
                        "date": item.get('date'),
                        "title": item.get('title'),
                        "media_type": item.get('media_type', 'image'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"📷 Loaded {len(documents)} APOD entries")
            await asyncio.sleep(0.5)  # Simulate network delay
        
        except Exception as e:
            logger.error(f"Failed to load NASA APOD data: {e}")
        
        return documents
    
    async def _load_nasa_missions_data(self) -> List[Document]:
        """Load NASA missions and projects data (simulated)"""
        documents = []
        
        try:
            # Simulated NASA mission data
            missions = [
                {
                    "title": "Artemis III",
                    "description": "NASA's mission to return humans to the Moon and establish sustainable lunar exploration. This historic mission will land the first woman and first person of color on the lunar surface, focusing on the Moon's South Pole region.",
                    "status": "In Development",
                    "startDate": "2024-01-01",
                    "endDate": "2026-12-31",
                    "program": "Artemis Program",
                    "technologyAreas": ["Lunar Surface Operations", "Life Support Systems", "Propulsion", "Spacesuits", "Landing Systems"],
                    "benefits": "Sustainable lunar presence, scientific discovery, technology demonstration, and stepping stone to Mars exploration",
                    "budget": "$93 billion (program total)",
                    "crew": "4 astronauts",
                    "duration": "6.5 days on lunar surface"
                },
                {
                    "title": "Europa Clipper",
                    "description": "Flagship mission to study Jupiter's moon Europa and its subsurface ocean. The spacecraft will perform detailed reconnaissance to investigate Europa's habitability and potential for life.",
                    "status": "Active",
                    "startDate": "2024-10-14",
                    "endDate": "2034-01-01",
                    "program": "Discovery Program",
                    "technologyAreas": ["Planetary Science", "Astrobiology", "Remote Sensing", "Radiation Shielding"],
                    "benefits": "Understanding Europa's potential for harboring life, subsurface ocean characteristics, and ice shell dynamics",
                    "budget": "$5.2 billion",
                    "instruments": "9 scientific instruments including cameras, spectrometers, and radar",
                    "orbits": "49 close flybys of Europa"
                },
                {
                    "title": "OSIRIS-APEX",
                    "description": "Extended mission to study asteroid Apophis using the OSIRIS-REx spacecraft. Will provide detailed observations of this potentially hazardous asteroid during its close approach to Earth.",
                    "status": "Active",
                    "startDate": "2023-09-01",
                    "endDate": "2029-06-01",
                    "program": "New Frontiers",
                    "technologyAreas": ["Asteroid Science", "Spacecraft Navigation", "Planetary Defense"],
                    "benefits": "Understanding near-Earth asteroids, planetary defense capabilities, and asteroid composition",
                    "budget": "$200 million (extended mission)",
                    "target": "99942 Apophis asteroid",
                    "approach": "18-month study starting in 2029"
                },
                {
                    "title": "James Webb Space Telescope Operations",
                    "description": "Revolutionary space observatory providing unprecedented infrared observations of the universe. JWST is transforming our understanding of cosmic evolution from the first galaxies to planetary systems.",
                    "status": "Active",
                    "startDate": "2021-12-25",
                    "endDate": "2031-06-01",
                    "program": "Great Observatories",
                    "technologyAreas": ["Space Telescopes", "Infrared Astronomy", "Cryogenic Systems", "Precision Pointing"],
                    "benefits": "Studying early universe, exoplanet atmospheres, star and galaxy formation, and solar system objects",
                    "budget": "$10 billion",
                    "mirror": "6.5-meter segmented primary mirror",
                    "location": "L2 Lagrange point, 1.5 million km from Earth"
                },
                {
                    "title": "Mars Sample Return",
                    "description": "Ambitious multi-mission campaign to collect samples from Mars and return them to Earth for detailed analysis. Collaboration between NASA and ESA to bring Martian samples to terrestrial laboratories.",
                    "status": "In Development",
                    "startDate": "2028-01-01",
                    "endDate": "2033-12-31",
                    "program": "Mars Exploration",
                    "technologyAreas": ["Mars Landing", "Sample Collection", "Mars Ascent", "Interplanetary Transfer"],
                    "benefits": "Definitive search for past life on Mars, understanding Martian geology and climate evolution",
                    "budget": "$11 billion",
                    "phases": "Sample recovery, Mars ascent, Earth return",
                    "samples": "Collecting samples from Perseverance rover"
                },
                {
                    "title": "Gateway Lunar Space Station",
                    "description": "Multi-purpose outpost orbiting the Moon to support deep space exploration. Gateway will serve as a staging point for lunar surface missions and future Mars expeditions.",
                    "status": "In Development",
                    "startDate": "2025-01-01",
                    "endDate": "2030-12-31",
                    "program": "Artemis Program",
                    "technologyAreas": ["Space Stations", "Life Support", "Power Systems", "International Cooperation"],
                    "benefits": "Sustainable lunar exploration, crew safety, international partnerships, deep space preparation",
                    "budget": "$5 billion",
                    "orbit": "Near-rectilinear halo orbit around Moon",
                    "partners": "NASA, ESA, CSA, JAXA"
                },
                {
                    "title": "Dragonfly Titan Mission",
                    "description": "Revolutionary rotorcraft mission to explore Saturn's moon Titan. Dragonfly will fly between different locations on Titan's surface to study its prebiotic chemistry and potential for life.",
                    "status": "In Development",
                    "startDate": "2027-06-01",
                    "endDate": "2036-12-31",
                    "program": "New Frontiers",
                    "technologyAreas": ["Rotorcraft", "Astrobiology", "Atmospheric Flight", "Planetary Science"],
                    "benefits": "Understanding prebiotic chemistry, exploring diverse terrains, searching for signs of life",
                    "budget": "$3.35 billion",
                    "vehicle": "Nuclear-powered dual-quadcopter",
                    "duration": "2.7 years of surface operations"
                },
                {
                    "title": "Roman Space Telescope",
                    "description": "Next-generation space telescope designed to investigate dark energy, dark matter, and exoplanets. Will provide wide-field infrared surveys of unprecedented scale.",
                    "status": "In Development",
                    "startDate": "2027-05-01",
                    "endDate": "2032-05-01",
                    "program": "Astrophysics Flagship",
                    "technologyAreas": ["Space Telescopes", "Dark Energy", "Exoplanet Detection", "Wide-Field Imaging"],
                    "benefits": "Understanding cosmic acceleration, discovering thousands of exoplanets, studying galaxy evolution",
                    "budget": "$4.2 billion",
                    "field": "Field of view 100 times larger than Hubble",
                    "resolution": "Similar to Hubble but much wider coverage"
                }
            ]
            
            for project in missions:
                content = f"""
Project: {project.get('title', 'Unknown Project')}
Description: {project.get('description', 'No description available')}
Status: {project.get('status', 'Unknown')}
Start Date: {project.get('startDate', 'Unknown')}
End Date: {project.get('endDate', 'Ongoing')}
Program: {project.get('program', 'Unknown Program')}
Technology Areas: {', '.join(project.get('technologyAreas', []))}
Benefits: {project.get('benefits', 'No benefits listed')}
Budget: {project.get('budget', 'Not specified')}
Additional Details: {project.get('crew', '')} {project.get('duration', '')} {project.get('instruments', '')} {project.get('orbits', '')} {project.get('target', '')} {project.get('approach', '')} {project.get('mirror', '')} {project.get('location', '')} {project.get('phases', '')} {project.get('samples', '')} {project.get('orbit', '')} {project.get('partners', '')} {project.get('vehicle', '')} {project.get('field', '')} {project.get('resolution', '')}
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "space_missions",
                        "source": "nasa_techport",
                        "type": "mission_project",
                        "project_id": f"sim_{project['title'].replace(' ', '_').lower()}",
                        "title": project.get('title'),
                        "status": project.get('status'),
                        "program": project.get('program'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"🚀 Loaded {len(documents)} NASA mission projects")
            await asyncio.sleep(0.3)  # Simulate network delay
        
        except Exception as e:
            logger.error(f"Failed to load NASA missions data: {e}")
        
        return documents
    
    async def _load_spacex_data(self) -> List[Document]:
        """Load SpaceX launches and rocket data (simulated)"""
        documents = []
        
        try:
            # Simulated SpaceX launch data
            launches = [
                {
                    "name": "Starship IFT-3",
                    "flight_number": "IFT-3",
                    "date_utc": "2024-03-14T13:25:00.000Z",
                    "rocket": "Starship",
                    "success": True,
                    "details": "Third integrated flight test of Starship and Super Heavy",
                    "crew": [],
                    "payloads": ["Starlink Satellites"]
                },
                {
                    "name": "Crew-8",
                    "flight_number": "174",
                    "date_utc": "2024-03-03T07:53:00.000Z",
                    "rocket": "Falcon 9",
                    "success": True,
                    "details": "Eighth operational crewed flight to the International Space Station",
                    "crew": ["Matthew Dominick", "Michael Barratt", "Jeanette Epps", "Alexander Grebenkin"],
                    "payloads": ["Dragon Crew Capsule"]
                }
            ]
            
            for launch in launches:
                content = f"""
Mission: {launch.get('name', 'Unknown Mission')}
Flight Number: {launch.get('flight_number', 'Unknown')}
Date: {launch.get('date_utc', 'Unknown')}
Rocket: {launch.get('rocket', 'Unknown')}
Success: {launch.get('success', 'Unknown')}
Details: {launch.get('details', 'No details available')}
Crew: {', '.join(launch.get('crew', []))}
Payloads: {len(launch.get('payloads', []))} payload(s)
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "space_missions",
                        "source": "spacex_launches",
                        "type": "launch_mission",
                        "flight_number": launch.get('flight_number'),
                        "mission_name": launch.get('name'),
                        "success": launch.get('success'),
                        "date": launch.get('date_utc'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            # Simulated rocket data
            rockets = [
                {
                    "name": "Falcon 9",
                    "type": "Medium Lift",
                    "active": True,
                    "first_flight": "2010-06-04",
                    "height": {"meters": 70},
                    "diameter": {"meters": 3.7},
                    "mass": {"kg": 549054},
                    "description": "Two-stage orbital launch vehicle designed for reliable and safe transport of satellites and crew",
                    "engines": {"number": 9},
                    "success_rate_pct": 97,
                    "cost_per_launch": 62000000
                },
                {
                    "name": "Starship",
                    "type": "Super Heavy Lift",
                    "active": False,
                    "first_flight": "2023-04-20",
                    "height": {"meters": 120},
                    "diameter": {"meters": 9},
                    "mass": {"kg": 5000000},
                    "description": "Fully reusable super heavy-lift launch vehicle designed for Mars missions and deep space exploration",
                    "engines": {"number": 33},
                    "success_rate_pct": 67,
                    "cost_per_launch": 10000000
                }
            ]
            
            for rocket in rockets:
                content = f"""
Rocket: {rocket.get('name', 'Unknown Rocket')}
Type: {rocket.get('type', 'Unknown Type')}
Active: {rocket.get('active', 'Unknown')}
First Flight: {rocket.get('first_flight', 'Unknown')}
Height: {rocket.get('height', {}).get('meters', 'Unknown')} meters
Diameter: {rocket.get('diameter', {}).get('meters', 'Unknown')} meters
Mass: {rocket.get('mass', {}).get('kg', 'Unknown')} kg
Description: {rocket.get('description', 'No description available')}
Engines: {rocket.get('engines', {}).get('number', 'Unknown')} engines
Success Rate: {rocket.get('success_rate_pct', 'Unknown')}%
Cost per Launch: ${rocket.get('cost_per_launch', 'Unknown')}
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "spacecraft_technology",
                        "source": "spacex_rockets",
                        "type": "rocket_specifications",
                        "rocket_name": rocket.get('name'),
                        "active": rocket.get('active'),
                        "success_rate": rocket.get('success_rate_pct'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"🚀 Loaded {len(documents)} SpaceX documents")
            await asyncio.sleep(0.4)  # Simulate network delay
        
        except Exception as e:
            logger.error(f"Failed to load SpaceX data: {e}")
        
        return documents
    
    async def _load_celestial_bodies_data(self) -> List[Document]:
        """Load data about celestial bodies"""
        documents = []
        
        # Static celestial bodies data (planets, major moons)
        celestial_bodies = [
            {
                "name": "Earth",
                "type": "Planet",
                "description": "Third planet from the Sun, the only known planet with life",
                "mass_kg": 5.972e24,
                "radius_km": 6371,
                "distance_from_sun_au": 1.0,
                "orbital_period_days": 365.25,
                "moons": 1,
                "atmosphere": "Nitrogen (78%), Oxygen (21%), other gases"
            },
            {
                "name": "Mars",
                "type": "Planet", 
                "description": "Fourth planet from the Sun, known as the Red Planet",
                "mass_kg": 6.417e23,
                "radius_km": 3390,
                "distance_from_sun_au": 1.52,
                "orbital_period_days": 687,
                "moons": 2,
                "atmosphere": "Carbon dioxide (95%), Argon (2%), Nitrogen (2%)"
            },
            {
                "name": "Moon",
                "type": "Natural Satellite",
                "description": "Earth's only natural satellite, influences tides and has been visited by humans",
                "mass_kg": 7.342e22,
                "radius_km": 1737,
                "distance_from_earth_km": 384400,
                "orbital_period_days": 27.3,
                "surface_gravity": "1.62 m/s²"
            },
            {
                "name": "International Space Station",
                "type": "Artificial Satellite",
                "description": "Large space station in low Earth orbit, international collaboration project",
                "altitude_km": 408,
                "orbital_period_minutes": 93,
                "mass_kg": 420000,
                "crew_capacity": 7,
                "operational_since": "2000"
            }
        ]
        
        try:
            for body in celestial_bodies:
                content = f"""
Name: {body.get('name')}
Type: {body.get('type')}
Description: {body.get('description')}
Mass: {body.get('mass_kg', 'Unknown')} kg
Radius: {body.get('radius_km', 'Unknown')} km
Distance from Sun: {body.get('distance_from_sun_au', 'N/A')} AU
Orbital Period: {body.get('orbital_period_days', body.get('orbital_period_minutes', 'Unknown'))} {'days' if 'orbital_period_days' in body else 'minutes' if 'orbital_period_minutes' in body else ''}
Moons: {body.get('moons', 'N/A')}
Atmosphere: {body.get('atmosphere', 'Unknown')}
Special Features: {body.get('surface_gravity', '')} {body.get('crew_capacity', '')} {body.get('operational_since', '')}
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "astronomical_objects",
                        "source": "celestial_bodies_database",
                        "type": body.get('type', 'unknown').lower().replace(' ', '_'),
                        "name": body.get('name'),
                        "object_type": body.get('type'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"🌍 Loaded {len(documents)} celestial body documents")
        
        except Exception as e:
            logger.error(f"Failed to load celestial bodies data: {e}")
        
        return documents
    
    async def _load_real_time_space_data(self) -> List[Document]:
        """Load real-time space data (simulated)"""
        documents = []
        
        try:
            # Simulated ISS position data
            current_time = time.time()
            simulated_iss = {
                "latitude": "45.8456",
                "longitude": "-123.4567", 
                "timestamp": current_time
            }
            
            content = f"""
International Space Station Current Position
Timestamp: {datetime.fromtimestamp(current_time).isoformat()}
Latitude: {simulated_iss['latitude']}°
Longitude: {simulated_iss['longitude']}°
Altitude: Approximately 408 km above Earth
Orbital Speed: Approximately 27,600 km/h
Crew: Currently 7 astronauts (simulated)
Mission: Continuous scientific research and international cooperation
            """.strip()
            
            doc = Document(
                content=content,
                metadata={
                    "category": "real_time_data",
                    "source": "iss_tracking",
                    "type": "current_position",
                    "latitude": simulated_iss['latitude'],
                    "longitude": simulated_iss['longitude'],
                    "timestamp": current_time,
                    "processed_date": datetime.now().isoformat()
                }
            )
            documents.append(doc)
            
            logger.info(f"🛰️ Loaded {len(documents)} real-time space documents")
            await asyncio.sleep(0.2)  # Simulate network delay
        
        except Exception as e:
            logger.error(f"Failed to load real-time space data: {e}")
        
        return documents
    
    async def _load_exoplanet_data(self) -> List[Document]:
        """Load exoplanet discovery data"""
        documents = []
        
        # Sample exoplanet data (in production, would query NASA Exoplanet Archive)
        exoplanets = [
            {
                "name": "Kepler-452b",
                "discovery_year": 2015,
                "host_star": "Kepler-452",
                "distance_ly": 1402,
                "description": "Earth-sized planet in habitable zone, potential Earth cousin",
                "orbital_period_days": 385,
                "discovery_method": "Transit"
            },
            {
                "name": "TRAPPIST-1e",
                "discovery_year": 2017,
                "host_star": "TRAPPIST-1",
                "distance_ly": 40,
                "description": "One of seven Earth-sized planets in TRAPPIST-1 system",
                "orbital_period_days": 6.1,
                "discovery_method": "Transit"
            },
            {
                "name": "Proxima Centauri b",
                "discovery_year": 2016,
                "host_star": "Proxima Centauri",
                "distance_ly": 4.24,
                "description": "Closest known exoplanet to Earth, potentially habitable",
                "orbital_period_days": 11.2,
                "discovery_method": "Radial Velocity"
            }
        ]
        
        try:
            for planet in exoplanets:
                content = f"""
Exoplanet: {planet.get('name')}
Discovery Year: {planet.get('discovery_year')}
Host Star: {planet.get('host_star')}
Distance from Earth: {planet.get('distance_ly')} light years
Description: {planet.get('description')}
Orbital Period: {planet.get('orbital_period_days')} days
Discovery Method: {planet.get('discovery_method')}
Significance: Located in potentially habitable zone of its star system
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "astronomical_objects",
                        "source": "exoplanet_archive",
                        "type": "exoplanet",
                        "name": planet.get('name'),
                        "discovery_year": planet.get('discovery_year'),
                        "distance_ly": planet.get('distance_ly'),
                        "host_star": planet.get('host_star'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"🪐 Loaded {len(documents)} exoplanet documents")
        
        except Exception as e:
            logger.error(f"Failed to load exoplanet data: {e}")
        
        return documents
    
    async def _load_space_technology_data(self) -> List[Document]:
        """Load space technology and instrument data"""
        documents = []
        
        # Space technology database
        technologies = [
            {
                "name": "James Webb Space Telescope",
                "type": "Space Observatory",
                "launch_date": "2021-12-25",
                "description": "Largest space telescope, infrared observations of distant universe",
                "primary_mirror": "6.5 meters",
                "instruments": ["NIRCam", "NIRSpec", "MIRI", "FGS/NIRISS"],
                "mission_duration": "5-10 years (planned)"
            },
            {
                "name": "Perseverance Rover",
                "type": "Mars Rover",
                "launch_date": "2020-07-30",
                "description": "Advanced rover searching for signs of ancient life on Mars",
                "landing_site": "Jezero Crater",
                "instruments": ["PIXL", "SHERLOC", "SUPERCAM", "Mastcam-Z"],
                "mission_duration": "At least 2 years (ongoing)"
            },
            {
                "name": "Falcon Heavy",
                "type": "Heavy Launch Vehicle",
                "first_flight": "2018-02-06",
                "description": "Most powerful operational rocket, reusable heavy-lift launch vehicle",
                "payload_capacity": "63,800 kg to LEO",
                "configuration": "Triple-core rocket with side boosters",
                "applications": "Heavy satellite deployment, deep space missions"
            }
        ]
        
        try:
            for tech in technologies:
                content = f"""
Technology: {tech.get('name')}
Type: {tech.get('type')}
Launch/First Flight: {tech.get('launch_date', tech.get('first_flight', 'Unknown'))}
Description: {tech.get('description')}
Key Specifications: {tech.get('primary_mirror', tech.get('payload_capacity', tech.get('landing_site', 'Various specifications')))}
Instruments/Configuration: {', '.join(tech.get('instruments', [tech.get('configuration', 'Standard configuration')]))}
Mission Duration: {tech.get('mission_duration', tech.get('applications', 'Ongoing operations'))}
                """.strip()
                
                doc = Document(
                    content=content,
                    metadata={
                        "category": "spacecraft_technology",
                        "source": "space_technology_database",
                        "type": tech.get('type', 'unknown').lower().replace(' ', '_'),
                        "name": tech.get('name'),
                        "technology_type": tech.get('type'),
                        "processed_date": datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            logger.info(f"🔧 Loaded {len(documents)} space technology documents")
        
        except Exception as e:
            logger.error(f"Failed to load space technology data: {e}")
        
        return documents
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """Get data loading statistics"""
        return {
            "processed_documents": self.processed_documents,
            "failed_requests": self.failed_requests,
            "success_rate": self.processed_documents / (self.processed_documents + self.failed_requests) if (self.processed_documents + self.failed_requests) > 0 else 0.0,
            "supported_categories": list(self.data_categories.keys()),
            "data_sources": list(self.base_urls.keys()),
            "categories_info": self.data_categories
        }


# Global space data loader instance
_space_data_loader = None


def get_space_data_loader() -> SpaceDataLoader:
    """Get global space data loader instance"""
    global _space_data_loader
    if _space_data_loader is None:
        _space_data_loader = SpaceDataLoader()
    return _space_data_loader