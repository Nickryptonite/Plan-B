import React, { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { TopBar } from "../components/TopBar";
import { Modal, TrustBadge } from "./WorkerDashboard";
import { API, useAuth } from "../auth";
import { formatINR } from "../components/TaskCard";
import { Users, Briefcase, ClipboardText, Coins, ChartBar, EnvelopeSimple, ShieldCheck, Trophy } from "@phosphor-icons/react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell,
} from "recharts";

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

const MiniStat = ({ label, value, bg, testid }) => (
  <div className="border-2 border-slate-900 rounded-xl p-4" style={{ backgroundColor: bg, boxShadow: "3px 3px 0px #0F172A" }} data-testid={testid}>
    <div className="sq-label text-slate-700">{label}</div>
    <div className="text-2xl font-black mt-1" style={{ fontFamily: "Outfit" }}>{value}</div>
  </div>
);

const Funnel = ({ label, value, total, color }) => {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-semibold">{label}</span>
        <span className="text-slate-600">{value} <span className="text-xs">({pct.toFixed(0)}%)</span></span>
      </div>
      <div className="h-3 bg-slate-200 rounded-full border-2 border-slate-900 overflow-hidden">
        <div className="h-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
};

const COLORS = ["#FF5A5F", "#10B981", "#FACC15", "#C4B5FD", "#BAE6FD", "#FFDAB9", "#A7F3D0", "#F59E0B"];

