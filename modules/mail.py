import asyncio
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import re

# Set up your email credentials
EMAIL_ADDRESS = 'cybergottalent.se@gmail.com'
APP_PASSWORD = 'nanz wkos rloh mign'


# Function to send an email with an attachment
async def send_email(recipient, subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {attachment_path}')
            msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)


# Function to send a test reminder email with ticket details
async def send_test_email():
    recipient = 'itsaladdin1@gmail.com'
    subject = 'Redo för Cyber Got Talent Show'
    body = f"Hej där,\n\n"
    body += f"Vi hoppas att ni har en fantastisk dag. Vi vill meddela er om en liten ändring i planerna för vår kommande Cyber Got Talent Show.\n\n"
    body += f"Vi vill meddela dig om en viktig uppdatering gällande Cyber Got Talent Show, där du kommer att uppträda. På grund av att det "
    body += f"är öppet hus på skolan på torsdag den 25 april har vi beslutat att flytta evenemanget till fredag den 26 april.\n\n"
    body += f"Vi vill också informera dig om att vi kommer att ringa dig idag för att diskutera denna förändring närmare och säkerställa att "
    body += f"du är informerad och bekväm med det nya datumet och tiden.\n\nVi förstår att detta kan påverka dina förberedelser, och vi är här "
    body += f"för att stödja dig och svara på eventuella frågor eller funderingar du kan ha. Tveka inte att kontakta oss om det är något du vill "
    body += f"diskutera eller om det finns särskilda arrangemang vi behöver göra för ditt uppträdande.\n\n"
    body += f"Tack för din förståelse och flexibilitet i denna situation. Vi ser verkligen fram emot att se dig lysa på scenen under Cyber Got Talent Show!\n\n"
    body += f"Vänliga hälsningar,\nCyber Got Talent Teamet"

    # Extract name from the PDF and create a new PDF with ticket details
    pdf_path = 'Show.pdf'
    name = extract_name_from_pdf(pdf_path)
    if name:
        ticket_details = {'ticket_number': '00', 'row': '1', 'seat': '7'}
        attachment_path = add_ticket_details_to_pdf(pdf_path, name, ticket_details)
        await send_email(recipient, subject, body, attachment_path)
    else:
        await send_email(recipient, subject, body)

    print(f"Email sent successfully to {recipient}")


# Function to extract the name from a PDF file
def extract_name_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                print(f"Page text: {text}")  # Debugging output
                name_match = re.search(r'Namn:\s*(.*)', text)
                if name_match:
                    return name_match.group(1).strip()
    except Exception as e:
        print(f"Error extracting name from PDF: {e}")
    return None


# Function to add ticket details to the PDF
def add_ticket_details_to_pdf(pdf_path, name, ticket_details):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Add the ticket details to the PDF
    can.drawString(120, 450, name)
    can.drawString(120, 430, ticket_details['row'])
    can.drawString(200, 430, ticket_details['seat'])
    can.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)

    existing_pdf = PdfReader(open(pdf_path, "rb"))
    output = PdfWriter()

    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        if i == 0:  # Add text to the first page only
            page.merge_page(new_pdf.pages[0])
        output.add_page(page)

    output_path = f"{name}_ticket.pdf"
    with open(output_path, "wb") as outputStream:
        output.write(outputStream)

    return output_path


# Example usage
if __name__ == "__main__":
    asyncio.run(send_test_email())
