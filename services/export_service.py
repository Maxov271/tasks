"""
Excel/CSV/JSON/PDF export funksiyalari. Katta hajmdagi export'lar har doim
Celery background task sifatida chaqiriladi (bot/handlers ichida to'g'ridan-to'g'ri
chaqirilmaydi) — tayyor bo'lgach fayl foydalanuvchiga yuboriladi.
"""
import csv
import io
import json


def export_tasks_to_csv(tasks) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Sarlavha", "Deadline", "Prioritet", "Bajarildimi"])
    for t in tasks:
        writer.writerow([t.id, t.title, t.deadline, t.priority, "Ha" if t.is_done else "Yo'q"])
    buffer.seek(0)
    return buffer


def export_tasks_to_json(tasks) -> str:
    data = [
        {
            "id": t.id, "title": t.title,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "priority": t.priority, "is_done": t.is_done,
        }
        for t in tasks
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_tasks_to_excel(tasks):
    """openpyxl talab qilinadi (requirements.txt'da bor)."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Tasks"
    ws.append(["ID", "Sarlavha", "Deadline", "Prioritet", "Bajarildimi"])
    for t in tasks:
        ws.append([t.id, t.title, str(t.deadline or ""), t.priority, "Ha" if t.is_done else "Yo'q"])
    return wb


def export_tasks_to_pdf(tasks, title="Vazifalar hisoboti"):
    """weasyprint yoki reportlab talab qilinadi. Bu yerda soddalashtirilgan
    reportlab misoli keltirilgan."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, title)
    y -= 30
    c.setFont("Helvetica", 10)
    for t in tasks:
        line = f"#{t.id} {t.title} — {t.priority} — {'bajarildi' if t.is_done else 'ochiq'}"
        c.drawString(50, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer
