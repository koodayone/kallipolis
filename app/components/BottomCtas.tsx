"use client";

import { motion } from "framer-motion";
import ActionBadge from "./ActionBadge";

export default function BottomCtas() {
  return (
    <motion.div
      className="flex justify-center md:pt-12 md:pb-2 md:gap-4 max-md:pt-8 max-md:pb-2 max-md:gap-3 max-md:flex-wrap max-md:px-4"
      style={{ background: "#060d1f" }}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <ActionBadge label="Reach Out" neonColor="#f5e6c8" opacity={1} icon="mail" inline href="mailto:dayonekoo@kallipolis.us" />
      <ActionBadge label="Mission" neonColor="#f5e6c8" opacity={1} icon="tree" inline href="/mission" />
    </motion.div>
  );
}
