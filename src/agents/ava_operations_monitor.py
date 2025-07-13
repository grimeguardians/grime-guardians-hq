"""
Ava Operations Monitor - Proactive Real-Time Monitoring System
Monitors all appointments, check-ins, and operational compliance in real-time
"""

import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass, field
from enum import Enum

from ..integrations.gohighlevel_service import ghl_service
from ..config.settings import settings

logger = structlog.get_logger()


class AlertLevel(Enum):
    """Alert escalation levels."""
    WARNING = "warning"      # 5 minutes late (9:50 for 9:45 target)
    URGENT = "urgent"        # 10 minutes late (9:55 for 9:45 target)
    CRITICAL = "critical"    # 15 minutes late (10:00 for 9:45 target)


class CheckInStatus(Enum):
    """Check-in status tracking."""
    NOT_DUE = "not_due"              # Too early to check in
    DUE_SOON = "due_soon"            # Within 5 minutes of target time
    OVERDUE = "overdue"              # Past target check-in time
    CHECKED_IN = "checked_in"        # Successfully checked in


@dataclass
class MonitoredAppointment:
    """Appointment being monitored for check-ins."""
    appointment_id: str
    contact_name: str
    cleaner_assigned: str
    client_time: datetime           # Client appointment time (e.g., 10:00 AM)
    target_checkin: datetime        # Required check-in time (e.g., 9:45 AM)
    address: str
    phone: str
    email: str
    
    # Tracking state
    status: CheckInStatus = CheckInStatus.NOT_DUE
    checked_in_time: Optional[datetime] = None
    alerts_sent: Set[AlertLevel] = field(default_factory=set)
    last_ping_time: Optional[datetime] = None


