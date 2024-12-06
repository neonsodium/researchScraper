import os
import smtplib
import ssl
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_with_attachment(
    subject, body, sender_email, receiver_email, password, file_path, max_attachment_size_mb=25
):
    try:
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message["Bcc"] = receiver_email  # Recommended for mass emails

        # Add body to the email
        message.attach(MIMEText(body, "plain"))

        # Generate a unique filename for the attachment
        attachment_filename = os.path.basename(file_path)

        # Check file size
        file_size = os.path.getsize(file_path)  # in bytes
        if file_size > max_attachment_size_mb * 1024 * 1024:
            # File size exceeds the specified limit, send a link to the file on the server
            body_25mb = f"\n\nAttachment: File size exceeds {max_attachment_size_mb} MB. Download it from the server: http://ec2-3-96-154-236.ca-central-1.compute.amazonaws.com/output/{attachment_filename}"
            message.attach(MIMEText(body_25mb, "plain"))
        else:
            # Open the file in binary mode
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add a header with the unique filename for the attachment
            part.add_header("Content-Disposition", f"attachment; filename={attachment_filename}")

            # Add the attachment to the message
            message.attach(part)

        # Convert the message to a string
        text = message.as_string()

        # Log in to the server using a secure context and send the email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)

        print("Email sent successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if len(sys.argv) != 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

# Example usage:
subject = "Webscraping output file"
body = """The scraping process has been completed. Please find the output file attached.

attachment:
"""
sender_email = "connect.bankinglabs@gmail.com"
receiver_email = "vedanthicloud@gmail.com"
password = "acve ynep wrui tuvd"
filename = sys.argv[1]  # Get the filename from the command-line argument

send_email_with_attachment(subject, body, sender_email, receiver_email, password, filename)
