from .base import BaseRenderer
from .product_demo import ProductDemoRenderer
from .influencer import InfluencerRenderer
from .testimonial import TestimonialRenderer
from .lifestyle import LifestyleRenderer
from .before_after import BeforeAfterRenderer

def get_renderer(ad_type: str, variants_output, avatar_config, campaign_context) -> BaseRenderer:
    """Factory to return the correct renderer subclass based on ad_type."""
    renderers = {
        "product_demo": ProductDemoRenderer,
        "lifestyle": LifestyleRenderer,
        "influencer": InfluencerRenderer,
        "testimonial": TestimonialRenderer,
        "before_after": BeforeAfterRenderer,
    }
    
    # Normalize ad_type
    ad_type_clean = str(ad_type).lower().replace(" ", "_").replace("-", "_")
    
    cls = renderers.get(ad_type_clean, BaseRenderer)
    print(f"   [RendererFactory] Returning {cls.__name__} for ad_type: {ad_type}")
    return cls(variants_output, avatar_config, campaign_context)
