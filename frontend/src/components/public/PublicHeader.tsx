import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import logo from '../../assets/logo.svg';

interface PublicHeaderProps {
  variant?: 'landing' | 'guide';
}

const PublicHeader: React.FC<PublicHeaderProps> = ({ variant = 'landing' }) => {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-[#dda15e]/40 bg-[#fefae0]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5" onClick={() => setOpen(false)}>
          <img src={logo} alt="" className="h-9 w-9 object-contain" />
          <span
            className="text-2xl font-semibold tracking-tight text-[#283618]"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            FarmLite
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {variant === 'landing' ? (
            <>
              <a href="#features" className="text-sm font-medium text-[#283618]/80 hover:text-[#283618]">
                Features
              </a>
              <a href="#how-it-works" className="text-sm font-medium text-[#283618]/80 hover:text-[#283618]">
                How it works
              </a>
              <Link to="/user-guide" className="text-sm font-medium text-[#283618]/80 hover:text-[#283618]">
                User Guide
              </Link>
            </>
          ) : (
            <Link to="/" className="text-sm font-medium text-[#283618]/80 hover:text-[#283618]">
              &larr; Back to Home
            </Link>
          )}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-sm font-semibold text-[#283618] hover:bg-[#dda15e]/25"
          >
            Log In
          </Link>
          <Link
            to="/register"
            className="rounded-lg bg-[#bc6c25] px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#a85f20]"
          >
            Get Started
          </Link>
        </div>

        <button
          type="button"
          aria-label={open ? 'Close menu' : 'Open menu'}
          className="rounded-md p-2 text-[#283618] md:hidden"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-[#dda15e]/40 bg-[#fefae0] px-5 pb-4 pt-2 md:hidden">
          <div className="flex flex-col gap-1">
            {variant === 'landing' ? (
              <>
                <a href="#features" className="rounded-md px-3 py-2 text-[#283618]" onClick={() => setOpen(false)}>
                  Features
                </a>
                <a href="#how-it-works" className="rounded-md px-3 py-2 text-[#283618]" onClick={() => setOpen(false)}>
                  How it works
                </a>
                <Link to="/user-guide" className="rounded-md px-3 py-2 text-[#283618]" onClick={() => setOpen(false)}>
                  User Guide
                </Link>
              </>
            ) : (
              <Link to="/" className="rounded-md px-3 py-2 text-[#283618]" onClick={() => setOpen(false)}>
                &larr; Back to Home
              </Link>
            )}
            <div className="mt-2 flex gap-2 border-t border-[#dda15e]/40 pt-3">
              <Link
                to="/login"
                className="flex-1 rounded-lg px-4 py-2 text-center text-sm font-semibold text-[#283618] ring-1 ring-[#283618]/20"
                onClick={() => setOpen(false)}
              >
                Log In
              </Link>
              <Link
                to="/register"
                className="flex-1 rounded-lg bg-[#bc6c25] px-4 py-2 text-center text-sm font-semibold text-white"
                onClick={() => setOpen(false)}
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default PublicHeader;
