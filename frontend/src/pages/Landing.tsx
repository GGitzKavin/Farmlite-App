import React from 'react';
import { Link } from 'react-router-dom';
import {
  Tractor,
  Syringe,
  Wheat,
  Activity,
  Bell,
  Bot,
  Users,
  BookOpen,
  ArrowRight,
  UserPlus,
  ClipboardList,
  Sprout,
} from 'lucide-react';
import PublicHeader from '../components/public/PublicHeader';
import PublicFooter from '../components/public/PublicFooter';
import WheatMotif from '../components/public/WheatMotif';

const features = [
  {
    icon: Tractor,
    title: 'Livestock records',
    body: 'Create a digital profile for every animal, including breed, age, weight, and history, in one searchable herd book.',
  },
  {
    icon: Users,
    title: 'Batch management',
    body: 'Add or update groups of animals at once instead of repeating the same entry one by one.',
  },
  {
    icon: Syringe,
    title: 'Vaccination alerts',
    body: 'Log a vaccination once and FarmLite works out the next due date, flagging anything overdue automatically.',
  },
  {
    icon: Wheat,
    title: 'Feed inventory',
    body: 'Keep track of feed stock on hand so shortages and wastage show up before they become a problem.',
  },
  {
    icon: Bot,
    title: 'AI feed recommendations',
    body: 'Enter a cow\u2019s details and get a daily feeding suggestion built from a trained yield-prediction model.',
  },
  {
    icon: Activity,
    title: 'Health tracking',
    body: 'Record check-ups, treatments, and conditions against each animal\u2019s timeline.',
  },
  {
    icon: Bell,
    title: 'Notifications',
    body: 'A single dashboard of what needs attention today: overdue vaccinations, low stock, and more.',
  },
  {
    icon: BookOpen,
    title: 'Built for small farms',
    body: 'No sensors, no installs, no enterprise pricing; just a browser and a herd to look after.',
  },
];

const steps = [
  {
    icon: UserPlus,
    title: 'Create your account',
    body: 'Register with your email in under a minute, with no setup calls or hardware to install.',
  },
  {
    icon: Tractor,
    title: 'Add your herd',
    body: 'Enter animals one at a time or in a batch, with the details FarmLite needs to track them.',
  },
  {
    icon: ClipboardList,
    title: 'Log vaccinations & health',
    body: 'Record events as they happen; FarmLite calculates due dates and raises alerts for you.',
  },
  {
    icon: Sprout,
    title: 'Get feed guidance',
    body: 'Open AI Feed Recommendations, enter an animal\u2019s details, and receive a daily feeding plan.',
  },
];

