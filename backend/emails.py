"""Resend email helper. No-op gracefully when RESEND_API_KEY is missing."""
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def _wrap(title: str, body_html: str, cta_label: str = None, cta_url: str = None) -> str:
    cta_block = ""
    if cta_label and cta_url:
        cta_block = f"""
        <table cellspacing="0" cellpadding="0" style="margin: 24px 0;"><tr><td>
          <a href="{cta_url}" style="display:inline-block;padding:14px 28px;background:#FF5A5F;color:#fff;text-decoration:none;font-weight:800;border:2px solid #0F172A;border-radius:12px;box-shadow:4px 4px 0px #0F172A;font-family:Arial,sans-serif;">{cta_label}</a>
        </td></tr></table>
        """
    return f"""
    <html><body style="margin:0;padding:0;background:#FFFDF9;font-family:Arial,Helvetica,sans-serif;color:#0F172A;">
    <table width="100%" cellspacing="0" cellpadding="0" style="background:#FFFDF9;padding:32px 16px;"><tr><td align="center">
      <table width="600" cellspacing="0" cellpadding="0" style="background:#fff;border:2px solid #0F172A;border-radius:16px;box-shadow:4px 4px 0px #0F172A;">
        <tr><td style="padding:32px;">
          <div style="font-size:24px;font-weight:900;margin-bottom:8px;">
            <span style="display:inline-block;background:#FF5A5F;color:#fff;padding:4px 10px;border-radius:8px;border:2px solid #0F172A;">S</span>
            &nbsp;SideQuest
          </div>
          <h1 style="font-size:24px;font-weight:900;margin:24px 0 8px;">{title}</h1>
          <div style="font-size:15px;line-height:1.6;color:#475569;">{body_html}</div>
          {cta_block}
          <div style="margin-top:32px;padding-top:16px;border-top:2px dashed #cbd5e1;font-size:12px;color:#94a3b8;">
            Your side quest to financial independence. © 2026 SideQuest.
          </div>
        </td></tr>
      </table>
    </td></tr></table>
    </body></html>
    """


async def _send(to: str, subject: str, html: str) -> bool:
    if not RESEND_API_KEY:
        logger.info(f"[email skipped: no RESEND_API_KEY] to={to} subj={subject}")
        return False
    try:
        await asyncio.to_thread(
            resend.Emails.send,
            {"from": SENDER_EMAIL, "to": [to], "subject": subject, "html": html},
        )
        logger.info(f"[email sent] to={to} subj={subject}")
        return True
    except Exception as e:
        logger.warning(f"[email failed] to={to} err={e}")
        return False


async def send_waitlist_confirmation(name: str, email: str, referral_link: str):
    html = _wrap(
        f"You're in, {name.split()[0] if name else 'there'}! 🎉",
        f"""<p>Welcome to the SideQuest waitlist. We're building a place where students like you earn real money completing micro-tasks for real businesses.</p>
        <p><strong>Your referral link</strong> — share it, jump the queue:</p>
        <p style="background:#FACC15;border:2px solid #0F172A;border-radius:8px;padding:12px;font-family:monospace;word-break:break-all;">{referral_link}</p>
        <p>Top referrers get priority onboarding + a Founding Member badge.</p>""",
        "Open SideQuest", APP_BASE_URL or None,
    )
    return await _send(email, "Welcome to SideQuest 🚀", html)


async def send_task_assigned(name: str, email: str, task_title: str, deadline: str):
    html = _wrap(
        "New quest assigned!",
        f"""<p>Hey {name.split()[0]}, a task is now yours to deliver:</p>
        <p style="font-size:18px;font-weight:800;color:#0F172A;">"{task_title}"</p>
        <p>Deadline: <strong>{deadline}</strong>. Open your dashboard to begin.</p>""",
        "Open dashboard", f"{APP_BASE_URL}/worker" if APP_BASE_URL else None,
    )
    return await _send(email, f"Task assigned: {task_title}", html)


async def send_payment_cleared(name: str, email: str, task_title: str, amount: float):
    html = _wrap(
        "Payment cleared 💸",
        f"""<p>Great news, {name.split()[0]} — payment for "{task_title}" has been processed.</p>
        <p style="font-size:24px;font-weight:900;color:#10B981;">₹{int(amount):,}</p>
        <p>It'll reflect in your bank/UPI within 1–3 business days.</p>""",
        "View earnings", f"{APP_BASE_URL}/worker" if APP_BASE_URL else None,
    )
    return await _send(email, f"₹{int(amount):,} paid for {task_title}", html)
