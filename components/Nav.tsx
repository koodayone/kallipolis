export default function Nav() {
  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <span className="text-xl font-bold tracking-tight text-gray-900">
          Kallipolis
        </span>

        {/* Navigation links */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#" className="text-sm text-gray-600 hover:text-gray-900">About</a>
          <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Vision</a>
          <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Problem</a>
          <a href="#" className="text-sm text-gray-600 hover:text-gray-900">Solution</a>
        </div>

        {/* CTA buttons */}
        <div className="flex items-center gap-3">
          <button className="text-sm text-gray-700 px-4 py-2 rounded-md hover:bg-gray-100">
            Sign In
          </button>
          <button className="text-sm text-white bg-gray-900 px-4 py-2 rounded-md hover:bg-gray-700">
            Get Started
          </button>
        </div>
      </div>
    </nav>
  );
}