export default function AdminDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [allTasks, setAllTasks] = useState([]);
  const [allSubs, setAllSubs] = useState([]);
  const [waitlist, setWaitlist] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [reviewSub, setReviewSub] = useState(null);

  const loadAll = async () => {
    try {
      const [s, an, u, t, sub, w, fb] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/analytics`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/tasks`),
        axios.get(`${API}/submissions`),
        axios.get(`${API}/admin/waitlist`),
        axios.get(`${API}/admin/feedback`),
      ]);
      setStats(s.data);
      setAnalytics(an.data);
      setUsers(u.data);
      setAllTasks(t.data);
      setAllSubs(sub.data);
      setWaitlist(w.data);
      setFeedback(fb.data);
    } catch (e) {
      toast.error("Could not load admin data");
    }
  };

  useEffect(() => { loadAll(); }, []);

  const markPaid = async (id) => {
    try {
      await axios.post(`${API}/submissions/${id}/mark-paid`);
      toast.success("Marked as paid");
      loadAll();
    } catch (e) {
      toast.error("Could not mark paid");
    }
  };

  const review = async (action, feedback) => {
    try {
      await axios.post(`${API}/submissions/${reviewSub.submission_id}/review`, { action, feedback });
      toast.success("Reviewed");
      setReviewSub(null);
      loadAll();
    } catch (e) { toast.error("Failed"); }
  };

  const updateRole = async (uid, role) => {
    try {
      await axios.post(`${API}/admin/users/${uid}/role`, { role });
      toast.success("Role updated");
      loadAll();
    } catch (e) { toast.error("Failed"); }
  };

  if (!stats) return <div className="min-h-screen flex items-center justify-center">Loading admin...</div>;

  const userRoleData = [
    { name: "Workers", value: stats.workers, color: "#10B981" },
    { name: "Clients", value: stats.clients, color: "#FF5A5F" },
    { name: "Other", value: Math.max(0, stats.total_users - stats.workers - stats.clients), color: "#FACC15" },
  ];

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar title="Admin" />
      <div className="sq-container px-4 md:px-8 py-8">
        <span className="sq-label text-[#FF5A5F]">Admin Control Room</span>
        <h1 className="sq-h2 mt-1 mb-6">Hi {user?.name?.split(" ")[0]}, here's the platform.</h1>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Stat label="Users" value={stats.total_users} icon={Users} color="#C4B5FD" />
          <Stat label="Tasks" value={stats.total_tasks} icon={Briefcase} color="#BAE6FD" />
          <Stat label="Pending Reviews" value={stats.pending_submissions} icon={ClipboardText} color="#FACC15" />
          <Stat label="Total Paid Out" value={formatINR(stats.total_paid)} icon={Coins} color="#A7F3D0" />
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {["overview", "analytics", "users", "tasks", "submissions", "payments", "waitlist", "feedback"].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`sq-btn !px-4 !py-2 text-sm ${tab === t ? "sq-btn-primary" : "sq-btn-secondary"}`}
              data-testid={`admin-tab-${t}`}
            >
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {tab === "analytics" && analytics && (
          <div className="space-y-6" data-testid="admin-analytics">
            <div>
              <span className="sq-label text-[#FF5A5F]">Platform metrics</span>
              <h3 className="sq-h3 mt-1 mb-3">Validation snapshot</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                <MiniStat label="Total Users" value={analytics.total_users} bg="#C4B5FD" testid="metric-total-users" />
                <MiniStat label="Workers" value={analytics.workers} bg="#A7F3D0" testid="metric-workers" />
                <MiniStat label="Clients" value={analytics.clients} bg="#FFDAB9" testid="metric-clients" />
                <MiniStat label="Total Tasks" value={analytics.total_tasks} bg="#BAE6FD" testid="metric-tasks" />
                <MiniStat label="Completion" value={`${analytics.completion_rate}%`} bg="#FACC15" testid="metric-completion" />
                <MiniStat label="Pending Reviews" value={analytics.pending_submissions} bg="#FCA5A5" testid="metric-pending" />
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              <div className="sq-card p-6">
                <h3 className="sq-h3 mb-4">Task funnel</h3>
                <Funnel label="Open" value={analytics.open_tasks} total={analytics.total_tasks} color="#10B981" />
                <Funnel label="Assigned" value={analytics.assigned_tasks} total={analytics.total_tasks} color="#3B82F6" />
                <Funnel label="In review" value={analytics.in_review_tasks} total={analytics.total_tasks} color="#F59E0B" />
                <Funnel label="Completed" value={analytics.completed_tasks} total={analytics.total_tasks} color="#0F172A" />
              </div>
              <div className="sq-card p-6">
                <h3 className="sq-h3 mb-4">Submission quality</h3>
                <Funnel label="Approved" value={analytics.approved_submissions} total={analytics.total_submissions} color="#10B981" />
                <Funnel label="Pending" value={analytics.pending_submissions} total={analytics.total_submissions} color="#FACC15" />
                <Funnel label="Rejected" value={analytics.rejected_submissions} total={analytics.total_submissions} color="#EF4444" />
                <div className="mt-4 pt-4 border-t-2 border-dashed border-slate-300 text-sm">
                  <span className="text-slate-500">Platform approval rate: </span>
                  <span className="font-black text-lg" style={{ fontFamily: "Outfit" }}>{analytics.submission_approval_rate}%</span>
                </div>
              </div>
            </div>

            <div className="sq-card p-6">
              <h3 className="sq-h3 mb-4 flex items-center gap-2"><Trophy size={20} weight="fill" className="text-[#FACC15]" /> Top reliable workers</h3>
              {(analytics.top_workers || []).length === 0 ? (
                <p className="text-slate-500 text-sm">No worker has completed a task yet.</p>
              ) : (
                <div className="space-y-2">
                  {analytics.top_workers.map((w, idx) => (
                    <div key={w.user_id} className="flex items-center gap-3 p-3 border-2 border-slate-900 rounded-lg bg-[#FFFDF9]" data-testid={`top-worker-${idx}`}>
                      <div className="w-8 h-8 rounded-full bg-[#FF5A5F] text-white border-2 border-slate-900 flex items-center justify-center font-black text-sm">{idx + 1}</div>
                      <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm truncate" style={{ fontFamily: "Outfit" }}>{w.name}</div>
                        <div className="text-xs text-slate-500">{w.tasks_completed} task{w.tasks_completed !== 1 ? "s" : ""} • {formatINR(w.earnings)} earned</div>
                      </div>
                      <TrustBadge level={w.trust_level} />
                      <div className="text-right">
                        <div className="text-xs text-slate-500">Score</div>
                        <div className="font-black text-lg" style={{ fontFamily: "Outfit" }}>{w.reliability_score}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "overview" && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="sq-card p-6">
              <h3 className="sq-h3 mb-4 flex items-center gap-2"><ChartBar size={20} weight="bold" /> Earnings by Category</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.by_category}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="category" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#FF5A5F" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="sq-card p-6">
              <h3 className="sq-h3 mb-4 flex items-center gap-2"><Users size={20} weight="bold" /> User Mix</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={userRoleData} dataKey="value" nameKey="name" outerRadius={100} label>
                    {userRoleData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.color} stroke="#0F172A" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="sq-card p-6 lg:col-span-2">
              <h3 className="sq-h3 mb-4">Quick stats</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><div className="sq-label text-slate-500">Open Tasks</div><div className="text-2xl font-black">{stats.open_tasks}</div></div>
                <div><div className="sq-label text-slate-500">Completed</div><div className="text-2xl font-black">{stats.completed_tasks}</div></div>
                <div><div className="sq-label text-slate-500">Submissions</div><div className="text-2xl font-black">{stats.total_submissions}</div></div>
                <div><div className="sq-label text-slate-500">Waitlist</div><div className="text-2xl font-black">{stats.waitlist_count}</div></div>
              </div>
            </div>
          </div>
        )}

        {tab === "users" && (
          <div className="sq-card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b-2 border-slate-900">
                <tr className="text-left">
                  <th className="p-3">Name</th><th className="p-3">Email</th><th className="p-3">Role</th>
                  <th className="p-3">Trust</th><th className="p-3">Score</th><th className="p-3">Done</th>
                  <th className="p-3">Earnings</th><th className="p-3">Spent</th><th className="p-3">Set role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.user_id} className="border-b border-slate-200" data-testid={`user-row-${u.user_id}`}>
                    <td className="p-3 font-semibold">{u.name}</td>
                    <td className="p-3 text-slate-600 text-xs">{u.email}</td>
                    <td className="p-3"><span className="sq-badge bg-[#FACC15] text-xs">{u.role || "—"}</span></td>
                    <td className="p-3">{u.role === "worker" ? <TrustBadge level={u.trust_level} /> : "—"}</td>
                    <td className="p-3">{u.role === "worker" ? <span className="font-bold">{u.reliability_score}</span> : "—"}</td>
                    <td className="p-3">{u.role === "worker" ? u.tasks_completed : "—"}</td>
                    <td className="p-3">{formatINR(u.earnings)}</td>
                    <td className="p-3">{formatINR(u.spent)}</td>
                    <td className="p-3">
                      <select value={u.role || ""} onChange={(e) => updateRole(u.user_id, e.target.value)} className="sq-input !p-1 text-xs" data-testid={`role-select-${u.user_id}`}>
                        <option value="">—</option>
                        <option value="worker">worker</option>
                        <option value="client">client</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "tasks" && (
          <div className="sq-card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b-2 border-slate-900">
                <tr className="text-left">
                  <th className="p-3">Title</th><th className="p-3">Category</th><th className="p-3">Client</th>
                  <th className="p-3">Budget</th><th className="p-3">Assigned</th><th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {allTasks.map((t) => (
                  <tr key={t.task_id} className="border-b border-slate-200">
                    <td className="p-3 font-semibold">{t.title}</td>
                    <td className="p-3">{t.category}</td>
                    <td className="p-3">{t.client_name}</td>
                    <td className="p-3">{formatINR(t.budget)}</td>
                    <td className="p-3">{t.assigned_to_name || "—"}</td>
                    <td className="p-3"><span className="sq-badge bg-white">{t.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "submissions" && (
          <div className="space-y-3">
            {allSubs.map((s) => (
              <div key={s.submission_id} className="sq-card p-5 flex flex-wrap justify-between gap-3 items-center">
                <div>
                  <div className="font-bold" style={{ fontFamily: "Outfit" }}>{s.task_title}</div>
                  <div className="text-xs text-slate-500">{s.worker_name} → {new Date(s.created_at).toLocaleDateString()}</div>
                </div>
                <div className="flex gap-2 items-center">
                  <span className="sq-badge bg-white">{s.status}</span>
                  {s.status === "pending" && (
                    <button onClick={() => setReviewSub(s)} className="sq-btn sq-btn-primary !px-3 !py-1.5 text-xs">Review</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "payments" && (
          <div className="space-y-3">
            {allSubs.filter((s) => s.status === "approved").map((s) => {
              const task = allTasks.find((t) => t.task_id === s.task_id);
              return (
                <div key={s.submission_id} className="sq-card p-5 flex flex-wrap justify-between gap-3 items-center" data-testid={`payment-${s.submission_id}`}>
                  <div>
                    <div className="font-bold">{s.task_title}</div>
                    <div className="text-xs text-slate-500">Pay {s.worker_name} • {formatINR(task?.budget || 0)}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`sq-badge ${s.payment_status === "paid" ? "bg-[#10B981] text-white" : "bg-[#FACC15]"}`}>{s.payment_status}</span>
                    {s.payment_status !== "paid" && (
                      <button onClick={() => markPaid(s.submission_id)} className="sq-btn sq-btn-success !px-3 !py-1.5 text-xs" data-testid={`mark-paid-${s.submission_id}`}>
                        Mark paid
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
            {allSubs.filter((s) => s.status === "approved").length === 0 && (
              <div className="sq-card p-10 text-center text-slate-600">No approved submissions awaiting payment.</div>
            )}
          </div>
        )}

        {tab === "waitlist" && (
          <div className="sq-card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b-2 border-slate-900">
                <tr className="text-left"><th className="p-3">Name</th><th className="p-3">Email</th><th className="p-3">Role</th><th className="p-3">Referrals</th><th className="p-3">Code</th><th className="p-3">Interest</th><th className="p-3">Joined</th></tr>
              </thead>
              <tbody>
                {waitlist.map((w) => (
                  <tr key={w.waitlist_id} className="border-b border-slate-200">
                    <td className="p-3 font-semibold">{w.name}</td>
                    <td className="p-3">{w.email}</td>
                    <td className="p-3"><span className="sq-badge bg-[#FACC15]">{w.role}</span></td>
                    <td className="p-3"><span className="font-black">{w.referrals_count || 0}</span></td>
                    <td className="p-3 font-mono text-xs">{w.referral_code || "—"}</td>
                    <td className="p-3 text-slate-600">{w.interest || "—"}</td>
                    <td className="p-3 text-xs text-slate-500">{new Date(w.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "feedback" && (
          <div className="space-y-3">
            {feedback.length === 0 ? (
              <div className="sq-card p-10 text-center text-slate-600">No feedback yet.</div>
            ) : feedback.map((f) => (
              <div key={f.feedback_id} className="sq-card p-5">
                <div className="flex items-center gap-2 mb-2 text-xs text-slate-500">
                  <EnvelopeSimple size={14} weight="bold" />
                  {f.name || "Anonymous"} {f.email && `· ${f.email}`} · {new Date(f.created_at).toLocaleDateString()}
                </div>
                <p className="text-slate-800">{f.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {reviewSub && (
        <Modal onClose={() => setReviewSub(null)}>
          <span className="sq-label text-[#FF5A5F]">Review</span>
          <h2 className="sq-h2 mt-1 mb-2">{reviewSub.task_title}</h2>
          <div className="text-sm text-slate-500 mb-3">{reviewSub.worker_name}</div>
          <p className="text-slate-800 whitespace-pre-line mb-3">{reviewSub.submission_text}</p>
          {reviewSub.submission_url && (
            <a href={reviewSub.submission_url} target="_blank" rel="noreferrer" className="text-[#FF5A5F] font-bold underline text-sm mb-3 block">View work →</a>
          )}
          <div className="flex gap-2 mt-4">
            <button onClick={() => review("reject", "")} className="sq-btn sq-btn-secondary flex-1">Reject</button>
            <button onClick={() => review("approve", "")} className="sq-btn sq-btn-success flex-1">Approve</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
