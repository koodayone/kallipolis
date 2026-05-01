"use client";

import { motion } from "framer-motion";
import type { CSSProperties, ReactNode } from "react";

/** FadeUp — the standard scroll-triggered entrance pattern used across
 *  the marketing site. Wraps any block of children with a 20px translate
 *  + fade-in animation that fires once when the block enters the viewport.
 *
 *  Centralized so the cadence (duration, distance, easing, threshold) is
 *  consistent across the home page and all explore subpages. Tune all
 *  pages at once by editing this file.
 *
 *  `delay` allows light staggering within a section without each call
 *  site repeating the full motion config:
 *    <FadeUp>{header}</FadeUp>
 *    <FadeUp delay={0.1}>{firstCard}</FadeUp>
 *    <FadeUp delay={0.2}>{secondCard}</FadeUp>
 */
type Props = {
  children: ReactNode;
  delay?: number;
  className?: string;
  style?: CSSProperties;
};

export default function FadeUp({ children, delay = 0, className, style }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
      className={className}
      style={style}
    >
      {children}
    </motion.div>
  );
}
