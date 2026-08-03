import React, { useState, useEffect } from 'react';

// Mock Data Structure (Replace with your backend state/props)
const INSIGHTS_DATA = [
  {
    id: 'most-viewed',
    title: 'Most Viewed Items',
    icon: '◎',
    items: [
      { id: 1, name: 'Charcoal Blazer', detail: '14 views' },
      { id: 2, name: 'Dark Blue Jeans', detail: '11 views' },
      { id: 3, name: 'White Sneakers', detail: '9 views' },
    ],
  },
  {
    id: 'most-worn',
    title: 'Most Worn Items',
    icon: '◈',
    items: [
      { id: 1, name: 'Navy T-Shirt', detail: '8 outfits' },
      { id: 2, name: 'Dark Blue Jeans', detail: '7 outfits' },
      { id: 3, name: 'Grey Hoodie', detail: '4 outfits' },
    ],
  },
  {
    id: 'recently-added',
    title: 'Recently Added',
    icon: '↑',
    items: [
      { id: 1, name: 'Leather Jacket', detail: 'Added 2 days ago' },
      { id: 2, name: 'Linen Shirt', detail: 'Added 4 days ago' },
      { id: 3, name: 'Beige Chinos', detail: 'Added 1 week ago' },
    ],
  },
  {
    id: 'seasonal-picks',
    title: 'Seasonal Picks',
    icon: '◐',
    items: [
      { id: 1, name: 'Floral Summer Dress', detail: 'Summer' },
      { id: 2, name: 'Denim Shorts', detail: 'Summer' },
      { id: 3, name: 'Sunglasses', detail: 'Summer' },
    ],
  },
];

export default function WardrobeInsights() {
  const [activeCategoryIndex, setActiveCategoryIndex] = useState(0);
  const [isAuto, setIsAuto] = useState(true);

  const totalCategories = INSIGHTS_DATA.length;
  const currentCategory = INSIGHTS_DATA[activeCategoryIndex];

  // Auto-play feature (slides every 4 seconds)
  useEffect(() => {
    if (!isAuto) return;

    const interval = setInterval(() => {
      setActiveCategoryIndex((prev) => (prev + 1) % totalCategories);
    }, 4000);

    return () => clearInterval(interval);
  }, [isAuto, totalCategories]);

  const handleNext = () => {
    setIsAuto(false); // Pause auto-slide when user interacts manually
    setActiveCategoryIndex((prev) => (prev + 1) % totalCategories);
  };

  const handlePrev = () => {
    setIsAuto(false);
    setActiveCategoryIndex((prev) => (prev - 1 + totalCategories) % totalCategories);
  };

  const handleSelectCategory = (index) => {
    setIsAuto(false);
    setActiveCategoryIndex(index);
  };

  return (
    <div className="w-full border border-gray-300 bg-white text-gray-900 font-mono text-sm shadow-sm my-4">
      {/* SECTION HEADER & CONTROL BAR */}
      <div className="flex justify-between items-center px-4 py-2 border-b border-gray-200 bg-gray-50 text-xs">
        <span className="font-bold tracking-wider text-gray-500 uppercase">
          WARDROBE INSIGHTS
        </span>

        {/* CONTROLS */}
        <div className="flex items-center gap-2">
          {/* Category Quick Select Icons */}
          <div className="flex border border-gray-300 rounded overflow-hidden bg-white">
            {INSIGHTS_DATA.map((cat, idx) => (
              <button
                key={cat.id}
                onClick={() => handleSelectCategory(idx)}
                className={`px-2 py-1 text-xs transition-colors border-r border-gray-200 last:border-r-0 ${
                  activeCategoryIndex === idx
                    ? 'bg-black text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                title={cat.title}
              >
                {cat.icon}
              </button>
            ))}
          </div>

          {/* Left/Right Arrow Navigation */}
          <div className="flex border border-gray-300 rounded overflow-hidden bg-white">
            <button
              onClick={handlePrev}
              className="px-2 py-1 text-xs hover:bg-gray-100 border-r border-gray-200"
            >
              ←
            </button>
            <button
              onClick={handleNext}
              className="px-2 py-1 text-xs hover:bg-gray-100"
            >
              →
            </button>
          </div>

          {/* Slider Progress Bar */}
          <div className="flex items-center gap-1 ml-2">
            {INSIGHTS_DATA.map((_, idx) => (
              <span
                key={idx}
                className={`h-1 transition-all duration-300 rounded-full ${
                  activeCategoryIndex === idx ? 'w-4 bg-black' : 'w-2 bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* SLIDING CONTENT BODY */}
      <div className="p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative">
        {/* Left Side: Category Title */}
        <div className="flex items-start gap-3 min-w-[200px]">
          <span className="text-2xl mt-1">{currentCategory.icon}</span>
          <div>
            <h3 className="font-bold text-base text-gray-900">{currentCategory.title}</h3>
            <p className="text-xs text-gray-400 mt-1">
              {totalCategories} categories available
            </p>
          </div>
          <div className="hidden md:block h-12 w-[1px] bg-gray-200 ml-4" />
        </div>

        {/* Middle: 3 Ranked Items */}
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-6 w-full">
          {currentCategory.items.map((item) => (
            <div key={item.id} className="flex items-center gap-3">
              <span className="flex items-center justify-center border border-gray-400 w-6 h-6 text-xs font-bold">
                {item.id}
              </span>
              <div>
                <p className="font-bold text-gray-800 text-sm">{item.name}</p>
                <p className="text-xs text-gray-400">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Right Side: AUTO indicator */}
        <div className="flex items-center gap-1 text-[10px] text-gray-400 uppercase tracking-widest self-end md:self-center">
          <span className={`w-2 h-2 rounded-full ${isAuto ? 'bg-black' : 'bg-gray-300'}`} />
          {isAuto ? 'AUTO' : 'PAUSED'}
        </div>
      </div>
    </div>
  );
}