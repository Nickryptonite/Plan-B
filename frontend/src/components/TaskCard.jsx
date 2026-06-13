import React from "react";
import { CATEGORY_ACCENTS } from "../constants";
import { CurrencyInr, Calendar, Tag, User as UserIcon } from "@phosphor-icons/react";

const formatINR = (n) => `₹${Number(n).toLocaleString("en-IN")}`;

const STATUS_COLORS = {
  open: "#10B981",
  assigned: "#3B82F6",
  in_review: "#F59E0B",
  completed: "#0F172A",
  cancelled: "#94A3B8",
};

export const TaskCard = ({ task, onClick, action, actionLabel = "View", testId }) => {
  const accent = CATEGORY_ACCENTS[task.category] || "#FFDAB9";
  return (
    <div
      data-testid={testId || `task-card-${task.task_id}`}
      className="sq-card sq-card-hover p-5 flex flex-col gap-3 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="sq-badge" style={{ backgroundColor: accent }}>{task.category}</span>
        <span
          className="sq-badge text-white"
          style={{ backgroundColor: STATUS_COLORS[task.status] || "#0F172A" }}
        >
          {task.status.replace("_", " ")}
        </span>
      </div>
      <h3 className="sq-h3 leading-snug line-clamp-2">{task.title}</h3>
      <p className="text-sm text-slate-600 line-clamp-2">{task.description}</p>
      <div className="flex flex-wrap gap-2 pt-1">
        {(task.required_skills || []).slice(0, 3).map((s) => (
          <span key={s} className="sq-chip">
            <Tag size={12} weight="bold" /> {s}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between pt-3 mt-auto border-t-2 border-dashed border-slate-300">
        <div className="flex items-center gap-1 font-bold text-slate-900">
          <CurrencyInr size={18} weight="bold" />
          {formatINR(task.budget)}
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-600">
          <Calendar size={14} weight="bold" /> {task.deadline}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-slate-500">
          <UserIcon size={12} weight="bold" /> {task.client_name}
        </div>
        {action && (
          <button
            onClick={(e) => { e.stopPropagation(); action(task); }}
            className="sq-btn sq-btn-primary !px-3 !py-1.5 text-xs"
            data-testid={`task-action-${task.task_id}`}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
};

export { formatINR };
