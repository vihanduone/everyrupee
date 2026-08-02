import resend

FROM_EMAIL = "EveryRupee <reports@oriax.online>"

def send_email(to, subject, html):

    try:

        resend.Emails.send({

            "from": FROM_EMAIL,

            "to": to,

            "subject": subject,

            "html": html

        })

        print("Email sent")

        return True

    except Exception as e:

        print(e)

        return False