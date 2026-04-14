// Root template — re-mounts on every route change, giving us a single,
// consistent fade-in for every page (home, /atlas, /sources, /partnerships).
// Pair with Next.js <Link>-based navigation (no manual fade-out before push),
// so perceived latency is only the fade-in, not fade-out + router + fade-in.

export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="page-fade-in">{children}</div>;
}
