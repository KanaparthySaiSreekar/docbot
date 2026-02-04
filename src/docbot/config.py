"""Configuration system with complete schema and environment separation."""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Nested configuration models for better organization

class ClinicConfig(BaseModel):
    """Clinic information for WhatsApp messages and prescriptions."""
    name: str = "Default Clinic"
    address: str = "123 Default Street, City, State, PIN"
    phone: str = "+91 1234567890"
    doctor_name: str = "Dr. Default"
    doctor_degree: str = "MBBS"
    doctor_registration: str = "REG123456"
    signature_image_path: str = "signature.png"


class ScheduleConfig(BaseModel):
    """Doctor's working schedule configuration."""
    working_days: list[int] = Field(default=[0, 1, 2, 3, 4, 5])  # Monday-Saturday
    start_time: str = "09:00"  # HH:MM format
    end_time: str = "17:00"
    break_start: str = "13:00"
    break_end: str = "14:00"
    slot_duration_minutes: int = 15
    max_appointments_per_day: int = 50


class FeesConfig(BaseModel):
    """Consultation fees configuration."""
    online_consultation: int = 500  # INR


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "docbot.db"


class AuthConfig(BaseModel):
    """Authentication configuration for Google OAuth."""
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret_key: str = ""


class WhatsAppConfig(BaseModel):
    """WhatsApp Cloud API configuration."""
    phone_number_id: str = ""
    access_token: str = ""
    verify_token: str = ""
    api_version: str = "v21.0"


class RazorpayConfig(BaseModel):
    """Razorpay payment gateway configuration."""
    key_id: str = ""
    key_secret: str = ""
    webhook_secret: str = ""


class GoogleCalendarConfig(BaseModel):
    """Google Calendar integration configuration."""
    credentials_path: str = "google_calendar_credentials.json"
    calendar_id: str = ""


class AppConfig(BaseModel):
    """Application-level configuration."""
    env: str = "test"  # test or prod
    base_url: str = "http://localhost:8000"
    timezone: str = "Asia/Kolkata"
    debug: bool = True
    log_level: str = "DEBUG"


class Settings(BaseModel):
    """Complete application configuration schema."""
    clinic: ClinicConfig = Field(default_factory=ClinicConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    fees: FeesConfig = Field(default_factory=FeesConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    razorpay: RazorpayConfig = Field(default_factory=RazorpayConfig)
    google_calendar: GoogleCalendarConfig = Field(default_factory=GoogleCalendarConfig)
    app: AppConfig = Field(default_factory=AppConfig)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load configuration from environment-specific JSON file.

    Reads DOCBOT_ENV from environment (defaults to "test").
    Loads config.{env}.json (e.g., config.test.json).

    If file is missing: logs warning, uses defaults.
    If file has invalid fields: logs warning per field, uses defaults.

    Returns:
        Settings: Validated configuration with graceful defaults.
    """
    env = os.getenv("DOCBOT_ENV", "test")
    config_file = Path(f"config.{env}.json")

    logger.info(f"Loading configuration from {config_file}")

    config_data: dict[str, Any] = {}

    if not config_file.exists():
        logger.warning(
            f"Configuration file {config_file} not found. Using defaults.",
            extra={"env": env, "config_file": str(config_file)}
        )
    else:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.info(f"Configuration loaded successfully from {config_file}")
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse {config_file}: {e}. Using defaults.",
                extra={"env": env, "error": str(e)}
            )
        except Exception as e:
            logger.warning(
                f"Failed to read {config_file}: {e}. Using defaults.",
                extra={"env": env, "error": str(e)}
            )

    # Validate and construct Settings with Pydantic
    try:
        # Override app.env with the environment variable
        if "app" not in config_data:
            config_data["app"] = {}
        config_data["app"]["env"] = env

        settings = Settings(**config_data)
        logger.info("Configuration validated successfully")
        return settings
    except Exception as e:
        logger.error(
            f"Configuration validation failed: {e}. Using full defaults.",
            extra={"error": str(e)}
        )
        # Return defaults with correct env set
        return Settings(app=AppConfig(env=env))
