import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
import httpx

from immi_crawler.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_alert(diff_text: str) -> None:
    """Send markdown alert via Telegram Bot API.
    
    Args:
        diff_text: Plain/Markdown diff content.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram Bot configuration missing. Telegram notification skipped.")
        return
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": f"🚨 *Immi Crawler Change Alert* 🚨\n\n{diff_text}",
        "parse_mode": "Markdown"
    }
    
    logger.info("Sending Telegram alert...")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
    logger.info("Telegram alert sent successfully.")


async def send_email_alert(diff_html: str) -> None:
    """Send HTML alert via SMTP.
    
    Args:
        diff_html: Formatted HTML diff content.
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP host configuration missing. Email notification skipped.")
        return
        
    message = MIMEMultipart("alternative")
    message["Subject"] = "🚨 Immi Crawler: Skill Occupation List Changes Detected"
    message["From"] = settings.SMTP_SENDER
    message["To"] = settings.SMTP_RECIPIENT
    
    html_part = MIMEText(diff_html, "html")
    message.attach(html_part)
    
    logger.info(f"Sending SMTP email alert to {settings.SMTP_RECIPIENT}...")
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=False,  # Can be adjusted based on port
        timeout=10.0
    )
    logger.info("Email alert sent successfully.")


async def notify_diff(added: list[dict[str, str]], removed: list[dict[str, str]]) -> None:
    """Consolidate diff datasets and dispatch notifications to enabled backends.
    
    Args:
        added: List of added occupation-visa records.
        removed: List of removed occupation-visa records.
    """
    if not added and not removed:
        logger.info("No additions or removals detected. Skipping notifications.")
        return
        
    # Construct Plaintext/Markdown alert message for Telegram
    diff_lines = []
    if added:
        diff_lines.append("*Added Occupations:*")
        for item in added:
            diff_lines.append(f"➕ {item['occupation']} (Subclass {item['visa_subclass']} - {item['stream']})")
    if removed:
        if added:
            diff_lines.append("")
        diff_lines.append("*Removed Occupations:*")
        for item in removed:
            diff_lines.append(f"➖ {item['occupation']} (Subclass {item['visa_subclass']} - {item['stream']})")
            
    diff_text = "\n".join(diff_lines)
    
    # Construct HTML alert message for Email
    html_parts = [
        "<html>",
        "<body style='font-family: Arial, sans-serif; color: #333;'>",
        "<h2 style='color: #d32f2f;'>Immi Crawler: Occupation-Visa List Changes</h2>",
        "<p>The following changes were detected in the latest crawl compared to the previous run snapshot:</p>"
    ]
    if added:
        html_parts.append("<h3 style='color: #2e7d32;'>➕ Added Occupations</h3><ul>")
        for item in added:
            html_parts.append(
                f"<li><b>{item['occupation']}</b> (Subclass {item['visa_subclass']} - {item['stream']})</li>"
            )
        html_parts.append("</ul>")
    if removed:
        html_parts.append("<h3 style='color: #c62828;'>➖ Removed Occupations</h3><ul>")
        for item in removed:
            html_parts.append(
                f"<li><b>{item['occupation']}</b> (Subclass {item['visa_subclass']} - {item['stream']})</li>"
            )
        html_parts.append("</ul>")
    html_parts.append("<hr/><p style='font-size: 11px; color: #888;'>This is an automated message from the Immi Crawler service.</p></body></html>")
    diff_html = "\n".join(html_parts)
    
    backend = settings.NOTIFIER_BACKEND.lower()
    
    if backend in ("email", "both"):
        try:
            await send_email_alert(diff_html)
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
            
    if backend in ("telegram", "both"):
        try:
            await send_telegram_alert(diff_text)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}", exc_info=True)
