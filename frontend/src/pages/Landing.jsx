import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { TopBar } from "../components/TopBar";
import { CATEGORIES, CATEGORY_ACCENTS } from "../constants";
import { API } from "../auth";
import {
  Lightning, Rocket, Target, Coins, Sparkle, CheckCircle, Question, Briefcase,
  GraduationCap, ArrowRight, Star, MagnifyingGlass, CaretDown, Copy,
} from "@phosphor-icons/react";

const HOW_IT_WORKS = [
  { icon: GraduationCap, title: "Sign up free", desc: "Create your worker profile, pick the skills you've got." },
  { icon: MagnifyingGlass, title: "Pick a quest", desc: "Browse paid micro-tasks from real businesses & creators." },
  { icon: Rocket, title: "Deliver work", desc: "Submit from your laptop, your hostel, your home. On your time." },
  { icon: Coins, title: "Get paid", desc: "Earnings tracked. Skill badges build. Wallet grows." },
];

const WORKER_BENEFITS = [
  { icon: Coins, t: "Earn from anywhere", d: "Hostel, library, home — finish tasks in your free hours." },
  { icon: Sparkle, t: "Build real experience", d: "Resume-worthy work for startups and creators." },
  { icon: Target, t: "Pick what fits you", d: "Choose tasks that match your skills & schedule." },
  { icon: Star, t: "Skill badges", d: "Unlock badges as you complete categories of work." },
];

const CLIENT_BENEFITS = [
  { icon: Lightning, t: "Move fast", d: "Post a task in 60 seconds. Get applications same day." },
  { icon: Briefcase, t: "Affordable & focused", d: "Pay only for the micro-task you need — not full retainers." },
  { icon: CheckCircle, t: "Vetted student talent", d: "Energetic workers from top colleges & exam batches." },
];

const FAQS = [
  { q: "Who can join as a worker?", a: "Any student, fresher, or government exam aspirant from India. We're starting with college students and broadening from there." },
  { q: "How do I get paid?", a: "For the MVP, payments are tracked manually by our team and settled to your UPI/bank account within 3 days of task approval." },
  { q: "Is there a fee?", a: "No fee to join. We charge a small platform fee on completed tasks (clients only) — free during the beta." },
  { q: "What kind of tasks are available?", a: "Data entry, design (Canva, thumbnails), social media, research, translation, AI content cleanup, Excel, transcription, and more." },
  { q: "Can I do this alongside my studies?", a: "Yes — that's the whole point. Pick tasks that fit your week, no minimum hours required." },
];

