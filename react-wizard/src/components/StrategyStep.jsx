import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Trash2,
  Info,
  Instagram,
  Facebook,
  Twitter,
  Youtube,
  Compass,
  Smile,
  MessageSquare,
  ShieldCheck,
  Zap,
  Sparkles
} from 'lucide-react';

import { aiAssistService } from '../services/api';

const EMOTIONS = [
  "Confidence", "Security", "Greed", "Fear of Missing Out (FOMO)",
  "Belonging", "Status", "Guilt", "Generosity", "Empowerment",
  "Curiosity", "Nostalgia", "Relief", "Excitement", "Love", "Pride"
];

const VOICES = [
  "Minimalist & Premium", "Authentic & Raw", "Witty & Sarcastic",
  "Bold & Aggressive", "Professional & Clinical", "Friendly & Casual",
  "Urgent & Hype", "Empathetic & Soft", "Inspirational & Grand"
];

const FUNNEL_INFO = {
  cold: "Top of Funnel: Target users who have never heard of your brand or product before. Focus on awareness and education.",
  warm: "Middle of Funnel: Target users who are aware of the problem or have interacted with your brand. Focus on consideration.",
  hot: "Bottom of Funnel: Target users who are ready to buy or have already shown high intent. Focus on conversion and risk reversal."
};