class AvaOperationsMonitor:
    """
    Proactive Operations Monitoring System for Ava.
    
    Continuously monitors:
    - Appointment schedule compliance
    - Check-in status tracking
    - Real-time alerting and escalation
    - Communication with cleaners and management
    """
    
    def __init__(self, discord_bot):
        self.discord_bot = discord_bot
        self.monitored_appointments: Dict[str, MonitoredAppointment] = {}
        self.monitoring_active = False
        self.check_interval = 60  # Check every minute
        
        # Discord channels for alerts
        self.ops_channel_id = int(settings.discord_checkin_channel_id)
        self.ops_lead_id = int(settings.discord_ops_lead_id)
        
        # Check-in triggers
        self.arrival_triggers = ['🚗', 'arrived', 'here', 'on site', 'at location']
        self.finished_triggers = ['🏁', 'finished', 'complete', 'done']
        
    async def start_monitoring(self):
        """Start the proactive monitoring system."""
        if self.monitoring_active:
            logger.warning("Operations monitoring already active")
            return
            
        self.monitoring_active = True
        logger.info("🔥 Starting Ava Operations Monitoring System")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Load today's appointments
        await self._load_todays_appointments()
        
        logger.info(f"📊 Monitoring {len(self.monitored_appointments)} appointments")
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        logger.info("🛑 Stopping Ava Operations Monitoring System")
    
    async def _monitoring_loop(self):
        """Main monitoring loop - runs continuously."""
        while self.monitoring_active:
            try:
                await self._check_all_appointments()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _load_todays_appointments(self):
        """Load today's appointments for monitoring."""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            appointments = await ghl_service.get_appointments(today, tomorrow)
            
            for apt in appointments:
                # Calculate target check-in time (15 minutes early)
                target_checkin = apt.start_time - timedelta(minutes=15)
                
                monitored_apt = MonitoredAppointment(
                    appointment_id=apt.id,
                    contact_name=apt.contact_name,
                    cleaner_assigned=apt.assigned_user,
                    client_time=apt.start_time,
                    target_checkin=target_checkin,
                    address=apt.address,
                    phone=apt.contact_phone,
                    email=apt.contact_email
                )
                
                self.monitored_appointments[apt.id] = monitored_apt
                
                logger.debug(f"📅 Loaded appointment: {apt.contact_name} at {apt.start_time.strftime('%H:%M')} (target check-in: {target_checkin.strftime('%H:%M')})")
                
        except Exception as e:
            logger.error(f"Error loading appointments: {e}")
    
    async def _check_all_appointments(self):
        """Check all monitored appointments for compliance."""
        now = datetime.now()
        
        for apt_id, apt in self.monitored_appointments.items():
            await self._check_appointment_status(apt, now)
    
    async def _check_appointment_status(self, apt: MonitoredAppointment, now: datetime):
        """Check individual appointment status and send alerts if needed."""
        try:
            # Skip if already checked in
            if apt.status == CheckInStatus.CHECKED_IN:
                return
            
            # Calculate time differences
            time_to_checkin = (apt.target_checkin - now).total_seconds() / 60  # minutes
            time_since_checkin = (now - apt.target_checkin).total_seconds() / 60  # minutes
            
            # Update status based on timing
            if time_to_checkin > 5:
                apt.status = CheckInStatus.NOT_DUE
            elif time_to_checkin > 0:
                apt.status = CheckInStatus.DUE_SOON
            else:
                apt.status = CheckInStatus.OVERDUE
            
            # Handle overdue check-ins with escalating alerts
            if apt.status == CheckInStatus.OVERDUE:
                await self._handle_overdue_checkin(apt, time_since_checkin)
                
        except Exception as e:
            logger.error(f"Error checking appointment {apt.appointment_id}: {e}")
    
    async def _handle_overdue_checkin(self, apt: MonitoredAppointment, minutes_late: float):
        """Handle overdue check-ins with escalating alerts."""
        try:
            alert_level = None
            
            # Determine alert level based on how late they are
            if minutes_late >= 15 and AlertLevel.CRITICAL not in apt.alerts_sent:
                alert_level = AlertLevel.CRITICAL
            elif minutes_late >= 10 and AlertLevel.URGENT not in apt.alerts_sent:
                alert_level = AlertLevel.URGENT
            elif minutes_late >= 5 and AlertLevel.WARNING not in apt.alerts_sent:
                alert_level = AlertLevel.WARNING
            
            # Send alert if needed
            if alert_level:
                await self._send_escalating_alert(apt, alert_level, minutes_late)
                apt.alerts_sent.add(alert_level)
                apt.last_ping_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error handling overdue check-in for {apt.appointment_id}: {e}")
    
    async def _send_escalating_alert(self, apt: MonitoredAppointment, level: AlertLevel, minutes_late: float):
        """Send escalating alerts to cleaner and management."""
        try:
            # Get alert details
            alert_config = self._get_alert_config(level, minutes_late)
            
            # Format times for display
            target_time = apt.target_checkin.strftime("%I:%M %p")
            client_time = apt.client_time.strftime("%I:%M %p")
            current_time = datetime.now().strftime("%I:%M %p")
            
            # Message to cleaner (would integrate with SMS/text later)
            cleaner_message = f"""
🚨 **{alert_config['emoji']} {alert_config['title']}**

**{apt.cleaner_assigned}** - You have a cleaning appointment that requires immediate attention:

📅 **Client**: {apt.contact_name}
🕐 **Target Check-in**: {target_time}
🕐 **Client Appointment**: {client_time}
🕐 **Current Time**: {current_time}
⏰ **You are {minutes_late:.0f} minutes late for check-in**

📍 **Address**: {apt.address}
📞 **Client Phone**: {apt.phone}

**Required Action**: Send 🚗 emoji or "arrived" message immediately!

{alert_config['urgency_message']}
"""
            
            # Message to operations lead
            ops_message = f"""
🚨 **{alert_config['emoji']} OPERATIONS ALERT - {alert_config['title']}**

**Cleaner**: {apt.cleaner_assigned}
**Client**: {apt.contact_name}
**Address**: {apt.address}
**Target Check-in**: {target_time}
**Client Appointment**: {client_time}
**Status**: {minutes_late:.0f} minutes late for check-in

{alert_config['management_action']}
"""
            
            # Send to operations channel
            ops_channel = self.discord_bot.get_channel(self.ops_channel_id)
            if ops_channel:
                await ops_channel.send(ops_message)
            
            # Send DM to operations lead
            ops_lead = self.discord_bot.get_user(self.ops_lead_id)
            if ops_lead:
                try:
                    await ops_lead.send(ops_message)
                except discord.Forbidden:
                    logger.warning("Cannot send DM to ops lead")
            
            # Log the alert
            logger.warning(f"{alert_config['emoji']} {level.value.upper()} alert sent for {apt.contact_name} appointment")
            
            # TODO: Integrate with SMS/GoHighLevel messaging to contact cleaner directly
            
        except Exception as e:
            logger.error(f"Error sending escalating alert: {e}")
    
    def _get_alert_config(self, level: AlertLevel, minutes_late: float) -> Dict[str, str]:
        """Get alert configuration based on level."""
        configs = {
            AlertLevel.WARNING: {
                "emoji": "⚠️",
                "title": "CHECK-IN REMINDER",
                "urgency_message": "Please confirm your status immediately.",
                "management_action": "📱 **Action**: Monitor for next 5 minutes."
            },
            AlertLevel.URGENT: {
                "emoji": "🔥",
                "title": "URGENT - LATE CHECK-IN",
                "urgency_message": "⚠️ This is urgent - client appointment is approaching!",
                "management_action": "📞 **Action**: Consider calling cleaner if no response in 2 minutes."
            },
            AlertLevel.CRITICAL: {
                "emoji": "🚨",
                "title": "CRITICAL - CLIENT APPOINTMENT TIME",
                "urgency_message": "🚨 CRITICAL: Client appointment time has arrived without check-in!",
                "management_action": "📞 **IMMEDIATE ACTION**: Call cleaner and client now!"
            }
        }
        return configs[level]
    
    async def handle_checkin_message(self, message, username: str) -> bool:
        """Handle check-in messages from cleaners."""
        try:
            content = message.content.lower()
            
            # Check for arrival triggers
            if any(trigger in content for trigger in self.arrival_triggers):
                return await self._process_arrival_checkin(username, message)
            
            # Check for finished triggers
            if any(trigger in content for trigger in self.finished_triggers):
                return await self._process_finished_checkin(username, message)
                
            return False
            
        except Exception as e:
            logger.error(f"Error handling check-in message: {e}")
            return False
    
    async def _process_arrival_checkin(self, cleaner_name: str, message) -> bool:
        """Process arrival check-in from cleaner."""
        try:
            now = datetime.now()
            
            # Find appointment for this cleaner
            for apt in self.monitored_appointments.values():
                if (apt.cleaner_assigned.lower() == cleaner_name.lower() and 
                    apt.status != CheckInStatus.CHECKED_IN and
                    abs((apt.target_checkin - now).total_seconds()) < 3600):  # Within 1 hour
                    
                    # Mark as checked in
                    apt.status = CheckInStatus.CHECKED_IN
                    apt.checked_in_time = now
                    
                    # Calculate timing
                    minutes_difference = (now - apt.target_checkin).total_seconds() / 60
                    
                    if minutes_difference <= 0:
                        timing_status = f"✅ **ON TIME** ({abs(minutes_difference):.0f} min early)"
                        emoji = "✅"
                    elif minutes_difference <= 5:
                        timing_status = f"⚠️ **LATE** ({minutes_difference:.0f} min late)"
                        emoji = "⚠️"
                    else:
                        timing_status = f"🚨 **VERY LATE** ({minutes_difference:.0f} min late)"
                        emoji = "🚨"
                    
                    # Send confirmation
                    confirmation = f"""
{emoji} **CHECK-IN CONFIRMED**

**Cleaner**: {cleaner_name}
**Client**: {apt.contact_name}
**Address**: {apt.address}
**Status**: {timing_status}
**Check-in Time**: {now.strftime('%I:%M %p')}
**Client Appointment**: {apt.client_time.strftime('%I:%M %p')}
"""
                    
                    # Send to operations channel
                    ops_channel = self.discord_bot.get_channel(self.ops_channel_id)
                    if ops_channel:
                        await ops_channel.send(confirmation)
                    
                    # Reply to cleaner
                    await message.channel.send(f"{emoji} Check-in confirmed for {apt.contact_name}! {timing_status}")
                    
                    logger.info(f"✅ Check-in processed: {cleaner_name} -> {apt.contact_name}")
                    return True
            
            # No matching appointment found
            await message.channel.send("❓ No appointment found for check-in. Please verify your assignment.")
            return False
            
        except Exception as e:
            logger.error(f"Error processing arrival check-in: {e}")
            return False
    
    async def _process_finished_checkin(self, cleaner_name: str, message) -> bool:
        """Process completion check-in from cleaner."""
        try:
            # Similar logic to arrival, but for completion
            # This would integrate with photo submission and checklist verification
            
            await message.channel.send("🏁 Completion noted! Please ensure photos and checklist are submitted.")
            return True
            
        except Exception as e:
            logger.error(f"Error processing finished check-in: {e}")
            return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status for display."""
        now = datetime.now()
        
        status = {
            "monitoring_active": self.monitoring_active,
            "total_appointments": len(self.monitored_appointments),
            "checked_in": len([apt for apt in self.monitored_appointments.values() 
                             if apt.status == CheckInStatus.CHECKED_IN]),
            "overdue": len([apt for apt in self.monitored_appointments.values() 
                          if apt.status == CheckInStatus.OVERDUE]),
            "upcoming": len([apt for apt in self.monitored_appointments.values() 
                           if apt.client_time > now and apt.status != CheckInStatus.CHECKED_IN])
        }
        
        return status