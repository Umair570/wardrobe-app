// import StatsCarousel from '../components/StatsCarousel'

// const QUICK_ACCESS = [
//   {
//     title: 'My Wardrobe',
//     body: 'Browse and manage all your clothing items in one place.',
//     cta: 'Open Wardrobe',
//     page: 'wardrobe',
//   },
//   {
//     title: 'AI Stylist',
//     body: 'Chat with your AI stylist and get personalized outfit suggestions.',
//     cta: 'Ask Stylist',
//     page: 'stylist',
//   },
//   {
//     title: 'Upload Item',
//     body: 'Add a new clothing item and let AI detect and classify it automatically.',
//     cta: 'Upload Now',
//     page: 'upload',
//   },
// ]

// const HOW_IT_WORKS = [
//   { n: '01', title: 'Upload Photo', body: 'Take or upload a photo of your clothing item.' },
//   { n: '02', title: 'AI Detection', body: 'Our AI detects, classifies, and removes the background.' },
//   { n: '03', title: 'Build Wardrobe', body: 'Items are saved to your digital wardrobe automatically.' },
//   { n: '04', title: 'Get Outfits', body: 'Ask the AI stylist for outfit recommendations.' },
// ]

// export default function HomePage({ onNavigate, items }) {
//   return (
//     <div className="max-w-6xl mx-auto px-6 py-14">
//       <StatsCarousel items={items} />

//       <div className="grid md:grid-cols-2 gap-12 items-center pb-14 border-b border-ink/10">
//         <div>
//           <p className="eyebrow mb-3">AI-Powered Style Assistant</p>
//           <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-[1.05] mb-5">
//             Your Digital Wardrobe, Reinvented.
//           </h1>
//           <p className="text-soft max-w-md mb-7">
//             Upload your clothes, let AI detect and classify them, then get personalized
//             outfit recommendations from your virtual stylist.
//           </p>
//           <div className="flex items-center gap-3">
//             <button onClick={() => onNavigate('upload')} className="btn-primary">
//               Upload Clothing
//             </button>
//             <button onClick={() => onNavigate('wardrobe')} className="btn-outline">
//               View Wardrobe
//             </button>
//           </div>
//         </div>
//         <div className="placeholder-box aspect-square w-full max-w-sm md:ml-auto">
//           Hero Illustration
//           <br />
//           Placeholder
//         </div>
//       </div>

//       <div className="py-14 border-b border-ink/10">
//         <p className="eyebrow mb-6">Quick Access</p>
//         <div className="grid md:grid-cols-3 gap-5">
//           {QUICK_ACCESS.map((card) => (
//             <div key={card.title} className="panel p-5 flex flex-col">
//               <div className="placeholder-box h-24 mb-4">Icon</div>
//               <h3 className="font-semibold mb-1.5">{card.title}</h3>
//               <p className="text-sm text-soft mb-5 flex-1">{card.body}</p>
//               <button onClick={() => onNavigate(card.page)} className="btn-outline self-start">
//                 {card.cta}
//               </button>
//             </div>
//           ))}
//         </div>
//       </div>

//       <div className="py-14">
//         <p className="eyebrow mb-6">How AI Wardrobe Works</p>
//         <div className="grid md:grid-cols-4 gap-5">
//           {HOW_IT_WORKS.map((step) => (
//             <div key={step.n} className="panel p-5">
//               <p className="font-mono text-2xl text-faint mb-3">{step.n}</p>
//               <h3 className="font-semibold mb-1.5">{step.title}</h3>
//               <p className="text-sm text-soft">{step.body}</p>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   )
// }

import StatsCarousel from '../components/StatsCarousel';
import { Sparkles, Upload, Shirt, MessageSquare, ArrowRight, Layers } from 'lucide-react';

