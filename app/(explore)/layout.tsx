import Nav from "../components/Nav";
import Footer from "../components/Footer";

export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Nav />
      <div style={{ background: "#060d1f", minHeight: "100vh" }}>
        {children}
      </div>
      <Footer />
    </>
  );
}
