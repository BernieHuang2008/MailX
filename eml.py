import os
from email import policy
from email.parser import BytesParser
from datetime import datetime


def parse_eml_file(file_path):
    with open(file_path, 'rb') as f:
        message = BytesParser(policy=policy.default).parse(f)

    envelope_from = message["From"]
    envelope_to = message["To"]
    subject = message["Subject"]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    sanitized_subject = subject.replace(" ", "_").replace("/", "_")
    filename = f"{sanitized_subject}_{timestamp}"

    recipient_addresses = envelope_to.split(",")
    for recipient_address in recipient_addresses:
        local_part, domain = recipient_address.strip().split("@", 1)

        folder = os.path.join("emails", local_part)
        if not os.path.exists(folder):
            os.makedirs(folder)

        save_email_content(folder, filename, message, envelope_from, envelope_to, subject, timestamp)


def save_email_content(folder: str, filename: str, message, envelope_from: str, envelope_to: str, subject: str,
                       timestamp: str) -> None:
    # 保存头部信息
    header_content = f"From: {envelope_from}\nTo: {envelope_to}\nSubject: {subject}\nDate: {timestamp}\n\n"

    text_content = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if part.get_content_maintype() == 'text' and content_type == "text/plain":
                text = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                text_content += text + "\n\n"
            else:
                attachment_filename = part.get_filename()
                if attachment_filename:
                    attachment_data = part.get_payload(decode=True)
                    with open(os.path.join(folder, attachment_filename), "wb") as f:
                        f.write(attachment_data)
    else:
        text_content = message.get_payload(decode=True).decode(message.get_content_charset() or 'utf-8')

    with open(os.path.join(folder, f"{filename}.txt"), "w") as f:
        f.write(header_content)
        f.write(text_content)


if __name__ == "__main__":
    parse_eml_file("test.eml")