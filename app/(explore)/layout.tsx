import Nav from "../components/Nav";
import Footer from "../components/Footer";

export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Nav />
      <div className="md:min-h-screen max-md:min-h-[100dvh]" style={{ background: "#060d1f" }}>
        {children}
      </div>
      <Footer />
    </>
  );
}
