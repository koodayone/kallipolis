"use client";

import { useEffect, useRef } from "react";

export default function PageFadeIn({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Start invisible, fade in
    el.style.opacity = "0";
    requestAnimationFrame(() => {
      el.style.transition = "opacity 0.5s ease";
      el.style.opacity = "1";
    });
  }, []);

  return <div ref={ref}>{children}</div>;
}
