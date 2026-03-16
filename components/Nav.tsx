import Image from "next/image";

export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 w-full" style={{ backgroundColor: "#002366" }}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo + wordmark */}
        <div className="flex items-center gap-3">
          <Image
            src="/kallipolis-logo.png"
            alt="Kallipolis logo"
            height={40}
            width={40}
            className="object-contain"
          />
          <span
            className="text-white text-xl leading-none"
            style={{ fontFamily: "var(--font-days-one)" }}
          >
            Kallipolis
          </span>
        </div>

        {/* Navigation links */}
        <div className="hidden md:flex items-center gap-8">
          {["About", "Vision", "Problem", "Solution"].map((link) => (
            <a
              key={link}
              href="#"
              className="text-sm text-white/80 hover:text-white transition-colors"
            >
              {link}
            </a>
          ))}
        </div>

        {/* CTA buttons */}
        <div className="flex items-center gap-3">
          <button className="text-sm text-white border border-white px-4 py-2 rounded-md hover:bg-white/10 transition-colors">
            Sign In
          </button>
          <button
            className="text-sm font-medium px-4 py-2 rounded-md hover:bg-gray-100 transition-colors"
            style={{ backgroundColor: "#ffffff", color: "#002366" }}
          >
            Get Started
          </button>
        </div>

      </div>
    </nav>
  );
}
