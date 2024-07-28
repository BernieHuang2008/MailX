import os
import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage
from email import policy
from email.parser import BytesParser
from email.message import Message
from datetime import datetime


class CustomHandler(AsyncMessage):
    async def handle_message(self, message: Message) -> None:
        await self.process_message(message)

    async def process_message(self, message: Message) -> None:
        envelope_from = message["From"]
        envelope_to = message["To"]
        subject = message["Subject"]
        content = message.as_string()

        print(f"Message from: {envelope_from}")
        print(f"Message to  : {envelope_to}")
        print(f"Message data: {content}")

        recipient_addresses = envelope_to.split(",")
        for recipient_address in recipient_addresses:
            local_part, domain = recipient_address.strip().split("@", 1)

            folder = os.path.join("emails", local_part)
            if not os.path.exists(folder):
                os.makedirs(folder)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            sanitized_subject = subject.replace(" ", "_").replace("/", "_")
            filename = f"{sanitized_subject}_{timestamp}"

            try:
                self.save_email_content(folder, filename, message, envelope_from, envelope_to, subject, timestamp)
            except Exception as e:
                print(f"Error saving email to {filename}: {e}")

    def save_email_content(self, folder: str, filename: str, message: Message, envelope_from: str, envelope_to: str,
                           subject: str, timestamp: str) -> None:
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

    def process_eml_file(self, file_path: str) -> None:
        with open(file_path, 'rb') as f:
            message = BytesParser(policy=policy.default).parse(f)
        asyncio.run(self.process_message(message))


async def main():
    handler = CustomHandler()
    controller = Controller(handler, hostname="0.0.0.0", port=25)
    controller.start()
    print("Server started on localhost:25")

    try:
        await asyncio.Event().wait()  # Keep the server running
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()


if __name__ == "__main__":
    asyncio.run(main())