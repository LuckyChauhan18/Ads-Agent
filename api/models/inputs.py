from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProductInput(BaseModel):
    product_name: str
    brand_name: str
    category: str
    root_product: str
    price_range: str
    description: str
    features: List[str]
    product_url: Optional[str] = None

class OfferAndRiskReversal(BaseModel):
    discount: str
    guarantee: str

class FounderInput(BaseModel):
    campaign_id: str
    funnel_stage: str
    primary_emotions: List[str]
    user_problem_raw: str
    objections: List[str]
    trust_signals_available: List[str]
    offer_and_risk_reversal: OfferAndRiskReversal
    brand_voice: str
    platform: str

class AvatarPreferences(BaseModel):
    gender: str
    style: str
    age_range: str
    ethnicity_hint: str

class VoicePreferences(BaseModel):
    gender: str
    tone: str
    pace: str
    language: str
    accent_hint: str

class DeliveryStyle(BaseModel):
    energy: str
    camera_angle: str
    expression: str
    body_language: str

class PlatformSpecs(BaseModel):
    aspect_ratio: str
    resolution: str
    format: str
    max_duration_seconds: int

class Overrides(BaseModel):
    force_avatar_id: Optional[str] = None
    force_voice_id: Optional[str] = None

class AvatarInput(BaseModel):
    avatar_preferences: AvatarPreferences
    voice_preferences: VoicePreferences
    delivery_style: DeliveryStyle
    platform_specs: PlatformSpecs
    overrides: Overrides
