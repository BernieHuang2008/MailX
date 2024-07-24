import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email():
    from_address = "testsender@example.com"
    to_address = "testrecipient@example.com"
    subject = "Test Email with Attachment"
    body = "This is a test email with both plain text and HTML content."

    # 创建MIMEMultipart对象
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    # 添加纯文本部分
    msg.attach(MIMEText(body, 'plain'))

    # 添加HTML部分
    html = "<html><body><p>This is an <b>HTML</b> test email.</p></body></html>"
    msg.attach(MIMEText(html, 'html'))

    # 创建并添加附件
    filename = "test_attachment.txt"
    with open(filename, "w") as f:
        f.write("This is a test attachment.")

    attachment = MIMEBase('application', 'octet-stream')
    with open(filename, "rb") as f:
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
    msg.attach(attachment)

    # 设置SMTP服务器
    try:
        server = smtplib.SMTP('localhost', 25)  # 使用localhost和指定端口（假设SMTP服务器在本地运行）
        server.sendmail(from_address, to_address, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_email()