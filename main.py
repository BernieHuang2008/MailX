import os
import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage
from email.message import Message
from datetime import datetime

class CustomHandler(AsyncMessage):
    async def handle_message(self, message: Message) -> None:
        envelope_from = message["From"]
        envelope_to = message["To"]
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
            filename = f"email_{timestamp}"

            try:
                self.save_email_content(folder, filename, message)
            except Exception as e:
                print(f"Error saving email to {filename}: {e}")

    def save_email_content(self, folder: str, filename: str, message: Message) -> None:
        text_content = ""

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                if part.get_content_maintype() == 'text':
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
            f.write(text_content)

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