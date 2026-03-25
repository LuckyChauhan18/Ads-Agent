import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion'
import { Package, Database, Brain, Target, Layout, FileText, User, Video, Sparkles, ChevronRight, ChevronLeft } from 'lucide-react'
import { workflowService } from '../services/api'

import ProductStep from './ProductStep'
import CurationStep from './CurationStep'
import StrategyStep from './StrategyStep'
import CompetitorStep from './CompetitorStep'
import PatternStep from './PatternStep'
import ScriptStep from './ScriptStep'
import AvatarStep from './AvatarStep'
import ReviewStep from './ReviewStep'
import VideoStep from './VideoStep'
import LoadingOverlay from './LoadingOverlay'
import RenderProgressOverlay from './RenderProgressOverlay'

const STEPS = [
  { id: 1, name: 'Product', icon: Package, bg: 'bg-step-1' },
  { id: 2, name: 'Audience', icon: Target, bg: 'bg-step-4' },
  { id: 3, name: 'Ad Type', icon: Layout, bg: 'bg-step-5' },
  { id: 4, name: 'Curate', icon: Database, bg: 'bg-step-2' },
  { id: 5, name: 'Research', icon: Brain, bg: 'bg-step-3' },
  { id: 6, name: 'AI Strategy', icon: Sparkles, bg: 'bg-step-4' },
  { id: 7, name: 'Pattern', icon: Layout, bg: 'bg-step-5' },
  { id: 8, name: 'Script', icon: FileText, bg: 'bg-step-6' },
  { id: 9, name: 'Storyboard', icon: Video, bg: 'bg-step-8' },
  { id: 10, name: 'Avatar', icon: User, bg: 'bg-step-7' },
  { id: 11, name: 'Video Preview', icon: Sparkles, bg: 'bg-step-9' },
]

