import os
import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage
from email.message import Message


class CustomHandler(AsyncMessage):
    async def handle_message(self, message: Message) -> None:
        envelope_from = message["From"]
        envelope_to = message["To"]
        content = message.as_string()

        print(f"Message from: {envelope_from}")
        print(f"Message to  : {envelope_to}")
        print(f"Message data: {content}")

        # 假设收件人的电子邮件地址为单个地址，而不是多个地址
        recipient_address = envelope_to
        local_part, domain = recipient_address.split("@", 1)

        # 确保目标目录存在
        folder = os.path.join("emails", local_part)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 将电子邮件内容保存到文件
        with open(os.path.join(folder, "email.txt"), "a") as f:
            f.write(content + "\n\n")


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
