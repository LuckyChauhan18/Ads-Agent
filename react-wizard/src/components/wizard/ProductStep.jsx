import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Upload, X, Camera, Image as ImageIcon, Loader2 } from 'lucide-react';
import { aiAssistService } from '../../services/api';

const ProductStep = ({ data, updateData }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const logoInputRef = useRef(null);
  const imagesInputRef = useRef(null);

  const handleGenerateDescription = async () => {
    if (isGenerating) return;

    const existingIds = [];

    // Extract IDs from existing logo
    if (data.product_logo && typeof data.product_logo === 'string' && data.product_logo.includes('/api/files/')) {
      const id = data.product_logo.split('/api/files/')[1];
      if (id) existingIds.push(id);
    }

    // Extract IDs from existing images
    if (data.product_images) {
      data.product_images.forEach(url => {
        if (typeof url === 'string' && url.includes('/api/files/')) {
          const id = url.split('/api/files/')[1];
          if (id) existingIds.push(id);
        }
      });
    }

    // Check if we have any visual context (files or existing IDs)
    const hasNewFiles = data.product_logo_file || (data.product_images_files && data.product_images_files.length > 0);
    const hasExistingFiles = existingIds.length > 0;

    if (!hasNewFiles && !hasExistingFiles) {
      alert("Please upload at least one product image or logo to generate a description.");
      return;
    }

    setIsGenerating(true);
    const formData = new FormData();

    // Append new files
    if (data.product_logo_file) {
      formData.append('files', data.product_logo_file);
    }
    if (data.product_images_files) {
      data.product_images_files.forEach(file => {
        formData.append('files', file);
      });
    }

    // Append existing file IDs
    if (existingIds.length > 0) {
      formData.append('file_ids', existingIds.join(','));
    }

    formData.append('brand_name', data.brand_name || '');
    formData.append('product_name', data.product_name || '');

    try {
      const res = await aiAssistService.runGenerateDescription(formData);
      updateData({ description: res.data.description });
    } catch (e) {
      console.error(e);
      alert("Failed to generate description. Make sure the backend is running and Gemini API key is configured.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      updateData({
        product_logo: URL.createObjectURL(file),
        product_logo_file: file
      });
    }
  };

  const handleImagesUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      const newUrls = files.map(f => URL.createObjectURL(f));
      updateData({
        product_images: [...(data.product_images || []), ...newUrls],
        product_images_files: [...(data.product_images_files || []), ...files]
      });
    }
  };

  const removeImage = (index) => {
    const newUrls = [...(data.product_images || [])];
    const newFiles = [...(data.product_images_files || [])];
    newUrls.splice(index, 1);
    newFiles.splice(index, 1);
    updateData({ product_images: newUrls, product_images_files: newFiles });
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="step-form"
    >
      <div className="section-header">
        <h2>Product Identity</h2>
        <p className="subtitle">Tell us about what you're selling.</p>
      </div>

      <div className="input-grid">
        {/* Brand & Product */}
        <div className="input-group">
          <label>Brand Name</label>
          <input
            type="text"
            value={data.brand_name || ''}
            onChange={(e) => updateData({ brand_name: e.target.value })}
            placeholder="e.g. Apple"
          />
        </div>
        <div className="input-group">
          <label>Product Name</label>
          <input
            type="text"
            value={data.product_name || ''}
            onChange={(e) => updateData({ product_name: e.target.value })}
            placeholder="e.g. MacBook Air M3"
          />
        </div>

        {/* Visual Identity */}
        <div className="input-group">
          <label>Product Logo</label>
          <div
            className="upload-box logo-upload"
            onClick={() => logoInputRef.current?.click()}
          >
            {data.product_logo ? (
              <img src={data.product_logo} alt="Logo" className="preview-logo" />
            ) : (
              <div className="upload-placeholder">
                <Camera size={20} />
                <span>Upload Logo</span>
              </div>
            )}
            <input
              type="file"
              ref={logoInputRef}
              hidden
              accept="image/*"
              onChange={handleLogoUpload}
            />
          </div>
        </div>

        <div className="input-group">
          <label>Product Images</label>
          <div className="images-upload-container">
            <div
              className="upload-box image-add"
              onClick={() => imagesInputRef.current?.click()}
            >
              <Upload size={20} />
              <input
                type="file"
                ref={imagesInputRef}
                hidden
                multiple
                accept="image/*"
                onChange={handleImagesUpload}
              />
            </div>
            <div className="images-preview-list">
              <AnimatePresence>
                {data.product_images?.map((url, i) => (
                  <motion.div
                    key={url}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    className="image-preview-item"
                  >
                    <img src={url} alt={`Product ${i}`} />
                    <button className="remove-btn" onClick={() => removeImage(i)}>
                      <X size={12} />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Category & Root */}
        <div className="input-group">
          <label>Category</label>
          <input
            type="text"
            value={data.category || ''}
            onChange={(e) => updateData({ category: e.target.value })}
            placeholder="e.g. Laptops"
          />
        </div>
        <div className="input-group">
          <label>Root Product</label>
          <input
            type="text"
            value={data.root_product || ''}
            onChange={(e) => updateData({ root_product: e.target.value })}
            placeholder="e.g. laptop"
          />
        </div>
        <div className="input-group">
          <label>Target Video Length <span className="mandatory">*</span></label>
          <select
            className="modern-select"
            value={data.ad_length || 30}
            onChange={(e) => updateData({ ad_length: parseInt(e.target.value) })}
          >
            <option value={15}>15 Seconds (Punchy)</option>
            <option value={30}>30 Seconds (Standard)</option>
            <option value={45}>45 Seconds (Detailed)</option>
            <option value={60}>60 Seconds (Long Story)</option>
          </select>
        </div>

        <div className="input-group full-width">
          <label>Price Range</label>
          <input
            type="text"
            value={data.price_range || ''}
            onChange={(e) => updateData({ price_range: e.target.value })}
            placeholder="e.g. ₹1,14,900–₹1,64,900"
          />
        </div>

        <div className="input-group full-width">
          <label>Product URL <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)' }}>(for Buy Now CTA)</span></label>
          <input
            type="url"
            value={data.product_url || ''}
            onChange={(e) => updateData({ product_url: e.target.value })}
            placeholder="e.g. https://www.amazon.in/your-product"
          />
        </div>

        {/* Description with Generate Feature */}
        <div className="input-group full-width relative">
          <div className="label-row">
            <label>Description</label>
            <button
              className={`generate-btn ${isGenerating ? 'loading' : ''}`}
              onClick={handleGenerateDescription}
              disabled={isGenerating}
              title="Generate with AI based on images"
            >
              {isGenerating ? <Loader2 className="spin" size={14} /> : <Sparkles size={14} />}
              <span>{isGenerating ? 'Generating...' : 'Generate with AI'}</span>
            </button>
          </div>
          <textarea
            value={data.description || ''}
            onChange={(e) => updateData({ description: e.target.value })}
            placeholder="Brief description of the product..."
            style={{ minHeight: '100px' }}
          />
        </div>

        <div className="input-group full-width">
          <label>Key Features (Comma separated)</label>
          <textarea
            value={data.features?.join(', ') || ''}
            onChange={(e) => updateData({ features: e.target.value.split(',').map(f => f.trim()) })}
            placeholder="Apple M3 Chip, 18-Hour Battery Life..."
            style={{ minHeight: '80px' }}
          />
        </div>
      </div>

      <style>{`
        .step-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
          height: 100%;
          overflow-y: auto;
          overflow-x: hidden;
          padding-right: 12px;
        }
        .section-header {
          margin-bottom: 8px;
        }
        .subtitle {
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.5);
        }
        .mandatory {
          color: #ff4d4d;
          margin-left: 2px;
        }
        .modern-select {
          width: 100%;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.08);
          padding: 12px 16px;
          border-radius: 10px;
          font-size: 1rem;
          color: white;
          outline: none;
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 12px center;
          background-size: 16px;
        }
        .modern-select option {
          background: #1a1a1a;
          color: white;
        }
        .modern-select:focus {
          border-color: #6366f1;
        }
        .input-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .full-width {
          grid-column: span 2;
        }
        input, textarea {
          width: 100% !important;
          box-sizing: border-box;
        }
        .label-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .generate-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          border: none;
          border-radius: 6px;
          padding: 4px 10px;
          color: white;
          font-size: 0.7rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .generate-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }
        .generate-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .spin {
          animation: rotate 1s linear infinite;
        }
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        
        .upload-box {
          height: 120px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px dashed rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        .upload-box:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: rgba(255, 255, 255, 0.4);
        }
        .upload-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          color: rgba(255, 255, 255, 0.4);
          font-size: 0.75rem;
        }
        .preview-logo {
          height: 100px;
          width: 100px;
          object-fit: contain;
        }
        .images-upload-container {
          display: flex;
          gap: 12px;
          align-items: center;
          height: 120px;
        }
        .image-add {
          width: 120px;
          flex-shrink: 0;
          color: rgba(255, 255, 255, 0.4);
        }
        .images-preview-list {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          padding-bottom: 4px;
        }
        .image-preview-item {
          width: 110px;
          height: 110px;
          border-radius: 8px;
          position: relative;
          background: black;
          flex-shrink: 0;
        }
        .image-preview-item img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 8px;
        }
        .remove-btn {
          position: absolute;
          top: -4px;
          right: -4px;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #ef4444;
          color: white;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }
      `}</style>
    </motion.div>
  );
};

export default ProductStep;
