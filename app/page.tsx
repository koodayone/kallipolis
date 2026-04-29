import Nav from "./components/Nav";
import Vision from "./components/Vision";
import SyncedShowcase from "./components/SyncedShowcase";
import ActionBadge from "./components/ActionBadge";
import PartnershipsSection from "./components/PartnershipsSection";
import EpistemologySection from "./components/EpistemologySection";
import Promise from "./components/Promise";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <main>
      <Nav />
      <Vision />
      <SyncedShowcase />
      <div id="partnerships"><PartnershipsSection /></div>
      <div id="methodology"><EpistemologySection /></div>
      <Promise />
      <div className="flex justify-center md:pt-12 md:pb-2 md:gap-4 max-md:pt-8 max-md:pb-2 max-md:gap-3 max-md:flex-wrap max-md:px-4" style={{ background: "#060d1f" }}>
        <ActionBadge label="Reach Out" neonColor="#f5e6c8" opacity={1} icon="mail" inline href="mailto:dayonekoo@kallipolis.us" />
        <ActionBadge label="Mission" neonColor="#f5e6c8" opacity={1} icon="tree" inline href="/mission" />
        <ActionBadge label="Get Started" neonColor="#f5e6c8" opacity={1} icon="play" inline />
      </div>
      <Footer />
    </main>
  );
}
