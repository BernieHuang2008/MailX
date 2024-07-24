import os
import json
from email import policy
from email.parser import BytesParser
from datetime import datetime
from bs4 import BeautifulSoup

PARSED_FILES_RECORD = "parsed_files.json"
EMAILS_DIRECTORY = "emails"


def load_parsed_files():
    print("Loading parsed files record...")
    if os.path.exists(PARSED_FILES_RECORD):
        with open(PARSED_FILES_RECORD, "r") as f:
            data = json.load(f)
            print(f"Loaded parsed files: {data}")
            return data
    return {}


def save_parsed_files(parsed_files):
    print("Saving parsed files record...")
    with open(PARSED_FILES_RECORD, "w") as f:
        json.dump(parsed_files, f, indent=4)
    print(f"Saved parsed files: {parsed_files}")


def parse_eml_file(file_path, parsed_files):
    print(f"Parsing EML file: {file_path}")
    with open(file_path, 'rb') as f:
        message = BytesParser(policy=policy.default).parse(f)

    envelope_from = message["From"]
    envelope_to = message["To"]
    subject = message["Subject"]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    sanitized_subject = subject.replace(" ", "_").replace("/", "_").replace(":", "_")
    filename = f"{sanitized_subject}_{timestamp}"

    recipient_addresses = envelope_to.split(",")
    folders = []
    for recipient_address in recipient_addresses:
        local_part, domain = recipient_address.strip().split("@", 1)

        folder = os.path.join(EMAILS_DIRECTORY, local_part)
        folders.append(folder)
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: {folder}")

        save_email_content(folder, filename, message, envelope_from, envelope_to, subject, timestamp)
        create_identifier_file(folder, file_path, timestamp)

    parsed_files[file_path] = {"timestamp": timestamp, "folders": folders}


def save_email_content(folder: str, filename: str, message, envelope_from: str, envelope_to: str, subject: str,
                       timestamp: str) -> None:
    header_content = f"From: {envelope_from}\nTo: {envelope_to}\nSubject: {subject}\nDate: {timestamp}\n\n"
    text_content = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if part.get_content_maintype() == 'text':
                charset = part.get_content_charset() or 'utf-8'
                text = part.get_payload(decode=True).decode(charset)
                if content_type == "text/plain":
                    text_content += text + "\n\n"
                elif content_type == "text/html":
                    soup = BeautifulSoup(text, 'html.parser')
                    text_content += soup.get_text() + "\n\n"
            else:
                attachment_filename = part.get_filename()
                if attachment_filename:
                    attachment_data = part.get_payload(decode=True)
                    with open(os.path.join(folder, attachment_filename), "wb") as f:
                        f.write(attachment_data)
                    print(f"Saved attachment: {attachment_filename}")
    else:
        content_type = message.get_content_type()
        charset = message.get_content_charset() or 'utf-8'
        text = message.get_payload(decode=True).decode(charset)
        if content_type == "text/plain":
            text_content = text
        elif content_type == "text/html":
            soup = BeautifulSoup(text, 'html.parser')
            text_content = soup.get_text()

    with open(os.path.join(folder, f"{filename}.txt"), "w") as f:
        f.write(header_content)
        f.write(text_content)
    print(f"Saved email content to: {os.path.join(folder, f'{filename}.txt')}")


def create_identifier_file(folder, file_path, timestamp):
    identifier_content = {
        "file_path": file_path,
        "timestamp": timestamp
    }
    with open(os.path.join(folder, "identifier.json"), "w") as f:
        json.dump(identifier_content, f, indent=4)
    print(f"Created identifier file in: {folder}")


def check_identifier_files(parsed_files):
    if not os.path.exists(EMAILS_DIRECTORY):
        print(f"{EMAILS_DIRECTORY} directory does not exist. Skipping check.")
        return

    for local_part in os.listdir(EMAILS_DIRECTORY):
        folder = os.path.join(EMAILS_DIRECTORY, local_part)
        identifier_file = os.path.join(folder, "identifier.json")
        if os.path.exists(identifier_file):
            with open(identifier_file, "r") as f:
                identifier_content = json.load(f)
                file_path = identifier_content.get("file_path")
                timestamp = identifier_content.get("timestamp")
                if file_path not in parsed_files or parsed_files[file_path]["timestamp"] != timestamp:
                    if file_path in parsed_files:
                        del parsed_files[file_path]
                    os.remove(identifier_file)
                    print(f"Removed mismatched identifier file: {identifier_file}")
        else:
            # If identifier.json is missing, remove corresponding entry in parsed_files
            files_to_remove = [file for file, _ in parsed_files.items() if file.startswith(folder)]
            for file in files_to_remove:
                del parsed_files[file]
            print(f"Removed entries for missing identifier files in: {folder}")


def scan_eml_files(directory, first_run=False):
    parsed_files = load_parsed_files()
    current_files = set()

    # Ensure the emails directory exists
    if not os.path.exists(EMAILS_DIRECTORY):
        os.makedirs(EMAILS_DIRECTORY)
        print(f"Created emails directory: {EMAILS_DIRECTORY}")

    if not first_run:
        # Check identifier files and update JSON file
        check_identifier_files(parsed_files)

    # Scan and parse new files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".eml"):
                file_path = os.path.join(root, file)
                current_files.add(file_path)
                if file_path not in parsed_files:
                    print(f"Parsing new file: {file_path}")
                    parse_eml_file(file_path, parsed_files)
                else:
                    # Verify if the folders for the parsed file still exist
                    if all(os.path.exists(folder) for folder in parsed_files[file_path]["folders"]):
                        print(f"File already parsed: {file_path}")
                    else:
                        print(f"Folder for parsed file does not exist, re-parsing: {file_path}")
                        parse_eml_file(file_path, parsed_files)

    save_parsed_files(parsed_files)


if __name__ == "__main__":
    eml_directory = "eml"  # 你的eml文件夹路径
    if not os.path.exists(eml_directory):
        print(f"EML directory '{eml_directory}' does not exist.")
    else:
        first_run = not os.path.exists(PARSED_FILES_RECORD)
        scan_eml_files(eml_directory, first_run)
        print("Scan complete.")