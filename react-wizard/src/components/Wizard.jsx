import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
  const location = useLocation();

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
  const [dirty, setDirty] = useState({
    1: true, 2: true, 3: true, 4: true, 5: true, 6: true, 7: true, 8: true
  })

  useEffect(() => {
    if (location.state && location.state.editCampaign) {
      const c = location.state.editCampaign;
      setState(prev => ({
        ...prev,
        product: {
          brand_name: c.brand_name || c.product_info?.brand_name || '',
          product_name: c.product_name || c.product_info?.product_name || '',
          category: c.category || c.product_info?.category || c.campaign_psychology?.founder_data?.category || '',
          root_product: c.root_product || c.product_info?.root_product || c.campaign_psychology?.founder_data?.root_product || '',
          ad_length: c.ad_length || c.product_info?.ad_length || 30,
          platform: c.platform || c.product_info?.platform || 'instagram',
          product_logo: c.product_logo || c.product_info?.product_logo || null,
          product_images: c.product_images || c.product_info?.product_images || [],
          description: c.description || c.product_info?.description || c.campaign_psychology?.product_understanding?.description || '',
          price_range: c.price_range || c.product_info?.price_range || '',
          product_url: c.product_url || c.product_info?.product_url || '',
          features: c.features || c.product_info?.features || c.campaign_psychology?.product_understanding?.features || [],
        },
        strategy: {
          ...c.campaign_psychology?.founder_data,
          campaign_id: c._id || c.campaign_id,
        },
        research: {
          understanding: c.campaign_psychology?.product_understanding || c.discovery_results?.understanding || null,
          competitors: c.research?.results || c.pattern_blueprint?.competitor_results || []
        },
        curatedBrands: c.curated_brands || c.discovery_results?.brands || [],
        blueprint: {
          campaign_psychology: c.campaign_psychology,
          pattern_blueprint: c.pattern_blueprint?.pattern_blueprint
        },
        script: c.final_storyboard,
        avatar: c.avatar_config || prev.avatar,
        renderResult: c.video_url || null
      }));
      setDirty({
        1: false, 2: false, 3: false,
        4: !c.campaign_psychology,
        5: !c.pattern_blueprint,
        6: false,
        7: false,
        8: !c.video_url
      });
      // Clear location state to prevent reload loops
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const updateState = (key, val) => setState(prev => ({ ...prev, [key]: { ...prev[key], ...val } }))

  const handleNext = async () => {
    if (currentStep === 1) {
      const hasBrands = state.curatedBrands && state.curatedBrands.length > 0;
      const hasResearch = state.research?.competitors && state.research.competitors.length > 0;

      // Skip Discovery/Research if we already have the data and Step 1 isn't dirty
      if (!dirty[1] && (hasBrands || hasResearch)) {
        setCurrentStep(hasResearch ? 3 : 2); // Go to research results if we already have them, else curation
        return;
      }

      const camId = state.strategy?.campaign_id || `${state.product.brand_name?.toLowerCase().replace(/\s/g, '_') || 'ad'}_${new Date().getTime().toString().slice(-4)}`;
      if (!state.strategy?.campaign_id) {
        setState(prev => ({ ...prev, strategy: { ...prev.strategy, campaign_id: camId } }));
      }

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
        const res = await workflowService.runDiscovery({ ...state.product, campaign_id: camId })
        setState(prev => ({
          ...prev,
          curatedBrands: res.data.results.brands,
          research: { understanding: res.data.results.understanding, competitors: [] }
        }))
        setDirty(prev => ({ ...prev, 1: false }))
        setCurrentStep(2)
      } catch (e) { alert('Discovery failed.') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 2) {
      if (!dirty[2] && state.research?.competitors?.length > 0) {
        setCurrentStep(3);
        return;
      }
      setLoading({ active: true, message: 'Scraping Meta Ads DNA...' })
      try {
        const res = await workflowService.runResearch({
          ...state.product,
          campaign_id: state.strategy.campaign_id
        }, state.curatedBrands)
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: res.data.results } }))
        setDirty(prev => ({ ...prev, 2: false }))
        setCurrentStep(3)
      } catch (e) { alert('Research failed.') }
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
      if (!dirty[4] && state.blueprint) {
        setCurrentStep(5);
        return;
      }
      setLoading({ active: true, message: 'Crafting Ad Pattern & Psychology...' })
      try {
        const res = await workflowService.runPsychology({
          founder_data: {
            ...state.product,
            ...state.strategy,
            ad_length: state.product.ad_length || 30,
            category: state.product.category,
            root_product: state.product.root_product
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
        setDirty(prev => ({ ...prev, 4: false }))
        setCurrentStep(5)
      } catch (e) { alert('Psychology analysis failed.') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 5) {
      if (!dirty[5] && state.script) {
        setCurrentStep(6);
        return;
      }
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
        setDirty(prev => ({ ...prev, 5: false }))
        setCurrentStep(6)
      } catch (e) { alert('Script generation failed.') }
      setLoading({ active: false, message: '' })
    } else if (currentStep === 8) {
      if (!dirty[8] && state.renderResult) {
        setCurrentStep(9);
        return;
      }
      setLoading({ active: true, message: 'Initiating final video render...' })
      try {
        const res = await workflowService.runRender({
          script_output: state.script,
          avatar_config: state.avatar,
          campaign_psychology: state.blueprint.campaign_psychology,
          campaign_id: state.strategy.campaign_id
        })
        const variants = res.data.results.render_results;
        if (variants && variants.length > 0 && variants[0].local_path) {
          const filename = variants[0].local_path.split(/[\\/]/).pop();
          const videoUrl = `http://localhost:8000/videos/${filename}`;
          setState(prev => ({ ...prev, renderResult: videoUrl }));
          setDirty(prev => ({ ...prev, 8: false }))
          setCurrentStep(9);
        } else {
          alert('Render completed but video was not found.');
        }
      } catch (e) {
        console.error(e);
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
      case 1: return <ProductStep data={state.product} updateData={(d) => {
        updateState('product', d)
        setDirty(prev => ({ ...prev, 1: true, 2: true, 4: true, 5: true, 8: true }))
      }} />
      case 2: return <CurationStep brands={state.curatedBrands} updateBrands={(val) => {
        setState(prev => ({ ...prev, curatedBrands: val }))
        setDirty(prev => ({ ...prev, 2: true, 4: true, 5: true, 8: true }))
      }} />
      case 3: return <CompetitorStep research={state.research} updateCompetitor={(i, val) => {
        const newCompetitors = [...(state.research?.competitors || [])]
        if (newCompetitors[i]) {
          newCompetitors[i].top_punchline = val
        }
        setState(prev => ({ ...prev, research: { ...prev.research, competitors: newCompetitors } }))
        setDirty(prev => ({ ...prev, 4: true, 5: true, 8: true }))
      }} />
      case 4: return <StrategyStep data={state.strategy} updateData={(d) => {
        updateState('strategy', d)
        setDirty(prev => ({ ...prev, 4: true, 5: true, 8: true }))
      }} />
      case 5: return <PatternStep blueprint={state.blueprint?.pattern_blueprint} updateBlueprint={(d) => {
        setState(prev => ({ ...prev, blueprint: { ...prev.blueprint, pattern_blueprint: { ...prev.blueprint.pattern_blueprint, ...d } } }))
        setDirty(prev => ({ ...prev, 5: true, 8: true }))
      }} />
      case 6: return <ScriptStep script={state.script} updateScene={(i, val) => {
        const newScenes = [...state.script.scenes]
        newScenes[i].voiceover = val
        setState(prev => ({ ...prev, script: { ...prev.script, scenes: newScenes } }))
        setDirty(prev => ({ ...prev, 8: true }))
      }} />
      case 7: return <AvatarStep data={state.avatar} updateData={(d) => {
        updateState('avatar', d)
        setDirty(prev => ({ ...prev, 8: true }))
      }} />
      case 8: return <ReviewStep state={state} updateData={(d) => {
        setState(prev => ({ ...prev, ...d }))
        setDirty(prev => ({ ...prev, 8: true }))
      }} />
      case 9: return <VideoStep videoUrl={state.renderResult} productUrl={state.product?.product_url} script={state.script} />
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
