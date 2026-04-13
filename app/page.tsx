import Nav from "./components/Nav";
import Vision from "./components/Vision";
import SyncedShowcase from "./components/SyncedShowcase";
import ActionBadge from "./components/ActionBadge";
import PartnershipsSection from "./components/PartnershipsSection";
import Promise from "./components/Promise";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <main>
      <Nav />
      <Vision />
      <SyncedShowcase />
      <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" href="/sources" />
      <PartnershipsSection />
      <ActionBadge label="Explore Partnerships" neonColor="#b0a0ff" opacity={1} icon="chainlink" href="/partnerships" />
      <Promise />
      <div style={{ background: "#060d1f", paddingTop: 48, paddingBottom: 8, display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Reach Out" neonColor="#f5e6c8" opacity={1} icon="mail" inline />
        <ActionBadge label="Get Started" neonColor="#f5e6c8" opacity={1} icon="play" inline />
      </div>
      <Footer />
    </main>
  );
}
