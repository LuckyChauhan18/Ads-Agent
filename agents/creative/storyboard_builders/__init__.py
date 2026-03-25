from .base import BaseStoryboardBuilder
from .influencer import InfluencerStoryboardBuilder
from .lifestyle import LifestyleStoryboardBuilder
from .product_demo import ProductDemoStoryboardBuilder
from .testimonial import TestimonialStoryboardBuilder
from .before_after import BeforeAfterStoryboardBuilder

def get_storyboard_builder(ad_type, script_output, avatar_config, campaign_context, **kwargs):
    """Factory function to get the appropriate StoryboardBuilder subclass."""
    
    builders = {
        "influencer": InfluencerStoryboardBuilder,
        "lifestyle": LifestyleStoryboardBuilder,
        "product_demo": ProductDemoStoryboardBuilder,
        "testimonial": TestimonialStoryboardBuilder,
        "before_after": BeforeAfterStoryboardBuilder
    }
    
    builder_class = builders.get(ad_type.lower(), BaseStoryboardBuilder)
    print(f"   [Factory] Selected StoryboardBuilder: {builder_class.__name__} for '{ad_type}'")
    return builder_class(script_output, avatar_config, campaign_context, **kwargs)
