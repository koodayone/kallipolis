import Nav from "./components/Nav";
import Vision from "./components/Vision";
import SyncedShowcase from "./components/SyncedShowcase";
import PartnershipsSection from "./components/PartnershipsSection";
import EpistemologySection from "./components/EpistemologySection";
import Promise from "./components/Promise";
import BottomCtas from "./components/BottomCtas";
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
      <BottomCtas />
      <Footer />
    </main>
  );
}
