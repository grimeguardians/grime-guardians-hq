"""
Ava Operations Monitor
Real-time monitoring of job check-ins, KPIs, compliance alerts, and revenue tracking.
Runs as a background task feeding alerts to Discord.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ..config.settings import get_settings
from ..utils.time_utils import now_ct

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class CheckInAlert:
    """Alert for a missed or late check-in."""
    contractor_id: str
    contractor_name: str
    job_id: str
    scheduled_time: datetime
    alert_type: str          # 'missed_arrival', 'missed_finish', 'no_photos', 'late'
    minutes_late: int = 0
    auto_flagged: bool = True
    escalate_to_discord: bool = True


@dataclass
class KPISnapshot:
    """Point-in-time KPI summary."""
    timestamp: datetime
    daily_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    checklist_compliance_pct: float
    photo_submission_pct: float
    on_time_arrival_pct: float
    jobs_completed_today: int
    jobs_scheduled_today: int
    active_violations: int
    revenue_to_weekly_target: float     # negative = behind
    revenue_to_monthly_target: float


@dataclass
class JobMonitorEntry:
    """Tracks a single job through its lifecycle."""
    job_id: str
    contractor_id: str
    contractor_name: str
    client_name: str
    address: str
    scheduled_start: datetime
    arrival_deadline: datetime          # scheduled_start - 15 min buffer
    status: str = "scheduled"           # scheduled, arrived, in_progress, finished, flagged
    arrived_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    photos_submitted: bool = False
    checklist_submitted: bool = False
    alerts_sent: List[str] = field(default_factory=list)


# ─── KPI Targets (from Operating Manual 2026) ────────────────────────────────

TARGETS = {
    "daily_revenue": 1_400.0,
    "weekly_revenue": 9_615.0,
    "monthly_revenue": 42_000.0,
    "annual_revenue": 500_000.0,
    "checklist_compliance_pct": 90.0,
    "photo_submission_pct": 90.0,
    "on_time_arrival_pct": 95.0,
    "customer_satisfaction": 9.0,
    "jobs_per_day_min": 6,
    "jobs_per_day_max": 10,
}

ARRIVAL_BUFFER_MINUTES = settings.checkin_buffer_minutes   # 15


class AvaOperationsMonitor:
    """
    Real-time operations monitor for Ava.

    Monitors:
    - Job check-in / check-out compliance
    - Late arrivals — auto-flag + Discord alert
    - Photo and checklist submission compliance
    - KPI tracking vs. Operating Manual targets
    - Revenue progress toward $500K/2026 goal

    Designed as a stateless reducer: receives job/event data,
    returns alerts and KPI updates for Discord delivery.
    """

    def __init__(self):
        self.active_jobs: Dict[str, JobMonitorEntry] = {}
        self.daily_alerts: List[CheckInAlert] = []
        self.kpi_history: List[KPISnapshot] = []
        self._monitor_task: Optional[asyncio.Task] = None

    # ─── Job Lifecycle ────────────────────────────────────────────────────────

    def register_job(self, job_data: Dict[str, Any]) -> JobMonitorEntry:
        """
        Register a job for monitoring.

        Args:
            job_data: Dict with job_id, contractor_id, contractor_name,
                      client_name, address, scheduled_start (ISO string or datetime).

        Returns:
            JobMonitorEntry ready for monitoring.
        """
        scheduled = job_data.get("scheduled_start")
        if isinstance(scheduled, str):
            scheduled = datetime.fromisoformat(scheduled)

        entry = JobMonitorEntry(
            job_id=job_data["job_id"],
            contractor_id=job_data["contractor_id"],
            contractor_name=job_data.get("contractor_name", "Unknown"),
            client_name=job_data.get("client_name", "Unknown Client"),
            address=job_data.get("address", ""),
            scheduled_start=scheduled,
            arrival_deadline=scheduled - timedelta(minutes=ARRIVAL_BUFFER_MINUTES),
        )

        self.active_jobs[entry.job_id] = entry
        logger.info(f"Registered job {entry.job_id} for {entry.contractor_name} at {scheduled}")
        return entry

    def record_arrival(self, job_id: str, arrival_time: Optional[datetime] = None) -> Optional[CheckInAlert]:
        """
        Record a contractor arrival ping. Returns alert if late.

        Args:
            job_id: The job ID.
            arrival_time: Arrival timestamp (defaults to now).

        Returns:
            CheckInAlert if late, None if on time.
        """
        job = self.active_jobs.get(job_id)
        if not job:
            logger.warning(f"Arrival ping for unknown job: {job_id}")
            return None

        now = arrival_time or now_ct()
        job.arrived_at = now
        job.status = "arrived"

        if now > job.arrival_deadline:
            minutes_late = int((now - job.arrival_deadline).total_seconds() / 60)
            alert = CheckInAlert(
                contractor_id=job.contractor_id,
                contractor_name=job.contractor_name,
                job_id=job_id,
                scheduled_time=job.scheduled_start,
                alert_type="late",
                minutes_late=minutes_late,
                auto_flagged=True,
                escalate_to_discord=True,
            )
            job.alerts_sent.append("late_arrival")
            self.daily_alerts.append(alert)
            logger.warning(
                f"LATE ARRIVAL: {job.contractor_name} — job {job_id} — {minutes_late} min late"
            )
            return alert

        logger.info(f"On-time arrival: {job.contractor_name} — job {job_id}")
        return None

    def record_finish(self, job_id: str, finish_time: Optional[datetime] = None,
                      photos_submitted: bool = False,
                      checklist_submitted: bool = False) -> List[CheckInAlert]:
        """
        Record job completion. Returns list of compliance alerts.

        Args:
            job_id: The job ID.
            finish_time: Finish timestamp (defaults to now).
            photos_submitted: Whether before/after photos were submitted.
            checklist_submitted: Whether the cleaning checklist was submitted.

        Returns:
            List of compliance alerts (empty if fully compliant).
        """
        job = self.active_jobs.get(job_id)
        if not job:
            logger.warning(f"Finish ping for unknown job: {job_id}")
            return []

        now = finish_time or now_ct()
        job.finished_at = now
        job.status = "finished"
        job.photos_submitted = photos_submitted
        job.checklist_submitted = checklist_submitted

        alerts = []

        if not photos_submitted:
            alert = CheckInAlert(
                contractor_id=job.contractor_id,
                contractor_name=job.contractor_name,
                job_id=job_id,
                scheduled_time=job.scheduled_start,
                alert_type="no_photos",
                auto_flagged=True,
                escalate_to_discord=True,
            )
            alerts.append(alert)
            job.alerts_sent.append("no_photos")
            logger.warning(f"NO PHOTOS: {job.contractor_name} — job {job_id}")

        if not checklist_submitted:
            alert = CheckInAlert(
                contractor_id=job.contractor_id,
                contractor_name=job.contractor_name,
                job_id=job_id,
                scheduled_time=job.scheduled_start,
                alert_type="no_checklist",
                auto_flagged=True,
                escalate_to_discord=False,
            )
            alerts.append(alert)
            job.alerts_sent.append("no_checklist")

        self.daily_alerts.extend(alerts)
        return alerts

    def check_missed_arrivals(self, grace_minutes: int = 30) -> List[CheckInAlert]:
        """
        Scan active jobs for missed arrivals (no ping received past deadline + grace).

        Args:
            grace_minutes: Minutes after arrival_deadline before flagging as missed.

        Returns:
            List of CheckInAlerts for jobs with no arrival ping.
        """
        now = now_ct()
        alerts = []

        for job_id, job in self.active_jobs.items():
            if job.arrived_at is not None or job.status in ("finished", "flagged"):
                continue

            deadline_with_grace = job.arrival_deadline + timedelta(minutes=grace_minutes)
            if now > deadline_with_grace and "missed_arrival" not in job.alerts_sent:
                minutes_late = int((now - job.arrival_deadline).total_seconds() / 60)
                alert = CheckInAlert(
                    contractor_id=job.contractor_id,
                    contractor_name=job.contractor_name,
                    job_id=job_id,
                    scheduled_time=job.scheduled_start,
                    alert_type="missed_arrival",
                    minutes_late=minutes_late,
                    auto_flagged=True,
                    escalate_to_discord=True,
                )
                job.status = "flagged"
                job.alerts_sent.append("missed_arrival")
                self.daily_alerts.append(alert)
                alerts.append(alert)
                logger.error(
                    f"MISSED ARRIVAL: {job.contractor_name} — job {job_id} — "
                    f"{minutes_late} min past deadline"
                )

        return alerts

    # ─── KPI Tracking ─────────────────────────────────────────────────────────

    def compute_kpi_snapshot(self, raw_metrics: Dict[str, Any]) -> KPISnapshot:
        """
        Compute a KPI snapshot from raw metrics data.

        Args:
            raw_metrics: Dict with daily_revenue, weekly_revenue, monthly_revenue,
                         jobs_completed_today, jobs_scheduled_today,
                         checklist_compliance_pct, photo_submission_pct,
                         on_time_arrival_pct, active_violations.

        Returns:
            KPISnapshot with targets delta.
        """
        snapshot = KPISnapshot(
            timestamp=now_ct(),
            daily_revenue=raw_metrics.get("daily_revenue", 0.0),
            weekly_revenue=raw_metrics.get("weekly_revenue", 0.0),
            monthly_revenue=raw_metrics.get("monthly_revenue", 0.0),
            checklist_compliance_pct=raw_metrics.get("checklist_compliance_pct", 0.0),
            photo_submission_pct=raw_metrics.get("photo_submission_pct", 0.0),
            on_time_arrival_pct=raw_metrics.get("on_time_arrival_pct", 0.0),
            jobs_completed_today=raw_metrics.get("jobs_completed_today", 0),
            jobs_scheduled_today=raw_metrics.get("jobs_scheduled_today", 0),
            active_violations=raw_metrics.get("active_violations", 0),
            revenue_to_weekly_target=raw_metrics.get("weekly_revenue", 0.0) - TARGETS["weekly_revenue"],
            revenue_to_monthly_target=raw_metrics.get("monthly_revenue", 0.0) - TARGETS["monthly_revenue"],
        )
        self.kpi_history.append(snapshot)
        return snapshot

    def get_kpi_status_message(self, snapshot: KPISnapshot) -> str:
        """
        Format KPI snapshot into a Discord-ready status message.

        Args:
            snapshot: KPISnapshot to format.

        Returns:
            Formatted string for Discord embed.
        """
        weekly_delta = snapshot.revenue_to_weekly_target
        monthly_delta = snapshot.revenue_to_monthly_target

        weekly_icon = "+" if weekly_delta >= 0 else "-"
        monthly_icon = "+" if monthly_delta >= 0 else "-"

        compliance_flags = []
        if snapshot.checklist_compliance_pct < TARGETS["checklist_compliance_pct"]:
            compliance_flags.append(f"Checklist: {snapshot.checklist_compliance_pct:.0f}% (target 90%)")
        if snapshot.photo_submission_pct < TARGETS["photo_submission_pct"]:
            compliance_flags.append(f"Photos: {snapshot.photo_submission_pct:.0f}% (target 90%)")
        if snapshot.on_time_arrival_pct < TARGETS["on_time_arrival_pct"]:
            compliance_flags.append(f"On-Time: {snapshot.on_time_arrival_pct:.0f}% (target 95%)")

        lines = [
            f"**Ava KPI Report** — {snapshot.timestamp.strftime('%a %b %d, %I:%M %p')}",
            f"",
            f"**Revenue**",
            f"  Daily:   ${snapshot.daily_revenue:,.0f} / ${TARGETS['daily_revenue']:,.0f}",
            f"  Weekly:  ${snapshot.weekly_revenue:,.0f} / ${TARGETS['weekly_revenue']:,.0f}  ({weekly_icon}${abs(weekly_delta):,.0f})",
            f"  Monthly: ${snapshot.monthly_revenue:,.0f} / ${TARGETS['monthly_revenue']:,.0f}  ({monthly_icon}${abs(monthly_delta):,.0f})",
            f"",
            f"**Jobs Today**: {snapshot.jobs_completed_today}/{snapshot.jobs_scheduled_today} completed",
            f"**Active Violations**: {snapshot.active_violations}",
        ]

        if compliance_flags:
            lines.append("")
            lines.append("**Compliance Flags**")
            for flag in compliance_flags:
                lines.append(f"  {flag}")
        else:
            lines.append("")
            lines.append("All compliance targets met.")

        return "\n".join(lines)

    def format_alert_for_discord(self, alert: CheckInAlert) -> str:
        """
        Format a CheckInAlert into a Discord message.

        Args:
            alert: The alert to format.

        Returns:
            Formatted string for #alerts or #strikes channel.
        """
        alert_labels = {
            "late": f"LATE ARRIVAL ({alert.minutes_late} min)",
            "missed_arrival": f"MISSED ARRIVAL ({alert.minutes_late} min past deadline)",
            "no_photos": "PHOTOS NOT SUBMITTED",
            "no_checklist": "CHECKLIST NOT SUBMITTED",
            "missed_finish": "FINISH PING NOT RECEIVED",
        }
        label = alert_labels.get(alert.alert_type, alert.alert_type.upper())
        time_str = alert.scheduled_time.strftime("%I:%M %p")

        return (
            f"**{label}**\n"
            f"Contractor: {alert.contractor_name}\n"
            f"Job: `{alert.job_id}` | Scheduled: {time_str}\n"
            f"Auto-flagged: {'Yes' if alert.auto_flagged else 'No'}"
        )

    # ─── Background Monitor Loop ──────────────────────────────────────────────

    async def start_monitoring(self, discord_bot=None,
                               check_interval_seconds: int = 300) -> None:
        """
        Start the background monitoring loop.

        Args:
            discord_bot: Optional Discord bot instance for sending alerts.
            check_interval_seconds: How often to run checks (default 5 min).
        """
        logger.info(f"Ava monitor started — checking every {check_interval_seconds}s")

        while True:
            try:
                missed_alerts = self.check_missed_arrivals()

                if missed_alerts and discord_bot:
                    for alert in missed_alerts:
                        msg = self.format_alert_for_discord(alert)
                        await self._send_discord_alert(discord_bot, msg, alert.alert_type)

                logger.debug(f"Monitor tick: {len(self.active_jobs)} active jobs, "
                             f"{len(self.daily_alerts)} alerts today")

            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)

            await asyncio.sleep(check_interval_seconds)

    async def _send_discord_alert(self, discord_bot, message: str, alert_type: str) -> None:
        """
        Route an alert to the appropriate Discord channel.

        Args:
            discord_bot: Discord bot client.
            message: Formatted alert message.
            alert_type: Alert type string to determine routing.
        """
        try:
            strikes_types = {"late", "missed_arrival", "no_photos"}
            channel_name = (
                settings.discord_strikes_channel
                if alert_type in strikes_types
                else settings.discord_channel_alerts
            )

            guild = discord_bot.guilds[0] if discord_bot.guilds else None
            if not guild:
                logger.warning("No Discord guild available for alert routing")
                return

            channel = next(
                (c for c in guild.text_channels if c.name == channel_name), None
            )
            if channel:
                await channel.send(message)
                logger.info(f"Alert sent to #{channel_name}: {alert_type}")
            else:
                logger.warning(f"Discord channel #{channel_name} not found")

        except Exception as e:
            logger.error(f"Discord alert delivery failed: {e}")

    # ─── Daily Reset ──────────────────────────────────────────────────────────

    def reset_daily_counters(self) -> Dict[str, int]:
        """
        Reset daily tracking state. Call at midnight or start of new shift day.

        Returns:
            Summary of the day's alerts before reset.
        """
        summary = {
            "total_alerts": len(self.daily_alerts),
            "late_arrivals": sum(1 for a in self.daily_alerts if a.alert_type == "late"),
            "missed_arrivals": sum(1 for a in self.daily_alerts if a.alert_type == "missed_arrival"),
            "no_photos": sum(1 for a in self.daily_alerts if a.alert_type == "no_photos"),
            "active_jobs_cleared": len(self.active_jobs),
        }

        self.daily_alerts.clear()
        self.active_jobs.clear()
        logger.info(f"Daily counters reset. Summary: {summary}")
        return summary


# Singleton
ava_monitor = AvaOperationsMonitor()
