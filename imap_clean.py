import imaplib
import email
from collections import Counter
import getpass
import argparse

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

    # Message deletion process
    while True:
        print("\nWhich sender's messages would you like to delete? (type 'exit' to quit)")
        chosen_sender = input("Enter the email address of the sender: ")

        if chosen_sender.lower() == 'exit':
            break
        else:
            # Delete
            delete_messages_from_sender(mail, chosen_sender)

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
