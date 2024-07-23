import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

"""
read test.eml and send to localhost:25
"""
# Read the contents of the email file
with open('test.eml', 'r') as file:
    email_content = file.read()

# Create a MIME message object
msg = MIMEMultipart()
msg.attach(MIMEText(email_content, 'plain'))

# Set the sender and recipient
msg['From'] = 'berniehuang2008@163.com'
msg['To'] = 'bernie@openteens.org'

# Connect to the SMTP server and send the email
with smtplib.SMTP('localhost', 25) as server:
    server.send_message(msg)
