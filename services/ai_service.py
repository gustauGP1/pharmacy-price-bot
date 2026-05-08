"""
AI service using Groq API.
Provides intelligent search query processing and suggestions.
"""

from typing import Optional, List, Dict, Any
import time

from groq import AsyncGroq
from groq import APIError, RateLimitError

from config.settings import get_settings
from utils.logger import logger


class AIService:
    """
    AI service using Groq API for intelligent query processing.
    Uses Llama 3 for natural language understanding.
    """
    
    def __init__(self):
        """Initialize AI service."""
        self.settings = get_settings()
        self.client: Optional[AsyncGroq] = None
        self._is_initialized = False
    
    def initialize(self) -> None:
        """Initialize Groq client."""
        try:
            if not self.settings.ai_enabled:
                logger.warning("⚠️ AI is disabled in settings")
                return
            
            logger.info("🤖 Initializing Groq AI client...")
            
            self.client = AsyncGroq(
                api_key=self.settings.groq_api_key,
            )
            
            self._is_initialized = True
            logger.info(f"✅ Groq AI initialized with model: {self.settings.groq_model}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq AI: {e}")
            self._is_initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if AI service is initialized."""
        return self._is_initialized and self.client is not None
    
    async def _call_groq(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Call Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            str: AI response or None
        """
        if not self.is_initialized:
            return None
        
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            duration = int((time.time() - start_time) * 1000)
            logger.debug(f"Groq API call completed in {duration}ms")
            
            return response.choices[0].message.content
            
        except RateLimitError as e:
            logger.warning(f"⚠️ Groq rate limit exceeded: {e}")
            return None
        except APIError as e:
            logger.error(f"❌ Groq API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error calling Groq: {e}")
            return None
    
    async def normalize_query(self, query: str) -> str:
        """
        Normalize search query using AI.
        Corrects spelling, removes unnecessary words, standardizes format.
        
        Args:
            query: User's search query
            
        Returns:
            str: Normalized query
        """
        if not self.is_initialized:
            return query.lower().strip()
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente que normaliza búsquedas de medicamentos en Chile. "
                        "Tu tarea es corregir errores ortográficos, estandarizar nombres de medicamentos, "
                        "y devolver SOLO el nombre del medicamento normalizado, sin explicaciones adicionales. "
                        "Si el usuario busca un medicamento genérico, usa el nombre genérico. "
                        "Si busca una marca, mantén el nombre de la marca."
                    )
                },
                {
                    "role": "user",
                    "content": f"Normaliza esta búsqueda de medicamento: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.1, max_tokens=50)
            
            if response:
                normalized = response.strip().lower()
                logger.info(f"Query normalized: '{query}' -> '{normalized}'")
                return normalized
            
            return query.lower().strip()
            
        except Exception as e:
            logger.warning(f"Error normalizing query: {e}")
            return query.lower().strip()
    
    async def correct_spelling(self, query: str) -> str:
        """
        Correct spelling errors in query.
        
        Args:
            query: User's search query
            
        Returns:
            str: Corrected query
        """
        if not self.is_initialized:
            return query
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un corrector ortográfico especializado en nombres de medicamentos chilenos. "
                        "Corrige SOLO errores ortográficos evidentes. "
                        "Devuelve únicamente el texto corregido, sin explicaciones."
                    )
                },
                {
                    "role": "user",
                    "content": f"Corrige esta búsqueda: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.1, max_tokens=50)
            
            if response:
                corrected = response.strip()
                if corrected.lower() != query.lower():
                    logger.info(f"Spelling corrected: '{query}' -> '{corrected}'")
                return corrected
            
            return query
            
        except Exception as e:
            logger.warning(f"Error correcting spelling: {e}")
            return query
    
    async def suggest_alternatives(
        self,
        query: str,
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Suggest alternative search terms.
        
        Args:
            query: User's search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List[str]: List of alternative queries
        """
        if not self.is_initialized:
            return []
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente farmacéutico en Chile. "
                        f"Sugiere {max_suggestions} alternativas de búsqueda para medicamentos. "
                        "Incluye nombres genéricos, marcas comerciales, y variaciones comunes. "
                        "Devuelve SOLO una lista separada por comas, sin numeración ni explicaciones."
                    )
                },
                {
                    "role": "user",
                    "content": f"Sugiere alternativas para: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.5, max_tokens=100)
            
            if response:
                # Parse comma-separated suggestions
                suggestions = [s.strip() for s in response.split(",")]
                suggestions = [s for s in suggestions if s and len(s) > 2]
                logger.info(f"Generated {len(suggestions)} suggestions for '{query}'")
                return suggestions[:max_suggestions]
            
            return []
            
        except Exception as e:
            logger.warning(f"Error generating suggestions: {e}")
            return []
    
    async def extract_medicine_info(self, query: str) -> Dict[str, Any]:
        """
        Extract structured information from query.
        
        Args:
            query: User's search query
            
        Returns:
            dict: Extracted information (name, dosage, presentation, etc.)
        """
        if not self.is_initialized:
            return {"name": query, "dosage": None, "presentation": None}
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente que extrae información estructurada de búsquedas de medicamentos. "
                        "Extrae: nombre del medicamento, dosis (ej: 500mg), y presentación (ej: 20 comprimidos). "
                        "Responde en formato JSON con las claves: name, dosage, presentation. "
                        "Si no encuentras algún dato, usa null."
                    )
                },
                {
                    "role": "user",
                    "content": f"Extrae información de: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.1, max_tokens=150)
            
            if response:
                import json
                try:
                    info = json.loads(response)
                    logger.debug(f"Extracted info from '{query}': {info}")
                    return info
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI response as JSON")
            
            return {"name": query, "dosage": None, "presentation": None}
            
        except Exception as e:
            logger.warning(f"Error extracting medicine info: {e}")
            return {"name": query, "dosage": None, "presentation": None}
    
    async def is_medicine_query(self, query: str) -> bool:
        """
        Determine if query is about medicine/pharmacy products.
        
        Args:
            query: User's query
            
        Returns:
            bool: True if medicine-related
        """
        if not self.is_initialized:
            # Simple heuristic fallback
            medicine_keywords = [
                "mg", "ml", "comprimido", "cápsula", "tableta",
                "jarabe", "crema", "gel", "gotas", "ampolla"
            ]
            query_lower = query.lower()
            return any(keyword in query_lower for keyword in medicine_keywords)
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Determina si una búsqueda es sobre medicamentos o productos farmacéuticos. "
                        "Responde SOLO 'sí' o 'no', sin explicaciones."
                    )
                },
                {
                    "role": "user",
                    "content": f"¿Esta búsqueda es sobre medicamentos?: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.1, max_tokens=10)
            
            if response:
                return "sí" in response.lower() or "si" in response.lower()
            
            return True  # Default to True if uncertain
            
        except Exception as e:
            logger.warning(f"Error checking if medicine query: {e}")
            return True
    
    async def generate_search_tips(self, query: str) -> Optional[str]:
        """
        Generate helpful search tips for user.
        
        Args:
            query: User's search query
            
        Returns:
            str: Search tips or None
        """
        if not self.is_initialized:
            return None
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente farmacéutico amigable. "
                        "Da un consejo breve (máximo 2 líneas) para mejorar la búsqueda de medicamentos. "
                        "Sé conciso y útil."
                    )
                },
                {
                    "role": "user",
                    "content": f"Dame un consejo para buscar: {query}"
                }
            ]
            
            response = await self._call_groq(messages, temperature=0.7, max_tokens=100)
            
            if response:
                return response.strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Error generating search tips: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on AI service.
        
        Returns:
            dict: Health status
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "not_initialized",
                    "healthy": False,
                }
            
            # Test with simple query
            start_time = time.time()
            response = await self._call_groq(
                [{"role": "user", "content": "test"}],
                max_tokens=10
            )
            duration = int((time.time() - start_time) * 1000)
            
            return {
                "status": "connected",
                "healthy": response is not None,
                "model": self.settings.groq_model,
                "response_time_ms": duration,
            }
            
        except Exception as e:
            logger.error(f"❌ AI health check failed: {e}")
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get or create AI service instance.
    
    Returns:
        AIService: AI service instance
    """
    global _ai_service
    
    if _ai_service is None:
        _ai_service = AIService()
        _ai_service.initialize()
    
    return _ai_service


__all__ = [
    "AIService",
    "get_ai_service",
]

# Made with Bob