import openai
from typing import List, Dict, Any
from app.config import settings
from app.models.request_models import UserPreferences
from app.models.response_models import RecommendationResponse, BookRecommendation, TasteProfile
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class GPTService:
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)  # Use AsyncOpenAI
    
    async def generate_recommendations(self, movies: List[str], preferences: UserPreferences = None) -> List[RecommendationResponse]:
        """
        Generate unified book recommendations based on user's overall taste profile
        derived from their movie preferences
        """
        prompt = self._build_unified_prompt(movies, preferences)
        
        try:
            response = await self.client.chat.completions.create(  # Add await
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Increased for better responses
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return self._parse_unified_response(content, movies)
            
        except Exception as e:
            logger.error(f"GPT API error: {str(e)}")
            # Return fallback instead of raising
            return self._create_fallback_response(movies)
    
    def _get_system_prompt(self) -> str:
        """Enhanced system prompt for unified recommendations"""
        return """You are an expert literary curator who specializes in analyzing user's overall taste profile from their movie preferences and recommending books that match their unified aesthetic and thematic preferences.

Your task is to:
1. Analyze the collection of movies to identify common themes, genres, narrative styles, emotional tones, and artistic preferences
2. Create a unified taste profile that captures the user's overall preferences
3. Recommend books that align with this unified profile, not individual movies
4. Focus on books that would appeal to someone with this specific combination of tastes

Consider these aspects when analyzing:
- Narrative complexity and structure
- Emotional depth and tone
- Genre blending and hybrid elements
- Character development preferences
- Thematic interests (existential, social, psychological, etc.)
- Visual and atmospheric preferences
- Pacing and storytelling style
- Cultural and historical interests

Always respond with valid JSON format."""

    def _build_unified_prompt(self, movies: List[str], preferences: UserPreferences = None) -> str:
        """Build a prompt that asks for unified recommendations based on taste profile"""
        movies_str = ", ".join(movies)
        books_count = getattr(settings, 'books_per_recommendation', 3)  # Default to 3 if not set
        
        prompt = f"""Based on these movies: {movies_str}

First, analyze the user's overall taste profile by identifying:
1. Common themes and motifs across these movies
2. Preferred narrative styles and storytelling approaches
3. Emotional and tonal preferences
4. Genre inclinations and artistic sensibilities
5. Character archetype preferences
6. Visual and atmospheric elements they're drawn to

Then recommend exactly {books_count} books that would appeal to someone with this unified taste profile. These should be books that complement their overall aesthetic and thematic preferences, not books that match individual movies.

Focus on books that:
- Share thematic DNA with their movie choices
- Match their preferred narrative complexity
- Align with their emotional and tonal preferences
- Appeal to their artistic sensibilities
- Offer similar character depth and development
"""
        
        if preferences:
            prompt += "\n\nAdditional user preferences to consider:\n"
            if preferences.mood:
                prompt += f"- Mood preference: {preferences.mood}\n"
            if preferences.pace:
                prompt += f"- Pacing preference: {preferences.pace}\n"
            if preferences.genre_preferences:
                prompt += f"- Preferred genres: {', '.join(preferences.genre_preferences)}\n"
            if preferences.genre_blocklist:
                prompt += f"- Avoid these genres: {', '.join(preferences.genre_blocklist)}\n"
        
        prompt += f"""

Format your response as valid JSON with this structure:
{{
  "taste_profile": {{
    "themes": ["theme1", "theme2", "theme3"],
    "narrative_style": "description of preferred storytelling approach",
    "emotional_tone": "description of preferred emotional register",
    "genre_fusion": "description of genre preferences and blending",
    "character_preferences": "description of preferred character types",
    "artistic_sensibilities": "description of aesthetic preferences",
    "confidence_score": 0.85
  }},
  "unified_recommendations": [
    {{
      "title": "Book Title",
      "author": "Author Name",
      "reason": "Detailed explanation of why this book matches their unified taste profile",
      "taste_match_score": 0.95,
      "primary_appeal": "What aspect of their taste this book primarily satisfies"
    }}
  ]
}}

Ensure each book recommendation reason is substantial (100+ words) and explains how it connects to their overall taste profile. The response MUST be valid JSON."""
        
        return prompt
    
    def _parse_unified_response(self, content: str, movies: List[str]) -> List[RecommendationResponse]:
        """Parse the unified response into the expected format"""
        try:
            # Clean up the response to extract JSON
            content = content.strip()
            
            # Find JSON boundaries
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.error("No valid JSON found in GPT response")
                return self._create_fallback_response(movies)
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            if 'unified_recommendations' not in data:
                logger.error("Missing unified_recommendations in response")
                return self._create_fallback_response(movies)
            
            # Extract unified recommendations
            unified_books = []
            for book_data in data.get('unified_recommendations', []):
                if not book_data.get('title') or not book_data.get('author'):
                    continue
                    
                book = BookRecommendation(
                    title=book_data['title'],
                    author=book_data['author'],
                    reason=book_data.get('reason', ''),
                    taste_match_score=book_data.get('taste_match_score'),
                    primary_appeal=book_data.get('primary_appeal')
                )
                unified_books.append(book)
            
            if not unified_books:
                logger.error("No valid book recommendations found")
                return self._create_fallback_response(movies)
            
            # Create taste profile
            taste_profile_data = data.get('taste_profile', {})
            taste_profile = TasteProfile(
                themes=taste_profile_data.get('themes', []),
                narrative_style=taste_profile_data.get('narrative_style', ''),
                emotional_tone=taste_profile_data.get('emotional_tone', ''),
                genre_fusion=taste_profile_data.get('genre_fusion', ''),
                character_preferences=taste_profile_data.get('character_preferences', ''),
                artistic_sensibilities=taste_profile_data.get('artistic_sensibilities', ''),
                confidence_score=taste_profile_data.get('confidence_score', 0.7)
            )
            
            # Return as a single recommendation response for the unified taste
            movie_summary = self._create_movie_summary(movies, taste_profile_data)
            
            return [RecommendationResponse(
                movie=movie_summary,
                books=unified_books,
                taste_profile=taste_profile
            )]
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Content: {content}")
            return self._create_fallback_response(movies)
        except Exception as e:
            logger.error(f"Error parsing unified response: {e}")
            return self._create_fallback_response(movies)
    
    def _create_movie_summary(self, movies: List[str], taste_profile: Dict) -> str:
        """Create a summary of the user's movie selection and taste profile"""
        if len(movies) == 1:
            return f"Based on your interest in {movies[0]}"
        elif len(movies) == 2:
            return f"Based on your taste for {movies[0]} and {movies[1]}"
        else:
            return f"Based on your taste profile from {', '.join(movies[:-1])}, and {movies[-1]}"
    
    def _create_fallback_response(self, movies: List[str]) -> List[RecommendationResponse]:
        """Fallback response in case of parsing errors"""
        logger.warning("Using fallback response due to GPT parsing error")
        
        # Create a simple unified recommendation
        fallback_books = [
            BookRecommendation(
                title="The Seven Husbands of Evelyn Hugo",
                author="Taylor Jenkins Reid",
                reason="A compelling narrative that combines character depth with emotional complexity, appealing to viewers who appreciate sophisticated storytelling.",
                taste_match_score=0.8,
                primary_appeal="Character-driven storytelling"
            ),
            BookRecommendation(
                title="Klara and the Sun",
                author="Kazuo Ishiguro",
                reason="Masterful blend of speculative elements with profound human themes, perfect for those who enjoy thoughtful, emotionally resonant narratives.",
                taste_match_score=0.85,
                primary_appeal="Thoughtful speculative fiction"
            ),
            BookRecommendation(
                title="The Midnight Library",
                author="Matt Haig",
                reason="Philosophical exploration of life choices and possibilities, combining accessibility with deeper existential themes.",
                taste_match_score=0.75,
                primary_appeal="Philosophical exploration"
            )
        ]
        
        fallback_taste_profile = TasteProfile(
            themes=["character development", "emotional depth", "existential themes"],
            narrative_style="Layered, character-driven storytelling",
            emotional_tone="Thoughtful and introspective",
            genre_fusion="Literary fiction with speculative elements",
            character_preferences="Complex, well-developed characters",
            artistic_sensibilities="Appreciation for literary craftsmanship",
            confidence_score=0.6
        )
        
        movie_summary = self._create_movie_summary(movies, {})
        
        return [RecommendationResponse(
            movie=movie_summary,
            books=fallback_books,
            taste_profile=fallback_taste_profile
        )]

    async def analyze_taste_profile(self, movies: List[str], preferences: UserPreferences = None) -> Dict[str, Any]:
        """
        Separate method to analyze and return just the taste profile
        Useful for frontend display or further processing
        """
        prompt = f"""Analyze the taste profile of someone who enjoys these movies: {", ".join(movies)}

Identify and describe:
1. Common themes and motifs
2. Preferred narrative styles
3. Emotional and tonal preferences
4. Genre inclinations
5. Character archetype preferences
6. Visual and atmospheric elements

Provide a detailed analysis in JSON format:
{{
  "themes": ["list of common themes"],
  "narrative_style": "description",
  "emotional_tone": "description",
  "genre_fusion": "description",
  "character_preferences": "description",
  "artistic_sensibilities": "description",
  "confidence_score": 0.85
}}"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing artistic and narrative preferences from media consumption patterns. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_str = content[json_start:json_end]
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error analyzing taste profile: {e}")
            return {
                "themes": ["character-driven narratives", "emotional depth"],
                "narrative_style": "Complex, layered storytelling",
                "emotional_tone": "Thoughtful and engaging",
                "genre_fusion": "Blend of multiple genres",
                "character_preferences": "Well-developed, complex characters",
                "artistic_sensibilities": "Appreciation for craftsmanship",
                "confidence_score": 0.5
            }