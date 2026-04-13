import Nav from "./components/Nav";
import Vision from "./components/Vision";
import SyncedShowcase from "./components/SyncedShowcase";
import ExploreOntology from "./components/ExploreOntology";
import Promise from "./components/Promise";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <main>
      <Nav />
      <Vision />
      <SyncedShowcase />
      <ExploreOntology label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" />
      <Promise />
      <Footer />
    </main>
  );
}
