# services/getcourse.py
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class GetCourseService:
    
    def __init__(self):
        self.api_base_url = settings.GETCOURSE_API_URL  
        self.api_key = settings.GETCOURSE_SECRET_KEY 
    
    async def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        logger.debug(f"GetCourse API response: {response_text}")
                        return await response.json()
                    else:
                        logger.warning(f"GetCourse API returned status {response.status} for {url}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"GetCourse API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GetCourse request: {e}")
            return None
    
    def _is_user_found_in_export(self, exports_data: Dict[str, Any]) -> bool:
        try:
            if not exports_data or not exports_data.get("success"):
                return False
            
            info = exports_data.get("info", {})
            items = info.get("items", [])
            
            if not items or len(items) == 0:
                logger.debug("No items in export data")
                return False
            
            first_item = items[0]
            if not first_item or len(first_item) == 0:
                logger.debug("First item is empty")
                return False
            
            first_field = str(first_item[0]).strip()
            second_field = str(first_item[1]).strip() if len(first_item) > 1 else ""
            
            if first_field == "-1":
                logger.debug("User ID is -1 (not found)")
                return False
            
            if "Пользователь не найден" in second_field or "не найден" in second_field.lower():
                logger.debug(f"User not found message detected: {second_field}")
                return False
            
            if "User not found" in second_field or "not found" in second_field.lower():
                logger.debug(f"User not found message detected: {second_field}")
                return False

            has_real_data = any(
                str(field).strip() and str(field).strip() != "-1" 
                for field in first_item[2:5] 
            )
            
            if not has_real_data:
                logger.debug("No real user data found in fields")
                return False
            
            logger.debug("User found in export data")
            return True
            
        except Exception as e:
            logger.error(f"Error checking if user found in export: {e}")
            return False
    
    async def verify_user(self, email: str) -> bool:
        try:
            users_url = f"{self.api_base_url}/account/users?key={self.api_key}&email={email}"
            users_data = await self._make_request(users_url)
            
            logger.debug(f"Users API response for {email}: {users_data}")
            
            if not users_data or not users_data.get("success"):
                logger.warning(f"User check failed for {email}: {users_data.get('error_message', 'Unknown error') if users_data else 'No response'}")
                return False
            
            export_id = users_data.get("info", {}).get("export_id")
            if not export_id:
                logger.warning(f"No export_id found for {email}")
                return False
            
            await asyncio.sleep(5)
            
            exports_url = f"{self.api_base_url}/account/exports/{export_id}?key={self.api_key}"
            logger.debug(f"Fetching exports from: {exports_url}")
            
            exports_data = await self._make_request(exports_url)
            logger.debug(f"Exports API response for {email}: {exports_data}")
            
            if exports_data and exports_data.get("success"):
                if self._is_user_found_in_export(exports_data):
                    logger.info(f"✅ GetCourse verification successful for {email}")
                    return True
                else:
                    logger.warning(f"❌ User {email} not found in export data (despite success=true)")
                    return False
            else:
                error_msg = exports_data.get('error_message', 'Unknown error') if exports_data else 'No response'
                logger.warning(f"❌ Export check failed for {email}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"GetCourse verification error for {email}: {e}")
            return False
    
    async def get_user_info(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            users_url = f"{self.api_base_url}/account/users?key={self.api_key}&email={email}"
            users_data = await self._make_request(users_url)
            
            if not users_data or not users_data.get("success"):
                return None
            
            export_id = users_data.get("info", {}).get("export_id")
            if not export_id:
                return None
            
            await asyncio.sleep(5)
            
            exports_url = f"{self.api_base_url}/account/exports/{export_id}?key={self.api_key}"
            exports_data = await self._make_request(exports_url)
            
            if not exports_data or not exports_data.get("success"):
                return None
            
            if not self._is_user_found_in_export(exports_data):
                logger.debug(f"User {email} not found in GetCourse")
                return None
            
            info = exports_data.get("info", {})
            fields = info.get("fields", [])
            items = info.get("items", [])
            
            if not items or len(items) == 0:
                return None
            
            user_data_row = items[0]
            

            user_info = {
                "email": email,
                "registered": True,
                "export_id": export_id
            }

            for i, field_name in enumerate(fields):
                if i < len(user_data_row):
                    value = user_data_row[i]
                    if value and str(value).strip() and str(value).strip() != "-1":
                        clean_field = field_name.strip().lower().replace(" ", "_")
                        user_info[clean_field] = value
            
            logger.info(f"Retrieved user info for {email}: {list(user_info.keys())}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting GetCourse user info for {email}: {e}")
            return None
    
    async def check_user_access(self, email: str, course_id: Optional[str] = None) -> bool:
        try:
            user_info = await self.get_user_info(email)
            
            if not user_info or not user_info.get("registered"):
                logger.debug(f"User {email} not registered or info not found")
                return False
            
            if not course_id:
                logger.debug(f"User {email} is registered (no course check)")
                return True
            
            course_fields = [
                f"завершил_курс_{course_id}",
                f"course_{course_id}_completed",
                "завершил_курс_по_инвестициям",  #
                "завершил_курс_по_сайтам"
            ]
            
            for field in course_fields:
                if field.lower() in user_info:
                    course_status = str(user_info[field.lower()]).lower()
                    if course_status in ["да", "yes", "true", "1", "completed"]:
                        logger.info(f"User {email} has access to course {course_id}")
                        return True
            
            logger.warning(f"Course access check not definitive for {email}; assuming registered = access")
            return True
            
        except Exception as e:
            logger.error(f"Error checking user access for {email}: {e}")
            return False


getcourse_service = GetCourseService()