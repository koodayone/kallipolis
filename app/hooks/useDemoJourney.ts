"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export type DemoPhase =
  | "idle"
  | "typing"
  | "loading"
  | "rows"
  | "highlighting"
  | "expanding"
  | "detail"
  | "hold";

const PHASE_ORDER: DemoPhase[] = [
  "idle", "typing", "loading", "rows", "highlighting", "expanding", "detail", "hold",
];

export type DemoJourneyConfig = {
  query: string;
  detailSteps?: number;
  timings?: Partial<{
    idlePause: number;
    typeSpeed: number;
    postTypePause: number;
    loadingDuration: number;
    rowsPause: number;
    highlightSettle: number;
    stepDuration: number;
    finalHold: number;
    fadeDuration: number;
  }>;
};

const DEFAULTS = {
  idlePause: 1000,
  typeSpeed: 42,
  postTypePause: 600,
  loadingDuration: 700,
  rowsPause: 1500,
  highlightSettle: 300,
  stepDuration: 3500,
  finalHold: 0,
  fadeDuration: 400,
};

export type DemoJourneyState = {
  phase: DemoPhase;
  typedText: string;
  isRowExpanded: boolean;
  highlightedRow: boolean;
  dimOtherRows: boolean;
  showRows: boolean;
  detailStep: number;
  containerRef: React.RefObject<HTMLDivElement | null>;
};

/** Returns true if `current` is at or past `target` in the phase sequence. */
export function phaseAtLeast(current: DemoPhase, target: DemoPhase): boolean {
  return PHASE_ORDER.indexOf(current) >= PHASE_ORDER.indexOf(target);
}

export function useDemoJourney(config: DemoJourneyConfig): DemoJourneyState {
  const tRef = useRef({ ...DEFAULTS, ...config.timings });
  const queryRef = useRef(config.query);
  const stepsRef = useRef(config.detailSteps ?? 1);

  const [phase, setPhase] = useState<DemoPhase>("idle");
  const [typedText, setTypedText] = useState("");
  const [detailStep, setDetailStep] = useState(0);
  const [visible, setVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !visible) setVisible(true); },
      { threshold: 0.2 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible]);

  const clearTimers = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  const runCycle = useCallback(() => {
    const t = tRef.current;
    const query = queryRef.current;
    const totalSteps = stepsRef.current;

    setTypedText("");
    setPhase("idle");
    setDetailStep(0);

    timerRef.current = setTimeout(() => {
      setPhase("typing");

      let i = 0;
      intervalRef.current = setInterval(() => {
        i++;
        setTypedText(query.slice(0, i));
        if (i >= query.length) {
          if (intervalRef.current) clearInterval(intervalRef.current);

          timerRef.current = setTimeout(() => {
            setPhase("loading");

            timerRef.current = setTimeout(() => {
              setPhase("rows");

              timerRef.current = setTimeout(() => {
                setPhase("highlighting");

                timerRef.current = setTimeout(() => {
                  setPhase("expanding");

                  timerRef.current = setTimeout(() => {
                    setPhase("detail");
                    setDetailStep(1);

                    // Step through detail sub-phases — no loop, rest forever
                    let step = 1;
                    function advanceStep() {
                      step++;
                      if (step <= totalSteps) {
                        setDetailStep(step);
                        timerRef.current = setTimeout(advanceStep, t.stepDuration);
                      } else {
                        // All steps shown — arrive at rest and stay there
                        timerRef.current = setTimeout(() => {
                          setDetailStep(totalSteps + 1);
                        }, t.stepDuration);
                      }
                    }

                    if (totalSteps > 1) {
                      timerRef.current = setTimeout(advanceStep, t.stepDuration);
                    } else {
                      // Single step — fade to rest after stepDuration
                      timerRef.current = setTimeout(() => {
                        setDetailStep(totalSteps + 1);
                      }, t.stepDuration);
                    }

                  }, 300);
                }, t.highlightSettle);
              }, t.rowsPause);
            }, t.loadingDuration);
          }, t.postTypePause);
        }
      }, t.typeSpeed);
    }, t.idlePause);
  }, []);

  useEffect(() => {
    if (!visible) return;
    runCycle();
    return clearTimers;
  }, [visible, runCycle, clearTimers]);

  return {
    phase,
    typedText,
    isRowExpanded: phaseAtLeast(phase, "expanding") && phase !== "hold",
    highlightedRow: phase === "highlighting" || phase === "expanding",
    dimOtherRows: phaseAtLeast(phase, "highlighting"),
    showRows: phaseAtLeast(phase, "rows") && phase !== "hold",
    detailStep,
    containerRef,
  };
}
