import imaplib
import email
from collections import Counter
import getpass
import argparse

def parse_folder(folder_info):
    # Split the folder information and return the parts
    parts = folder_info.decode().split(' ')
    return parts[0], parts[1], ' '.join(parts[2:]).strip('"')

def delete_messages_from_sender(mail, sender):
    # Select the folder (e.g., 'inbox')
    mail.select('inbox')

    # Search for all messages from the sender
    result, data = mail.search(None, f'(FROM "{sender}")')
    if result == 'OK':
        for num in data[0].split():
            mail.store(num, '+FLAGS', '\\Deleted')
        mail.expunge()
        print(f"All messages from {sender} have been deleted.")
    else:
        print("No messages found for this sender.")

def main(username, password, imap_url):
    # Connect to the IMAP server
    mail = imaplib.IMAP4_SSL(imap_url)
    mail.login(username, password)

    # Get the list of folders
    result, folders = mail.list()
    if result == 'OK':
        print("List of folders and number of messages in each:")
        for folder in folders:
            flags, delimiter, folder_name = parse_folder(folder)
            print(f"Attempting to select folder: {folder_name}")
            try:
                folder_name_quoted = '"' + folder_name.replace('"', '\\"') + '"'
                mail.select(f'"{folder_name_quoted}"', readonly=True)
                result, data = mail.search(None, 'ALL')
                if result == 'OK':
                    num_messages = len(data[0].split())
                    print(f"{folder_name}: {num_messages} messages")
            except imaplib.IMAP4.error as e:
                print(f"Error selecting folder {folder_name}: {e}")
    else:
        print("Unable to retrieve folder list.")
        mail.logout()
        exit()

    # Select the folder from which to count senders (e.g., 'inbox')
    mail.select('inbox')

    # Search for all messages
    result, data = mail.search(None, 'ALL')
    mail_ids = data[0].split()

    # Count the senders
    sender_count = Counter()

    total_emails = len(mail_ids)
    print(f"\nTotal messages to process in 'inbox': {total_emails}")

    for idx, block in enumerate(mail_ids, 1):
        result, data = mail.fetch(block, '(RFC822.HEADER)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                email_from = message['from']
                sender_count[email_from] += 1

        # Print the progress
        print(f"Processed {idx} of {total_emails} messages...", end='\r')

    # Filter and print senders with more than 100 messages
    print("\nSenders with more than 100 messages in 'inbox':")
    filtered_senders = [item for item in sender_count.items() if item[1] > 100]

    # Sort the filtered senders by message count, in descending order
    filtered_senders.sort(key=lambda x: x[1], reverse=True)

    for sender, count in filtered_senders:
        print(f"Sender: {sender}, Number of messages: {count}")

    # Message deletion process
    while True:
        if filtered_senders:
            print("\nWhich sender's messages would you like to delete? (type 'exit' to quit)")
            chosen_sender = input("Enter the email address of the sender: ")

            if chosen_sender.lower() == 'exit':
                break

            # Check if the chosen sender is in the list
            if any(chosen_sender in sender for sender, _ in filtered_senders):
                delete_messages_from_sender(mail, chosen_sender)
            else:
                print("Sender not found in the list of frequent senders or unrecognized command.")
        else:
            print("No sender with more than 100 messages found. Exiting.")
            break

    # Don't forget to close the connection
    mail.logout()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IMAP Email Counter")
    parser.add_argument("username", help="Email account username")
    parser.add_argument("server", help="IMAP server address")
    parser.add_argument("-p", "--password", help="Email account password", required=False)

    args = parser.parse_args()

    if args.password is None:
        args.password = getpass.getpass("Enter your password: ")

    main(args.username, args.password, args.server)