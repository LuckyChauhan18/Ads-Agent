import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion'
import { Package, Database, Brain, Target, Layout, FileText, User, Video, Sparkles, ChevronRight, ChevronLeft } from 'lucide-react'
import { workflowService } from '../services/api'
import { toast } from './Toast'

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
  { id: 2, name: 'Curate', icon: Database, bg: 'bg-step-2' },
  { id: 3, name: 'Research', icon: Brain, bg: 'bg-step-3' },
  { id: 4, name: 'Strategy', icon: Target, bg: 'bg-step-4' },
  { id: 5, name: 'Pattern', icon: Layout, bg: 'bg-step-5' },
  { id: 6, name: 'Script', icon: FileText, bg: 'bg-step-6' },
  { id: 7, name: 'Avatar', icon: User, bg: 'bg-step-7' },
  { id: 8, name: 'Storyboard', icon: Video, bg: 'bg-step-8' },
  { id: 9, name: 'Video Preview', icon: Sparkles, bg: 'bg-step-9' },
]

function Wizard() {
  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState({ active: false, message: '' })
  const [state, setState] = useState({
    product: {},
    curatedBrands: [],
    strategy: {},
    research: null,
    blueprint: null,
    script: null,
    avatar: { style: 'Professional', gender: 'Female', language: 'Hindi/English Mixed' },
    renderResult: null,
    renderFailed: false,
  })

  const updateState = (key, val) => setState(prev => ({ ...prev, [key]: { ...prev[key], ...val } }))

  const handleNext = async () => {
    if (currentStep === 1) {
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

      setLoading({ active: true, message: 'LLM is discovering competitors...' })
      try {
        const res = await workflowService.runDiscovery(state.product)
        setState(prev => ({ ...prev, curatedBrands: res.data.results.brands, research: { understanding: res.data.results.understanding, competitors: [] } }))
        setCurrentStep(2)
      } catch (e) { toast('Discovery failed: ' + (e.response?.data?.detail || e.message), 'error') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 2) {
      setLoading({ active: true, message: 'Scraping Meta Ads DNA...' })
      try {
        const res = await workflowService.runResearch(state.product, state.curatedBrands)
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: res.data.results } }))
        setCurrentStep(3)
      } catch (e) { toast('Research failed: ' + (e.response?.data?.detail || e.message), 'error') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 3) {
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
      setCurrentStep(4)
    } else if (currentStep === 4) {
      setLoading({ active: true, message: 'Crafting Ad Pattern & Psychology...' })
      try {
        const res = await workflowService.runPsychology({
          founder_data: {
            ...state.strategy,
            ad_length: state.product.ad_length || 30 // Ensure ad_length is included in strategy payload
          },
          competitor_results: state.research.competitors,
          understanding: state.research.understanding
        })
        const campaignId = res.data.campaign_id;
        setState(prev => ({
          ...prev,
          blueprint: res.data.results,
          strategy: { ...prev.strategy, campaign_id: campaignId }
        }))
        setCurrentStep(5)
      } catch (e) { toast('Strategy analysis failed: ' + (e.response?.data?.detail || e.message), 'error') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 5) {
      setLoading({ active: true, message: 'Generating Scene-by-Scene Script...' })
      try {
        const res = await workflowService.runScript({
          pattern_blueprint: state.blueprint.pattern_blueprint,
          campaign_psychology: state.blueprint.campaign_psychology,
          avatar_config: state.avatar,
          ad_length: state.product.ad_length || 30, // FIXED: accurately pass selection
          language: state.avatar.language,
          campaign_id: state.strategy.campaign_id
        })
        setState(prev => ({ ...prev, script: res.data.results }))
        setCurrentStep(6)
      } catch (e) { toast('Script generation failed: ' + (e.response?.data?.detail || e.message), 'error') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 8) {
      setLoading({ active: true, message: 'Initiating final video render...' })
      try {
        const res = await workflowService.runRender({
          script_output: state.script,
          avatar_config: state.avatar,
          campaign_psychology: {
            ...state.blueprint.campaign_psychology,
            campaign_id: state.strategy.campaign_id
          },
          campaign_id: state.strategy.campaign_id
        })
        const variants = res.data.results.render_results;
        if (variants && variants.length > 0 && variants[0].local_path) {
          const filename = variants[0].local_path.split(/[\\/]/).pop();
          const videoUrl = `http://localhost:8000/videos/${filename}`;
          setState(prev => ({ ...prev, renderResult: videoUrl }));
          toast('Video rendered successfully!', 'success');
          setCurrentStep(9);
        } else if (variants && variants.length > 0 && variants[0].prompts) {
          setState(prev => ({
            ...prev,
            runwayPrompts: variants[0].prompts,
            runwayVisualContext: variants[0].visual_context || null,
            renderResult: null
          }));
          toast('Runway ML prompts generated!', 'success');
          setCurrentStep(9);
        } else {
          toast('Render completed but no output was found. Check server logs.', 'warning');
        }
      } catch (e) {
        console.error(e);
        setState(prev => ({ ...prev, renderFailed: true }));
        toast('Render failed: ' + (e.response?.data?.detail || e.message), 'error');
      }
      setLoading({ active: false, message: '' })
    } else {
      setCurrentStep(prev => prev + 1)
    }
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return <ProductStep data={state.product} updateData={(d) => updateState('product', d)} />
      case 2: return <CurationStep brands={state.curatedBrands} updateBrands={(val) => setState(prev => ({ ...prev, curatedBrands: val }))} />
      case 3: return <CompetitorStep research={state.research} updateCompetitor={(i, val) => {
        const newCompetitors = [...(state.research?.competitors || [])]
        if (newCompetitors[i]) {
          newCompetitors[i].top_punchline = val
        }
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: newCompetitors } }))
      }} />
      case 4: return <StrategyStep data={state.strategy} updateData={(d) => updateState('strategy', d)} />
      case 5: return <PatternStep blueprint={state.blueprint?.pattern_blueprint} updateBlueprint={(d) => {
        setState(prev => ({ ...prev, blueprint: { ...prev.blueprint, pattern_blueprint: { ...prev.blueprint.pattern_blueprint, ...d } } }))
      }} />
      case 6: return <ScriptStep script={state.script} updateScene={(i, val) => {
        const newScenes = [...state.script.scenes]
        newScenes[i].voiceover = val
        setState(prev => ({ ...prev, script: { ...prev.script, scenes: newScenes } }))
      }} />
      case 7: return <AvatarStep data={state.avatar} updateData={(d) => updateState('avatar', d)} />
      case 8: return <ReviewStep state={state} updateData={(d) => setState(prev => ({ ...prev, ...d }))} />
      case 9: return <VideoStep videoUrl={state.renderResult} productUrl={state.product?.product_url} script={state.script} runwayPrompts={state.runwayPrompts} visualContext={state.runwayVisualContext} />
      default: return null
    }
  }

  const activeStep = STEPS.find(s => s.id === currentStep)

  return (
    <div className="wizard-inner-container">
      <LoadingOverlay active={loading.active && currentStep !== 8} message={loading.message} />
      <RenderProgressOverlay
        active={loading.active && currentStep === 8}
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
            {step.id < 9 && <div className="step-line" />}
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
            onClick={() => setCurrentStep(prev => prev - 1)}
            disabled={loading.active}
          >
            <ChevronLeft size={20} /> Back
          </button>
        )}
        <button
          className={`btn ${currentStep === 8 ? 'btn-premium' : (currentStep === 9 ? 'btn-primary' : 'btn-primary')}`}
          onClick={currentStep === 9 ? () => window.location.reload() : handleNext}
          disabled={loading.active}
        >
          {currentStep === 8 ? 'Confirm & Render' : (currentStep === 9 ? 'Start New' : 'Continue')} <ChevronRight size={20} />
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
