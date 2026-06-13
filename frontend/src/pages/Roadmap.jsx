import React from "react";
import { TopBar } from "../components/TopBar";
import { CheckCircle, Sparkle, Rocket, Crown } from "@phosphor-icons/react";

const ROADMAP = [
  { phase: "Now (MVP)", icon: CheckCircle, color: "#A7F3D0", items: [
    "Google login & role selection", "Worker & Client dashboards", "Task posting + applications",
    "Manual payment tracking", "Admin moderation", "Waitlist + feedback",
  ]},
  { phase: "Next (Q2)", icon: Sparkle, color: "#FACC15", items: [
    "AI task matching", "Worker ratings & reviews", "Skill certifications",
    "Categorised search & filters", "In-app messaging",
  ]},
  { phase: "Soon (Q3)", icon: Rocket, color: "#BAE6FD", items: [
    "Automated payments (UPI/Stripe)", "Client subscriptions", "Mobile app (iOS + Android)",
    "Bulk task templates", "Time-tracking",
  ]},
  { phase: "Vision", icon: Crown, color: "#C4B5FD", items: [
    "Recruitment partnerships with companies", "Verified portfolios for hiring",
    "Campus ambassador program", "Scholarships funded by SideQuest earnings",
  ]},
];

export default function Roadmap() {
  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar />
      <div className="sq-container px-4 md:px-8 py-12 md:py-20">
        <span className="sq-label text-[#FF5A5F]">Roadmap</span>
        <h1 className="sq-h1 mt-2 mb-3">What we're building, in order.</h1>
        <p className="text-slate-700 max-w-2xl mb-12">We're keeping the MVP simple and shipping fast. Here's the bigger vision.</p>

        <div className="grid md:grid-cols-2 gap-6">
          {ROADMAP.map((stage, i) => {
            const Icon = stage.icon;
            return (
              <div key={stage.phase} className="sq-card p-6" style={{ backgroundColor: stage.color }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-white border-2 border-slate-900 flex items-center justify-center">
                    <Icon size={24} weight="bold" />
                  </div>
                  <h2 className="sq-h3" style={{ fontFamily: "Outfit" }}>{stage.phase}</h2>
                </div>
                <ul className="space-y-2">
                  {stage.items.map((item, j) => (
                    <li key={j} className="flex items-start gap-2 text-slate-900">
                      <CheckCircle size={18} weight={i === 0 ? "fill" : "bold"} className="mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
