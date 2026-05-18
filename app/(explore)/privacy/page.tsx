import FadeUp from "../../components/FadeUp";

// ── Section primitives (light theme) ─────────────────────────────────────

const GREEN = "#2D5016";
const TEXT = "#1a1a2e";
const BODY = "#3d3a36";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: GREEN, marginBottom: 16 }}>
      {children}
    </p>
  );
}

function GreenDivider() {
  return <div style={{ width: 64, height: 2, background: GREEN, borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
}

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
    <p style={{ fontSize: 16, lineHeight: 1.75, color: BODY, marginTop: 16 }}>
      {children}
    </p>
  );
}

function SectionDivider() {
  return <div style={{ width: "100%", height: 1, background: TEXT, opacity: 0.08, margin: "48px 0" }} />;
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
          <Paragraph>
            Kallipolis aims to serve public institutions, and we think privacy
            is a right. We collect very little, we don't track you across
            the web, and we don't sell data. This page explains the specifics.
          </Paragraph>

          <SectionDivider />

          {/* Information We Collect */}
          <SectionHeading>Information We Collect</SectionHeading>

          <Paragraph>
            When you visit our site, we automatically collect technical information
            such as your IP address, the pages you visit, and timestamps. We do not
            require accounts or use cookies or third-party services to track
            your activity.
          </Paragraph>

          <SectionDivider />

          {/* How We Use This Information */}
          <SectionHeading>How We Use This Information</SectionHeading>

          <Paragraph>
            We use the information described above to operate, maintain, and improve
            our service. This includes monitoring performance, understanding how
            visitors navigate and interact with the site and its applications,
            identifying technical issues, and evaluating the effectiveness of our
            outreach. We do not serve advertising or sell this information.
          </Paragraph>

          <SectionDivider />

          {/* What We Do Not Collect */}
          <SectionHeading>What We Do Not Collect</SectionHeading>

          <Paragraph>
            We do not require user accounts or passwords. We do not use cookies for
            tracking or advertising purposes. We do not embed third-party analytics,
            social media widgets, or advertising scripts. We do not collect names,
            email addresses, or payment information through the site.
          </Paragraph>

          <SectionDivider />

          {/* Data Sharing */}
          <SectionHeading>Data Sharing</SectionHeading>

          <Paragraph>
            We do not sell, rent, or share personal information with third parties
            for their own purposes. Our infrastructure is hosted on Google Cloud
            Platform in the United States. We may disclose information if required
            by law or to protect the rights and safety of our service.
          </Paragraph>

          <SectionDivider />

          {/* Data Retention */}
          <SectionHeading>Data Retention</SectionHeading>

          <Paragraph>
            Server logs and analytics data are retained for operational purposes.
            We retain this data only as long as it is useful for the purposes
            described above.
          </Paragraph>

          <SectionDivider />

          {/* Changes */}
          <SectionHeading>Changes to This Policy</SectionHeading>

          <Paragraph>
            We may update this policy to reflect changes in our practices or for
            legal or operational reasons.
          </Paragraph>

          <SectionDivider />

          {/* Contact */}
          <SectionHeading>Contact</SectionHeading>

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

        </FadeUp>
      </section>

      {/* ── Footer border ── */}
      <div style={{ background: "#F5F2EB", paddingTop: 80 }}>
        <div style={{ maxWidth: 640, margin: "0 auto", height: 1, background: TEXT, opacity: 0.08 }} />
      </div>
    </div>
  );
}
