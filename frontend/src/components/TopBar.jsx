import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, API } from "../auth";
import { SignOut, User as UserIcon, House } from "@phosphor-icons/react";

export const TopBar = ({ title }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const dashHref = user?.role === "admin" ? "/admin" : user?.role === "client" ? "/client" : "/worker";

  return (
    <header className="border-b-2 border-slate-900 bg-white sticky top-0 z-40">
      <div className="sq-container flex items-center justify-between px-4 md:px-8 py-3">
        <Link to={user ? dashHref : "/"} className="flex items-center gap-2" data-testid="topbar-logo">
          <div className="w-9 h-9 rounded-lg bg-[#FF5A5F] border-2 border-slate-900 flex items-center justify-center font-black text-white" style={{ boxShadow: "3px 3px 0px #0F172A" }}>
            S
          </div>
          <span className="font-black text-lg tracking-tight" style={{ fontFamily: "Outfit" }}>
            SideQuest
          </span>
        </Link>
        <div className="flex items-center gap-2 md:gap-3">
          {title && <span className="hidden md:inline sq-label text-slate-500">{title}</span>}
          {user ? (
            <>
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 border-2 border-slate-900 rounded-full bg-[#FFFDF9]">
                {user.picture ? (
                  <img src={user.picture} alt={user.name} className="w-6 h-6 rounded-full border border-slate-900" />
                ) : (
                  <UserIcon size={16} weight="bold" />
                )}
                <span className="text-sm font-semibold" data-testid="topbar-username">{user.name}</span>
                {user.role && <span className="sq-badge bg-[#FACC15]">{user.role}</span>}
              </div>
              <button
                onClick={logout}
                className="sq-btn sq-btn-secondary !px-3 !py-2 text-sm"
                data-testid="logout-btn"
              >
                <SignOut size={16} weight="bold" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/" className="sq-btn sq-btn-secondary !px-3 !py-2 text-sm" data-testid="topbar-home-btn">
                <House size={16} weight="bold" /> Home
              </Link>
              <button
                onClick={() => navigate("/login")}
                className="sq-btn sq-btn-primary !px-4 !py-2 text-sm"
                data-testid="topbar-login-btn"
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
