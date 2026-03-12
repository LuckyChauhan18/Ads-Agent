import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Target, Wind, Zap, AlertCircle, CheckCircle2, Gift, MessageSquare, Gauge, Hash, TrendingUp, Eye, Edit2 } from 'lucide-react';

const CompetitorStep = ({ research, updateCompetitor }) => {
  const [expandedCard, setExpandedCard] = useState(null);

  if (!research) return (
    <div className="flex flex-col items-center justify-center min-h-100 gap-6">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
        <div className="absolute inset-0 w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin-slow" style={{ animationDirection: 'reverse' }} />
      </div>
      <p className="text-white/60 text-lg animate-pulse">Analyzing competitor ecosystems...</p>
    </div>
  );

  // Check if competitors array exists and has items
  if (!research.competitors || !Array.isArray(research.competitors) || research.competitors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-100 gap-6 bg-linear-to-br from-red-500/5 to-orange-500/5 rounded-2xl border border-red-500/20 p-12">
        <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center">
          <AlertCircle className="w-10 h-10 text-red-400" />
        </div>
        <div className="text-center">
          <p className="text-white/80 text-lg font-semibold mb-2">No competitor data available</p>
          <p className="text-white/50 text-sm">Please go back and run research again.</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      {/* Header Section */}
      <div className="flex justify-between items-start mb-8 pb-6 border-b border-white/5">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-linear-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-3xl font-bold bg-linear-to-r from-white via-white to-white/60 bg-clip-text text-transparent">
              Market DNA Insights
            </h2>
          </div>
          <p className="text-white/50 text-base ml-15">
            Deep architectural breakdown of how your competitors are winning.
          </p>
        </div>
        <div className="flex items-center gap-2 px-5 py-3 rounded-full bg-linear-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 backdrop-blur-sm shadow-lg shadow-indigo-500/5">
          <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          <Brain className="w-4 h-4 text-indigo-300" />
          <span className="text-sm font-semibold text-indigo-200">Deep DNA Extraction Active</span>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-linear-to-br from-green-500/10 to-emerald-500/10 rounded-xl p-5 border border-green-500/20">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-green-400" />
            <div>
              <p className="text-sm text-white/50">Competitors Analyzed</p>
              <p className="text-2xl font-bold text-white">{research.competitors.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-linear-to-br from-blue-500/10 to-cyan-500/10 rounded-xl p-5 border border-blue-500/20">
          <div className="flex items-center gap-3">
            <Eye className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-sm text-white/50">Total Ads Scanned</p>
              <p className="text-2xl font-bold text-white">
                {research.competitors.reduce((sum, c) => sum + (c.actual_count || 0), 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-linear-to-br from-purple-500/10 to-pink-500/10 rounded-xl p-5 border border-purple-500/20">
          <div className="flex items-center gap-3">
            <Zap className="w-8 h-8 text-purple-400" />
            <div>
              <p className="text-sm text-white/50">Patterns Identified</p>
              <p className="text-2xl font-bold text-white">
                {research.competitors.filter(c => c.actual_count > 0).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Competitor Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {research.competitors.map((c, i) => {
          const primaryAd = c.ads && c.ads.length > 0 ? c.ads[0].dna : null;
          const isExpanded = expandedCard === i;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className="group relative"
            >
              <div className="absolute inset-0 bg-linear-to-br from-purple-500/5 to-blue-500/5 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-300 opacity-0 group-hover:opacity-100" />
              
              <div className="relative bg-linear-to-br from-white/2 to-white/1 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden hover:border-white/20 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/10 hover:-translate-y-1">
                {/* Card Header */}
                <div className="relative bg-linear-to-r from-white/5 to-transparent p-6 border-b border-white/5">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">{c.company}</h3>
                      <div className="flex gap-2">
                        <span className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg bg-green-500/10 text-green-300 border border-green-500/20">
                          {primaryAd?.tone || 'Professional'}
                        </span>
                        <span className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          {primaryAd?.hook_type || 'Discovery'}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col items-center bg-black/20 backdrop-blur-sm rounded-xl px-4 py-3 border border-white/5">
                      <div className="flex items-baseline gap-1">
                        <span className="text-3xl font-black bg-linear-to-br from-green-400 to-emerald-500 bg-clip-text text-transparent">
                          {c.actual_count}
                        </span>
                        <span className="text-white/20 text-sm font-bold">/</span>
                        <span className="text-white/30 text-lg font-semibold">{c.target_count}</span>
                      </div>
                      <span className="text-[10px] uppercase font-bold text-white/30 tracking-wider mt-1">DNA Points</span>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-6 space-y-5">
                  {/* Hook & Punchline Grid */}
                  <div className="grid grid-cols-1 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/40">
                        <Wind className="w-3 h-3" />
                        <span>Hook</span>
                      </div>
                      <div className="bg-white/2 backdrop-blur-sm rounded-xl p-4 border border-white/5 min-h-20">
                        <p className="text-sm leading-relaxed text-white/70 italic">
                          {primaryAd?.refined_hook || primaryAd?.hook || "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/40">
                        <Target className="w-3 h-3" />
                        <span>Punch Line</span>
                        <Edit2 className="w-3 h-3 ml-auto text-indigo-400/60" />
                      </div>
                      <div
                        className="bg-linear-to-br from-indigo-500/5 to-purple-500/5 backdrop-blur-sm rounded-xl p-4 border border-indigo-500/20 min-h-20 cursor-text hover:border-indigo-400/30 transition-colors focus-within:border-indigo-400/50 focus-within:bg-indigo-500/10"
                        contentEditable
                        onBlur={(e) => updateCompetitor(i, e.target.innerText)}
                        suppressContentEditableWarning={true}
                      >
                        <p className="text-sm leading-relaxed text-white font-medium outline-none">
                          {c.top_punchline}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Strategy Matrix */}
                  <div className="bg-linear-to-br from-white/2 to-transparent rounded-xl p-5 border border-white/5">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-white/30">
                          <AlertCircle className="w-3 h-3" />
                          <span>Problem</span>
                        </div>
                        <p className="text-sm font-medium text-white/80 leading-snug">
                          {primaryAd?.problem || "Implied/Contextual"}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-white/30">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Solution</span>
                        </div>
                        <p className="text-sm font-medium text-white/80 leading-snug">
                          {primaryAd?.solution || "Product Benefits"}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-white/30">
                          <Gift className="w-3 h-3" />
                          <span>Offer</span>
                        </div>
                        <p className="text-sm font-bold text-yellow-300 leading-snug">
                          {primaryAd?.offer || "None Detected"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Footer Meta */}
                  <div className="flex flex-wrap gap-2 pt-4 border-t border-white/5">
                    <div className="flex items-center gap-2 text-xs font-medium text-white/40 bg-white/2 px-3 py-2 rounded-lg border border-white/5">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>{primaryAd?.angle || 'Lifestyle'} Angle</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium text-white/40 bg-white/2 px-3 py-2 rounded-lg border border-white/5">
                      <Gauge className="w-3.5 h-3.5" />
                      <span>{primaryAd?.text_length || 'Medium'} chars</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium text-white/40 bg-white/2 px-3 py-2 rounded-lg border border-white/5">
                      <Hash className="w-3.5 h-3.5" />
                      <span>Emojis: {primaryAd?.emoji_usage ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-bold text-indigo-200 bg-linear-to-r from-indigo-500/10 to-purple-500/10 px-3 py-2 rounded-lg border border-indigo-500/20 ml-auto">
                      <Zap className="w-3.5 h-3.5" />
                      <span>High Converting</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default CompetitorStep;
