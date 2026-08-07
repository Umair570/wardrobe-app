from typing import Optional

from pydantic import BaseModel, Field


class WardrobeItem(BaseModel):
    """
    Representation of a wardrobe item passed to the LLM for context.
    Matches the schema used by the retrieval service.
    """
    id: str = Field(description="Unique identifier for the item in the wardrobe.")
    category: Optional[str] = Field(default=None, description="Category of the garment (e.g. shirt, pants).")
    type: Optional[str] = Field(default=None, description="Type of the garment (e.g. t-shirt, jeans).")
    color: Optional[str] = Field(default=None, description="Color of the garment.")
    style: Optional[str] = Field(default=None, description="Style of the garment (e.g. casual, formal).")
    season: Optional[str] = Field(default=None, description="Season the garment is suited for.")
    pattern: Optional[str] = Field(default=None, description="Pattern of the garment.")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the garment.")


class OutfitRecommendation(BaseModel):
    """
    A single outfit expressed as wardrobe item IDs.
    These are the IDs the visualization endpoint consumes.
    """
    top_id: Optional[str] = Field(default=None, description="ID of the upper body garment.")
    bottom_id: Optional[str] = Field(default=None, description="ID of the lower body garment.")
    outerwear_id: Optional[str] = Field(default=None, description="ID of the jacket or coat.")
    shoes_id: Optional[str] = Field(default=None, description="ID of the footwear.")

    def item_ids(self) -> list[str]:
        """Non-null item IDs, in layering order — ready for POST /visualization."""
        return [i for i in (self.top_id, self.bottom_id, self.outerwear_id, self.shoes_id) if i]


class OutfitOption(OutfitRecommendation):
    """
    One of the three options the stylist offers. The user picks one and sends its
    `item_ids()` to the visualization endpoint for the FASHN try-on render.
    """
    title: str = Field(default="Outfit", description="Short label for this option.")
    rationale: str = Field(default="", description="Why this option suits the request.")


class StylistResponse(BaseModel):
    """
    Final structured response from the stylist agent.
    """
    message: str = Field(description="Conversational reply introducing the options.")
    outfits: list[OutfitOption] = Field(
        default_factory=list,
        description="Up to three distinct outfit options, best first.",
    )

    @property
    def primary(self) -> OutfitRecommendation:
        """First option, for callers that only handle a single outfit."""
        if not self.outfits:
            return OutfitRecommendation()
        best = self.outfits[0]
        return OutfitRecommendation(
            top_id=best.top_id,
            bottom_id=best.bottom_id,
            outerwear_id=best.outerwear_id,
            shoes_id=best.shoes_id,
        )
