from io import BytesIO
import requests
import qrcode

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

from database.db import get_membership


def create_membership_pdf(telegram_id):
    member = get_membership(telegram_id)
    if not member:
        return None

    # CR80 Dimensions in Points (Standard Credit/ID Card size: 3.375" x 2.125")
    CARD_WIDTH = 243
    CARD_HEIGHT = 153
    CORNER_RADIUS = 8  # Subtle, clean corner rounding

    file = BytesIO()
    pdf = canvas.Canvas(file, pagesize=(CARD_WIDTH, CARD_HEIGHT))
    pdf.setTitle("Membership Card")

    # DATABASE MAP
    member_code = str(member[1] or "0000").strip()
    full_name = str(member[2] or "Unknown").strip()
    phone = str(member[4] or "-").strip()
    membership_type = str(member[8] or "Basic").strip().upper()
    expiry = str(member[11] or "-").strip()
    status = str(member[12] or "Pending").strip().upper()
    photo = member[14] if len(member) > 14 else None

    # Premium Corporate Color Palette
    PRIMARY = HexColor("#0F172A")    # Sleek Slate Dark (Header/Primary)
    ACCENT_GOLD = HexColor("#D97706") # Rich Amber/Gold
    BG_CARD = HexColor("#FFFFFF")     # Clean Stark White
    TEXT_MAIN = HexColor("#1E293B")   # Charcoal Body text
    TEXT_MUTED = HexColor("#64748B")  # Soft Slate Grey labels
    LIGHT_GRAY = HexColor("#F1F5F9")  # Photo placeholder fallback

    # ==========================================
    # 1. DEFINE ROUNDED CARD CLIP PATH (No corner artifacts)
    # ==========================================
    path = pdf.beginPath()
    path.roundRect(0, 0, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS)
    pdf.saveState()
    pdf.clipPath(path, stroke=0, fill=1)

    # Base background color fill within clipped area
    pdf.setFillColor(BG_CARD)
    pdf.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=True, stroke=False)

    # ==========================================
    # 2. HEADER BANNER DESIGN
    # ==========================================
    HEADER_H = 32
    pdf.setFillColor(PRIMARY)
    pdf.rect(0, CARD_HEIGHT - HEADER_H, CARD_WIDTH, HEADER_H, fill=True, stroke=False)
    
    # Elegant gold stripe divider accent underneath header
    pdf.setFillColor(ACCENT_GOLD)
    pdf.rect(0, CARD_HEIGHT - HEADER_H - 2, CARD_WIDTH, 2, fill=True, stroke=False)

    # Header Title Typography
    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(12, CARD_HEIGHT - 20, "KAAYYOO KOOF MEMBERSHIP")

    # ==========================================
    # 3. PHOTO DESIGN (Aligned perfectly with details)
    # ==========================================
    photo_x = 12
    photo_y = 48
    photo_w = 46
    photo_h = 56

    # Draw border framework for picture slot
    pdf.setStrokeColor(HexColor("#E2E8F0"))
    pdf.setLineWidth(1)
    pdf.rect(photo_x, photo_y, photo_w, photo_h, fill=False, stroke=True)

    photo_loaded = False
    if photo and str(photo).startswith("http"):
        try:
            response = requests.get(photo, timeout=5)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                pdf.drawImage(ImageReader(img_data), photo_x+0.5, photo_y+0.5, photo_w-1, photo_h-1)
                photo_loaded = True
        except:
            photo_loaded = False

    if not photo_loaded:
        # Minimalist placeholder if request fails or lacks image
        pdf.setFillColor(LIGHT_GRAY)
        pdf.rect(photo_x+0.5, photo_y+0.5, photo_w-1, photo_h-1, fill=True, stroke=False)
        pdf.setFillColor(TEXT_MUTED)
        pdf.setFont("Helvetica-Bold", 6)
        pdf.drawCentredString(photo_x + (photo_w / 2), photo_y + 32, "NO")
        pdf.drawCentredString(photo_x + (photo_w / 2), photo_y + 22, "PHOTO")

    # ==========================================
    # 4. TYPOGRAPHY & LAYOUT (Left Side Data Columns)
    # ==========================================
    data_x = 68
    start_y = CARD_HEIGHT - 48
    
    # Member Name (Large focal point)
    pdf.setFillColor(TEXT_MAIN)
    pdf.setFont("Helvetica-Bold", 10)
    # Crop extremely long text cleanly to prevent layout spillover
    display_name = full_name[:22] + "..." if len(full_name) > 22 else full_name
    pdf.drawString(data_x, start_y, display_name)

    # Member ID Subtext block
    pdf.setFillColor(TEXT_MUTED)
    pdf.setFont("Helvetica", 6)
    pdf.drawString(data_x, start_y - 12, "MEMBER ID")
    pdf.setFillColor(TEXT_MAIN)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(data_x, start_y - 21, member_code)

    # Contact Details
    pdf.setFillColor(TEXT_MUTED)
    pdf.setFont("Helvetica", 6)
    pdf.drawString(data_x, start_y - 32, "CONTACT")
    pdf.setFillColor(TEXT_MAIN)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(data_x, start_y - 40, phone)

    # Membership Class/Tier
    pdf.setFillColor(ACCENT_GOLD)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawString(data_x, start_y - 52, f"{membership_type} TIER")

    # ==========================================
    # 5. FOOTER DESIGN (Status & Expiry)
    # ==========================================
    # Adaptive Pill-Badge Color Scheme for Account Status
    badge_bg = HexColor("#DEF7EC") if status == "APPROVED" else HexColor("#FFEDD5")
    badge_text = HexColor("#03543F") if status == "APPROVED" else HexColor("#9A3412")

    badge_x = 12
    badge_y = 16
    badge_w = 54
    badge_h = 14

    # Status Pill Container
    pdf.setFillColor(badge_bg)
    pdf.roundRect(badge_x, badge_y, badge_w, badge_h, 4, fill=True, stroke=False)
    
    # Status Pill Text
    pdf.setFillColor(badge_text)
    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.drawCentredString(badge_x + (badge_w / 2), badge_y + 4.5, status)

    # Expiry Meta Text Right next to the status pill
    pdf.setFillColor(TEXT_MUTED)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(data_x + 2, badge_y + 4.5, f"Expires: {expiry}")

    # ==========================================
    # 6. QR CODE SYSTEM (Perfect square layout alignment)
    # ==========================================
    qr_text = f"ID:{member_code}\nName:{full_name}\nPhone:{phone}\nTier:{membership_type}\nExp:{expiry}"
    
    qr = qrcode.QRCode(box_size=4, border=0)
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    qr_img.save(buf, format="PNG") # type: ignore
    buf.seek(0)

    qr_size = 46
    qr_x = CARD_WIDTH - qr_size - 14
    qr_y = 20

    # Draw the QR
    pdf.drawImage(ImageReader(buf), qr_x, qr_y, qr_size, qr_size)
    
    # Bottom Center Caption under verification code
    pdf.setFillColor(TEXT_MUTED)
    pdf.setFont("Helvetica-Bold", 4.5)
    pdf.drawCentredString(qr_x + (qr_size / 2), qr_y - 6, "SCAN TO VERIFY")

    # Restore regular non-clipping operations before applying standard card stroke cut out 
    pdf.restoreState()

    # Outer Thin Technical Cut Guide line (exactly on the outer canvas seam)
    pdf.setStrokeColor(HexColor("#CBD5E0"))
    pdf.setLineWidth(0.75)
    pdf.roundRect(0, 0, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, fill=False, stroke=True)

    pdf.showPage()
    pdf.save()

    file.seek(0)
    file.name = f"{member_code}_membership_card.pdf"
    return file