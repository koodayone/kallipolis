"use client";

import { useState } from "react";
import FadeUp from "../../components/FadeUp";

// ── Section primitives (light theme) ─────────────────────────────────────

const GREEN = "#2D5016";
const TEXT = "#1a1a2e";
const BODY = "#3d3a36";

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2
      className="text-[20px] md:text-[26px] leading-[1.2] tracking-[-0.01em]"
      style={{ fontFamily: "var(--font-days-one)", fontWeight: 400, color: GREEN, marginBottom: 20 }}
    >
      {children}
    </h2>
  );
}

function Paragraph({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 16, lineHeight: 1.75, color: BODY, marginTop: 0 }}>
      {children}
    </p>
  );
}

function Accordion({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        borderTop: `1px solid ${TEXT}11`,
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "24px 0",
          background: "none",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <span
          className="text-[17px] md:text-[20px] leading-[1.2] tracking-[-0.01em]"
          style={{
            fontFamily: "var(--font-days-one)",
            fontWeight: 400,
            color: GREEN,
          }}
        >
          {title}
        </span>
        <span
          style={{
            fontSize: 20,
            color: GREEN,
            opacity: 0.6,
            transition: "transform 300ms ease",
            transform: open ? "rotate(45deg)" : "rotate(0deg)",
            flexShrink: 0,
            marginLeft: 16,
          }}
        >
          +
        </span>
      </button>
      <div
        style={{
          display: "grid",
          gridTemplateRows: open ? "1fr" : "0fr",
          transition: "grid-template-rows 300ms ease",
        }}
      >
        <div style={{ overflow: "hidden" }}>
          <div style={{ paddingBottom: 24 }}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────

export default function PrivacyPage() {
  return (
    <div className="md:min-h-screen max-md:min-h-[100dvh]" style={{ background: "#F5F2EB" }}>

      {/* ── Header ── */}
      <section className="md:pt-[120px] md:px-16 max-md:pt-16 max-md:px-6">
        <FadeUp style={{ maxWidth: 640, margin: "0 auto" }}>
          <SectionHeading>
            Kallipolis Privacy Statement
          </SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.75, color: BODY, marginTop: 16, marginBottom: 48 }}>
            Kallipolis aims to serve public institutions, and we think privacy
            is a right. We collect minimal information, we don&apos;t track you across
            the web, and we don&apos;t sell data. This page explains the specifics.
          </p>

          {/* ── Accordion sections ── */}

          <Accordion title="Information We Collect">
            <Paragraph>
              When you visit our site, we automatically collect technical information
              such as your IP address, the pages you visit, and timestamps. We do not
              require accounts or use cookies or third-party services to track
              your activity.
            </Paragraph>
          </Accordion>

          <Accordion title="How We Use This Information">
            <Paragraph>
              We use the information described above to operate, maintain, and improve
              our service. This includes monitoring performance, understanding how
              visitors navigate and interact with the site and its applications,
              identifying technical issues, and evaluating the effectiveness of our
              outreach. We do not serve advertising or sell this information.
            </Paragraph>
          </Accordion>

          <Accordion title="What We Do Not Collect">
            <Paragraph>
              We do not require user accounts or passwords. We do not use cookies for
              tracking or advertising purposes. We do not embed third-party analytics,
              social media widgets, or advertising scripts. We do not collect names,
              email addresses, or payment information through the site.
            </Paragraph>
          </Accordion>

          <Accordion title="Data Sharing">
            <Paragraph>
              We do not sell, rent, or share personal information with third parties
              for their own purposes. Our infrastructure is hosted on Google Cloud
              Platform in the United States. We may disclose information if required
              by law or to protect the rights and safety of our service.
            </Paragraph>
          </Accordion>

          <Accordion title="Data Retention">
            <Paragraph>
              Server logs and analytics data are retained for operational purposes.
              We retain this data only as long as it is useful for the purposes
              described above.
            </Paragraph>
          </Accordion>

          <Accordion title="Changes to This Policy">
            <Paragraph>
              We may update this policy to reflect changes in our practices or for
              legal or operational reasons.
            </Paragraph>
          </Accordion>

          <Accordion title="Contact">
            <Paragraph>
              If you have questions about this policy or our data practices, contact
              us at{" "}
              <a
                href="mailto:dayonekoo@kallipolis.us"
                style={{ color: GREEN, textDecoration: "underline", textUnderlineOffset: 3 }}
              >
                dayonekoo@kallipolis.us
              </a>.
            </Paragraph>
          </Accordion>

          {/* Bottom border to close the last accordion */}
          <div style={{ borderTop: `1px solid ${TEXT}11` }} />

        </FadeUp>
      </section>

      {/* ── Footer border ── */}
      <div style={{ background: "#F5F2EB", paddingTop: 80 }}>
        <div style={{ maxWidth: 640, margin: "0 auto", height: 1, background: TEXT, opacity: 0.08 }} />
      </div>
    </div>
  );
}
