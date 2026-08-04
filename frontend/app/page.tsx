"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { SiteNav } from "@/components/layout/site-nav";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";
import { HeroParallax } from "@/components/landing/hero-parallax";
import { HowItWorks } from "@/components/landing/how-it-works";
import { FeatureCard } from "@/components/landing/feature-cards";
import { QuoteBand } from "@/components/landing/quote-band";

const FEATURES = [
  {
    title: "Instant visualization",
    copy: "See any outfit on your own body before you wear it.",
    rich: true,
  },
  { title: "AI stylist", copy: "Ask anything. Get outfits pulled from your own wardrobe." },
  { title: "One closet, sorted", copy: "Everything you own, organized automatically." },
];

const STATS = [
  { value: "12k+", label: "Looks styled" },
  { value: "4.9", label: "User rating" },
  { value: "2.4M", label: "Garments tagged" },
];

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden bg-cream dark:bg-[#161611]">
      <div
        aria-hidden
        className="motion-reduce:animate-none pointer-events-none absolute -right-40 -top-52 h-[600px] w-[600px] animate-drift-a rounded-full bg-forest/20 blur-3xl"
      />
      <SiteNav />

      <section className="relative mx-auto grid max-w-6xl gap-14 px-6 py-24 md:grid-cols-[1.05fr_1fr] md:px-12">
        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <span className="mb-6 inline-block rounded-full bg-forest/10 px-3.5 py-1.5 font-sans text-xs font-medium uppercase tracking-widest text-forest dark:bg-forest/20 dark:text-[#8fbfa4]">
            AI Wardrobe
          </span>
          <h1 className="font-heading text-[clamp(42px,5vw,68px)] font-semibold leading-[1.06] tracking-tight text-ink dark:text-cream">
            Dress with
            <br />
            <span className="italic text-forest dark:text-[#8fbfa4]">intelligence.</span>
          </h1>
          <p className="mt-6 max-w-[42ch] font-sans text-[17px] leading-relaxed text-ink/65 dark:text-cream/65">
            See yourself in every outfit. Ask your stylist. Wear only what you own.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-5">
            <Link href="/auth">
              <Button size="lg" className="active:scale-[0.97]">
                Get Started
              </Button>
            </Link>
            <Link
              href="#how"
              className="group relative border-b border-ink/30 pb-1 font-sans text-sm font-semibold text-ink transition-colors hover:border-forest dark:border-cream/30 dark:text-cream dark:hover:border-[#8fbfa4]"
            >
              <span className="relative">
                Explore demo →
                <span className="absolute -bottom-1 left-0 h-px w-0 bg-forest transition-all duration-300 group-hover:w-full dark:bg-[#8fbfa4]" />
              </span>
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
        >
          <HeroParallax />
        </motion.div>
      </section>

      {/* Social proof stat row */}
      <section className="border-y border-ink/6 dark:border-cream/6">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-12 gap-y-4 px-6 py-6 md:px-12">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="flex items-baseline gap-2"
            >
              <span className="font-heading text-2xl font-semibold text-forest dark:text-[#8fbfa4]">{stat.value}</span>
              <span className="font-sans text-xs uppercase tracking-widest text-ink/45 dark:text-cream/45">{stat.label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      <HowItWorks />

      <section id="features" className="mx-auto max-w-6xl px-6 pb-20 md:px-12">
        <div className="grid gap-7 md:grid-cols-3">
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.title} title={f.title} copy={f.copy} index={i} rich={f.rich} />
          ))}
        </div>
      </section>

      <QuoteBand />
      <Footer />
    </div>
  );
}
