import React from 'react';
import { Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Tractor,
  Users,
  Syringe,
  Wheat,
  Activity,
  Bell,
  Bot,
  User,
  Pencil,
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import PublicHeader from '../components/public/PublicHeader';
import PublicFooter from '../components/public/PublicFooter';

const sections = [
  { id: 'dashboard', title: 'Dashboard', icon: LayoutDashboard },
  { id: 'livestock', title: 'Livestock', icon: Tractor },
  { id: 'batch-management', title: 'Batch Management', icon: Users },
  { id: 'vaccinations', title: 'Vaccinations', icon: Syringe },
  { id: 'feed-inventory', title: 'Feed Inventory', icon: Wheat },
  { id: 'health-tracking', title: 'Health Tracking', icon: Activity },
  { id: 'notifications', title: 'Notifications', icon: Bell },
  { id: 'ai-feed', title: 'AI Feed Recommendations', icon: Bot },
  { id: 'profile', title: 'Profile', icon: User },
  { id: 'editing-deleting', title: 'Editing & Deleting Records', icon: Pencil },
  { id: 'troubleshooting', title: 'Troubleshooting', icon: HelpCircle },
];

const faqs = [
  {
    q: 'I logged in but my animals aren\u2019t showing up.',
    a: 'Refresh the page once. Records load from the server after login, and occasionally the first load is slow on a weak connection. If the list is still empty, confirm you\u2019re logged into the same account you used to add the animals; records are tied to your account.',
  },
  {
    q: 'A vaccination alert seems wrong or hasn\u2019t appeared.',
    a: 'Alerts are calculated from the last recorded vaccination date and its interval. Check the Vaccinations page and confirm the date entered for that animal is correct; an incorrect date will shift the due-date calculation.',
  },
  {
    q: 'The AI feed recommendation looks off for my animal.',
    a: 'Recommendations are only as good as the inputs. Double-check breed, age, weight, and lactation stage before reading the suggestion, and treat the output as guidance rather than a substitute for veterinary or nutritional advice.',
  },
  {
    q: 'I can\u2019t find the option to remove an animal.',
    a: 'Open the animal from the Livestock list, then use the delete option on its detail page. See Editing & Deleting Records below for the full steps.',
  },
  {
    q: 'The page looks broken or a feature won\u2019t load.',
    a: 'Try a hard refresh (Ctrl+Shift+R on Windows, Cmd+Shift+R on Mac). If that doesn\u2019t help, log out and back in. This clears a stale session without losing any saved records.',
  },
];

const SectionHeading: React.FC<{ id: string; icon: React.ElementType; title: string }> = ({ id, icon: Icon, title }) => (
  <div id={id} className="flex scroll-mt-24 items-center gap-3">
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#606c38]/10">
      <Icon className="h-5 w-5 text-[#606c38]" />
    </div>
    <h2
      className="text-xl font-medium text-[#283618] sm:text-2xl"
      style={{ fontFamily: 'var(--font-display)' }}
    >
      {title}
    </h2>
  </div>
);

const UserGuide: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#fefae0]" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      <PublicHeader variant="guide" />

      {/* Intro */}
      <section className="border-b border-[#dda15e]/30 bg-white/50">
        <div className="mx-auto max-w-6xl px-6 py-12 sm:px-8">
          <span className="inline-block rounded-full bg-[#606c38]/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#606c38]">
            User Guide
          </span>
          <h1
            className="mt-4 text-3xl font-medium text-[#283618] sm:text-4xl"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            How to use FarmLite
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#283618]/75">
            A plain-language walkthrough of every module in the app. Jump to a
            section from the list below, or read top to bottom if you\u2019re
            setting FarmLite up for the first time.
          </p>
          <Link
            to="/register"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#bc6c25] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-[#a85f20]"
          >
            Get Started <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <div className="mx-auto max-w-6xl gap-10 px-6 py-12 sm:px-8 lg:flex lg:items-start">
        {/* Table of contents */}
        <aside className="mb-10 lg:sticky lg:top-24 lg:mb-0 lg:w-64 lg:shrink-0">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#bc6c25]">On this page</h2>
          <nav className="mt-3 space-y-1">
            {sections.map(({ id, title, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-[#283618]/75 hover:bg-[#606c38]/10 hover:text-[#283618]"
              >
                <Icon className="h-4 w-4 shrink-0 text-[#606c38]" />
                {title}
              </a>
            ))}
          </nav>
        </aside>

        {/* Content */}
        <div className="min-w-0 flex-1 space-y-14">
          <div className="space-y-4">
            <SectionHeading id="dashboard" icon={LayoutDashboard} title="Dashboard" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              The Dashboard is the first screen after logging in. It gives a
              snapshot of your herd: how many animals are recorded, any
              vaccinations or health items needing attention, and a shortcut
              to the modules you use most. Use it as a starting point each
              session before drilling into a specific module.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="livestock" icon={Tractor} title="Livestock" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Livestock is your full herd list. Each entry stores an
              animal&rsquo;s identifying details: tag/ID, breed, age,
              weight, and type. From here you can:
            </p>
            <ul className="ml-1 max-w-3xl list-disc space-y-1.5 pl-5 text-[15px] leading-relaxed text-[#283618]/80">
              <li>Add a new animal one at a time with <strong>Add Animal</strong>.</li>
              <li>Search or filter the list to find a specific animal quickly.</li>
              <li>Open an animal to view its full profile, including linked health and vaccination history.</li>
            </ul>
          </div>

          <div className="space-y-4">
            <SectionHeading id="batch-management" icon={Users} title="Batch Management" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              When several animals arrive together or share the same details
              (for example, a group of calves from the same batch), Batch
              Management lets you record them in one pass instead of
              repeating the same form. Enter the shared details once, then
              enter the count of animals to create. FarmLite generates the
              individual records for you, which can still be edited
              separately afterwards.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="vaccinations" icon={Syringe} title="Vaccinations" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Log each vaccination against the animal it was given to,
              including the date and the vaccine or interval used. FarmLite
              calculates the next due date automatically and surfaces
              upcoming or overdue vaccinations as alerts, so tracking doesn&rsquo;t
              rely on memory or a separate notebook.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="feed-inventory" icon={Wheat} title="Feed Inventory" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Feed Inventory keeps a running record of feed stock, including what
              you have, how much, and when it was last updated. Update
              quantities as feed is used or restocked so shortages and
              overstocking show up early rather than being discovered at
              feeding time.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="health-tracking" icon={Activity} title="Health Tracking" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Use Health Tracking to record check-ups, illnesses, treatments,
              and general condition notes against an animal over time. This
              builds a running history that\u2019s useful both for day-to-day
              care and for spotting recurring issues with a particular
              animal.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="notifications" icon={Bell} title="Notifications" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Notifications brings together everything that needs attention,
              including overdue or upcoming vaccinations and low feed stock,
              in a single list. Check this page each time you log in as a
              quick way to see what to act on today.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="ai-feed" icon={Bot} title="AI Feed Recommendations" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              This module is specific to cattle. Select an animal (or enter
              its details directly), including age, weight, breed, lactation
              stage, and body condition, and FarmLite returns a suggested
              daily feeding plan generated by a trained prediction model.
              Treat the result as an advisory recommendation. It is there to
              support your own judgement, not replace it, and it
              works best with accurate, up-to-date animal details.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="profile" icon={User} title="Profile" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Profile holds your account details. Use it to review your
              registered information and manage your account settings.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="editing-deleting" icon={Pencil} title="Editing & Deleting Records" />
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Every record in FarmLite, whether an animal, a vaccination
              entry, or a health note, follows the same pattern:
            </p>
            <ol className="ml-1 max-w-3xl list-decimal space-y-1.5 pl-5 text-[15px] leading-relaxed text-[#283618]/80">
              <li>Open the record from its list (Livestock, Vaccinations, Health Tracking, and so on).</li>
              <li>Use the <strong>Edit</strong> option to update any field, then save.</li>
              <li>Use the <strong>Delete</strong> option to remove the record permanently.</li>
            </ol>
            <p className="max-w-3xl text-[15px] leading-relaxed text-[#283618]/80">
              Deleting a record cannot be undone, so double-check you have
              the right animal or entry open before confirming.
            </p>
          </div>

          <div className="space-y-4">
            <SectionHeading id="troubleshooting" icon={HelpCircle} title="Troubleshooting" />
            <div className="max-w-3xl divide-y divide-[#dda15e]/30 overflow-hidden rounded-2xl border border-[#dda15e]/30 bg-white">
              {faqs.map(({ q, a }) => (
                <details key={q} className="group p-5 open:bg-[#606c38]/5">
                  <summary className="cursor-pointer list-none text-[15px] font-semibold text-[#283618] marker:content-none">
                    <span className="flex items-center justify-between gap-4">
                      {q}
                      <span className="text-[#bc6c25] transition-transform group-open:rotate-45">+</span>
                    </span>
                  </summary>
                  <p className="mt-2.5 text-sm leading-relaxed text-[#283618]/75">{a}</p>
                </details>
              ))}
            </div>
          </div>
        </div>
      </div>

      <PublicFooter />
    </div>
  );
};

export default UserGuide;
