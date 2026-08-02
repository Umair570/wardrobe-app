import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, MessageSquare, Flame } from 'lucide-react';

// Color-rich preset outfits with realistic transparent background photography
const OUTFIT_PRESETS = [
  {
    id: 'casual',
    title: 'Casual Weekend Fit',
    matchScore: '98% Match',
    comment: '"Perfect combination for a relaxed casual day out!"',
    accentColor: 'from-blue-500/10 via-indigo-500/10 to-purple-500/10',
    badgeBg: 'bg-indigo-600 text-white',
    top: { 
      name: 'Navy Cotton Tee', 
      sub: 'Tops · Casual', 
      image: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-blue-50 border-blue-200/60'
    },
    bottom: { 
      name: 'Classic Blue Denim', 
      sub: 'Bottoms · Denim', 
      image: 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-indigo-50 border-indigo-200/60'
    },
  },
  {
    id: 'formal',
    title: 'Executive Chic Fit',
    matchScore: '95% Match',
    comment: '"Crisp silhouette ideal for high-impact presentations!"',
    accentColor: 'from-amber-500/10 via-rose-500/10 to-orange-500/10',
    badgeBg: 'bg-amber-600 text-white',
    top: { 
      name: 'Beige Trench & Blazer', 
      sub: 'Tops · Formal', 
      image: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-amber-50 border-amber-200/60'
    },
    bottom: { 
      name: 'Tailored Trousers', 
      sub: 'Bottoms · Suits', 
      image: 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-orange-50 border-orange-200/60'
    },
  },
  {
    id: 'streetwear',
    title: 'Urban Streetwear',
    matchScore: '93% Match',
    comment: '"Bold layering for a vibrant modern vibe!"',
    accentColor: 'from-emerald-500/10 via-teal-500/10 to-cyan-500/10',
    badgeBg: 'bg-emerald-600 text-white',
    top: { 
      name: 'Emerald Oversized Hoodie', 
      sub: 'Tops · Outerwear', 
      image: 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-emerald-50 border-emerald-200/60'
    },
    bottom: { 
      name: 'Utility Cargo Pants', 
      sub: 'Bottoms · Utility', 
      image: 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=300&q=80',
      bgColor: 'bg-teal-50 border-teal-200/60'
    },
  }
];

export default function AnimatedOutfitMatch() {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Speed up rotation: changes every 2.8 seconds for an energetic demo feel
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % OUTFIT_PRESETS.length);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  const currentOutfit = OUTFIT_PRESETS[currentIndex];

  return (
    <div className={`relative w-full overflow-hidden bg-gradient-to-br ${currentOutfit.accentColor} bg-white border border-gray-200/80 rounded-3xl p-6 shadow-xl transition-all duration-700 space-y-4`}>
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200/60 pb-3.5">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500 animate-spin" style={{ animationDuration: '4s' }} />
          <span className="text-xs font-extrabold text-gray-800 uppercase tracking-wider">
            {currentOutfit.title}
          </span>
        </div>
        <motion.span 
          key={`score-${currentOutfit.id}`}
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 15 }}
          className={`px-3 py-1 rounded-full text-xs font-bold shadow-sm flex items-center gap-1 ${currentOutfit.badgeBg}`}
        >
          <Flame className="w-3.5 h-3.5 fill-current" />
          {currentOutfit.matchScore}
        </motion.span>
      </div>

      {/* Dynamic Visual Stage */}
      <div className="relative h-48 flex items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.div 
            key={currentOutfit.id}
            className="grid grid-cols-2 gap-4 w-full"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
          >
            {/* TOP ITEM CARD */}
            <motion.div
              initial={{ x: -60, y: -20, opacity: 0, rotate: -8, scale: 0.9 }}
              animate={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 1 }}
              transition={{ type: 'spring', stiffness: 220, damping: 16 }}
              className={`${currentOutfit.top.bgColor} rounded-2xl p-3.5 border flex flex-col items-center text-center gap-2 shadow-sm hover:shadow-md transition-shadow`}
            >
              <div className="w-24 h-24 rounded-xl overflow-hidden bg-white/80 p-1 flex items-center justify-center shadow-inner">
                <img 
                  src={currentOutfit.top.image} 
                  alt={currentOutfit.top.name} 
                  className="w-full h-full object-cover rounded-lg transform hover:scale-105 transition-transform"
                />
              </div>
              <div>
                <span className="text-xs font-extrabold text-gray-900 block line-clamp-1">{currentOutfit.top.name}</span>
                <span className="text-[10px] text-gray-500 font-semibold">{currentOutfit.top.sub}</span>
              </div>
            </motion.div>

            {/* BOTTOM ITEM CARD */}
            <motion.div
              initial={{ x: 60, y: 20, opacity: 0, rotate: 8, scale: 0.9 }}
              animate={{ x: 0, y: 0, opacity: 1, rotate: 0, scale: 1 }}
              transition={{ type: 'spring', stiffness: 220, damping: 16, delay: 0.08 }}
              className={`${currentOutfit.bottom.bgColor} rounded-2xl p-3.5 border flex flex-col items-center text-center gap-2 shadow-sm hover:shadow-md transition-shadow`}
            >
              <div className="w-24 h-24 rounded-xl overflow-hidden bg-white/80 p-1 flex items-center justify-center shadow-inner">
                <img 
                  src={currentOutfit.bottom.image} 
                  alt={currentOutfit.bottom.name} 
                  className="w-full h-full object-cover rounded-lg transform hover:scale-105 transition-transform"
                />
              </div>
              <div>
                <span className="text-xs font-extrabold text-gray-900 block line-clamp-1">{currentOutfit.bottom.name}</span>
                <span className="text-[10px] text-gray-500 font-semibold">{currentOutfit.bottom.sub}</span>
              </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Stylist Comment Banner */}
      <AnimatePresence mode="wait">
        <motion.div 
          key={`comment-${currentOutfit.id}`}
          initial={{ y: 12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -12, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="p-3 bg-white/90 backdrop-blur-md rounded-xl border border-gray-200/80 flex items-center gap-3 shadow-sm"
        >
          <div className="w-7 h-7 rounded-lg bg-black text-white flex items-center justify-center shrink-0">
            <MessageSquare className="w-4 h-4" />
          </div>
          <p className="text-xs text-gray-800 font-bold italic">
            {currentOutfit.comment}
          </p>
        </motion.div>
      </AnimatePresence>

      {/* Progress Dots */}
      <div className="flex justify-center gap-2 pt-1">
        {OUTFIT_PRESETS.map((_, idx) => (
          <div
            key={idx}
            className={`h-2 rounded-full transition-all duration-300 ${
              idx === currentIndex ? 'w-6 bg-gray-900' : 'w-2 bg-gray-300'
            }`}
          />
        ))}
      </div>

    </div>
  );
}