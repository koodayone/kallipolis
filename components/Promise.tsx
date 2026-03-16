export default function Promise() {
  return (
    <section className="bg-promise-granite py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-pacific-navy mb-4">
          The Promise
        </p>
        <h2 className="text-[36px] md:text-[48px] font-bold leading-[1.12] tracking-[-0.02em] text-pure-text mb-14">
          Activating human potential, with California leading the way.
        </h2>

        {/* Illustration placeholder */}
        <div className="border-2 border-dashed border-gray-300 rounded-xl h-64 flex items-center justify-center mb-12">
          <span className="text-sm text-gray-400">Promise illustration — coming soon</span>
        </div>

        <a
          href="#"
          className="inline-block bg-sierra-gold text-pacific-navy font-semibold text-sm px-6 py-3 rounded-md hover:opacity-90 transition-opacity"
        >
          Get in Touch
        </a>
      </div>
    </section>
  );
}