export default function HomePage({ onNavigate, items = [] }) {
  const totalItems = items.length;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-12">
      
      {/* --- HERO SECTION --- */}
      <section className="grid md:grid-cols-2 gap-10 items-center pt-4 pb-8">
        {/* Left Column */}
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-black/5 text-black border border-black/10">
            <Sparkles className="w-3.5 h-3.5 text-black" />
            <span>AI-Powered Personal Stylist</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-black tracking-tight leading-tight">
            Your Digital Wardrobe, Reinvented.
          </h1>

          <p className="text-black/80 text-base sm:text-lg leading-relaxed max-w-lg">
            Upload your clothes, let AI automatically classify them, and generate personalized outfit recommendations tailored to your style.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <button
              onClick={() => onNavigate('upload')}
              className="inline-flex items-center gap-2 bg-black hover:bg-black/80 text-white font-medium px-6 py-3 rounded-xl shadow-md transition-all"
            >
              <Upload className="w-4 h-4" />
              Upload Clothing
            </button>

            <button
              onClick={() => onNavigate('wardrobe')}
              className="inline-flex items-center gap-2 bg-white hover:bg-black/5 text-black border border-black/20 font-medium px-6 py-3 rounded-xl shadow-sm transition-all"
            >
              View Wardrobe
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Column: Hero Graphic Card */}
        <div className="relative">
          <div className="bg-white/90 backdrop-blur-xl border border-black/15 rounded-3xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-black/10 pb-3">
              <span className="text-xs font-bold text-black uppercase tracking-wider">Today's Outfit Match</span>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-black text-white">98% Match</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-black/5 rounded-2xl p-4 border border-black/10 flex flex-col items-center justify-center text-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center">
                  <Shirt className="w-5 h-5" />
                </div>
                <span className="text-xs font-bold text-black">Navy Cotton Tee</span>
                <span className="text-[10px] text-black/60 font-medium">Tops · Casual</span>
              </div>

              <div className="bg-black/5 rounded-2xl p-4 border border-black/10 flex flex-col items-center justify-center text-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center">
                  <Layers className="w-5 h-5" />
                </div>
                <span className="text-xs font-bold text-black">Dark Baggy Jeans</span>
                <span className="text-[10px] text-black/60 font-medium">Bottoms · Denim</span>
              </div>
            </div>

            <div className="p-3 bg-black/5 rounded-xl border border-black/10 flex items-center gap-3">
              <MessageSquare className="w-5 h-5 text-black shrink-0" />
              <p className="text-xs text-black font-semibold">
                "Perfect combination for a relaxed casual day!"
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* --- STATS CAROUSEL (RESTORED HERE) --- */}
      <section>
        <StatsCarousel items={items} />
      </section>

      {/* --- DASHBOARD STATS & QUICK ACCESS --- */}
      <section className="grid sm:grid-cols-3 gap-6">
        <div 
          onClick={() => onNavigate('wardrobe')}
          className="bg-white/90 border border-black/15 rounded-2xl p-6 shadow-sm hover:border-black/40 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center">
              <Shirt className="w-5 h-5" />
            </div>
            <span className="text-2xl font-black text-black">{totalItems}</span>
          </div>
          <h3 className="text-base font-bold text-black group-hover:underline">My Wardrobe</h3>
          <p className="text-xs text-black/70 mt-1">Browse and manage all clothing items in one place.</p>
        </div>

        <div 
          onClick={() => onNavigate('stylist')}
          className="bg-white/90 border border-black/15 rounded-2xl p-6 shadow-sm hover:border-black/40 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center">
              <MessageSquare className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold px-2.5 py-1 bg-black text-white rounded-md">Active</span>
          </div>
          <h3 className="text-base font-bold text-black group-hover:underline">AI Stylist</h3>
          <p className="text-xs text-black/70 mt-1">Chat with your AI assistant for personalized outfits.</p>
        </div>

        <div 
          onClick={() => onNavigate('upload')}
          className="bg-white/90 border border-black/15 rounded-2xl p-6 shadow-sm hover:border-black/40 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-black text-white flex items-center justify-center">
              <Upload className="w-5 h-5" />
            </div>
            <span className="text-xs font-bold text-black">+ New</span>
          </div>
          <h3 className="text-base font-bold text-black group-hover:underline">Upload Item</h3>
          <p className="text-xs text-black/70 mt-1">Add new items with automatic background removal.</p>
        </div>
      </section>

      {/* --- HOW IT WORKS WORKFLOW --- */}
      <section className="bg-white/90 border border-black/15 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-black/10 pb-4">
          <h2 className="text-xl font-bold text-black">How AI Wardrobe Works</h2>
          <p className="text-xs font-medium text-black/60 mt-0.5">Automated detection and style recommendation engine</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="space-y-2">
            <span className="text-2xl font-black text-black">01</span>
            <h4 className="text-sm font-bold text-black">Upload Photo</h4>
            <p className="text-xs text-black/70">Take or upload a photo of your clothing item.</p>
          </div>

          <div className="space-y-2">
            <span className="text-2xl font-black text-black">02</span>
            <h4 className="text-sm font-bold text-black">AI Detection</h4>
            <p className="text-xs text-black/70">Our AI detects, classifies, and removes the background.</p>
          </div>

          <div className="space-y-2">
            <span className="text-2xl font-black text-black">03</span>
            <h4 className="text-sm font-bold text-black">Build Wardrobe</h4>
            <p className="text-xs text-black/70">Items are saved to your digital wardrobe automatically.</p>
          </div>

          <div className="space-y-2">
            <span className="text-2xl font-black text-black">04</span>
            <h4 className="text-sm font-bold text-black">Get Outfits</h4>
            <p className="text-xs text-black/70">Ask the AI stylist for tailored outfit recommendations.</p>
          </div>
        </div>
      </section>

    </div>
  );
}