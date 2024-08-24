import asyncio
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up your email credentials
EMAIL_ADDRESS = 'cybergottalent.se@gmail.com'
APP_PASSWORD = 'nanz wkos rloh mign'

# Function to send an email
async def send_email(recipient, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

# Function to fetch emails and names from SQLite database and send reminder emails
async def send_reminder_emails():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()

        # Create the 'customer' table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS customer (
                        email TEXT,
                        name TEXT
                     )''')

        # Fetch email and name from the customer table
        c.execute("SELECT email, name FROM customer")
        customers = c.fetchall()

        # Iterate through each customer and send reminder email
        for email, name in customers:
            # Customize the email body as needed
            subject = 'Påminnelse: Cyber Got Talent Show'
            body = f"Hej där {name},\n\n"
            body += f"Vi hoppas att ni har en fantastisk dag. Vi vill meddela er om en liten ändring i planerna för vår kommande Cyber Got Talent Show.\n\n"
            body += f"Eftersom vi kommer att ha öppet hus på Torsdag den 25 April har vi beslutat att skjuta upp evenemanget en dag framåt till "
            body += f"Fredag den 26 April klockan 12:00 till 13:00. Ingen oro, era platser som ni har köpt är fortfarande reserverade och väntar på er.\n\n"
            body += f"Om ni har några frågor eller behöver ytterligare information är ni välkomna att kontakta oss antingen via e-post på "
            body += f"cybergottalent.se@gmail.com eller genom våra sociala mediekanaler på Instagram (@cybergottalent_uf) och (@cybergottalent).\n\n"
            body += f"Glöm inte att det är bara två dagar kvar tills evenemanget. Vi hoppas att ni är lika spända som vi är och ser fram emot att få dela denna magiska dag med dig!\n\n"
            body += f"Med vänliga hälsningar,\nCyber Got Talent Teamet"

            # Send email
            await send_email(email, subject, body)

        # Close the database connection
        conn.close()
        print("Reminder emails sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_reminder_emails())
