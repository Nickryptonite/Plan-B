import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { TopBar } from "../components/TopBar";
import { TaskCard, formatINR } from "../components/TaskCard";
import { API, useAuth } from "../auth";
import { CATEGORIES } from "../constants";
import { Coins, CheckCircle, Briefcase, Sparkle, X, ArrowSquareOut } from "@phosphor-icons/react";

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
  const [category, setCategory] = useState("");
  const [selectedTask, setSelectedTask] = useState(null);
  const [submitOpen, setSubmitOpen] = useState(false);
  const [submitForm, setSubmitForm] = useState({ submission_text: "", submission_url: "" });
  const [submittingTask, setSubmittingTask] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    try {
      const [openRes, assignedRes, subsRes] = await Promise.all([
        axios.get(`${API}/tasks`, { params: { status: "open", category: category || undefined } }),
        axios.get(`${API}/tasks`, { params: { mine: "assigned" } }),
        axios.get(`${API}/submissions`, { params: { mine: "worker" } }),
      ]);
      setTasks(openRes.data);
      setAssigned(assignedRes.data);
      setSubmissions(subsRes.data);
    } catch (e) {
      toast.error("Could not load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); /* eslint-disable-next-line */ }, [category]);

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
    setSubmitForm({ submission_text: "", submission_url: "" });
    setSubmitOpen(true);
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
            <div className="flex flex-wrap gap-2 mb-5">
              <button onClick={() => setCategory("")} className={`sq-chip ${category === "" ? "bg-[#FACC15]" : ""}`} data-testid="filter-all">All</button>
              {CATEGORIES.map((c) => (
                <button key={c} onClick={() => setCategory(c)} className={`sq-chip ${category === c ? "bg-[#FACC15]" : ""}`} data-testid={`filter-${c.toLowerCase().replace(/\s+/g, "-")}`}>
                  {c}
                </button>
              ))}
            </div>
            {loading ? <p>Loading...</p> : tasks.length === 0 ? (
              <div className="sq-card p-10 text-center text-slate-600">No open tasks here yet. Check back soon!</div>
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
              <div className="sq-card p-10 text-center text-slate-600 col-span-full">No tasks assigned yet. Apply for one from the Available tab!</div>
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
              <div className="sq-card p-10 text-center text-slate-600">No submissions yet. Finish a task!</div>
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
          <div className="sq-card p-6 max-w-2xl">
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
              </div>
            </div>
            {user?.bio && <p className="text-slate-700 mb-4">{user.bio}</p>}
            <span className="sq-label text-slate-500">Your skills</span>
            <div className="flex flex-wrap gap-2 mt-2 mb-5">
              {(user?.skills || []).length === 0 ? (
                <span className="text-sm text-slate-500">No skills selected yet.</span>
              ) : (
                user.skills.map((s) => <span key={s} className="sq-chip bg-[#A7F3D0]">{s}</span>)
              )}
            </div>
            <span className="sq-label text-slate-500">Skill badges</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {completed === 0 ? (
                <span className="text-sm text-slate-500">Complete tasks to unlock badges!</span>
              ) : (
                <span className="sq-badge bg-[#FACC15]">🏆 First Quest Complete</span>
              )}
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
            className="sq-input mb-4"
            data-testid="submit-url-input"
          />
          <button onClick={submitWork} className="sq-btn sq-btn-primary w-full" data-testid="submit-work-btn">
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
