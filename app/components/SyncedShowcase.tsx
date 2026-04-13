"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ROTATION_COLLEGES, CYCLE_INTERVAL, FADE_DURATION } from "../lib/collegeRotation";
import AtlasPreview from "./AtlasPreview";
import ActionBadge from "./ActionBadge";
import StateAtlas from "./StateAtlas";
import EpistemologySection from "./EpistemologySection";

export default function SyncedShowcase() {
  const [collegeIndex, setCollegeIndex] = useState(0);
  const [displayIndex, setDisplayIndex] = useState(0);
  const initialized = useRef(false);
  const [opacity, setOpacity] = useState(1);
  const cycleRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      const rand = Math.floor(Math.random() * ROTATION_COLLEGES.length);
      setCollegeIndex(rand);
      setDisplayIndex(rand);
    }
  }, []);

  const startCycle = useCallback(() => {
    if (cycleRef.current) clearInterval(cycleRef.current);
    cycleRef.current = setInterval(() => {
      setOpacity(0);
      setTimeout(() => {
        setCollegeIndex((prev) => (prev + 1) % ROTATION_COLLEGES.length);
      }, FADE_DURATION);
    }, CYCLE_INTERVAL);
  }, []);

  useEffect(() => {
    startCycle();
    return () => { if (cycleRef.current) clearInterval(cycleRef.current); };
  }, [startCycle]);

  useEffect(() => {
    setDisplayIndex(collegeIndex);
    requestAnimationFrame(() => setOpacity(1));
  }, [collegeIndex]);

  return (
    <>
      <AtlasPreview activeIndex={displayIndex} opacity={opacity} />
      <StateAtlas activeIndex={displayIndex} opacity={opacity} />
      <ActionBadge label="Explore Atlas" neonColor={ROTATION_COLLEGES[displayIndex].neonHex} opacity={opacity} href="/atlas" />
      <EpistemologySection />
    </>
  );
}
