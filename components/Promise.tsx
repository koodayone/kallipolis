export default function Promise() {
  return (
    <section className="bg-white py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-sm font-semibold uppercase tracking-widest mb-4" style={{ color: "#002366" }}>
          The Promise
        </p>
        <h2 className="text-4xl font-bold text-gray-900 leading-tight mb-14">
          Activating human potential, with California leading the way.
        </h2>

        {/* Illustration placeholder */}
        <div className="border-2 border-dashed border-gray-300 rounded-xl h-64 flex items-center justify-center mb-12">
          <span className="text-sm text-gray-400">Transformation illustration — coming soon</span>
        </div>

        <a
          href="#"
          className="inline-block text-white text-sm px-6 py-3 rounded-md hover:opacity-90 transition-opacity"
          style={{ backgroundColor: "#002366" }}
        >
          Get in Touch
        </a>
      </div>
    </section>
  );
}
