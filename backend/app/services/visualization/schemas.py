from pydantic import BaseModel, Field
from typing import Optional

class VirtualTryOnRequest(BaseModel):
    person_image_url: str = Field(..., description="Absolute URL to the user's body photo")
    top_garment_url: Optional[str] = Field(None, description="Absolute URL to the top garment (shirt/sweater)")
    bottom_garment_url: Optional[str] = Field(None, description="Absolute URL to the bottom garment (pants/shorts)")
    dress_garment_url: Optional[str] = Field(None, description="Absolute URL to a dress garment")
    hf_token: Optional[str] = Field(None, description="HuggingFace API token for rate limits")
    
    # Validation to ensure at least one garment is provided
    def check_has_garment(self):
        if not any([self.top_garment_url, self.bottom_garment_url, self.dress_garment_url]):
            raise ValueError("At least one garment URL must be provided.")

class VirtualTryOnResponse(BaseModel):
    success: bool
    ai_image_url: Optional[str] = None
    error_message: Optional[str] = None
    provider: str = Field(..., description="The name of the VTON provider used (e.g., OOTDiffusion)")