const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#fefae0]" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <PublicHeader variant="landing" />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-16 sm:px-8 sm:py-20 md:grid-cols-[1.1fr_0.9fr] md:items-center md:py-28">
          <div>
            <span className="inline-block rounded-full bg-[#606c38]/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#606c38]">
              Livestock management &amp; decision support
            </span>
            <h1
              className="mt-5 text-4xl font-medium leading-[1.08] text-[#283618] sm:text-5xl lg:text-6xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Every animal, every record,
              <br className="hidden sm:block" /> in one field book.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-[#283618]/75">
              FarmLite is a lightweight, mobile-friendly system for small and
              medium-scale livestock farms, built to replace paper
              notebooks and guesswork with organised records, automatic
              vaccination reminders, and AI-assisted cattle feeding advice.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                to="/register"
                className="inline-flex items-center gap-2 rounded-lg bg-[#bc6c25] px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-[#a85f20]"
              >
                Get Started <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/login"
                className="rounded-lg px-6 py-3 text-base font-semibold text-[#283618] ring-1 ring-[#283618]/25 transition-colors hover:bg-[#283618]/5"
              >
                Log In
              </Link>
              <Link
                to="/user-guide"
                className="rounded-lg px-6 py-3 text-base font-semibold text-[#606c38] underline decoration-[#606c38]/30 underline-offset-4 hover:text-[#4f5a2f]"
              >
                View User Guide
              </Link>
            </div>
          </div>

          <div className="relative mx-auto flex h-64 w-64 items-center justify-center sm:h-80 sm:w-80">
            <div className="absolute inset-0 rounded-full bg-[#dda15e]/25" />
            <div className="absolute inset-6 rounded-full bg-[#606c38]/10" />
            <WheatMotif className="relative h-40 w-40 sm:h-52 sm:w-52" color="#606c38" />
          </div>
        </div>
      </section>

      {/* What it does */}
      <section className="border-y border-[#dda15e]/30 bg-white/50">
        <div className="mx-auto max-w-4xl px-6 py-14 text-center sm:px-8">
          <h2
            className="text-2xl font-medium text-[#283618] sm:text-3xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            What FarmLite does
          </h2>
          <p className="mt-4 text-base leading-relaxed text-[#283618]/75 sm:text-lg">
            Most small farms track animals on paper, in memory, or across a
            handful of spreadsheets, which makes it easy to miss a
            vaccination or lose track of feed. FarmLite centralises animal
            records and vaccination schedules, raises alerts before things
            are overdue, and adds an AI-based feed suggestion for cattle so
            feeding decisions are backed by data, not guesswork, all
            from a browser, on any device, without specialised hardware.
          </p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-16 sm:px-8 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2
            className="text-2xl font-medium text-[#283618] sm:text-3xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            Everything your herd records need
          </h2>
          <p className="mt-3 text-base text-[#283618]/70">
            Eight modules that cover the day-to-day of running a small livestock operation.
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="rounded-2xl border border-[#dda15e]/30 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#606c38]/10">
                <Icon className="h-5.5 w-5.5 text-[#606c38]" />
              </div>
              <h3 className="mt-4 text-base font-semibold text-[#283618]">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#283618]/70">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-[#606c38]/5 py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-6 sm:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2
              className="text-2xl font-medium text-[#283618] sm:text-3xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Getting started takes four steps
            </h2>
            <p className="mt-3 text-base text-[#283618]/70">
              From a blank account to your first feed recommendation in one sitting.
            </p>
          </div>

          <ol className="relative mt-14 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            <div
              className="pointer-events-none absolute left-0 right-0 top-6 hidden border-t-2 border-dashed border-[#bc6c25]/40 lg:block"
              aria-hidden="true"
            />
            {steps.map(({ icon: Icon, title, body }, index) => (
              <li key={title} className="relative flex flex-col items-center text-center lg:items-start lg:text-left">
                <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-[#bc6c25] text-white shadow-sm">
                  <span
                    className="absolute -top-2.5 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-[#283618] text-[11px] font-bold text-[#fefae0]"
                  >
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <Icon className="h-5.5 w-5.5" />
                </div>
                <h3 className="mt-4 text-base font-semibold text-[#283618]">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#283618]/70">{body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Quick tips / basic instructions */}
      <section id="quick-tips" className="mx-auto max-w-5xl px-6 py-16 sm:px-8 sm:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2
            className="text-2xl font-medium text-[#283618] sm:text-3xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            Quick tips before you dive in
          </h2>
        </div>

        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          <div className="rounded-2xl border border-[#dda15e]/30 bg-white p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#bc6c25]">Adding animals</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#283618]/75">
              Use <strong>Livestock &rarr; Add Animal</strong> for a single entry, or{' '}
              <strong>Batch Management</strong> when several animals share the same details, such as a new group arriving together.
            </p>
          </div>
          <div className="rounded-2xl border border-[#dda15e]/30 bg-white p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#bc6c25]">Staying on top of alerts</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#283618]/75">
              Check <strong>Notifications</strong> each time you log in. It collects overdue vaccinations and low feed stock in one place, so nothing needs to be remembered separately.
            </p>
          </div>
          <div className="rounded-2xl border border-[#dda15e]/30 bg-white p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#bc6c25]">Getting a feed recommendation</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#283618]/75">
              Open <strong>AI Feed Recommendations</strong>, select the animal, and fill in its current details. The more accurate the inputs, the more useful the suggested ration.
            </p>
          </div>
          <div className="rounded-2xl border border-[#dda15e]/30 bg-white p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[#bc6c25]">Need more detail?</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#283618]/75">
              The <Link to="/user-guide" className="font-semibold text-[#606c38] underline underline-offset-2">User Guide</Link> walks through every module, plus editing, deleting, and troubleshooting common issues.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-[#283618]">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 px-6 py-16 text-center sm:px-8">
          <h2
            className="text-2xl font-medium text-[#fefae0] sm:text-3xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            Ready to put your herd records in order?
          </h2>
          <p className="max-w-xl text-[#fefae0]/70">
            Create a free account and add your first animal in a couple of minutes.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-[#bc6c25] px-6 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-[#a85f20]"
            >
              Get Started <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/login"
              className="rounded-lg px-6 py-3 text-base font-semibold text-[#fefae0] ring-1 ring-[#fefae0]/30 transition-colors hover:bg-[#fefae0]/10"
            >
              Log In
            </Link>
            <Link
              to="/user-guide"
              className="rounded-lg px-6 py-3 text-base font-semibold text-[#dda15e] underline decoration-[#dda15e]/40 underline-offset-4 hover:text-[#e8b978]"
            >
              View User Guide
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
};

export default Landing;
