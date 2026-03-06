import React from 'react';
import { motion } from 'framer-motion';
import { Trash2, Plus, Target } from 'lucide-react';

const CurationStep = ({ brands, updateBrands }) => {
  const addBrand = () => {
    updateBrands([...brands, { name: '', target_count: 3 }]);
  };

  const removeBrand = (index) => {
    const newBrands = brands.filter((_, i) => i !== index);
    updateBrands(newBrands);
  };

  const updateBrand = (index, field, value) => {
    const newBrands = [...brands];
    newBrands[index][field] = value;
    updateBrands(newBrands);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="step-content"
    >
      <h2>Curate Competitor List</h2>
      <p className="subtitle">Edit brands and specify how many "Ads DNA" points to extract for each.</p>

      <div className="curation-list">
        {brands.map((brand, bIndex) => (
          <div key={bIndex} className="brand-row glass">
            <div className="brand-main">
              <input
                type="text"
                value={brand.name}
                onChange={(e) => updateBrand(bIndex, 'name', e.target.value)}
                placeholder="Competitor Name"
                className="brand-input"
              />
            </div>

            <div className="brand-count">
              <Target size={14} className="icon" />
              <input
                type="number"
                min="1"
                max="10"
                value={brand.target_count}
                onChange={(e) => updateBrand(bIndex, 'target_count', parseInt(e.target.value))}
                className="count-input"
              />
              <span className="label">Ads</span>
            </div>

            <button className="delete-btn" onClick={() => removeBrand(bIndex)}>
              <Trash2 size={18} />
            </button>
          </div>
        ))}

        <button className="add-brand-btn glass" onClick={addBrand}>
          <Plus size={20} /> Add Custom Brand
        </button>
      </div>

      <style>{`
        .curation-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-top: 24px;
        }
        .brand-row {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          border-radius: 16px;
        }
        .brand-main {
          flex: 1;
        }
        .brand-input {
          background: transparent;
          border: none;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 0;
          padding: 8px 0;
          font-weight: 600;
          font-size: 1.1rem;
        }
        .brand-input:focus {
          border-color: var(--indigo);
          background: transparent;
        }
        .brand-count {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(255, 255, 255, 0.05);
          padding: 8px 12px;
          border-radius: 10px;
        }
        .count-input {
          width: 50px;
          background: transparent;
          border: none;
          text-align: center;
          font-weight: 700;
          padding: 0;
        }
        .count-input:focus {
          background: transparent;
        }
        .label {
          font-size: 0.7rem;
          text-transform: uppercase;
          opacity: 0.6;
        }
        .delete-btn {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.3);
          cursor: pointer;
          transition: var(--transition);
        }
        .delete-btn:hover {
          color: var(--crimson);
          transform: scale(1.1);
        }
        .add-brand-btn {
          width: 100%;
          padding: 16px;
          border-radius: 16px;
          border: 1px dashed rgba(255, 255, 255, 0.2);
          background: transparent;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          cursor: pointer;
          font-weight: 600;
        }
        .add-brand-btn:hover {
          background: rgba(255, 255, 255, 0.05);
          border-color: white;
        }
        .subtitle {
          opacity: 0.6;
          font-size: 0.9rem;
          margin-top: -12px;
        }
      `}</style>
    </motion.div>
  );
};

export default CurationStep;
