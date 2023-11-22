import imaplib
import email
import getpass
import argparse
from email.header import decode_header

min_mb_check = 5

def get_attachment_size_and_sender(message):
    size = 0
    sender = message.get('From')
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        payload = part.get_payload(decode=True)
        if payload:
            size += len(payload)
    return size, sender

def choose_message(messages_with_attachments):
    while True:
        print("\nChoose a message to delete (type 'exit' to quit):")
        for idx, (msg_id, size, sender) in enumerate(messages_with_attachments, start=1):
            print(f"{idx}. Sender: {sender}, Message ID: {msg_id}, Attachment Size: {size:.2f} MB")

        choice = input("Enter your choice (number): ").strip().lower()
        if choice == 'exit':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(messages_with_attachments):
            return messages_with_attachments[int(choice) - 1][0]  # Return the message ID
        else:
            print("Invalid choice, please try again.")

def delete_message(mail, msg_id):
    mail.store(msg_id, '+FLAGS', '\\Deleted')
    mail.expunge()
    print(f"Message ID {msg_id} has been deleted.")

def main(username, password, imap_url):
    mail = imaplib.IMAP4_SSL(imap_url)
    mail.login(username, password)
    mail.select('inbox')

    result, data = mail.search(None, 'ALL')
    mail_ids = data[0].split()

    messages_with_attachments = []

    for idx, msg_id in enumerate(mail_ids, 1):
        result, data = mail.fetch(msg_id, '(RFC822)')
        if result == 'OK':
            message = email.message_from_bytes(data[0][1])
            attachment_size, sender = get_attachment_size_and_sender(message)
            attachment_size_mb = attachment_size / (1024 * 1024)  # Convert to MB
            if attachment_size_mb >= min_mb_check:  # Filter messages with attachments >= 10 MB
                messages_with_attachments.append((msg_id.decode(), attachment_size_mb, sender))

        print(f"Processed {idx} of {len(mail_ids)} messages...", end='\r')

    messages_with_attachments.sort(key=lambda x: x[1], reverse=True)  # Sort by attachment size

    while messages_with_attachments:
        chosen_msg_id = choose_message(messages_with_attachments)
        if chosen_msg_id is None:
            break
        delete_message(mail, chosen_msg_id)
        messages_with_attachments = [msg for msg in messages_with_attachments if msg[0] != chosen_msg_id]

    mail.logout()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IMAP Attachment Analyzer")
    parser.add_argument("username", help="Email account username")
    parser.add_argument("server", help="IMAP server address")
    parser.add_argument("-p", "--password", help="Email account password", required=False)
    args = parser.parse_args()

    if args.password is None:
        args.password = getpass.getpass("Enter your password: ")

    main(args.username, args.password, args.server)
