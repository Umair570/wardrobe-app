import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "motion/react";
import { ArrowUpRight, Scan, Sparkles, Layers } from "lucide-react";
import heroModel from "@/assets/hero-model.jpg";
import flatlay from "@/assets/wardrobe-flatlay.jpg";
import topKnit from "@/assets/items/top-cream-knit.png";
import bottomTrousers from "@/assets/items/bottom-black-trousers.png";
import shoesLoafers from "@/assets/items/shoes-black-loafers.png";
import outerCoat from "@/assets/items/outer-green-coat.png";
import { Button } from "@/components/ui/LuxButton";
import { Eyebrow, Surface } from "@/components/ui/Surface";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Atelier — Your Wardrobe, Digitized and Styled by AI" },
      {
        name: "description",
        content:
          "Photograph your clothes, build outfits on a visual studio canvas, and ask an AI stylist what to wear today.",
      },
      { property: "og:title", content: "Atelier — Your Wardrobe, Styled by AI" },
      {
        property: "og:description",
        content: "A digital closet with an AI stylist and a visual outfit studio.",
      },
    ],
  }),
  component: Landing,
});

const marqueeWords = ["Digital Closet", "Vector Search", "AI Stylist", "Virtual Try-On", "Cutout Engine"];

const steps = [
  { icon: Scan, title: "Shoot it", body: "Snap any garment. We cut the background out and store a clean, floating PNG." },
  { icon: Layers, title: "Stack it", body: "Assemble looks on a canvas where every piece layers like the real thing." },
  { icon: Sparkles, title: "Ask it", body: "Tell the stylist your plans. It searches your closet and returns a full outfit." },
];

function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-7">
        <span className="text-xl uppercase display-xl">Atelier</span>
        <div className="flex items-center gap-2">
          <Link to="/auth">
            <Button variant="ghost" size="sm">
              Sign in
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="ink" size="sm">
              Register
            </Button>
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-6 pb-20 pt-8 lg:grid-cols-[1.05fr_0.95fr] lg:pt-16">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <Eyebrow>
            <span className="h-1.5 w-1.5 rounded-full bg-forest" /> AI Wardrobe & Stylist
          </Eyebrow>
          <h1 className="mt-6 text-6xl uppercase sm:text-7xl xl:text-8xl display-xl">
            Your closet,
            <br />
            <span className="text-forest">rendered</span>
            <br />
            in full.
          </h1>
          <p className="mt-7 max-w-md text-base leading-relaxed text-muted-foreground">
            Every garment you own — cut out, catalogued and searchable. Build outfits visually,
            or let the stylist read your calendar mood and dress you in seconds.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/dashboard">
              <Button size="lg">
                Enter the atelier <ArrowUpRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/auth">
              <Button variant="outline" size="lg">
                Sign in
              </Button>
            </Link>
          </div>
          <dl className="mt-12 flex gap-10">
            {[
              ["SAM-2", "Cutout engine"],
              ["CLIP", "Semantic search"],
              ["Groq", "Stylist brain"],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="text-2xl uppercase display-xl">{k}</dt>
                <dd className="mt-1 text-[0.6rem] font-bold uppercase tracking-[0.2em] text-muted-foreground">
                  {v}
                </dd>
              </div>
            ))}
          </dl>
        </motion.div>

        <motion.div
          className="relative"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="overflow-hidden rounded-[2rem] shadow-luxe">
            <img
              src={heroModel}
              alt="Model wearing a forest green tailored overcoat"
              width={1024}
              height={1280}
              className="h-[560px] w-full object-cover"
            />
          </div>
          <Surface className="absolute -bottom-6 -left-4 w-52 p-4 sm:-left-10">
            <Eyebrow>Today's look</Eyebrow>
            <div className="mt-3 flex items-end gap-1">
              {[topKnit, bottomTrousers, shoesLoafers].map((src, i) => (
                <img
                  key={i}
                  src={src}
                  alt=""
                  width={768}
                  height={768}
                  loading="lazy"
                  className="h-14 w-14 object-contain animate-float-slow"
                  style={{ animationDelay: `${i * 0.6}s` }}
                />
              ))}
            </div>
          </Surface>
          <div className="absolute -right-3 top-8 rounded-full bg-ink px-4 py-2 text-[0.6rem] font-bold uppercase tracking-[0.22em] text-gold">
            Cutout ready
          </div>
        </motion.div>
      </section>

      <div className="border-y border-border bg-ink py-4">
        <div className="flex w-max animate-marquee gap-10 pr-10">
          {[...marqueeWords, ...marqueeWords, ...marqueeWords, ...marqueeWords].map((w, i) => (
            <span
              key={i}
              className="text-sm font-bold uppercase tracking-[0.3em] text-beige/50"
            >
              {w} <span className="text-gold">✦</span>
            </span>
          ))}
        </div>
      </div>

      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
          <div>
            <Eyebrow>The concept</Eyebrow>
            <h2 className="mt-5 text-4xl uppercase sm:text-5xl display-xl">
              A wardrobe that lives in vectors
            </h2>
            <p className="mt-6 max-w-md leading-relaxed text-muted-foreground">
              Each piece is embedded, tagged and indexed the moment you upload it — so "something
              warm but not heavy, in earth tones" is a real query, not a wish.
            </p>
          </div>
          <motion.img
            src={flatlay}
            alt="Flat lay of folded premium clothing in beige, cream, black and green"
            width={1024}
            height={768}
            loading="lazy"
            className="rounded-[2rem] shadow-soft"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.7 }}
          />
        </div>

        <div className="mt-20 grid gap-5 md:grid-cols-3">
          {steps.map(({ icon: Icon, title, body }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
            >
              <Surface className="h-full p-8 transition-transform duration-500 hover:-translate-y-1.5">
                <Icon className="h-6 w-6 text-forest" />
                <h3 className="mt-6 text-2xl uppercase">{title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{body}</p>
              </Surface>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-24">
        <div className="gradient-hero relative overflow-hidden rounded-[2.5rem] px-8 py-20 text-center shadow-luxe">
          <img
            src={outerCoat}
            alt=""
            width={768}
            height={768}
            loading="lazy"
            className="pointer-events-none absolute -left-10 top-6 h-64 w-64 object-contain opacity-30 animate-float-slow"
          />
          <h2 className="relative text-4xl uppercase text-beige sm:text-6xl display-xl">
            Get dressed
            <br />
            in one sentence
          </h2>
          <p className="relative mx-auto mt-6 max-w-sm text-sm leading-relaxed text-beige/70">
            "Dinner, outdoors, slightly cold." The stylist handles the rest.
          </p>
          <div className="relative mt-9 flex justify-center">
            <Link to="/auth">
              <Button variant="glow" size="lg">
                Create your account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border px-6 py-10 text-center text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground">
        Atelier — AI Wardrobe & Stylist
      </footer>
    </div>
  );
}
