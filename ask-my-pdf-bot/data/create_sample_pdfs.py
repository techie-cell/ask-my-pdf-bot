"""
Generate sample PDF files for testing the Ask My PDF Bot.
Run this script once after setting up the project:

    python data/create_sample_pdfs.py
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not installed. Run: pip install PyMuPDF")
    sys.exit(1)


def create_pdf(output_path: Path, title: str, pages: list[dict]) -> None:
    """Create a multi-page PDF with given content."""
    doc = fitz.open()

    for page_data in pages:
        page = doc.new_page(width=595, height=842)  # A4 size

        # Title
        page.insert_text(
            (50, 60),
            page_data.get("title", title),
            fontsize=16,
            fontname="helv",
            color=(0.1, 0.1, 0.5),
        )

        # Horizontal line under title
        page.draw_line((50, 75), (545, 75), color=(0.7, 0.7, 0.9), width=1)

        # Body text (wrapped manually)
        y_pos = 100
        body = page_data.get("body", "")
        words = body.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if len(test_line) > 85:
                page.insert_text((50, y_pos), line.strip(), fontsize=11, fontname="helv")
                y_pos += 18
                line = word + " "
                if y_pos > 800:
                    break
            else:
                line = test_line
        if line.strip():
            page.insert_text((50, y_pos), line.strip(), fontsize=11, fontname="helv")

        # Page footer
        page.insert_text(
            (50, 820),
            f"Page {page_data.get('page_num', 1)} | {title}",
            fontsize=9,
            color=(0.5, 0.5, 0.5),
        )

    doc.save(str(output_path))
    doc.close()
    print(f"Created: {output_path}")


def main():
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)

    # ── Sample PDF 1: Software License Agreement ──────────────
    create_pdf(
        output_dir / "sample_contract.pdf",
        title="Software License Agreement",
        pages=[
            {
                "title": "SOFTWARE LICENSE AGREEMENT",
                "page_num": 1,
                "body": (
                    "This Software License Agreement ('Agreement') is entered into as of January 15, 2024, "
                    "between TechCorp Solutions Inc., a Delaware corporation ('Licensor'), located at "
                    "123 Innovation Drive, San Francisco, CA 94105, and DataDriven Analytics LLC "
                    "('Licensee'), located at 456 Business Park, Austin, TX 78701. "
                    "\n\n"
                    "1. GRANT OF LICENSE. Subject to the terms and conditions of this Agreement, Licensor "
                    "hereby grants to Licensee a non-exclusive, non-transferable, limited license to use "
                    "the Software solely for Licensee's internal business purposes. "
                    "\n\n"
                    "2. LICENSE FEE. Licensee agrees to pay Licensor an annual license fee of $12,000 USD, "
                    "due within 30 days of the effective date and each anniversary thereof. "
                    "\n\n"
                    "3. TERM. This Agreement shall commence on the effective date and continue for a period "
                    "of three (3) years, unless earlier terminated in accordance with this Agreement."
                ),
            },
            {
                "title": "Terms and Conditions (continued)",
                "page_num": 2,
                "body": (
                    "4. RESTRICTIONS. Licensee shall not: (a) sublicense, sell, resell, transfer, assign, "
                    "or otherwise dispose of the Software; (b) modify or make derivative works based upon "
                    "the Software; (c) reverse engineer or access the Software to build a competitive product. "
                    "\n\n"
                    "5. CONFIDENTIALITY. Each party agrees to maintain the confidentiality of the other "
                    "party's proprietary information and not to disclose such information to third parties "
                    "without prior written consent. "
                    "\n\n"
                    "6. SUPPORT AND MAINTENANCE. Licensor shall provide technical support via email during "
                    "business hours (9am-5pm PST, Monday through Friday). Response time for critical issues "
                    "shall not exceed 4 business hours. "
                    "\n\n"
                    "7. LIMITATION OF LIABILITY. In no event shall Licensor be liable for indirect, "
                    "incidental, or consequential damages. Licensor's total liability shall not exceed "
                    "the fees paid in the preceding 12 months."
                ),
            },
            {
                "title": "Signatures and Appendix",
                "page_num": 3,
                "body": (
                    "8. TERMINATION. Either party may terminate this Agreement upon 30 days written notice. "
                    "Licensor may terminate immediately if Licensee breaches any material term. "
                    "\n\n"
                    "9. GOVERNING LAW. This Agreement shall be governed by the laws of the State of "
                    "California, without regard to conflict of law principles. "
                    "\n\n"
                    "10. ENTIRE AGREEMENT. This Agreement constitutes the entire agreement between the "
                    "parties and supersedes all prior negotiations, representations, and understandings. "
                    "\n\n"
                    "IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first "
                    "written above. "
                    "\n\n"
                    "TechCorp Solutions Inc.          DataDriven Analytics LLC "
                    "By: James Anderson               By: Sarah Mitchell "
                    "Title: CEO                       Title: CTO "
                    "Date: January 15, 2024           Date: January 15, 2024"
                ),
            },
        ],
    )

    # ── Sample PDF 2: Company Policy ──────────────────────────
    create_pdf(
        output_dir / "sample_policy.pdf",
        title="Employee Remote Work Policy",
        pages=[
            {
                "title": "REMOTE WORK POLICY",
                "page_num": 1,
                "body": (
                    "Effective Date: March 1, 2024 | Policy Number: HR-2024-007 "
                    "Department: Human Resources | Approved By: Board of Directors "
                    "\n\n"
                    "PURPOSE: This policy establishes guidelines for employees working remotely at "
                    "Horizon Technologies. It applies to all full-time and part-time employees. "
                    "\n\n"
                    "ELIGIBILITY: Employees who have completed a minimum of 6 months of employment, "
                    "maintain a performance rating of 'Meets Expectations' or higher, and have a "
                    "dedicated home workspace with reliable internet (minimum 25 Mbps) are eligible "
                    "for remote work arrangements. "
                    "\n\n"
                    "WORK HOURS: Remote employees must be available during core hours of 10:00 AM to "
                    "3:00 PM in their local time zone. Employees must respond to communications within "
                    "2 hours during their scheduled work hours. "
                    "\n\n"
                    "EQUIPMENT: The company will provide a laptop computer and required software licenses. "
                    "Employees are responsible for their own internet service. A monthly stipend of $75 "
                    "will be provided for internet and utility costs."
                ),
            },
            {
                "title": "Security and Compliance",
                "page_num": 2,
                "body": (
                    "SECURITY REQUIREMENTS: Remote employees must use the company VPN at all times when "
                    "accessing company systems. All company data must be stored on company-approved "
                    "cloud storage (Microsoft OneDrive or SharePoint). Employees must lock their "
                    "computer screen when stepping away. "
                    "\n\n"
                    "PERFORMANCE EXPECTATIONS: Remote employees are expected to maintain the same "
                    "productivity standards as in-office employees. Managers will conduct monthly "
                    "check-ins and quarterly performance reviews. "
                    "\n\n"
                    "MEETINGS: Employees must attend all required virtual team meetings with camera on. "
                    "At least one in-person visit to the office per quarter is required for team "
                    "collaboration days. "
                    "\n\n"
                    "VIOLATIONS: Failure to comply with this policy may result in revocation of remote "
                    "work privileges and disciplinary action up to and including termination. "
                    "\n\n"
                    "CONTACT: Questions about this policy should be directed to the HR department at "
                    "hr@horizontech.com or extension 2200."
                ),
            },
        ],
    )

    print("\n✅ Sample PDFs created successfully!")
    print("📁 Files saved to: data/")
    print("\nTest questions to try:")
    print("  - What is the license fee in the contract?")
    print("  - Who signed the software agreement?")
    print("  - What are the remote work hours?")
    print("  - What equipment does the company provide for remote workers?")


if __name__ == "__main__":
    main()
