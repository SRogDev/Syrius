import { Link } from '@tanstack/react-router';

export default function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="flex cursor-pointer items-center gap-3">
          <img
            src="/syrius-logo.webp"
            alt="Syrius logo — the star Sirius"
            className="h-8 w-8 object-contain"
          />
          <span className="font-display text-lg font-bold tracking-[0.3em] text-highlight">
            SYRIUS
          </span>
          <span className="hidden rounded-none border border-line px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-platinum sm:inline">
            Phase 5
          </span>
        </Link>
        <nav className="flex items-center gap-6 font-mono text-xs uppercase tracking-widest">
          <Link
            to="/"
            className="cursor-pointer text-platinum transition-colors hover:text-highlight [&.active]:text-highlight"
          >
            Home
          </Link>
          <Link
            to="/projects"
            className="cursor-pointer text-platinum transition-colors hover:text-highlight [&.active]:text-highlight"
          >
            Projects
          </Link>
        </nav>
      </div>
    </header>
  );
}
