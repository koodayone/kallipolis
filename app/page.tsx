import Nav from "@/components/Nav";
import Vision from "@/components/Vision";
import Problem from "@/components/Problem";
import InstitutionalView from "@/components/InstitutionalView";
import StateView from "@/components/StateView";
import Transformation from "@/components/Transformation";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main>
      <Nav />
      <Vision />
      <Problem />
      <InstitutionalView />
      <StateView />
      <Transformation />
      <Footer />
    </main>
  );
}
