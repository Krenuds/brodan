import httpx
import asyncio
import time
import logging
from typing import Dict, List, Tuple

# Configure logging for service checker
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ServiceChecker:
    """Utility to check if all required services are ready before bot startup"""
    
    def __init__(self):
        self.services = {
            'whisper-stt': {
                'url': 'http://whisper-stt:9000/docs',
                'name': 'STT Service'
            },
            'piper-tts': {
                'url': 'http://piper-tts:8080/health',
                'name': 'TTS Service'
            }
        }
        self.max_wait_time = 120  # Maximum time to wait for services (2 minutes)
        self.check_interval = 3   # Check every 3 seconds
        
    async def wait_for_all_services(self) -> bool:
        """Wait for all services to be ready with progress reporting"""
        print("🔍 Checking service readiness before bot startup...")
        
        start_time = time.time()
        
        while time.time() - start_time < self.max_wait_time:
            service_status = await self._check_all_services()
            ready_services = [name for name, ready in service_status.items() if ready]
            pending_services = [name for name, ready in service_status.items() if not ready]
            
            if not pending_services:
                print("✅ All services are ready!")
                return True
            
            # Progress reporting
            elapsed = int(time.time() - start_time)
            print(f"⏳ [{elapsed}s] Ready: {', '.join(ready_services) if ready_services else 'None'} | "
                  f"Waiting: {', '.join(pending_services)}")
            
            await asyncio.sleep(self.check_interval)
        
        # Timeout reached
        final_status = await self._check_all_services()
        failed_services = [name for name, ready in final_status.items() if not ready]
        
        print(f"❌ Timeout reached! Failed services: {', '.join(failed_services)}")
        return False
    
    async def _check_all_services(self) -> Dict[str, bool]:
        """Check readiness of all services"""
        results = {}
        
        # Check all services concurrently
        tasks = []
        for service_id, config in self.services.items():
            task = asyncio.create_task(
                self._check_service_health(service_id, config['url'], config['name'])
            )
            tasks.append((service_id, task))
        
        # Wait for all checks to complete
        for service_id, task in tasks:
            try:
                results[self.services[service_id]['name']] = await task
            except Exception as e:
                logger.debug(f"Error checking {service_id}: {e}")
                results[self.services[service_id]['name']] = False
        
        return results
    
    async def _check_service_health(self, service_id: str, url: str, name: str) -> bool:
        """Check if a specific service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                healthy = response.status_code == 200
                
                if healthy:
                    logger.debug(f"✅ {name} is ready")
                else:
                    logger.debug(f"❌ {name} returned status {response.status_code}")
                
                return healthy
                
        except httpx.ConnectError:
            logger.debug(f"🔌 {name} connection refused")
            return False
        except httpx.TimeoutException:
            logger.debug(f"⏱️ {name} timeout")
            return False
        except Exception as e:
            logger.debug(f"❌ {name} error: {e}")
            return False
    
    async def verify_service_endpoints(self) -> List[Tuple[str, bool, str]]:
        """Verify all service endpoints and return detailed status"""
        results = []
        
        for service_id, config in self.services.items():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(config['url'])
                    success = response.status_code == 200
                    status_msg = f"HTTP {response.status_code}"
                    
                    results.append((config['name'], success, status_msg))
                    
            except Exception as e:
                results.append((config['name'], False, str(e)))
        
        return results

# Convenience function for easy use in bot.py
async def wait_for_services() -> bool:
    """Wait for all required services to be ready"""
    checker = ServiceChecker()
    return await checker.wait_for_all_services()

async def check_service_status() -> List[Tuple[str, bool, str]]:
    """Get detailed status of all services"""
    checker = ServiceChecker()
    return await checker.verify_service_endpoints()