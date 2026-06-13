import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { TopBar } from "../components/TopBar";
import { TaskCard, formatINR } from "../components/TaskCard";
import { API, useAuth } from "../auth";
import { CATEGORIES } from "../constants";
import { Coins, CheckCircle, Briefcase, Sparkle, X, ArrowSquareOut, MagnifyingGlass, Trophy, Paperclip, ShieldCheck, ChartLineUp, Clock } from "@phosphor-icons/react";

const Stat = ({ label, value, icon: Icon, color = "#FACC15" }) => (
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

export default function WorkerDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("available");
  const [tasks, setTasks] = useState([]);
  const [assigned, setAssigned] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [badges, setBadges] = useState([]);
  const [category, setCategory] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("newest");
  const [selectedTask, setSelectedTask] = useState(null);
  const [submitOpen, setSubmitOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState({ submission_text: "", submission_url: "", file_path: "", file_name: "" });
  const [uploadingFile, setUploadingFile] = useState(false);
  const [submittingTask, setSubmittingTask] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    try {
      const [openRes, assignedRes, subsRes, badgesRes] = await Promise.all([
        axios.get(`${API}/tasks`, { params: { status: "open", category: category || undefined, q: query || undefined, sort } }),
        axios.get(`${API}/tasks`, { params: { mine: "assigned" } }),
        axios.get(`${API}/submissions`, { params: { mine: "worker" } }),
        axios.get(`${API}/badges`),
      ]);
      setTasks(openRes.data);
      setAssigned(assignedRes.data);
      setSubmissions(subsRes.data);
      setBadges(badgesRes.data);
    } catch (e) {
      toast.error("Could not load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, sort]);

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => loadAll(), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const apply = async (task) => {
    try {
      await axios.post(`${API}/tasks/${task.task_id}/apply`);
      toast.success("Applied! Task assigned to you 🎉");
      setSelectedTask(null);
      loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Could not apply");
    }
  };

  const openSubmit = (task) => {
    setSubmittingTask(task);
    setSubmitForm({ submission_text: "", submission_url: "", file_path: "", file_name: "" });
    setSubmitOpen(true);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      toast.error("File too large (max 25MB)");
      return;
    }
    setUploadingFile(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await axios.post(`${API}/upload`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setSubmitForm((f) => ({ ...f, file_path: res.data.path, file_name: res.data.filename }));
      toast.success("File uploaded");
    } catch (err) {
      toast.error("Upload failed");
    } finally {
      setUploadingFile(false);
    }
  };

  const submitWork = async () => {
    if (!submitForm.submission_text.trim()) return toast.error("Add a description of your work");
    try {
      await axios.post(`${API}/submissions`, {
        task_id: submittingTask.task_id,
        ...submitForm,
      });
      toast.success("Submitted for review!");
      setSubmitOpen(false);
      loadAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Could not submit");
    }
  };

  const completed = submissions.filter((s) => s.status === "approved").length;
  const pending = submissions.filter((s) => s.status === "pending").length;

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar title="Worker" />
      <div className="sq-container px-4 md:px-8 py-8">
        <div className="mb-6">
          <span className="sq-label text-[#FF5A5F]">Worker Dashboard</span>
          <h1 className="sq-h2 mt-1">Hey {user?.name?.split(" ")[0]} 👋</h1>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Stat label="Earnings" value={formatINR(user?.earnings || 0)} icon={Coins} color="#FACC15" />
          <Stat label="Completed" value={completed} icon={CheckCircle} color="#A7F3D0" />
          <Stat label="In Progress" value={assigned.length} icon={Briefcase} color="#BAE6FD" />
          <Stat label="Skills" value={user?.skills?.length || 0} icon={Sparkle} color="#C4B5FD" />
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {["available", "assigned", "history", "profile"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`sq-btn !px-4 !py-2 text-sm ${tab === t ? "sq-btn-primary" : "sq-btn-secondary"}`}
              data-testid={`worker-tab-${t}`}
            >
              {t === "available" ? "Available" : t === "assigned" ? "Assigned" : t === "history" ? "History" : "Profile"}
            </button>
          ))}
        </div>

        {tab === "available" && (
          <>
            <div className="flex flex-col md:flex-row gap-3 mb-4">
              <div className="relative flex-1">
                <MagnifyingGlass size={18} weight="bold" className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  placeholder="Search tasks by title, description or category..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="sq-input pl-10"
                  data-testid="worker-search-input"
                />
              </div>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="sq-input md:w-56"
                data-testid="worker-sort-select"
              >
                <option value="newest">Newest first</option>
                <option value="budget_desc">Budget: high → low</option>
                <option value="budget_asc">Budget: low → high</option>
                <option value="deadline">Deadline soonest</option>
              </select>
            </div>
            <div className="flex flex-wrap gap-2 mb-5">
              <button onClick={() => setCategory("")} className={`sq-chip ${category === "" ? "bg-[#FACC15]" : ""}`} data-testid="filter-all">All</button>
              {CATEGORIES.map((c) => (
                <button key={c} onClick={() => setCategory(c)} className={`sq-chip ${category === c ? "bg-[#FACC15]" : ""}`} data-testid={`filter-${c.toLowerCase().replace(/\s+/g, "-")}`}>
                  {c}
                </button>
              ))}
            </div>
            {loading ? <p>Loading...</p> : tasks.length === 0 ? (
              <div className="sq-card p-10 text-center" data-testid="empty-available">
                <MagnifyingGlass size={40} weight="bold" className="mx-auto mb-3 text-slate-400" />
                <h3 className="sq-h3 mb-2">No matching tasks</h3>
                <p className="text-slate-600 mb-4">
                  {query || category ? "Try clearing your search or category filter." : "New tasks drop daily — check back tomorrow."}
                </p>
                {(query || category) && (
                  <button onClick={() => { setQuery(""); setCategory(""); }} className="sq-btn sq-btn-primary !px-4 !py-2 text-sm" data-testid="clear-filters-btn">
                    Clear filters
                  </button>
                )}
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {tasks.map((t) => (
                  <TaskCard key={t.task_id} task={t} onClick={() => setSelectedTask(t)} action={apply} actionLabel="Apply" />
                ))}
              </div>
            )}
          </>
        )}

        {tab === "assigned" && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {assigned.length === 0 ? (
              <div className="sq-card p-10 text-center col-span-full" data-testid="empty-assigned">
                <Briefcase size={40} weight="bold" className="mx-auto mb-3 text-slate-400" />
                <h3 className="sq-h3 mb-2">No active quests yet</h3>
                <p className="text-slate-600 mb-4">Head to the Available tab and apply to your first task!</p>
                <button onClick={() => setTab("available")} className="sq-btn sq-btn-primary !px-4 !py-2 text-sm" data-testid="goto-available-btn">
                  Browse tasks →
                </button>
              </div>
            ) : (
              assigned.map((t) => (
                <TaskCard
                  key={t.task_id}
                  task={t}
                  action={openSubmit}
                  actionLabel={t.status === "in_review" ? "In Review" : "Submit Work"}
                  onClick={() => setSelectedTask(t)}
                />
              ))
            )}
          </div>
        )}

        {tab === "history" && (
          <div className="space-y-3">
            {submissions.length === 0 ? (
              <div className="sq-card p-10 text-center" data-testid="empty-history">
                <CheckCircle size={40} weight="bold" className="mx-auto mb-3 text-slate-400" />
                <h3 className="sq-h3 mb-2">No submissions yet</h3>
                <p className="text-slate-600">Once you submit work for a task, it'll show up here.</p>
              </div>
            ) : (
              submissions.map((s) => (
                <div key={s.submission_id} className="sq-card p-5 flex flex-wrap gap-4 justify-between items-center" data-testid={`submission-${s.submission_id}`}>
                  <div>
                    <div className="font-bold" style={{ fontFamily: "Outfit" }}>{s.task_title}</div>
                    <div className="text-xs text-slate-500 mt-1">{new Date(s.created_at).toLocaleDateString()}</div>
                    {s.feedback && <div className="text-sm text-slate-700 mt-2 italic">"{s.feedback}"</div>}
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className={`sq-badge ${s.status === "approved" ? "bg-[#A7F3D0]" : s.status === "rejected" ? "bg-[#FCA5A5]" : "bg-[#FACC15]"}`}>
                      {s.status}
                    </span>
                    <span className={`sq-badge ${s.payment_status === "paid" ? "bg-[#10B981] text-white" : "bg-white"}`}>
                      {s.payment_status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === "profile" && (
          <div className="space-y-6 max-w-3xl">
            <div className="sq-card p-6">
              <div className="flex items-center gap-4 mb-5">
                {user?.picture ? (
                  <img src={user.picture} alt={user.name} className="w-20 h-20 rounded-full border-2 border-slate-900" />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-[#FACC15] border-2 border-slate-900 flex items-center justify-center text-3xl font-black">
                    {user?.name?.[0]}
                  </div>
                )}
                <div>
                  <h3 className="sq-h3">{user?.name}</h3>
                  <p className="text-slate-600 text-sm">{user?.email}</p>
                  {user?.trust_level && <TrustBadge level={user.trust_level} />}
                </div>
              </div>
              {user?.bio && <p className="text-slate-700 mb-4">{user.bio}</p>}
              <span className="sq-label text-slate-500">Your skills</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {(user?.skills || []).length === 0 ? (
                  <span className="text-sm text-slate-500">No skills selected yet.</span>
                ) : (
                  user.skills.map((s) => <span key={s} className="sq-chip bg-[#A7F3D0]">{s}</span>)
                )}
              </div>
            </div>

            <ReliabilityCard user={user} />

            <div className="sq-card p-6">
              <span className="sq-label text-slate-500">Skill badges</span>
              <div className="grid sm:grid-cols-2 gap-3 mt-3">
                {badges.length === 0 ? (
                  <div className="text-sm text-slate-500 col-span-full">
                    No badges yet. Complete your first task to unlock your first skill badge!
                  </div>
                ) : (
                  badges.map((b) => (
                    <div key={b.category} className="sq-card p-4 bg-[#FFFDF9]" data-testid={`badge-${b.category.toLowerCase().replace(/\s+/g, "-")}`}>
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl border-2 border-slate-900 bg-[#FACC15] flex items-center justify-center">
                          <Trophy size={24} weight="fill" />
                        </div>
                        <div className="flex-1">
                          <div className="font-bold text-sm" style={{ fontFamily: "Outfit" }}>{b.category}</div>
                          <div className="text-xs text-slate-600">Level {b.level} • {b.completed_count} task{b.completed_count > 1 ? "s" : ""}</div>
                        </div>
                      </div>
                      <div className="mt-3 h-2 bg-slate-200 rounded-full border-2 border-slate-900 overflow-hidden">
                        <div className="h-full bg-[#FF5A5F]" style={{ width: `${Math.min(100, (b.completed_count % 5) * 20 + 20)}%` }} />
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{formatINR(b.total_earned || 0)} earned</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <Modal onClose={() => setSelectedTask(null)}>
          <span className="sq-badge bg-[#FACC15]">{selectedTask.category}</span>
          <h2 className="sq-h2 mt-3 mb-2">{selectedTask.title}</h2>
          <p className="text-slate-700 mb-4 whitespace-pre-line">{selectedTask.description}</p>
          <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
            <div><span className="sq-label text-slate-500">Budget</span><div className="font-bold">{formatINR(selectedTask.budget)}</div></div>
            <div><span className="sq-label text-slate-500">Deadline</span><div className="font-bold">{selectedTask.deadline}</div></div>
            <div><span className="sq-label text-slate-500">Client</span><div className="font-bold">{selectedTask.client_name}</div></div>
            <div><span className="sq-label text-slate-500">Status</span><div className="font-bold">{selectedTask.status}</div></div>
          </div>
          {selectedTask.status === "open" && (
            <button onClick={() => apply(selectedTask)} className="sq-btn sq-btn-primary w-full" data-testid="modal-apply-btn">
              Apply for this quest
            </button>
          )}
          {selectedTask.assigned_to === user?.user_id && selectedTask.status === "assigned" && (
            <button onClick={() => { setSelectedTask(null); openSubmit(selectedTask); }} className="sq-btn sq-btn-primary w-full" data-testid="modal-submit-btn">
              Submit work
            </button>
          )}
        </Modal>
      )}

      {/* Submit Modal */}
      {submitOpen && (
        <Modal onClose={() => setSubmitOpen(false)}>
          <span className="sq-label text-[#FF5A5F]">Submit Work</span>
          <h2 className="sq-h2 mt-1 mb-4">{submittingTask?.title}</h2>
          <textarea
            placeholder="Describe what you completed..."
            value={submitForm.submission_text}
            onChange={(e) => setSubmitForm({ ...submitForm, submission_text: e.target.value })}
            className="sq-input min-h-[120px] mb-3"
            data-testid="submit-text-input"
          />
          <input
            placeholder="Link to your work (Google Drive, Docs, Figma...)"
            value={submitForm.submission_url}
            onChange={(e) => setSubmitForm({ ...submitForm, submission_url: e.target.value })}
            className="sq-input mb-3"
            data-testid="submit-url-input"
          />
          <label className="block mb-4">
            <span className="sq-label text-slate-500 block mb-2">Attach a file (optional, max 25MB)</span>
            <div className="sq-card p-4 bg-[#FFFDF9] cursor-pointer hover:bg-white transition-colors">
              <input
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                data-testid="submit-file-input"
                disabled={uploadingFile}
              />
              <div className="flex items-center gap-2 text-sm">
                <Paperclip size={16} weight="bold" />
                <span className="font-semibold">
                  {uploadingFile ? "Uploading..." : submitForm.file_name ? submitForm.file_name : "Click to upload a file"}
                </span>
              </div>
            </div>
          </label>
          <button onClick={submitWork} disabled={uploadingFile} className="sq-btn sq-btn-primary w-full" data-testid="submit-work-btn">
            Submit for review <ArrowSquareOut size={18} weight="bold" />
          </button>
        </Modal>
      )}
    </div>
  );
}

export const Modal = ({ children, onClose }) => (
  <div className="fixed inset-0 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
    <div className="sq-card bg-white p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto relative" onClick={(e) => e.stopPropagation()}>
      <button onClick={onClose} className="absolute top-4 right-4 w-8 h-8 rounded-full border-2 border-slate-900 flex items-center justify-center bg-white" data-testid="modal-close">
        <X size={16} weight="bold" />
      </button>
      {children}
    </div>
  </div>
);

const TRUST_STYLES = {
  new:      { bg: "#E2E8F0", label: "New",      icon: Sparkle },
  rising:   { bg: "#BAE6FD", label: "Rising",   icon: ChartLineUp },
  trusted:  { bg: "#A7F3D0", label: "Trusted",  icon: ShieldCheck },
  verified: { bg: "#FACC15", label: "Verified", icon: ShieldCheck },
};

export const TrustBadge = ({ level, size = "sm" }) => {
  const cfg = TRUST_STYLES[level] || TRUST_STYLES.new;
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 sq-badge mt-1 ${size === "lg" ? "text-sm px-3 py-1.5" : ""}`}
      style={{ backgroundColor: cfg.bg }}
      data-testid={`trust-badge-${level}`}
    >
      <Icon size={size === "lg" ? 16 : 12} weight="fill" /> {cfg.label}
    </span>
  );
};

export const ReliabilityCard = ({ user }) => {
  const score = user?.reliability_score ?? 0;
  const approval = user?.approval_rate;
  const onTime = user?.on_time_rate;
  return (
    <div className="sq-card p-6" data-testid="reliability-card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <span className="sq-label text-[#FF5A5F]">Reliability</span>
          <h3 className="sq-h3 mt-1">Your trust score</h3>
        </div>
        <TrustBadge level={user?.trust_level || "new"} size="lg" />
      </div>
      <div className="flex items-end gap-2 mb-2">
        <span className="text-5xl font-black" style={{ fontFamily: "Outfit" }} data-testid="reliability-score">{score}</span>
        <span className="text-slate-500 pb-2">/ 100</span>
      </div>
      <div className="h-3 bg-slate-200 rounded-full border-2 border-slate-900 overflow-hidden mb-5">
        <div className="h-full bg-[#10B981]" style={{ width: `${score}%` }} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <Metric label="Accepted" value={user?.tasks_accepted || 0} icon={Briefcase} />
        <Metric label="Completed" value={user?.tasks_completed || 0} icon={CheckCircle} />
        <Metric label="Approval" value={approval !== null && approval !== undefined ? `${approval}%` : "—"} icon={Trophy} />
        <Metric label="On-time" value={onTime !== null && onTime !== undefined ? `${onTime}%` : "—"} icon={Clock} />
      </div>
    </div>
  );
};

const Metric = ({ label, value, icon: Icon }) => (
  <div className="border-2 border-slate-900 rounded-lg p-3 bg-[#FFFDF9]">
    <Icon size={16} weight="bold" className="mx-auto mb-1" />
    <div className="text-xs text-slate-500 uppercase font-bold">{label}</div>
    <div className="font-black text-lg" style={{ fontFamily: "Outfit" }}>{value}</div>
  </div>
);
