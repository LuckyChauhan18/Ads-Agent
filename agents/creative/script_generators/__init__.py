from .base import BaseScriptGenerator
from .influencer import InfluencerScriptGenerator
from .product_demo import ProductDemoScriptGenerator
from .lifestyle import LifestyleScriptGenerator
from .testimonial import TestimonialScriptGenerator
from .before_after import BeforeAfterScriptGenerator

def get_script_generator(ad_type: str, pattern_blueprint, campaign_context) -> BaseScriptGenerator:
    """Factory to get the correct script generator class."""
    if not ad_type:
        return BaseScriptGenerator(pattern_blueprint, campaign_context)
        
    ad_type_clean = ad_type.lower().replace(" ", "_").replace("/", "_")
    
    generators = {
        "influencer": InfluencerScriptGenerator,
        "product_demo": ProductDemoScriptGenerator,
        "lifestyle": LifestyleScriptGenerator,
        "testimonial": TestimonialScriptGenerator,
        "before_after": BeforeAfterScriptGenerator
    }
    
    generator_class = generators.get(ad_type_clean, BaseScriptGenerator)
    print(f"   [Factory] Selected ScriptGenerator: {generator_class.__name__} for '{ad_type}'")
    return generator_class(pattern_blueprint, campaign_context)
