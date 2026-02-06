"""PDF generation for prescriptions using xhtml2pdf."""
import base64
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from docbot.config import get_settings
from docbot.timezone_utils import utc_to_ist

logger = logging.getLogger(__name__)


def generate_prescription_pdf(
    prescription_id: str,
    appointment_id: str,
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    medicines: list[dict],  # [{"name": str, "dosage": str, "frequency": str, "duration": str, "notes": str}]
    instructions: str | None = None,
) -> bytes:
    """
    Generate prescription PDF from template.

    Returns PDF as bytes.
    """
    settings = get_settings()

    # Load signature image as base64
    signature_base64 = None
    sig_path = Path(settings.clinic.signature_image_path)
    if sig_path.exists():
        with open(sig_path, "rb") as f:
            signature_base64 = base64.b64encode(f.read()).decode("utf-8")
    else:
        logger.warning(f"Signature image not found: {sig_path}")

    # Setup Jinja2 template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("prescription.html")

    # Render HTML
    now_ist = utc_to_ist(datetime.now(timezone.utc))
    html_content = template.render(
        clinic=settings.clinic,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        prescription_date=now_ist.strftime("%Y-%m-%d"),
        appointment_id=appointment_id,
        medicines=medicines,
        instructions=instructions,
        signature_base64=signature_base64,
        generated_at=now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
    )

    # Generate PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

    if pisa_status.err:
        logger.error(f"Failed to generate PDF for prescription {prescription_id}: {pisa_status.err}")
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")

    pdf_bytes = pdf_buffer.getvalue()
    logger.info(f"Generated prescription PDF: {prescription_id}")
    return pdf_bytes
