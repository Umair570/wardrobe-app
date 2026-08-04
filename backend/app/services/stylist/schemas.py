from typing import Optional
from pydantic import BaseModel, Field

class WardrobeItem(BaseModel):
    """
    Representation of a wardrobe item passed to the LLM for context.
    Matches the schema used by the retrieval service.
    """
    id: str = Field(description="Unique identifier for the item in the wardrobe.")
    category: Optional[str] = Field(default=None, description="Category of the garment (e.g. upper_body, lower_body).")
    type: Optional[str] = Field(default=None, description="Type of the garment (e.g. t-shirt, jeans).")
    color: Optional[str] = Field(default=None, description="Color of the garment.")
    style: Optional[str] = Field(default=None, description="Style of the garment (e.g. casual, formal).")
    season: Optional[str] = Field(default=None, description="Season the garment is suited for.")
    pattern: Optional[str] = Field(default=None, description="Pattern of the garment.")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the garment.")

class OutfitRecommendation(BaseModel):
    """
    The structured outfit recommendation from the stylist LLM.
    Uses the exact IDs from the retrieved wardrobe context.
    """
    top_id: Optional[str] = Field(
        default=None, 
        description="The ID of the upper body or top garment recommended."
    )
    bottom_id: Optional[str] = Field(
        default=None, 
        description="The ID of the lower body or bottom garment recommended."
    )
    outerwear_id: Optional[str] = Field(
        default=None, 
        description="The ID of the outerwear or jacket recommended."
    )
    shoes_id: Optional[str] = Field(
        default=None, 
        description="The ID of the shoes or footwear recommended."
    )

class StylistResponse(BaseModel):
    """
    The final structured response expected from the Groq Stylist Service.
    """
    message: str = Field(
        description="A friendly, conversational explanation of why this outfit was chosen."
    )
    outfit: OutfitRecommendation = Field(
        description="The structured outfit recommendation using IDs."
    )
