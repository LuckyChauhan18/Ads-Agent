import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, User, Check, RefreshCw, Loader2, Wand2, Info, X, Upload } from 'lucide-react';
import { workflowService, aiAssistService } from '../services/api';

const AvatarStep = ({ data, updateData }) => {
  const [mode, setMode] = useState((data.selected_avatars && data.selected_avatars.length > 0) ? 'custom' : 'default');
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [options, setOptions] = useState(data.selected_avatars || []);
  const [historyOptions, setHistoryOptions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    if (mode === 'custom') {
      fetchAvatarHistory();
    }
  }, [mode]);

  const fetchAvatarHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await workflowService.runGetAvatarHistory();
      if (res.data.results) {
        setHistoryOptions(res.data.results);
      }
    } catch (e) {
      console.error("Failed to fetch avatar history", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const selectedAvatars = data.selected_avatars || [];

  const handleGenerate = async () => {
    if (generating) return;
    setGenerating(true);
    try {
      const res = await workflowService.runGenerateAvatars(
        data.gender || 'Auto',
        data.style || 'Professional',
        customPrompt
      );
      if (res.data.results) {
        const newAvatar = res.data.results;
        setOptions(prev => [newAvatar, ...prev]);
        // Auto-select the newly generated one (add to list)
        toggleAvatar(newAvatar);
      } else {
        alert('Generation failed. This often happens if the prompt contains names of famous people, celebrities, or restricted content due to AI safety policies.');
      }
    } catch (e) {
      alert('Generation failed. Please check your API key.');
    } finally {
      setGenerating(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await aiAssistService.runUploadAvatar(formData);
      if (res.data.results) {
        const newAvatar = res.data.results;
        setOptions(prev => [newAvatar, ...prev]);
        toggleAvatar(newAvatar);
      }
    } catch (err) {
      alert('Upload failed.');
    } finally {
      setUploading(false);
      e.target.value = ''; // Reset input
    }
  };

  const toggleAvatar = (opt) => {
    const exists = selectedAvatars.find(a => a.url === opt.url);
    let newSelection;
    if (exists) {
      newSelection = selectedAvatars.filter(a => a.url !== opt.url);
    } else {
      newSelection = [...selectedAvatars, opt];
    }

    updateData({
      selected_avatars: newSelection,
      // Legacy compatibility for single-avatar logic elsewhere if needed
      custom_avatar_url: newSelection.length > 0 ? newSelection[0].url : null,
      avatar_id: newSelection.length > 0 ? newSelection[0].id : null,
      style: newSelection.length > 0 ? newSelection[0].style : opt.style,
      gender: newSelection.length > 0 ? newSelection[0].gender : opt.gender
    });
  };

  const getSelectionIndex = (url) => {
    const index = selectedAvatars.findIndex(a => a.url === url);
    return index !== -1 ? index + 1 : null;
  };

  const clearPrompt = () => setCustomPrompt('');

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="avatar-step"
    >
      <div className="step-header">
        <h2 className="premium-gradient-text">Avatar & Delivery</h2>
        <p className="subtitle text-secondary">Choose one or more faces to represent your brand. They will rotate across scenes.</p>
      </div>

      <div className="mode-selector-wrapper card glass shadow-lg">
        <div className="mode-tabs">
          <button
            className={`tab-btn ${mode === 'default' ? 'active' : ''}`}
            onClick={() => {
              setMode('default');
              updateData({ selected_avatars: [], custom_avatar_url: null, avatar_id: null });
            }}
          >
            <div className="tab-icon"><User size={20} /></div>
            <div className="tab-label">
              <span>Regular Avatar</span>
              <small>Auto-selected by AI</small>
            </div>
          </button>
          <button
            className={`tab-btn ${mode === 'custom' ? 'active' : ''}`}
            onClick={() => setMode('custom')}
          >
            <div className="tab-icon sparkles-gold"><Sparkles size={20} /></div>
            <div className="tab-label">
              <span>AI Custom Avatar</span>
              <small>Generate unique identity</small>
            </div>
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {mode === 'default' ? (
          <motion.div
            key="default"
            initial={{ opacity: 0, scale: 0.98, filter: 'blur(10px)' }}
            animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 0.98, filter: 'blur(10px)' }}
            className="auto-selection-card card glass-premium"
          >
            <div className="magic-orb">
              <Wand2 size={48} className="wand-anim" />
              <div className="orb-glow"></div>
            </div>
            <h3>Gemini Intelligent Selection</h3>
            <p className="description">
              Our neural rendering engine will automatically pair your storyboard with the
              optimal presenter identity. It analyzes your industry, tone, and audience
              to ensure maximum resonance.
            </p>
            <div className="feature-badges">
              <span className="badge"><Check size={14} /> Narrative Sync</span>
              <span className="badge"><Check size={14} /> Tone Match</span>
              <span className="badge"><Check size={14} /> Dynamic Rendering</span>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="custom"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="custom-flow"
          >
            <div className="parameters-card card glass-premium shadow-xl">
              <div className="input-row">
                <div className="input-group">
                  <label>Target Gender</label>
                  <select
                    value={data.gender || 'Auto'}
                    onChange={(e) => updateData({ gender: e.target.value })}
                    className="premium-select"
                  >
                    <option>Auto</option>
                    <option>Male</option>
                    <option>Female</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Identity Style</label>
                  <select
                    value={data.style || 'Professional'}
                    onChange={(e) => updateData({ style: e.target.value })}
                    className="premium-select"
                  >
                    <option>Professional</option>
                    <option>Casual</option>
                    <option>Energetic</option>
                    <option>Traditional Indian</option>
                    <option>Modern tech</option>
                  </select>
                </div>
              </div>

              <div className="input-group full-width prompt-container">
                <div className="label-row">
                  <div className="label-with-hint">
                    <label>Visual Design Prompt</label>
                    <small className="text-secondary">(Priority Mode: Describe person, clothes, setting)</small>
                  </div>
                  {customPrompt && (
                    <button onClick={clearPrompt} className="btn-clear">
                      <X size={14} /> Clear
                    </button>
                  )}
                </div>
                <textarea
                  className="premium-textarea"
                  placeholder="E.g. A fit Indian athlete with a beard, wearing a sporty jersey, determined look, high-end studio lighting..."
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="action-row-split">
                <button
                  className={`btn-generate-premium ${generating ? 'generating' : ''}`}
                  onClick={handleGenerate}
                  disabled={generating || uploading}
                >
                  {generating ? (
                    <>
                      <Loader2 className="spin" size={20} />
                      <span>Generating Persona...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw size={20} className="refresh-icon" />
                      <span>Craft Custom Avatar</span>
                    </>
                  )}
                </button>

                <button
                  className={`btn-upload-premium ${uploading ? 'generating' : ''}`}
                  onClick={handleUploadClick}
                  disabled={uploading || generating}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                    accept="image/*"
                  />
                  {uploading ? (
                    <>
                      <Loader2 className="spin" size={20} />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={20} />
                      <span>Manual Upload</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="gallery-section">
              <div className="section-header">
                <div>
                  <h4>Created Persona Gallery</h4>
                  <p className="selection-hint">Tap to select multiple. They will appear in order (1, 2, 3...)</p>
                </div>
                <span className="count-badge">{selectedAvatars.length} Selected</span>
              </div>

              <div className="avatar-grid-wrapper">
                {options.length > 0 ? (
                  <div className="avatar-grid">
                    {options.map((opt) => {
                      const selIndex = getSelectionIndex(opt.url);
                      return (
                        <motion.div
                          layoutId={opt.id}
                          key={opt.id}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className={`avatar-card-premium ${selIndex ? 'selected' : ''}`}
                          onClick={() => toggleAvatar(opt)}
                        >
                          <img src={`http://localhost:8000${opt.url}`} alt="Avatar" />

                          <AnimatePresence>
                            {selIndex && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                exit={{ scale: 0 }}
                                className="selection-pill"
                              >
                                {selIndex}
                              </motion.div>
                            )}
                          </AnimatePresence>

                          <div className="card-overlay">
                            <div className="selection-indicator">
                              <Check size={16} />
                            </div>
                          </div>
                          {selIndex && <div className="active-highlight"></div>}
                        </motion.div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="empty-gallery glass shadow-inner">
                    <div className="empty-icon-box">
                      <Sparkles className="floating" />
                    </div>
                    <p>No personas generated or uploaded yet.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Avatar History Section */}
            {(historyOptions.length > 0 || loadingHistory) && (
              <div className="gallery-section history-section">
                <div className="section-header">
                  <div>
                    <h4>From Your History</h4>
                    <p className="selection-hint">Personas you've used in previous campaigns.</p>
                  </div>
                </div>

                <div className="avatar-grid-wrapper">
                  {loadingHistory ? (
                    <div className="loading-history">
                      <Loader2 className="spin" size={24} />
                      <span>Loading history...</span>
                    </div>
                  ) : (
                    <div className="avatar-grid">
                      {historyOptions.map((opt) => {
                        const selIndex = getSelectionIndex(opt.url);
                        return (
                          <motion.div
                            key={opt.id}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className={`avatar-card-premium history-card ${selIndex ? 'selected' : ''}`}
                            onClick={() => toggleAvatar(opt)}
                          >
                            <img src={opt.url.startsWith('http') ? opt.url : `http://localhost:8000${opt.url}`} alt="Avatar" />
                            {selIndex && (
                              <div className="selection-pill">{selIndex}</div>
                            )}
                            <div className="card-overlay">
                              <div className="selection-indicator">
                                <Check size={16} />
                              </div>
                            </div>
                            {selIndex && <div className="active-highlight"></div>}
                            <div className="history-date">
                              {new Date(opt.created_at).toLocaleDateString()}
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        .avatar-step {
          display: flex;
          flex-direction: column;
          gap: 32px;
          width: 100%;
          max-width: 900px;
          margin: 0 auto;
          padding-bottom: 40px;
        }

        .premium-gradient-text {
            background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .text-secondary { color: rgba(255, 255, 255, 0.5); }
        
        .mode-selector-wrapper {
            padding: 8px;
            border-radius: 20px;
        }

        .mode-tabs {
            display: flex;
            gap: 12px;
        }

        .tab-btn {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px 24px;
            border-radius: 14px;
            border: none;
            background: rgba(255, 255, 255, 0.03);
            cursor: pointer;
            text-align: left;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        }

        .tab-btn.active {
            background: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .tab-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            color: rgba(255,255,255,0.4);
            transition: all 0.4s ease;
        }

        .tab-btn.active .tab-icon {
            background: #6366f1;
            color: white;
        }

        .sparkles-gold { color: #fbbf24; }

        .tab-label {
            display: flex;
            flex-direction: column;
        }

        .tab-label span {
            font-weight: 700;
            font-size: 1.05rem;
            color: rgba(255, 255, 255, 0.8);
            transition: color 0.4s;
        }

        .tab-label small {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.3);
            transition: color 0.4s;
        }

        .tab-btn.active .tab-label span { color: #000; }
        .tab-btn.active .tab-label small { color: rgba(0,0,0,0.5); }

        .glass-premium {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .auto-selection-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 60px 40px;
            gap: 24px;
            border-radius: 32px;
            position: relative;
            overflow: hidden;
        }

        .magic-orb {
            width: 120px;
            height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .orb-glow {
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, #6366f1 0%, transparent 70%);
            opacity: 0.3;
            animation: pulse 3s infinite alternate;
        }

        .wand-anim { 
            color: #818cf8; 
            z-index: 1;
            animation: float 4s infinite ease-in-out;
        }

        .auto-selection-card h3 {
            font-size: 1.75rem;
            font-weight: 800;
            color: white;
        }

        .auto-selection-card p.description {
            color: rgba(255, 255, 255, 0.5);
            line-height: 1.7;
            max-width: 600px;
            font-size: 1.05rem;
        }

        .feature-badges {
            display: flex;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .badge {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            color: rgba(255,255,255,0.7);
            padding: 8px 18px;
            border-radius: 100px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .custom-flow {
            display: flex;
            flex-direction: column;
            gap: 40px;
        }

        .parameters-card {
            display: flex;
            flex-direction: column;
            gap: 28px;
            padding: 32px;
            border-radius: 28px;
        }

        .input-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        .input-group label {
            display: block;
            font-size: 0.85rem;
            font-weight: 700;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .premium-select, .premium-textarea {
            width: 100%;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 14px 18px;
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .premium-select:focus, .premium-textarea:focus {
            background: rgba(255,255,255,0.08);
            border-color: #6366f1;
            outline: none;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
        }

        .label-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .label-with-hint { display: flex; flex-direction: column; gap: 2px; }
        .label-with-hint label { margin-bottom: 0; }
        .label-with-hint small { font-size: 0.7rem; color: rgba(255,255,255,0.3); }

        .btn-clear {
            background: rgba(255,255,255,0.05);
            border: none;
            color: rgba(255,255,255,0.4);
            padding: 4px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .action-row-split {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
        }

        .btn-generate-premium, .btn-upload-premium {
            padding: 18px;
            border-radius: 18px;
            border: none;
            font-weight: 800;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
            position: relative;
            overflow: hidden;
        }

        .btn-generate-premium { background: white; color: black; }
        .btn-upload-premium { 
            background: rgba(255,255,255,0.05); 
            color: white; 
            border: 1px solid rgba(255,255,255,0.1);
        }

        .btn-generate-premium:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(255,255,255,0.1); }
        .btn-upload-premium:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); }

        .btn-generate-premium.generating, .btn-upload-premium.generating {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .gallery-section { display: flex; flex-direction: column; gap: 24px; }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            padding-bottom: 12px;
        }

        .selection-hint { font-size: 0.75rem; color: rgba(255,255,255,0.3); margin-top: 4px; }

        .avatar-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 20px;
        }

        .avatar-card-premium {
            aspect-ratio: 1/1.3;
            border-radius: 20px;
            overflow: hidden;
            cursor: pointer;
            position: relative;
            background: rgba(255,255,255,0.03);
            transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        }

        .avatar-card-premium img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }

        .avatar-card-premium:hover img { transform: scale(1.1); }

        .selection-pill {
            position: absolute;
            top: 12px;
            left: 12px;
            width: 28px;
            height: 28px;
            background: #6366f1;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.9rem;
            z-index: 5;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            border: 2px solid white;
        }

        .card-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.6), transparent);
            opacity: 0;
            transition: opacity 0.3s;
            display: flex;
            align-items: flex-end;
            justify-content: flex-end;
            padding: 12px;
        }

        .avatar-card-premium:hover .card-overlay { opacity: 1; }

        .active-highlight {
            position: absolute;
            inset: 0;
            border: 3px solid #6366f1;
            border-radius: 20px;
            box-shadow: inset 0 0 20px rgba(99, 102, 241, 0.4);
            pointer-events: none;
        }

        .empty-gallery {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 80px 20px;
            gap: 20px;
            border-radius: 24px;
            color: rgba(255, 255, 255, 0.2);
            text-align: center;
            background: rgba(0,0,0,0.1);
        }

        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }

        .history-section {
          margin-top: 20px;
          border-top: 1px solid rgba(255,255,255,0.05);
          padding-top: 30px;
        }
        .loading-history {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          padding: 40px;
          opacity: 0.5;
        }
        .history-card {
          aspect-ratio: 1/1.4;
        }
        .history-date {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: rgba(0,0,0,0.6);
          color: white;
          font-size: 0.65rem;
          padding: 4px;
          text-align: center;
          backdrop-filter: blur(4px);
        }
      `}</style>
    </motion.div>
  );
};

export default AvatarStep;