export default function Landing() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [waitlistOpen, setWaitlistOpen] = useState(false);
  const [waitForm, setWaitForm] = useState({ name: "", email: "", role: "worker", interest: "" });
  const [submitting, setSubmitting] = useState(false);
  const [openFaq, setOpenFaq] = useState(0);
  const [referralResult, setReferralResult] = useState(null);
  const refCode = searchParams.get("ref");

  useEffect(() => {
    if (refCode) {
      // Auto-open waitlist for referred visitors
      toast.success(`You were invited! Sign up to credit your friend.`);
    }
  }, [refCode]);

  const submitWaitlist = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await axios.post(`${API}/waitlist`, { ...waitForm, ref: refCode || undefined });
      if (res.data.already) {
        toast.success("You're already on the list! Here's your referral link.");
      } else {
        toast.success("You're in. Welcome to SideQuest 🎉");
      }
      setReferralResult({
        code: res.data.referral_code,
        link: res.data.referral_link,
      });
      setWaitForm({ name: "", email: "", role: "worker", interest: "" });
    } catch (e) {
      toast.error("Could not join waitlist. Try again?");
    } finally {
      setSubmitting(false);
    }
  };

  const copyReferral = () => {
    if (referralResult?.link) {
      navigator.clipboard.writeText(referralResult.link);
      toast.success("Copied! Share it with your friends.");
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="blob" style={{ width: 380, height: 380, top: -120, right: -80, background: "#FFDAB9" }} />
        <div className="blob" style={{ width: 320, height: 320, bottom: -120, left: -80, background: "#C4B5FD" }} />
        <div className="sq-container px-4 md:px-8 pt-12 md:pt-20 pb-16 md:pb-24 relative">
          <div className="grid lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-7">
              <span className="sq-badge bg-[#A7F3D0] mb-6 inline-block">For Students • Freshers • Aspirants</span>
              <h1 className="sq-h1 mb-5">
                Your <span className="bg-[#FACC15] px-3 inline-block border-2 border-slate-900 rounded-lg" style={{ boxShadow: "4px 4px 0px #0F172A" }}>side quest</span> to financial independence.
              </h1>
              <p className="text-lg md:text-xl text-slate-700 max-w-xl leading-relaxed mb-8">
                Earn money, gain real work experience, and build skills with flexible online micro-jobs — finished from your hostel, library, or home.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setWaitlistOpen(true)}
                  className="sq-btn sq-btn-primary"
                  data-testid="hero-join-waitlist-btn"
                >
                  Join the waitlist <ArrowRight size={18} weight="bold" />
                </button>
                <button
                  onClick={() => navigate("/login")}
                  className="sq-btn sq-btn-secondary"
                  data-testid="hero-signin-btn"
                >
                  Sign in with Google
                </button>
              </div>
              <div className="flex gap-6 mt-8 text-sm text-slate-600">
                <div><span className="font-black text-slate-900 text-lg">500+</span> early students</div>
                <div><span className="font-black text-slate-900 text-lg">11</span> task categories</div>
                <div><span className="font-black text-slate-900 text-lg">₹2L+</span> in pilot earnings</div>
              </div>
            </div>
            <div className="lg:col-span-5">
              <div className="relative">
                <div className="absolute -top-4 -left-4 w-20 h-20 bg-[#FACC15] border-2 border-slate-900 rounded-full z-10 flex items-center justify-center font-black text-slate-900 rotate-[-8deg]" style={{ boxShadow: "4px 4px 0px #0F172A", fontFamily: "Outfit" }}>
                  EARN
                </div>
                <div className="sq-card p-0 overflow-hidden">
                  <img
                    src="https://images.unsplash.com/photo-1515378960530-7c0da6231fb1?crop=entropy&cs=srgb&fm=jpg&q=85&w=900"
                    alt="Student working"
                    className="w-full h-[420px] object-cover"
                  />
                </div>
                <div className="absolute -bottom-4 -right-4 sq-card p-4 bg-white max-w-[200px]">
                  <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">This week</div>
                  <div className="text-2xl font-black" style={{ fontFamily: "Outfit" }}>₹3,200</div>
                  <div className="text-xs text-slate-600">3 tasks completed</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CATEGORIES MARQUEE */}
      <section className="py-8 border-y-2 border-slate-900 bg-[#0F172A] overflow-hidden">
        <div className="flex marquee-track gap-12 whitespace-nowrap">
          {[...CATEGORIES, ...CATEGORIES].map((c, i) => (
            <span key={i} className="text-3xl md:text-4xl font-black text-white" style={{ fontFamily: "Outfit", WebkitTextStroke: "1px white", color: "transparent" }}>
              ★ {c}
            </span>
          ))}
        </div>
      </section>

      {/* PROBLEM / SOLUTION */}
      <section className="sq-section">
        <div className="sq-container grid md:grid-cols-2 gap-8">
          <div className="sq-card p-8 bg-[#FFDAB9]">
            <span className="sq-label text-slate-700">The Problem</span>
            <h2 className="sq-h2 mt-3 mb-4">Students are broke. Tuition isn't.</h2>
            <p className="text-slate-800 leading-relaxed">
              Internships are scarce, part-time jobs are inflexible, and freelancing platforms are built for pros — not for an 18-year-old between exams. Real work experience? Locked behind "2 years experience required."
            </p>
          </div>
          <div className="sq-card p-8 bg-[#A7F3D0]">
            <span className="sq-label text-slate-700">Our Solution</span>
            <h2 className="sq-h2 mt-3 mb-4">Bite-sized paid tasks. On your schedule.</h2>
            <p className="text-slate-800 leading-relaxed">
              SideQuest connects students with real businesses needing small digital tasks done — design, research, content, data, translation. Finish between classes. Get paid. Build a portfolio that actually counts.
            </p>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="sq-section bg-white border-y-2 border-slate-900">
        <div className="sq-container">
          <div className="text-center mb-12">
            <span className="sq-label text-[#FF5A5F]">How it works</span>
            <h2 className="sq-h2 mt-2">Four steps. That's it.</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map((step, i) => {
              const Icon = step.icon;
              const accents = ["#FFDAB9", "#C4B5FD", "#A7F3D0", "#FACC15"];
              return (
                <div key={i} className="sq-card sq-card-hover p-6 relative">
                  <div className="absolute -top-3 -left-3 w-10 h-10 rounded-full bg-slate-900 text-white font-black flex items-center justify-center border-2 border-slate-900" style={{ fontFamily: "Outfit" }}>
                    {i + 1}
                  </div>
                  <div className="w-14 h-14 rounded-xl border-2 border-slate-900 flex items-center justify-center mb-4" style={{ backgroundColor: accents[i] }}>
                    <Icon size={28} weight="bold" />
                  </div>
                  <h3 className="font-bold text-lg mb-2" style={{ fontFamily: "Outfit" }}>{step.title}</h3>
                  <p className="text-sm text-slate-600">{step.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* WORKER BENEFITS */}
      <section className="sq-section">
        <div className="sq-container grid lg:grid-cols-12 gap-10">
          <div className="lg:col-span-5">
            <span className="sq-label text-[#10B981]">For Workers</span>
            <h2 className="sq-h2 mt-2 mb-4">Built for the student grind.</h2>
            <p className="text-slate-700 mb-6">Whether you're cramming for UPSC or pulling an all-nighter for semester exams — fit work into the gaps.</p>
            <button
              onClick={() => setWaitlistOpen(true)}
              className="sq-btn sq-btn-success"
              data-testid="worker-cta-btn"
            >
              I want to earn
            </button>
          </div>
          <div className="lg:col-span-7 grid sm:grid-cols-2 gap-5">
            {WORKER_BENEFITS.map((b, i) => {
              const Icon = b.icon;
              return (
                <div key={i} className="sq-card sq-card-hover p-5">
                  <Icon size={28} weight="bold" className="mb-3 text-[#FF5A5F]" />
                  <h4 className="font-bold mb-1" style={{ fontFamily: "Outfit" }}>{b.t}</h4>
                  <p className="text-sm text-slate-600">{b.d}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CLIENT BENEFITS */}
      <section className="sq-section bg-[#0F172A] text-white">
        <div className="sq-container grid lg:grid-cols-12 gap-10">
          <div className="lg:col-span-7 grid sm:grid-cols-3 gap-5 order-2 lg:order-1">
            {CLIENT_BENEFITS.map((b, i) => {
              const Icon = b.icon;
              const accents = ["#FACC15", "#A7F3D0", "#C4B5FD"];
              return (
                <div key={i} className="bg-white text-slate-900 border-2 border-white rounded-xl p-5" style={{ boxShadow: "4px 4px 0px #FACC15" }}>
                  <div className="w-12 h-12 rounded-xl border-2 border-slate-900 flex items-center justify-center mb-3" style={{ backgroundColor: accents[i] }}>
                    <Icon size={24} weight="bold" />
                  </div>
                  <h4 className="font-bold mb-1" style={{ fontFamily: "Outfit" }}>{b.t}</h4>
                  <p className="text-sm text-slate-600">{b.d}</p>
                </div>
              );
            })}
          </div>
          <div className="lg:col-span-5 order-1 lg:order-2">
            <span className="sq-label text-[#FACC15]">For Businesses</span>
            <h2 className="sq-h2 mt-2 mb-4 text-white">Get small things done. Fast.</h2>
            <p className="text-slate-300 mb-6">Startup founders, creators, agencies — outsource the tasks eating your day to talented students who'll do it for less.</p>
            <button
              onClick={() => { setWaitForm((f) => ({ ...f, role: "client" })); setWaitlistOpen(true); }}
              className="sq-btn sq-btn-accent"
              data-testid="client-cta-btn"
            >
              I want to post tasks
            </button>
          </div>
        </div>
      </section>

      {/* FEATURED CATEGORIES GRID */}
      <section className="sq-section">
        <div className="sq-container">
          <div className="text-center mb-10">
            <span className="sq-label text-[#FF5A5F]">Featured</span>
            <h2 className="sq-h2 mt-2">Task categories we love</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {CATEGORIES.map((c) => (
              <div
                key={c}
                className="sq-card sq-card-hover p-5 text-center"
                style={{ backgroundColor: CATEGORY_ACCENTS[c] }}
                data-testid={`category-${c.toLowerCase().replace(/\s+/g, "-")}`}
              >
                <div className="font-bold text-sm" style={{ fontFamily: "Outfit" }}>{c}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS PLACEHOLDER */}
      <section className="sq-section bg-white border-y-2 border-slate-900">
        <div className="sq-container">
          <div className="text-center mb-10">
            <span className="sq-label text-[#10B981]">Coming soon</span>
            <h2 className="sq-h2 mt-2">Real stories. Real students.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="sq-card p-6 bg-[#FFFDF9]">
                <div className="flex gap-1 mb-3">
                  {[1, 2, 3, 4, 5].map((s) => <Star key={s} size={16} weight="fill" className="text-[#FACC15]" />)}
                </div>
                <p className="text-slate-700 italic leading-relaxed">
                  "Once we onboard our first batch of students, their stories will live here. Watch this space."
                </p>
                <div className="flex items-center gap-3 mt-4 pt-4 border-t-2 border-dashed border-slate-300">
                  <div className="w-10 h-10 rounded-full bg-slate-200 border-2 border-slate-900" />
                  <div>
                    <div className="font-bold text-sm">Coming soon</div>
                    <div className="text-xs text-slate-500">Beta cohort, 2026</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="sq-section">
        <div className="sq-container max-w-3xl">
          <div className="text-center mb-10">
            <span className="sq-label text-[#FF5A5F]">FAQ</span>
            <h2 className="sq-h2 mt-2">Quick questions, quicker answers</h2>
          </div>
          <div className="space-y-3">
            {FAQS.map((f, i) => (
              <div key={i} className="sq-card overflow-hidden" data-testid={`faq-${i}`}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? -1 : i)}
                  className="w-full flex items-center justify-between p-5 text-left"
                >
                  <span className="font-bold text-base sm:text-lg pr-4" style={{ fontFamily: "Outfit" }}>
                    <Question size={20} weight="bold" className="inline mr-2 text-[#FF5A5F]" />
                    {f.q}
                  </span>
                  <CaretDown size={20} weight="bold" className={`transition-transform ${openFaq === i ? "rotate-180" : ""}`} />
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-5 text-slate-700 leading-relaxed border-t-2 border-dashed border-slate-300 pt-4">
                    {f.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WAITLIST CTA */}
      <section className="sq-section bg-[#FF5A5F]">
        <div className="sq-container text-center">
          <h2 className="text-3xl sm:text-5xl font-black text-white mb-4" style={{ fontFamily: "Outfit" }}>
            Ready to start your side quest?
          </h2>
          <p className="text-white/90 text-lg mb-8 max-w-xl mx-auto">Join early. Get matched with your first paid task in your first week.</p>
          <button
            onClick={() => setWaitlistOpen(true)}
            className="sq-btn sq-btn-accent text-lg"
            data-testid="footer-cta-btn"
          >
            Join the waitlist <ArrowRight size={20} weight="bold" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-[#0F172A] text-white py-10 px-4 md:px-8">
        <div className="sq-container flex flex-col md:flex-row justify-between gap-6 items-start md:items-center">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#FF5A5F] border-2 border-white flex items-center justify-center font-black">S</div>
              <span className="font-black text-lg" style={{ fontFamily: "Outfit" }}>SideQuest</span>
            </div>
            <p className="text-slate-400 text-sm">Your side quest to financial independence.</p>
          </div>
          <div className="flex gap-6 text-sm">
            <Link to="/roadmap" className="hover:text-[#FACC15]" data-testid="footer-roadmap-link">Roadmap</Link>
            <Link to="/login" className="hover:text-[#FACC15]" data-testid="footer-login-link">Sign in</Link>
          </div>
        </div>
        <div className="sq-container border-t border-slate-700 mt-6 pt-6 text-xs text-slate-500">
          © 2026 SideQuest. Made for students, by students.
        </div>
      </footer>

      {/* WAITLIST MODAL */}
      {waitlistOpen && (
        <div className="fixed inset-0 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => { setWaitlistOpen(false); setReferralResult(null); }}>
          <div className="sq-card bg-white p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <span className="sq-label text-[#FF5A5F]">Waitlist</span>
                <h3 className="sq-h2 mt-1">{referralResult ? "You're in! 🎉" : "Join the squad"}</h3>
              </div>
              <button onClick={() => { setWaitlistOpen(false); setReferralResult(null); }} className="text-2xl font-bold" data-testid="waitlist-close-btn">×</button>
            </div>
            {referralResult ? (
              <div data-testid="referral-result">
                <p className="text-slate-700 mb-3">Share your referral link — top referrers get priority access + a Founding Member badge.</p>
                <div className="sq-card p-3 bg-[#FACC15] mb-3 font-mono text-xs break-all" data-testid="referral-link">
                  {referralResult.link}
                </div>
                <button onClick={copyReferral} className="sq-btn sq-btn-primary w-full" data-testid="copy-referral-btn">
                  <Copy size={16} weight="bold" /> Copy link
                </button>
                <button onClick={() => { setWaitlistOpen(false); setReferralResult(null); }} className="sq-btn sq-btn-secondary w-full mt-2" data-testid="close-referral-btn">
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={submitWaitlist} className="space-y-3">
                {refCode && (
                  <div className="sq-chip bg-[#A7F3D0] text-xs">Invited via code: {refCode}</div>
                )}
                <input
                  required
                  placeholder="Your name"
                  value={waitForm.name}
                  onChange={(e) => setWaitForm({ ...waitForm, name: e.target.value })}
                  className="sq-input"
                  data-testid="waitlist-name-input"
                />
                <input
                  required
                  type="email"
                  placeholder="you@college.edu"
                  value={waitForm.email}
                  onChange={(e) => setWaitForm({ ...waitForm, email: e.target.value })}
                  className="sq-input"
                  data-testid="waitlist-email-input"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setWaitForm({ ...waitForm, role: "worker" })}
                    className={`flex-1 sq-btn ${waitForm.role === "worker" ? "sq-btn-primary" : "sq-btn-secondary"}`}
                    data-testid="waitlist-role-worker"
                  >
                    Worker
                  </button>
                  <button
                    type="button"
                    onClick={() => setWaitForm({ ...waitForm, role: "client" })}
                    className={`flex-1 sq-btn ${waitForm.role === "client" ? "sq-btn-primary" : "sq-btn-secondary"}`}
                    data-testid="waitlist-role-client"
                  >
                    Client
                  </button>
                </div>
                <textarea
                  placeholder="What kind of tasks excite you? (optional)"
                  value={waitForm.interest}
                  onChange={(e) => setWaitForm({ ...waitForm, interest: e.target.value })}
                  className="sq-input min-h-[80px]"
                  data-testid="waitlist-interest-input"
                />
                <button
                  type="submit"
                  disabled={submitting}
                  className="sq-btn sq-btn-primary w-full"
                  data-testid="waitlist-submit-btn"
                >
                  {submitting ? "Joining..." : "Count me in"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
