"use client";

import { useRef, useState, useCallback } from "react";

type Card = { accent: string; source: string; headline: string; url: string };

const cards: Card[] = [
  {
    accent: "#4A7C59",
    source: "World Economic Forum",
    headline: "92 million jobs displaced, 170 million created by 2030 — the transition window is now",
    url: "https://www.weforum.org/publications/the-future-of-jobs-report-2025/",
  },
  {
    accent: "#8C1515",
    source: "Stanford Digital Economy Lab",
    headline: "Early-career workers in AI-exposed roles have seen a 16% relative employment decline since generative AI adoption",
    url: "https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/",
  },
  {
    accent: "#B85C2A",
    source: "Anthropic",
    headline: "AI could eliminate 50% of entry-level white-collar jobs within five years — the CEO of Anthropic is sounding the alarm",
    url: "https://www.axios.com/2025/05/28/ai-jobs-white-collar-unemployment-anthropic",
  },
  {
    accent: "#6B7280",
    source: "Brookings Institution",
    headline: "6.1 million workers face high AI exposure with the lowest capacity to adapt",
    url: "https://www.brookings.edu/articles/measuring-us-workers-capacity-to-adapt-to-ai-driven-job-displacement/",
  },
  {
    accent: "#002366",
    source: "McKinsey Global Institute",
    headline: "Workers in the lowest wage jobs are up to 14 times more likely to need to change occupations by 2030 — and they are disproportionately women and people of color",
    url: "https://www.mckinsey.com/mgi/our-research/generative-ai-and-the-future-of-work-in-america",
  },
];

function highlightNumbers(text: string, accent: string) {
  const parts = text.split(/(\d+\.?\d*\s*(?:million|billion|times|%|M|B|K|pts?))/gi);
  return parts.map((part, i) =>
    /^\d/i.test(part)
      ? <span key={i} style={{ color: "#111827", fontWeight: 700 }}>{part}</span>
      : part
  );
}

export default function Problem() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const NUM_DOTS = 3; // pages = cards.length - visibleCards + 1 = 5 - 3 + 1

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const maxScroll = el.scrollWidth - el.clientWidth;
    if (maxScroll === 0) return;
    setActiveIndex(Math.round((el.scrollLeft / maxScroll) * (NUM_DOTS - 1)));
  }, []);

  const scrollToCard = (index: number) => {
    const el = scrollRef.current;
    if (!el) return;
    const maxScroll = el.scrollWidth - el.clientWidth;
    el.scrollTo({ left: (maxScroll * index) / (NUM_DOTS - 1), behavior: "smooth" });
  };

  return (
    <section className="bg-coastal-fog py-24 px-6">
      <style>{`
        .evidence-scroll::-webkit-scrollbar { height: 0; }
        .evidence-scroll::-webkit-scrollbar-track { background: transparent; }
        .evidence-scroll::-webkit-scrollbar-thumb { background: #6B7280; border-radius: 2px; }
        .evidence-card:hover { border-color: var(--card-accent) !important; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
        .evidence-card .link-icon { color: #D1D5DB; transition: color 0.2s; }
        .evidence-card:hover .link-icon { color: #6B7280; }
      `}</style>

      {/* Statement block */}
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-pacific-navy mb-4">
          The Moment
        </p>
        {/* Green divider rule */}
        <div style={{ width: 64, height: 2, background: "#4A7C59", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />

        <p className="text-[36px] md:text-[48px] font-bold leading-[1.12] tracking-[-0.02em] text-pure-text max-w-[700px] mx-auto">
          AI is disrupting the workforce. Institutions need to respond.
        </p>
      </div>

      {/* Evidence cards */}
      <div className="mt-16 max-w-7xl mx-auto" style={{ paddingLeft: 48, paddingRight: 48 }}>
        <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.15em", color: "#6B7280", marginBottom: 16 }}>
          The evidence
        </p>
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="evidence-scroll"
          style={{
            display: "flex",
            gap: 24,
            overflowX: "auto",
            scrollSnapType: "x mandatory",
            scrollbarWidth: "none",
            paddingTop: 6,
            paddingBottom: 16,
          }}
        >
          {cards.map((card) => (
            <a
              key={card.source}
              href={card.url}
              target="_blank"
              rel="noopener noreferrer"
              className="evidence-card"
              style={{
                flex: "0 0 calc(33.333% - 16px)",
                minWidth: 220,
                scrollSnapAlign: "start",
                background: "white",
                borderRadius: 10,
                border: "1px solid rgba(0,0,0,0.06)",
                padding: 28,
                display: "flex",
                flexDirection: "column",
                gap: 16,
                textDecoration: "none",
                cursor: "pointer",
                transition: "border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease",
                "--card-accent": card.accent,
              } as React.CSSProperties}
            >
              {/* Header row: accent bar + link icon */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ width: 32, height: 3, borderRadius: 2, background: card.accent }} />
                <span className="link-icon" style={{ fontSize: 14 }}>↗</span>
              </div>

              {/* Source */}
              <p style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6B7280", margin: 0 }}>
                {card.source}
              </p>

              {/* Headline with highlighted numbers */}
              <p style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.55, color: "#111827", margin: 0 }}>
                {highlightNumbers(card.headline, card.accent)}
              </p>
            </a>
          ))}
        </div>

        {/* Dot indicators */}
        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 20 }}>
          {Array.from({ length: NUM_DOTS }).map((_, i) => (
            <button
              key={i}
              onClick={() => scrollToCard(i)}
              aria-label={`Go to card ${i + 1}`}
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                border: "none",
                cursor: "pointer",
                padding: 0,
                background: i === activeIndex ? "#374151" : "#D1D5DB",
                transition: "background 0.2s",
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
