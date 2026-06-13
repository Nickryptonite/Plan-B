import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { TopBar } from "../components/TopBar";
import { TaskCard, formatINR } from "../components/TaskCard";
import { Modal } from "./WorkerDashboard";
import { API, useAuth } from "../auth";
import { CATEGORIES } from "../constants";
import { Briefcase, CheckCircle, CurrencyInr, ListPlus, ClipboardText } from "@phosphor-icons/react";

const Stat = ({ label, value, icon: Icon, color }) => (
  <div className="sq-card p-5">
    <div className="flex items-center justify-between mb-2">
      <span className="sq-label text-slate-500">{label}</span>
      <div className="w-9 h-9 rounded-lg border-2 border-slate-900 flex items-center justify-center" style={{ backgroundColor: color }}>
        <Icon size={18} weight="bold" />
      </div>
    </div>
    <div className="text-3xl font-black" style={{ fontFamily: "Outfit" }}>{value}</div>
  </div>
);

export default function ClientDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("active");
  const [tasks, setTasks] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [postOpen, setPostOpen] = useState(false);
  const [reviewSub, setReviewSub] = useState(null);
  const [form, setForm] = useState({
    title: "", description: "", category: "Data Entry", budget: 1000, deadline: "",
    required_skills: [],
  });
  const [saving, setSaving] = useState(false);

  const loadAll = async () => {
    try {
      const [tRes, sRes] = await Promise.all([
        axios.get(`${API}/tasks`, { params: { mine: "posted" } }),
        axios.get(`${API}/submissions`, { params: { mine: "client" } }),
      ]);
      setTasks(tRes.data);
      setSubmissions(sRes.data);
    } catch (e) {
      toast.error("Could not load data");
    }
  };

  useEffect(() => { loadAll(); }, []);

  const postTask = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.post(`${API}/tasks`, { ...form, budget: Number(form.budget) });
      toast.success("Task posted! Workers can now apply.");
      setPostOpen(false);
      setForm({ title: "", description: "", category: "Data Entry", budget: 1000, deadline: "", required_skills: [] });
      loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Could not post");
    } finally {
      setSaving(false);
    }
  };

  const review = async (action, feedback) => {
    try {
      await axios.post(`${API}/submissions/${reviewSub.submission_id}/review`, { action, feedback });
      toast.success(action === "approve" ? "Approved! 🎉" : "Rejected. Worker can resubmit.");
      setReviewSub(null);
      loadAll();
    } catch (e) {
      toast.error("Could not review");
    }
  };

  const toggleSkill = (s) => {
    setForm((f) => ({
      ...f,
      required_skills: f.required_skills.includes(s)
        ? f.required_skills.filter((x) => x !== s)
        : [...f.required_skills, s],
    }));
  };

  const active = tasks.filter((t) => t.status !== "completed");
  const completed = tasks.filter((t) => t.status === "completed");
  const pendingSubs = submissions.filter((s) => s.status === "pending");

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar title="Client" />
      <div className="sq-container px-4 md:px-8 py-8">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div>
            <span className="sq-label text-[#FF5A5F]">Client Dashboard</span>
            <h1 className="sq-h2 mt-1">Welcome, {user?.name?.split(" ")[0]} ✦</h1>
          </div>
          <button onClick={() => setPostOpen(true)} className="sq-btn sq-btn-primary" data-testid="post-task-btn">
            <ListPlus size={18} weight="bold" /> Post a task
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Stat label="Active Tasks" value={active.length} icon={Briefcase} color="#BAE6FD" />
          <Stat label="Completed" value={completed.length} icon={CheckCircle} color="#A7F3D0" />
          <Stat label="Pending Reviews" value={pendingSubs.length} icon={ClipboardText} color="#FACC15" />
          <Stat label="Spent" value={formatINR(user?.spent || 0)} icon={CurrencyInr} color="#C4B5FD" />
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {["active", "review", "completed"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`sq-btn !px-4 !py-2 text-sm ${tab === t ? "sq-btn-primary" : "sq-btn-secondary"}`}
              data-testid={`client-tab-${t}`}
            >
              {t === "active" ? "Active" : t === "review" ? `Review (${pendingSubs.length})` : "Completed"}
            </button>
          ))}
        </div>

        {tab === "active" && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {active.length === 0 ? (
              <div className="sq-card p-10 text-center text-slate-600 col-span-full">
                No active tasks. Post one to get started!
              </div>
            ) : active.map((t) => <TaskCard key={t.task_id} task={t} />)}
          </div>
        )}

        {tab === "review" && (
          <div className="space-y-3">
            {pendingSubs.length === 0 ? (
              <div className="sq-card p-10 text-center text-slate-600">No submissions to review right now.</div>
            ) : pendingSubs.map((s) => (
              <div key={s.submission_id} className="sq-card p-5" data-testid={`review-sub-${s.submission_id}`}>
                <div className="flex flex-wrap justify-between gap-3 mb-2">
                  <div>
                    <div className="font-bold" style={{ fontFamily: "Outfit" }}>{s.task_title}</div>
                    <div className="text-xs text-slate-500 mt-1">by {s.worker_name} • {new Date(s.created_at).toLocaleDateString()}</div>
                  </div>
                  <button onClick={() => setReviewSub(s)} className="sq-btn sq-btn-primary !px-4 !py-2 text-sm" data-testid={`open-review-${s.submission_id}`}>
                    Review
                  </button>
                </div>
                <p className="text-sm text-slate-700 line-clamp-2">{s.submission_text}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "completed" && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {completed.length === 0 ? (
              <div className="sq-card p-10 text-center text-slate-600 col-span-full">No completed tasks yet.</div>
            ) : completed.map((t) => <TaskCard key={t.task_id} task={t} />)}
          </div>
        )}
      </div>

      {/* POST TASK MODAL */}
      {postOpen && (
        <Modal onClose={() => setPostOpen(false)}>
          <span className="sq-label text-[#FF5A5F]">New Task</span>
          <h2 className="sq-h2 mt-1 mb-4">Post a quest</h2>
          <form onSubmit={postTask} className="space-y-3">
            <input required placeholder="Task title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="sq-input" data-testid="task-title-input" />
            <textarea required placeholder="What needs to be done? Be specific." value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="sq-input min-h-[100px]" data-testid="task-description-input" />
            <div className="grid grid-cols-2 gap-3">
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="sq-input" data-testid="task-category-select">
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
              <input required type="number" min="1" placeholder="Budget ₹" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} className="sq-input" data-testid="task-budget-input" />
            </div>
            <input required type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} className="sq-input" data-testid="task-deadline-input" />
            <div>
              <span className="sq-label text-slate-500">Required skills</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {CATEGORIES.map((s) => (
                  <button type="button" key={s} onClick={() => toggleSkill(s)} className={`sq-chip ${form.required_skills.includes(s) ? "bg-[#FACC15]" : ""}`} data-testid={`task-skill-${s.toLowerCase().replace(/\s+/g, "-")}`}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <button type="submit" disabled={saving} className="sq-btn sq-btn-primary w-full" data-testid="submit-task-btn">
              {saving ? "Posting..." : "Post task"}
            </button>
          </form>
        </Modal>
      )}

      {/* REVIEW SUB MODAL */}
      {reviewSub && (
        <ReviewModal sub={reviewSub} onClose={() => setReviewSub(null)} onReview={review} />
      )}
    </div>
  );
}

const ReviewModal = ({ sub, onClose, onReview }) => {
  const [feedback, setFeedback] = useState("");
  return (
    <Modal onClose={onClose}>
      <span className="sq-label text-[#FF5A5F]">Review submission</span>
      <h2 className="sq-h2 mt-1 mb-2">{sub.task_title}</h2>
      <div className="text-sm text-slate-500 mb-3">Submitted by {sub.worker_name}</div>
      <div className="sq-card p-4 bg-[#FFFDF9] mb-4">
        <p className="text-slate-800 whitespace-pre-line">{sub.submission_text}</p>
        {sub.submission_url && (
          <a href={sub.submission_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[#FF5A5F] font-bold mt-3 text-sm underline">
            View work →
          </a>
        )}
      </div>
      <textarea placeholder="Feedback (optional)" value={feedback} onChange={(e) => setFeedback(e.target.value)} className="sq-input min-h-[80px] mb-3" data-testid="review-feedback-input" />
      <div className="flex gap-2">
        <button onClick={() => onReview("reject", feedback)} className="sq-btn sq-btn-secondary flex-1" data-testid="review-reject-btn">Reject</button>
        <button onClick={() => onReview("approve", feedback)} className="sq-btn sq-btn-success flex-1" data-testid="review-approve-btn">Approve & Pay</button>
      </div>
    </Modal>
  );
};
