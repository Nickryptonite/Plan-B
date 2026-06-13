import React from "react";
import { TopBar } from "../components/TopBar";
import { GoogleLogo, Sparkle } from "@phosphor-icons/react";

export default function Login() {
  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-[#FFFDF9]">
      <TopBar />
      <div className="relative overflow-hidden">
        <div className="blob" style={{ width: 320, height: 320, top: -100, right: -80, background: "#C4B5FD" }} />
        <div className="blob" style={{ width: 320, height: 320, bottom: -100, left: -80, background: "#FFDAB9" }} />
        <div className="sq-container px-4 py-16 md:py-24 relative flex items-center justify-center min-h-[calc(100vh-80px)]">
          <div className="sq-card bg-white p-8 md:p-10 max-w-md w-full">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#FACC15] border-2 border-slate-900 mb-4" style={{ boxShadow: "4px 4px 0px #0F172A" }}>
                <Sparkle size={32} weight="fill" />
              </div>
              <span className="sq-label text-[#FF5A5F]">Welcome</span>
              <h1 className="sq-h2 mt-2 mb-2">Start your side quest</h1>
              <p className="text-slate-600 text-sm">Sign in with Google. Pick a role. Start earning or posting in seconds.</p>
            </div>
            <button
              onClick={handleLogin}
              className="sq-btn sq-btn-secondary w-full"
              data-testid="google-login-btn"
            >
              <GoogleLogo size={20} weight="bold" /> Continue with Google
            </button>
            <div className="mt-6 text-xs text-slate-500 text-center">
              By continuing, you agree to our friendly use of cookies for keeping you signed in.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
