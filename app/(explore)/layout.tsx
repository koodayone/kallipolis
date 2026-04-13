import Nav from "../components/Nav";
import Footer from "../components/Footer";
import PageFadeIn from "../components/PageFadeIn";

export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Nav />
      <PageFadeIn>
        <div style={{ background: "#060d1f", minHeight: "100vh" }}>
          {children}
        </div>
      </PageFadeIn>
      <Footer />
    </>
  );
}
