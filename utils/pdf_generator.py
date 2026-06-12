from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
def create_admission_pdf(student):
    filename = f"admission_{student[0]}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(150, 800, "SUMMER CAMP ADMISSION")
    c.setFont("Helvetica", 12)
    c.drawString(50, 740, f"Full Name: {student[1]}")
    c.drawString(50, 710, f"Phone: {student[3]}")
    c.drawString(50, 680, f"Email: {student[4]}")
    c.drawString(50, 640, f"Department: {student[8]}")
    c.drawString(50, 610, f"Course: {student[9]}")
    c.drawString(50, 580, f"Status: APPROVED")
    c.drawString(
        50,
        530,
        f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}"
    )
    c.drawString(
        50,
        480,
        "Congratulations! You are officially accepted."
    )
    c.save()
    return filename