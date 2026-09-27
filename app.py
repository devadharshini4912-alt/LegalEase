import io
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from groq import Groq

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.units import mm


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. "
        "Please add it to your .env file."
    )


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=API_KEY
)


# ============================================================
# DOCUMENT TYPES
# ============================================================

DOCUMENT_TYPES = {
    "rental_agreement": "Rental Agreement",
    "nda": "Non-Disclosure Agreement",
    "employment_agreement": "Employment Agreement",
    "service_agreement": "Service Agreement",
    "affidavit": "Affidavit",
    "authorization_letter": "Authorization Letter",
}


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_prompt(document_type, user_details):

    document_name = DOCUMENT_TYPES.get(
        document_type,
        "Legal Document"
    )

    prompt = f"""
You are LegalEase, an AI assistant that helps users create
structured legal document DRAFTS.

Create a professional legal document draft for:

DOCUMENT TYPE:
{document_name}

USER-PROVIDED INFORMATION:
{user_details}

IMPORTANT RULES:

1. Create only a legal document DRAFT.

2. Do not claim that the document is legally valid in every
   jurisdiction.

3. Do not provide personalized legal advice.

4. Do not invent names, dates, addresses, amounts, facts,
   clauses, or other information.

5. If important information is missing, use:
   [REQUIRED INFORMATION]

6. Preserve all information supplied by the user accurately.

7. Use clear and professional legal language.

8. Use appropriate headings and numbered sections.

9. Do not fabricate laws, statutes, court cases, legal
   references, or government requirements.

10. Do not assume facts that the user did not provide.

11. Include appropriate sections for the selected document type.

12. Keep the document practical and easy to edit.

13. Do not use Markdown code fences.

14. Return only the document draft.

15. At the end, add a short section titled:

Review Notice

The Review Notice should explain that the generated document
is an AI-assisted draft and should be reviewed by a qualified
legal professional before official use.

Structure the document appropriately for its document type.
"""

    return prompt


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        document_types=DOCUMENT_TYPES
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "message": "LegalEase backend is running"
    })


# ============================================================
# GENERATE LEGAL DOCUMENT
# ============================================================

@app.route("/generate", methods=["POST"])
def generate_document():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data was received."
            }), 400


        document_type = data.get(
            "document_type",
            ""
        ).strip()


        user_details = data.get(
            "user_details",
            ""
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not document_type:
            return jsonify({
                "success": False,
                "error": "Please select a document type."
            }), 400


        if document_type not in DOCUMENT_TYPES:
            return jsonify({
                "success": False,
                "error": "Invalid document type."
            }), 400


        if not user_details:
            return jsonify({
                "success": False,
                "error": "Please provide the required details."
            }), 400


        # ----------------------------------------------------
        # BUILD PROMPT
        # ----------------------------------------------------

        prompt = build_prompt(
            document_type,
            user_details
        )


        # ----------------------------------------------------
        # CALL GROQ
        # ----------------------------------------------------

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are LegalEase, a professional "
                        "legal document drafting assistant. "
                        "Generate only the requested legal "
                        "document draft."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=5000
        )


        # ----------------------------------------------------
        # GET GENERATED TEXT
        # ----------------------------------------------------

        generated_text = (
            response.choices[0]
            .message
            .content
        )


        if not generated_text:
            return jsonify({
                "success": False,
                "error": "Groq returned an empty response."
            }), 500


        # ----------------------------------------------------
        # SEND RESULT TO FRONTEND
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "document_type": DOCUMENT_TYPES[
                document_type
            ],
            "document": generated_text
        })


    except Exception as error:

        print(
            "GROQ ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# DOWNLOAD PDF
# ============================================================

@app.route("/download-pdf", methods=["POST"])
def download_pdf():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No document data received."
            }), 400


        document_text = data.get(
            "document",
            ""
        ).strip()


        if not document_text:
            return jsonify({
                "success": False,
                "error": "Document content is empty."
            }), 400


        document_type = data.get(
            "document_type",
            "Legal Document"
        )


        # ----------------------------------------------------
        # CREATE PDF BUFFER
        # ----------------------------------------------------

        buffer = io.BytesIO()


        # ----------------------------------------------------
        # CREATE PDF
        # ----------------------------------------------------

        pdf = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )


        # ----------------------------------------------------
        # PDF STYLES
        # ----------------------------------------------------

        styles = getSampleStyleSheet()


        title_style = ParagraphStyle(
            "LegalTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=15
        )


        body_style = ParagraphStyle(
            "LegalBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            spaceAfter=8
        )


        heading_style = ParagraphStyle(
            "LegalHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=8
        )


        # ----------------------------------------------------
        # PDF CONTENT
        # ----------------------------------------------------

        story = []


        story.append(
            Paragraph(
                "LegalEase",
                title_style
            )
        )


        story.append(
            Paragraph(
                document_type,
                heading_style
            )
        )


        story.append(
            Spacer(1, 10)
        )


        # ----------------------------------------------------
        # ADD DOCUMENT TEXT
        # ----------------------------------------------------

        lines = document_text.splitlines()


        for line in lines:

            cleaned_line = line.strip()


            if not cleaned_line:

                story.append(
                    Spacer(1, 6)
                )

                continue


            # Escape HTML characters
            safe_line = (
                cleaned_line
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )


            story.append(
                Paragraph(
                    safe_line,
                    body_style
                )
            )


        # ----------------------------------------------------
        # REVIEW NOTICE
        # ----------------------------------------------------

        story.append(
            Spacer(1, 12)
        )


        story.append(
            Paragraph(
                "<b>Review Notice</b>",
                heading_style
            )
        )


        story.append(
            Paragraph(
                "This document was generated with "
                "the assistance of LegalEase AI. "
                "It is an AI-generated draft and "
                "should be reviewed by a qualified "
                "legal professional before official use.",
                body_style
            )
        )


        # ----------------------------------------------------
        # BUILD PDF
        # ----------------------------------------------------

        pdf.build(story)

        buffer.seek(0)


        # ----------------------------------------------------
        # FILE NAME
        # ----------------------------------------------------

        filename = (
            "LegalEase_"
            + document_type.replace(" ", "_")
            + "_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            + ".pdf"
        )


        # ----------------------------------------------------
        # SEND PDF
        # ----------------------------------------------------

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )


    except Exception as error:

        print(
            "PDF ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )