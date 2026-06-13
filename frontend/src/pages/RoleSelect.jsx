import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { API, useAuth } from "../auth";
import { TopBar } from "../components/TopBar";
import { CATEGORIES } from "../constants";
import { Briefcase, GraduationCap, CheckCircle } from "@phosphor-icons/react";

export default function RoleSelect() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState(null);
  const [skills, setSkills] = useState([]);
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Please <a href="/login" className="underline font-bold">sign in</a> first.</p>
      </div>
    );
  }
  if (user.role) {
    navigate(`/${user.role}`);
    return null;
  }

  const toggleSkill = (s) => {
    setSkills((arr) => (arr.includes(s) ? arr.filter((x) => x !== s) : [...arr, s]));
  };

  const submit = async () => {
    if (!role) return toast.error("Pick a role to continue");
    setSaving(true);
    try {
      await axios.post(`${API}/auth/role`, { role, skills, bio });
      await refresh();
      navigate(`/${role}`);
      toast.success(`Welcome aboard! You're set up as a ${role}.`);
    } catch (e) {
      toast.error("Could not save. Try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar />
      <div className="sq-container px-4 py-10 max-w-3xl">
        <span className="sq-label text-[#FF5A5F]">Step 1 of 1</span>
        <h1 className="sq-h2 mt-2 mb-2">Hey {user.name?.split(" ")[0]}, what brings you here?</h1>
        <p className="text-slate-600 mb-8">Pick how you want to use SideQuest. You can change this later.</p>

        <div className="grid sm:grid-cols-2 gap-5 mb-8">
          <button
            onClick={() => setRole("worker")}
            className={`sq-card p-6 text-left ${role === "worker" ? "bg-[#A7F3D0]" : "bg-white"}`}
            data-testid="role-worker-btn"
          >
            <GraduationCap size={32} weight="bold" className="mb-3" />
            <h3 className="font-bold text-lg mb-1" style={{ fontFamily: "Outfit" }}>I'm a Worker</h3>
            <p className="text-sm text-slate-700">Student, fresher, or aspirant — I want to earn from micro-tasks.</p>
            {role === "worker" && <CheckCircle size={24} weight="fill" className="text-[#10B981] mt-3" />}
          </button>
          <button
            onClick={() => setRole("client")}
            className={`sq-card p-6 text-left ${role === "client" ? "bg-[#C4B5FD]" : "bg-white"}`}
            data-testid="role-client-btn"
          >
            <Briefcase size={32} weight="bold" className="mb-3" />
            <h3 className="font-bold text-lg mb-1" style={{ fontFamily: "Outfit" }}>I'm a Client</h3>
            <p className="text-sm text-slate-700">Business, creator, or agency — I want to post tasks and hire.</p>
            {role === "client" && <CheckCircle size={24} weight="fill" className="text-[#10B981] mt-3" />}
          </button>
        </div>

        {role === "worker" && (
          <div className="sq-card p-6 mb-6">
            <h3 className="font-bold mb-3" style={{ fontFamily: "Outfit" }}>Pick your skills</h3>
            <div className="flex flex-wrap gap-2 mb-4">
              {CATEGORIES.map((s) => (
                <button
                  key={s}
                  onClick={() => toggleSkill(s)}
                  className={`sq-chip ${skills.includes(s) ? "bg-[#FACC15]" : ""}`}
                  data-testid={`skill-chip-${s.toLowerCase().replace(/\s+/g, "-")}`}
                >
                  {s}
                </button>
              ))}
            </div>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="A 1-line bio (college, year, what you're great at)"
              className="sq-input"
              data-testid="bio-input"
            />
          </div>
        )}

        {role === "client" && (
          <div className="sq-card p-6 mb-6">
            <h3 className="font-bold mb-3" style={{ fontFamily: "Outfit" }}>About your business (optional)</h3>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about your business, what kind of tasks you'll post"
              className="sq-input"
              data-testid="bio-input"
            />
          </div>
        )}

        <button
          onClick={submit}
          disabled={saving || !role}
          className="sq-btn sq-btn-primary"
          data-testid="role-submit-btn"
        >
          {saving ? "Setting up..." : "Continue to dashboard"}
        </button>
      </div>
    </div>
  );
}
