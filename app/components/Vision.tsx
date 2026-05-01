"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import ActionBadge from "./ActionBadge";

export default function Vision() {
  // Hero parallax: as the user scrolls past the hero, the background image
  // translates down at ~0.85x scroll speed, creating depth and a deliberate
  // handoff into the next section. Subtle enough to feel like motion polish
  // rather than scroll-jacking.
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 800], [0, 120]);

  return (
    <section className="relative overflow-hidden px-6 pb-16 md:min-h-[760px] max-md:min-h-[600px] flex items-center">

      {/* 1. Background image — wrapped in a motion.div for parallax (the
          y transform stays on the wrapper so the img's own ken-burns
          CSS transform doesn't fight with Framer's). */}
      <motion.div
        aria-hidden="true"
        style={{ position: "absolute", inset: 0, zIndex: 0, y: heroY }}
      >
        <img
          src="/hero-illustration.jpg"
          alt=""
          aria-hidden="true"
          className="ken-burns"
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 75%" }}
        />
      </motion.div>

      {/* 2. Dark overlay */}
      <div aria-hidden="true" style={{ position: "absolute", inset: 0, background: "rgba(0,10,30,0.25)", zIndex: 1 }} />

      {/* 3. Gradient overlay */}
      <div aria-hidden="true" style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(0,18,64,0.65) 0%, rgba(0,35,102,0.5) 30%, rgba(10,74,143,0.25) 60%, rgba(26,111,173,0.08) 85%, transparent 100%)", zIndex: 2 }} />


      {/* 4. Content — vertically centered in the section via flex on the
          parent. The simplified composition (headline + CTA, no eyebrow
          or divider) self-balances inside this layout instead of being
          pushed down by hardcoded top padding. */}
      <div className="relative w-full" style={{ zIndex: 3 }}>
        <div className="max-w-3xl mx-auto text-center">
          {/* Headline + CTA entrance — the page composes itself as the
              visitor arrives, signalling "alive" on first paint without
              requiring any interaction. Headline leads, CTA follows with
              a short delay so the rhythm feels considered rather than
              both elements arriving at once. Slow durations (700–800ms)
              and ease-out keep it institutional, not bouncy. */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="text-[40px] md:text-[56px] leading-[1.08] tracking-[-0.03em] text-white mb-6"
            style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}
          >
            California&apos;s<br />intelligence layer for<br />workforce development
          </motion.h1>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4, ease: "easeOut" }}
            className="max-md:hidden"
            style={{ marginTop: 32 }}
          >
            <ActionBadge label="Preview" neonColor="#f5e6c8" opacity={1} icon="play" inline prominent ambient="glow" href="https://preview.kallipolis.us" newTab />
          </motion.div>
        </div>
      </div>

      {/* Radial gold glow — static accent at the bottom of the hero,
          ties to the brand gold without competing for the eye. */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)",
          width: 600, height: 260, pointerEvents: "none",
          background: "radial-gradient(ellipse at 50% 100%, rgba(255,204,51,0.13) 0%, rgba(255,204,51,0.04) 45%, transparent 70%)",
        }}
      />
    </section>
  );
}
