import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API, useAuth } from "../auth";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) {
      navigate("/login");
      return;
    }
    const sessionId = match[1];

    (async () => {
      try {
        const res = await axios.post(
          `${API}/auth/session`,
          { session_id: sessionId },
          { withCredentials: true }
        );
        setUser(res.data.user);
        // Clean URL fragment
        window.history.replaceState(null, "", window.location.pathname);

        const role = res.data.user.role;
        if (role === "admin") navigate("/admin", { state: { user: res.data.user } });
        else if (role === "client") navigate("/client", { state: { user: res.data.user } });
        else if (role === "worker") navigate("/worker", { state: { user: res.data.user } });
        else navigate("/select-role", { state: { user: res.data.user } });
      } catch (e) {
        setError("Sign-in failed. Try again.");
        setTimeout(() => navigate("/login"), 2000);
      }
    })();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FFFDF9]">
      <div className="sq-card p-8 text-center">
        <div className="w-12 h-12 mx-auto border-4 border-slate-900 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="font-bold" style={{ fontFamily: "Outfit" }}>
          {error || "Loading your dashboard..."}
        </p>
      </div>
    </div>
  );
}