function Wizard() {
  const [currentStep, setCurrentStep] = useState(() => {
    const saved = localStorage.getItem('wizard_step');
    return saved ? parseInt(saved, 10) : 1;
  });

  const [loading, setLoading] = useState({ active: false, message: '' })

  const [state, setState] = useState(() => {
    const saved = localStorage.getItem('wizard_state');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        localStorage.removeItem('wizard_state');
      }
    }
    return {
      product: {},
      curatedBrands: [],
      strategy: { ads_type: 'product_demo' },
      research: null,
      blueprint: null,
      script: null,
      audio_planning: null,
      script_planning: null,
      avatar: { style: 'Professional', gender: 'Female', language: 'Hindi/English Mixed' },
      renderResult: null,
      renderFailed: false,
    };
  });

  useEffect(() => {
    localStorage.setItem('wizard_state', JSON.stringify(state));
  }, [state]);

  useEffect(() => {
    localStorage.setItem('wizard_step', currentStep);
  }, [currentStep]);

  const updateState = (key, val) => setState(prev => ({ ...prev, [key]: { ...prev[key], ...val } }))

  const handleNext = async () => {
    if (currentStep === 1) {
      // Step 1 -> Step 2: Product Input complete. Setup Campaign ID.
      const camId = state.strategy?.campaign_id || `${state.product.brand_name?.toLowerCase().replace(/\s/g, '_') || 'ad'}_${new Date().getTime().toString().slice(-4)}`;
      setState(prev => ({ ...prev, strategy: { ...prev.strategy, campaign_id: camId } }));

      if (state.product.product_logo_file) {
        setLoading({ active: true, message: 'Uploading brand logo...' });
        try {
          const fd = new FormData();
          fd.append("files", state.product.product_logo_file);
          await workflowService.runUploadAssets(camId, "logo", fd);
        } catch (e) { console.error("Logo upload failed", e); }
      }

      if (state.product.product_images_files && state.product.product_images_files.length > 0) {
        setLoading({ active: true, message: 'Uploading product images...' });
        try {
          const fd = new FormData();
          state.product.product_images_files.forEach(f => fd.append("files", f));
          await workflowService.runUploadAssets(camId, "product", fd);
        } catch (e) { console.error("Product images upload failed", e); }
      }

      setCurrentStep(2); // Advance to Audience Basics
      setLoading({ active: false, message: '' });

    } else if (currentStep === 2) {
      // Step 2 -> Step 3: Audience Complete. Advance to Ad Type.
      setCurrentStep(3);

    } else if (currentStep === 3) {
      // Step 3 -> Step 4: Ad Type Selected. Trigger Discovery.
      setLoading({ active: true, message: 'LLM is discovering competitors...' })
      try {
        const res = await workflowService.runDiscovery(state.product)
        setState(prev => ({ ...prev, curatedBrands: res.data.results.brands, research: { understanding: res.data.results.understanding, competitors: [] } }))
        setCurrentStep(4) // Advance to Curation
      } catch (e) { alert('Discovery failed.') }
      setLoading({ active: false, message: '' })

    } else if (currentStep === 4) {
      // Step 4 -> Step 5: Curation Complete. Trigger Research Scraper.
      setLoading({ active: true, message: 'Scraping Meta Ads DNA...' })
      try {
        // Enforce state.strategy contains ads_type so filters hit correctly
        const res = await workflowService.runResearch(state.product, state.curatedBrands, state.strategy.ads_type)
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: res.data.results } }))
        setCurrentStep(5) // Advance to Research Comp View
      } catch (e) { alert('Research failed.') }
      setLoading({ active: false, message: '' })

    } else if (currentStep === 5) {
      // Step 5 -> Step 6: Research view confirmed. Trigger Strategy Prep.
      const features = state.product.features || [];
      setState(prev => ({
        ...prev,
        strategy: {
          funnel_stage: prev.strategy.funnel_stage || 'cold',
          primary_emotions: prev.strategy.primary_emotions || [],
          trust_signals_available: prev.strategy.trust_signals_available || features,
          offer_and_risk_reversal: prev.strategy.offer_and_risk_reversal || { offers: [{ discount: '', guarantee: '' }] },
          brand_voice: prev.strategy.brand_voice || '',
          platform: prev.strategy.platform || 'instagram',
          ...prev.strategy
        }
      }))
      setLoading({ active: true, message: 'Crafting Ad Pattern & Psychology...' })
      try {
        const res = await workflowService.runPsychology({
          founder_data: {
            ...state.strategy,
            ad_length: state.product.ad_length || 30
          },
          competitor_results: state.research.competitors,
          understanding: state.research.understanding
        })
        setState(prev => ({
          ...prev,
          blueprint: {
            ...res.data.results,
            pattern_blueprint: {
              ...res.data.results.pattern_blueprint,
              creative_dna: res.data.results.campaign_psychology?.creative_dna
            }
          },
        }))
        setCurrentStep(6) // Advance to AI Strategy output panel
      } catch (e) { alert('Psychology analysis failed.') }
      setLoading({ active: false, message: '' })

    } else if (currentStep === 6) {
      // Step 6 -> Step 7: Strategy Approved. Display Pattern Step next 
      setCurrentStep(7);

    } else if (currentStep === 7) {
      // Step 7 -> Step 8: Pattern Approved. Run Script.
      setLoading({ active: true, message: 'Generating Scene-by-Scene Script...' })
      try {
        // Ensure pattern_blueprint reads from the nested layout securely
        const patternData = state.blueprint.pattern_blueprint?.creative_dna || state.blueprint.creative_dna;
        const res = await workflowService.runScript({
          pattern_blueprint: patternData,
          campaign_psychology: state.blueprint.campaign_psychology,
          script_planning: state.blueprint.script_planning,
          avatar_config: state.avatar,
          ad_length: state.product.ad_length || 30,
          language: state.avatar.language,
          campaign_id: state.strategy.campaign_id
        })
        setState(prev => ({ 
          ...prev, 
          script: res.data.results,
          audio_planning: res.data.audio_planning,
          script_planning: res.data.script_planning
        }))
        setCurrentStep(8) // Go to Script page
      } catch (e) { alert('Script generation failed.') }
      setLoading({ active: false, message: '' })

    } else if (currentStep === 8) {
      // Step 8 -> Step 9: Script Review complete. Advance to Storyboard Frame review.
      setCurrentStep(9);

    } else if (currentStep === 9) {
      // Storyboard Approved.
      const needsAvatar = state.script_planning?.needs_avatar ?? (state.strategy.ads_type === 'influencer' || state.strategy.ads_type === 'testimonial');

      if (!needsAvatar) {
        // Skip Avatar, Trigger Render directly!
        setLoading({ active: true, message: 'Initiating final video render...' })
        try {
          const res = await workflowService.runRender({
            script_output: state.script,
            avatar_config: state.avatar,
            campaign_psychology: state.blueprint.campaign_psychology,
            campaign_id: state.strategy.campaign_id,
            audio_planning: state.audio_planning,
            script_planning: state.script_planning
          })
          const variants = res.data.results.render_results;
          if (variants && variants.length > 0 && variants[0].local_path) {
            const filename = variants[0].local_path.split(/[\\/]/).pop();
            const videoUrl = `http://localhost:8000/videos/${filename}`;
            setState(prev => ({ ...prev, renderResult: videoUrl }));
            setCurrentStep(11); // Skip to Video Preview 
          } else { alert('Render completed but video was not found.') }
        } catch (e) { setState(prev => ({ ...prev, renderFailed: true })); alert('Render failed.') }
        setLoading({ active: false, message: '' })
      } else {
        setCurrentStep(10); // Go to Avatar Step
      }

    } else if (currentStep === 10) {
      // Step 10 -> Step 11: Avatar complete. Trigger Render.
      setLoading({ active: true, message: 'Initiating final video render...' })
      try {
        const res = await workflowService.runRender({
          script_output: state.script,
          avatar_config: state.avatar,
          campaign_psychology: state.blueprint.campaign_psychology,
          campaign_id: state.strategy.campaign_id,
          audio_planning: state.audio_planning,
          script_planning: state.script_planning
        })
        const variants = res.data.results.render_results;
        if (variants && variants.length > 0 && variants[0].local_path) {
          const filename = variants[0].local_path.split(/[\\/]/).pop();
          const videoUrl = `http://localhost:8000/videos/${filename}`;
          setState(prev => ({ ...prev, renderResult: videoUrl }));
          setCurrentStep(11); // Final Preview Step
        } else {
          alert('Render completed but video was not found.');
        }
      } catch (e) {
        setState(prev => ({ ...prev, renderFailed: true }));
        alert('Render failed.');
      }
      setLoading({ active: false, message: '' })
    } else {
      setCurrentStep(prev => prev + 1)
    }
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return <ProductStep data={state.product} updateData={(d) => updateState('product', d)} />
      case 2: return <StrategyStep mode="basics" data={state.strategy} updateData={(d) => updateState('strategy', d)} product={state.product} />
      case 3: return <StrategyStep mode="ad_type" data={state.strategy} updateData={(d) => updateState('strategy', d)} />
      case 4: return <CurationStep brands={state.curatedBrands} updateBrands={(val) => setState(prev => ({ ...prev, curatedBrands: val }))} />
      case 5: return <CompetitorStep research={state.research} updateCompetitor={(i, val) => {
        const newCompetitors = [...(state.research?.competitors || [])]
        if (newCompetitors[i]) newCompetitors[i].top_punchline = val
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: newCompetitors } }))
      }} />
      case 6: return <StrategyStep mode="psychology" data={state.strategy} updateData={(d) => updateState('strategy', d)} />
      case 7: return <PatternStep blueprint={state.blueprint?.pattern_blueprint} updateBlueprint={(d) => {
        setState(prev => ({ ...prev, blueprint: { ...prev.blueprint, pattern_blueprint: { ...prev.blueprint.pattern_blueprint, ...d } } }))
      }} />
      case 8: return <ScriptStep script={state.script} updateScene={(i, val) => {
        const newScenes = [...state.script.scenes]
        newScenes[i].voiceover = val
        setState(prev => ({ ...prev, script: { ...prev.script, scenes: newScenes } }))
      }} />
      case 9: return <ReviewStep state={state} updateData={(d) => setState(prev => ({ ...prev, ...d }))} />
      case 10: return <AvatarStep data={state.avatar} updateData={(d) => updateState('avatar', d)} />
      case 11: return <VideoStep videoUrl={state.renderResult} productUrl={state.product?.product_url} script={state.script} />
      default: return null
    }
  }

  const activeStep = STEPS.find(s => s.id === currentStep)

  return (
    <div className="wizard-inner-container">
      <LoadingOverlay active={loading.active && currentStep !== 10 && currentStep !== 9} message={loading.message} />
      <RenderProgressOverlay
        active={loading.active && (currentStep === 9 || currentStep === 10)}
        message={loading.message}
        scenes={state.script?.scenes || []}
        failed={state.renderFailed}
      />

      <nav className="step-indicator">
        {STEPS.map((step) => (
          <React.Fragment key={step.id}>
            <div
              className={`step-bubble ${currentStep === step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}
              onClick={() => currentStep > step.id && !loading.active && setCurrentStep(step.id)}
              title={step.name}
            >
              <step.icon size={16} />
            </div>
            {step.id < 11 && <div className="step-line" />}
          </React.Fragment>
        ))}
      </nav>

      <div className="wizard-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="step-container"
          >
            {renderCurrentStep()}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="wizard-actions">
        {currentStep > 1 && (
          <button
            className="btn"
            onClick={() => {
              if (currentStep === 11) {
                const needsAvatar = state.script_planning?.needs_avatar ?? (state.strategy.ads_type === 'influencer' || state.strategy.ads_type === 'testimonial');
                if (!needsAvatar) {
                  setCurrentStep(9);
                  return;
                }
              }
              setCurrentStep(prev => prev - 1);
            }}
            disabled={loading.active}
          >
            <ChevronLeft size={20} /> Back
          </button>
        )}
        <button
          className={`btn ${((currentStep === 9 && !(state.script_planning?.needs_avatar ?? (state.strategy.ads_type === 'influencer' || state.strategy.ads_type === 'testimonial'))) || currentStep === 10) ? 'btn-premium' : 'btn-primary'}`}
          onClick={currentStep === 11 ? () => window.location.reload() : handleNext}
          disabled={loading.active}
        >
          {((currentStep === 9 && !(state.script_planning?.needs_avatar ?? (state.strategy.ads_type === 'influencer' || state.strategy.ads_type === 'testimonial'))) || currentStep === 10) ? 'Confirm & Render' : (currentStep === 11 ? 'Start New' : 'Continue')} <ChevronRight size={20} />
        </button>
      </div>

      <style>{`
        .wizard-inner-container {
          display: flex;
          flex-direction: column;
          flex: 1;
          min-height: 0;
          width: 100%;
          gap: 20px;
        }
        .step-indicator {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          padding: 10px 0;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .step-bubble {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: rgba(255,255,255,0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s;
          border: 1px solid rgba(255,255,255,0.1);
          color: rgba(255,255,255,0.4);
        }
        .step-bubble.active {
          background: var(--primary, #6366f1);
          color: white;
          transform: scale(1.1);
          box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
        }
        .step-bubble.completed {
          background: rgba(16, 185, 129, 0.2);
          color: #10b981;
          border-color: #10b981;
        }
        .step-line {
          width: 20px;
          height: 1px;
          background: rgba(255,255,255,0.1);
        }
        .wizard-content {
          flex: 1;
          overflow-y: auto;
          padding: 10px;
          min-height: 0;
        }
        .wizard-actions {
          display: flex;
          justify-content: flex-end;
          gap: 15px;
          padding-top: 20px;
          border-top: 1px solid rgba(255,255,255,0.05);
        }
        .step-container {
          width: 100%;
          height: 100%;
        }
      `}</style>
    </div>
  );
}

export default Wizard;
