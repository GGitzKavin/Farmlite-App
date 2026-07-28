import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../../assets/logo.svg';
import WheatMotif from './WheatMotif';

const PublicFooter: React.FC = () => (
  <footer className="bg-[#283618] text-[#fefae0]">
    <div className="mx-auto max-w-6xl px-6 py-12 sm:px-8">
      <div className="flex flex-col gap-10 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-sm">
          <div className="flex items-center gap-2.5">
            <img src={logo} alt="" className="h-8 w-8 object-contain" />
            <span
              className="text-xl font-semibold tracking-tight"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              FarmLite
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-[#fefae0]/70">
            A lightweight herd record book, vaccination reminder, and AI feed
            advisor for small and medium-scale livestock farms.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-8 sm:gap-16">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#dda15e]">Get started</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/register" className="text-[#fefae0]/80 hover:text-[#fefae0]">Create an account</Link></li>
              <li><Link to="/login" className="text-[#fefae0]/80 hover:text-[#fefae0]">Log in</Link></li>
              <li><Link to="/user-guide" className="text-[#fefae0]/80 hover:text-[#fefae0]">User Guide</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#dda15e]">On this page</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><a href="#features" className="text-[#fefae0]/80 hover:text-[#fefae0]">Features</a></li>
              <li><a href="#how-it-works" className="text-[#fefae0]/80 hover:text-[#fefae0]">How it works</a></li>
              <li><a href="#quick-tips" className="text-[#fefae0]/80 hover:text-[#fefae0]">Quick tips</a></li>
            </ul>
          </div>
        </div>

        <WheatMotif className="hidden h-16 w-16 opacity-40 sm:block" color="#dda15e" />
      </div>

      <div className="mt-10 border-t border-[#fefae0]/15 pt-6 text-xs text-[#fefae0]/50">
        FarmLite is a student livestock management and decision support project.
      </div>
    </div>
  </footer>
);

export default PublicFooter;