const StrategyStep = ({ data, updateData, mode = 'full', product = {} }) => {
  const [otherEmotion, setOtherEmotion] = useState('');
  const [showOtherEmotion, setShowOtherEmotion] = useState(false);
  const [otherVoice, setOtherVoice] = useState('');
  const [showOtherVoice, setShowOtherVoice] = useState(false);
  const [otherPlatform, setOtherPlatform] = useState('');
  const [isGeneratingSuggest, setIsGeneratingSuggest] = useState(false);

  const handleSuggestPainPoints = async () => {
    setIsGeneratingSuggest(true);
    try {
      const fd = new FormData();
      fd.append("product_name", product.product_name || "");
      fd.append("category", product.category || "");
      fd.append("description", product.description || "");

      const res = await aiAssistService.runSuggestPainPoints(fd);
      if (res.data?.results) {
        updateData({
          target_audience_problem: res.data.results
        });
      }
    } catch (e) {
      console.error("Suggest Pain Points Failed:", e);
    } finally {
      setIsGeneratingSuggest(false);
    }
  };

  const toggleEmotion = (emotion) => {
    const current = data.primary_emotions || [];
    if (current.includes(emotion)) {
      updateData({ primary_emotions: current.filter(e => e !== emotion) });
    } else {
      updateData({ primary_emotions: [...current, emotion] });
    }
  };

  const handleOtherEmotionAdd = () => {
    if (otherEmotion.trim()) {
      toggleEmotion(otherEmotion.trim());
      setOtherEmotion('');
      setShowOtherEmotion(false);
    }
  };

  const addOffer = () => {
    const currentOffers = data.offer_and_risk_reversal?.offers || [];
    updateData({
      offer_and_risk_reversal: {
        ...data.offer_and_risk_reversal,
        offers: [...currentOffers, { discount: '', guarantee: '' }]
      }
    });
  };

  const updateOffer = (index, field, value) => {
    const currentOffers = [...(data.offer_and_risk_reversal?.offers || [])];
    currentOffers[index] = { ...currentOffers[index], [field]: value };
    updateData({
      offer_and_risk_reversal: {
        ...data.offer_and_risk_reversal,
        offers: currentOffers
      }
    });
  };

  const removeOffer = (index) => {
    const currentOffers = (data.offer_and_risk_reversal?.offers || []).filter((_, i) => i !== index);
    updateData({
      offer_and_risk_reversal: {
        ...data.offer_and_risk_reversal,
        offers: currentOffers
      }
    });
  };

  const updateTrustSignal = (index, value) => {
    const signals = [...(data.trust_signals_available || [])];
    signals[index] = value;
    updateData({ trust_signals_available: signals });
  };

  const removeTrustSignal = (index) => {
    const signals = (data.trust_signals_available || []).filter((_, i) => i !== index);
    updateData({ trust_signals_available: signals });
  };

  const addTrustSignal = () => {
    updateData({ trust_signals_available: [...(data.trust_signals_available || []), ''] });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="step-content strategy-step"
    >
      <div className="section-header">
        <h2>Campaign Strategy</h2>
        <p>Define the psychological framework and offer structure for your ads.</p>
      </div>

      <div className="strategy-grid">
        {/* Left Column: Core Identity */}
        <div className="strategy-col">
          {(mode === 'basics' || mode === 'full') && (
            <>
              <div className="input-group glass-card">
                <label className="field-label">Campaign ID <span className="mandatory">*</span></label>
                <input
                  type="text"
                  className="glass-input"
                  value={data.campaign_id || ''}
                  onChange={(e) => updateData({ campaign_id: e.target.value })}
                  placeholder="e.g. MACBOOK_COLD_REEL_01"
                />
              </div>

              <div className="input-group glass-card">
                <label className="field-label flex-between">
                  Funnel Stage <span className="mandatory">*</span>
                  <Info size={14} className="info-icon" />
                </label>
                <div className="funnel-toggle-group">
                  {['cold', 'warm', 'hot'].map(stage => (
                    <div
                      key={stage}
                      className={`funnel-option ${data.funnel_stage === stage ? 'active' : ''}`}
                      onClick={() => updateData({ funnel_stage: stage })}
                      title={FUNNEL_INFO[stage]}
                    >
                      <span className="capitalize">{stage}</span>
                      <div className="funnel-tooltip">{FUNNEL_INFO[stage]}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {(mode === 'ad_type' || mode === 'full') && (
            <div className="input-group glass-card">
              <label className="field-label">Ad Type <span className="mandatory">*</span></label>
              <select
                className="glass-input"
                value={data.ads_type || 'product_demo'}
                onChange={(e) => updateData({ ads_type: e.target.value })}
                style={{ appearance: 'auto', background: 'rgba(0,0,0,0.3)' }}
              >
                <option value="influencer">Influencer (Narration)</option>
                <option value="product_demo">Product Demo (B-Roll)</option>
                <option value="testimonial">Testimonial (Social Proof)</option>
                <option value="before_after">Before/After (Transformation)</option>
                <option value="lifestyle">Lifestyle (Aesthetic)</option>
              </select>
            </div>
          )}

          {(mode === 'psychology' || mode === 'full') && (
            <div className="input-group glass-card">
              <label className="field-label">Primary Emotions (Multiple) <span className="mandatory">*</span></label>
              <div className="options-selector scroll-area">
                {EMOTIONS.map(emotion => (
                  <div
                    key={emotion}
                    className={`chip ${data.primary_emotions?.includes(emotion) ? 'active' : ''}`}
                    onClick={() => toggleEmotion(emotion)}
                  >
                    {emotion}
                  </div>
                ))}
                <div
                  className={`chip other-chip ${showOtherEmotion ? 'active' : ''}`}
                  onClick={() => setShowOtherEmotion(!showOtherEmotion)}
                >
                    + Other
                </div>
              </div>
              <AnimatePresence>
                {showOtherEmotion && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="other-input-container"
                  >
                    <input
                      type="text"
                      className="glass-input-sm"
                      placeholder="Type emotion..."
                      value={otherEmotion}
                      onChange={(e) => setOtherEmotion(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleOtherEmotionAdd()}
                    />
                    <button className="add-btn-sm" onClick={handleOtherEmotionAdd}>Add</button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {(mode === 'basics' || mode === 'full') && (
            <div className="input-group glass-card">
              <div className="flex-between">
                <label className="field-label">Target Audience Problem <span className="mandatory">*</span></label>
                <button 
                  type="button"
                  className="add-link-btn flex-center" 
                  onClick={handleSuggestPainPoints}
                  disabled={isGeneratingSuggest}
                  style={{ gap: '5px', fontSize: '0.8rem', opacity: isGeneratingSuggest ? 0.6 : 1 }}
                >
                  <Sparkles size={14} /> {isGeneratingSuggest ? 'Generating...' : 'Suggest with AI'}
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>Primary Problem</label>
                  <input
                    type="text"
                    className="glass-input-sm"
                    value={data.target_audience_problem?.primary_problem || ''}
                    onChange={(e) => updateData({
                      target_audience_problem: { ...(data.target_audience_problem || {}), primary_problem: e.target.value }
                    })}
                    placeholder="e.g. Dull skin caused by pollution"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>Root Cause</label>
                  <input
                    type="text"
                    className="glass-input-sm"
                    value={data.target_audience_problem?.root_cause || ''}
                    onChange={(e) => updateData({
                      target_audience_problem: { ...(data.target_audience_problem || {}), root_cause: e.target.value }
                    })}
                    placeholder="e.g. Pollution blockages & oil"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>Emotional Impact</label>
                  <input
                    type="text"
                    className="glass-input-sm"
                    value={data.target_audience_problem?.emotional_impact || ''}
                    onChange={(e) => updateData({
                      target_audience_problem: { ...(data.target_audience_problem || {}), emotional_impact: e.target.value }
                    })}
                    placeholder="e.g. Lack of confidence"
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>Desired Outcome</label>
                  <input
                    type="text"
                    className="glass-input-sm"
                    value={data.target_audience_problem?.desired_outcome || ''}
                    onChange={(e) => updateData({
                      target_audience_problem: { ...(data.target_audience_problem || {}), desired_outcome: e.target.value }
                    })}
                    placeholder="e.g. Instant glowing appearance"
                  />
                </div>
              </div>

              <div style={{ marginTop: '10px' }}>
                <label style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' }}>Extra Context / General Problem Notes</label>
                <textarea
                  className="glass-textarea"
                  value={data.user_problem_raw || ''}
                  onChange={(e) => updateData({ user_problem_raw: e.target.value })}
                  placeholder="Any extra context or general audience notes..."
                  rows={2}
                />
              </div>
            </div>
          )}

          {(mode === 'psychology' || mode === 'full') && (
            <div className="input-group glass-card">
              <label className="field-label">Common Objections (Optional)</label>
              <textarea
                className="glass-textarea"
                value={data.objections?.[0] || ''}
                onChange={(e) => updateData({ objections: [e.target.value] })}
                placeholder="Why would they say 'No'? (e.g. too expensive, trust issues)"
                rows={2}
              />
            </div>
          )}
        </div>

        {/* Right Column: Offer & Brand */}
        <div className="strategy-col">
          {(mode === 'psychology' || mode === 'full') && (
            <>
              <div className="input-group glass-card">
                <div className="flex-between">
                  <label className="field-label">Trust Signals / Proof</label>
                  <button className="add-link-btn" onClick={addTrustSignal}>+ Add Signal</button>
                </div>
                <div className="dynamic-list scroll-area-sm">
                  {(data.trust_signals_available || []).map((signal, idx) => (
                    <div key={idx} className="dynamic-row">
                      <input
                        type="text"
                        className="glass-input-sm"
                        value={signal}
                        onChange={(e) => updateTrustSignal(idx, e.target.value)}
                        placeholder="e.g. 5-Star Rating, 10k+ Customers"
                      />
                      <button className="icon-btn-danger" onClick={() => removeTrustSignal(idx)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="input-group glass-card">
                <div className="flex-between">
                  <label className="field-label">Offers & Risk Reversal</label>
                  <button className="add-link-btn" onClick={addOffer}>+ Add Offer</button>
                </div>
                <div className="dynamic-list scroll-area-sm">
                  {(data.offer_and_risk_reversal?.offers || []).map((offer, idx) => (
                    <div key={idx} className="offer-block">
                      <div className="offer-inputs">
                        <input
                          type="text"
                          className="glass-input-sm"
                          value={offer.discount}
                          onChange={(e) => updateOffer(idx, 'discount', e.target.value)}
                          placeholder="Offer (e.g. 20% Off)"
                        />
                        <input
                          type="text"
                          className="glass-input-sm"
                          value={offer.guarantee}
                          onChange={(e) => updateOffer(idx, 'guarantee', e.target.value)}
                          placeholder="Risk Reversal (e.g. 7-Day Refund)"
                        />
                      </div>
                      <button className="icon-btn-danger" onClick={() => removeOffer(idx)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="input-group glass-card">
                <label className="field-label">Brand Voice <span className="mandatory">*</span></label>
                <div className="options-selector scroll-area-sm">
                  {VOICES.map(voice => (
                    <div
                      key={voice}
                      className={`chip ${data.brand_voice === voice ? 'active' : ''}`}
                      onClick={() => updateData({ brand_voice: voice })}
                    >
                      {voice}
                    </div>
                  ))}
                  <div
                    className={`chip other-chip ${showOtherVoice ? 'active' : ''}`}
                    onClick={() => setShowOtherVoice(!showOtherVoice)}
                  >
                    + Custom
                  </div>
                </div>
                <AnimatePresence>
                  {showOtherVoice && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="other-input-container"
                    >
                      <input
                        type="text"
                        className="glass-input-sm"
                        placeholder="Describe your voice..."
                        value={otherVoice}
                        onChange={(e) => setOtherVoice(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && updateData({ brand_voice: otherVoice })}
                      />
                      <button className="add-btn-sm" onClick={() => updateData({ brand_voice: otherVoice })}>Set</button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </>
          )}

          {(mode === 'basics' || mode === 'full') && (
            <div className="input-group glass-card">
              <label className="field-label">Target Platforms (Select Multiple) <span className="mandatory">*</span></label>
              <div className="platform-grid">
                {[
                  { id: 'instagram', icon: Instagram, name: 'Instagram' },
                  { id: 'facebook', icon: Facebook, name: 'Facebook' },
                  { id: 'x', icon: Twitter, name: 'X / Twitter' },
                  { id: 'youtube', icon: Youtube, name: 'YouTube' }
                ].map(plat => {
                  const platforms = data.platforms || (data.platform ? [data.platform] : []);
                  const isActive = platforms.includes(plat.id);
                  return (
                    <div
                      key={plat.id}
                      className={`platform-btn ${isActive ? 'active' : ''}`}
                      onClick={() => {
                        const current = data.platforms || (data.platform ? [data.platform] : []);
                        const updated = isActive
                          ? current.filter(p => p !== plat.id)
                          : [...current, plat.id];
                        updateData({ platforms: updated, platform: updated[0] || '' });
                      }}
                    >
                      <plat.icon size={20} />
                      <span>{plat.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .strategy-step {
          width: 100%;
          max-width: 1000px;
          margin: 0 auto;
        }
        .section-header {
          margin-bottom: 24px;
          border-left: 4px solid var(--emerald);
          padding-left: 16px;
        }
        .section-header p {
          opacity: 0.6;
          font-size: 0.9rem;
        }

        .strategy-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 20px;
        }
        .strategy-col {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .glass-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 16px;
          border-radius: 12px;
          transition: all 0.3s ease;
        }
        .glass-card:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.12);
        }

        .field-label {
          display: block;
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 12px;
          color: rgba(255, 255, 255, 0.5);
        }
        .mandatory {
          color: var(--crimson, #ff4d4d);
          margin-left: 2px;
          font-size: 1rem;
        }
        .flex-between {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .funnel-toggle-group {
          display: flex;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 10px;
          padding: 4px;
          gap: 4px;
        }
        .funnel-option {
          flex: 1;
          padding: 10px;
          text-align: center;
          cursor: pointer;
          border-radius: 8px;
          font-size: 0.85rem;
          font-weight: 600;
          transition: 0.2s;
          position: relative;
        }
        .funnel-option.active {
          background: var(--emerald);
          color: black;
        }
        .funnel-tooltip {
          position: absolute;
          bottom: 110%;
          left: 50%;
          transform: translateX(-50%);
          background: #1a1a1a;
          color: white;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 0.75rem;
          width: 200px;
          z-index: 100;
          opacity: 0;
          pointer-events: none;
          transition: 0.3s;
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }
        .funnel-option:hover .funnel-tooltip {
          opacity: 1;
          bottom: 120%;
        }

        .options-selector {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          max-height: 120px;
          overflow-y: auto;
          padding-right: 4px;
        }
        .chip {
          padding: 6px 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          font-size: 0.8rem;
          cursor: pointer;
          transition: 0.2s;
        }
        .chip:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        .chip.active {
          background: var(--indigo);
          border-color: var(--indigo);
          color: white;
        }
        .other-chip {
          border-style: dashed;
          opacity: 0.7;
        }

        .scroll-area {
          scrollbar-width: thin;
          scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
        }
        .scroll-area-sm {
          max-height: 140px;
          overflow-y: auto;
          padding-right: 6px;
        }

        .dynamic-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .dynamic-row {
          display: flex;
          gap: 10px;
        }
        .offer-block {
          background: rgba(255, 255, 255, 0.02);
          padding: 10px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .offer-inputs {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .platform-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 10px;
          width: 100%;
        }
        .platform-btn {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: 0.2s;
          width: 100%;
          justify-content: flex-start;
        }
        .platform-btn:hover {
          background: rgba(255, 255, 255, 0.08);
        }
        .platform-btn.active {
          border-color: var(--emerald);
          background: rgba(16, 185, 129, 0.1);
          color: var(--emerald);
        }
        .platform-other {
          width: 100%;
        }

        .glass-input, .glass-input-sm {
          width: 100% !important;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 12px 16px;
          border-radius: 10px;
          font-size: 1rem;
          color: white;
          outline: none;
          box-sizing: border-box;
        }
        .glass-input-sm {
          padding: 8px 12px;
          font-size: 0.85rem;
        }
        .glass-input:focus, .glass-input-sm:focus {
          border-color: var(--indigo);
        }

        .glass-textarea {
          width: 100%;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 12px 16px;
          border-radius: 10px;
          font-size: 0.95rem;
          color: white;
          outline: none;
          resize: vertical;
          box-sizing: border-box;
        }

        .dynamic-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          width: 100%;
        }
        .dynamic-row {
          width: 100%;
          display: flex;
          gap: 10px;
        }
        .offer-block {
          width: 100%;
          background: rgba(255, 255, 255, 0.02);
          padding: 10px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .options-selector {
          width: 100%;
        }
        .chip {
          /* Keep chips as they are or make them full width? 
             User said "every input field", usually implies the text fields. 
             But just in case, I'll ensure the containers are definitely full-width. */
        }

        .add-link-btn {
          background: transparent;
          border: none;
          color: var(--emerald);
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          opacity: 0.8;
        }
        .add-btn-sm {
          padding: 6px 12px;
          background: var(--indigo);
          border: none;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
          color: white;
          cursor: pointer;
        }
        .icon-btn-danger {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.2);
          cursor: pointer;
          padding: 4px;
        }
        .icon-btn-danger:hover {
          color: #ff4d4d;
        }

        .other-input-container {
          margin-top: 10px;
          display: flex;
          gap: 8px;
        }
      `}</style>
    </motion.div>
  );
};

export default StrategyStep;
