"""
Email notification for new property matches.
Configure alert_email and SMTP credentials in config.py or environment variables.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from .models import Property
from .config import SEARCH_PROFILE


def send_new_properties_alert(new_properties: List[Property]):
    recipient = SEARCH_PROFILE.get("alert_email") or os.getenv("ALERT_EMAIL")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not recipient or not smtp_user or not smtp_pass:
        print("[notifier] Email not configured — skipping alert. Set ALERT_EMAIL, SMTP_USER, SMTP_PASS env vars.")
        return

    if not new_properties:
        return

    subject = f"[Auction Dashboard] {len(new_properties)} new propert{'y' if len(new_properties) == 1 else 'ies'} found"

    html_rows = ""
    for p in new_properties:
        price_str = f"€{p.price_eur:,.0f}" if p.price_eur else "Price TBD"
        area_str = f"{p.area_m2:.0f}m²" if p.area_m2 else "?"
        flags = []
        if p.is_historical:
            flags.append("Historic")
        if p.needs_refurbishment:
            flags.append("Needs refurb")
        flag_str = " · ".join(flags) if flags else ""
        html_rows += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee">
            <strong><a href="{p.url}">{p.title}</a></strong><br>
            <small>{p.location}</small>
          </td>
          <td style="padding:8px;border-bottom:1px solid #eee">{price_str}</td>
          <td style="padding:8px;border-bottom:1px solid #eee">{area_str}</td>
          <td style="padding:8px;border-bottom:1px solid #eee">{p.auction_date or '?'}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;color:#888">{flag_str}</td>
        </tr>"""

    html = f"""
    <html><body>
    <h2 style="color:#2c3e50">New auction properties matched your profile</h2>
    <p>Budget: ≤ €{SEARCH_PROFILE['max_price_eur']:,} · Regions: {', '.join(SEARCH_PROFILE['regions'].keys())}</p>
    <table style="border-collapse:collapse;width:100%;font-family:sans-serif;font-size:14px">
      <thead>
        <tr style="background:#f5f5f5">
          <th style="padding:8px;text-align:left">Property</th>
          <th style="padding:8px;text-align:left">Price</th>
          <th style="padding:8px;text-align:left">Size</th>
          <th style="padding:8px;text-align:left">Auction Date</th>
          <th style="padding:8px;text-align:left">Notes</th>
        </tr>
      </thead>
      <tbody>{html_rows}</tbody>
    </table>
    <p style="color:#888;font-size:12px;margin-top:20px">
      Open your dashboard for full details and to mark favourites.
    </p>
    </body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SEARCH_PROFILE["smtp_host"], SEARCH_PROFILE["smtp_port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
        print(f"[notifier] Alert sent to {recipient} — {len(new_properties)} properties")
    except Exception as e:
        print(f"[notifier] Failed to send email: {e}")
