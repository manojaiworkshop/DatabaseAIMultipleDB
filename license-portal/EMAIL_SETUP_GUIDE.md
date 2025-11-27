# Email Setup Guide - PGAIView License Portal

## Quick Setup (5 minutes)

### For Gmail Users (Recommended)

1. **Enable 2-Factor Authentication**
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it: "PGAIView License Portal"
   - Click "Generate"
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

3. **Update config.yml**
   ```yaml
   email:
     enabled: true
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "your-email@gmail.com"
     sender_password: "abcdefghijklmnop"  # Paste the 16-char app password
   ```

4. **Restart the Portal**
   ```bash
   cd license-portal
   ./start.sh
   ```

### For Outlook/Hotmail Users

1. **Update config.yml**
   ```yaml
   email:
     enabled: true
     smtp_server: "smtp.office365.com"
     smtp_port: 587
     sender_email: "your-email@outlook.com"
     sender_password: "your-outlook-password"
   ```

### For Other Email Providers

| Provider | SMTP Server | Port | Notes |
|----------|-------------|------|-------|
| Gmail | smtp.gmail.com | 587 | Requires app password |
| Outlook | smtp.office365.com | 587 | Use regular password |
| Yahoo | smtp.mail.yahoo.com | 587 | Requires app password |
| SendGrid | smtp.sendgrid.net | 587 | Use API key as password |
| AWS SES | email-smtp.us-east-1.amazonaws.com | 587 | Use SMTP credentials |
| Mailgun | smtp.mailgun.org | 587 | Use SMTP credentials |

## Testing Email Configuration

### Method 1: Generate a Test License

1. Open the portal: http://localhost:3000
2. Go to "Generate License" tab
3. Enter your email address
4. Fill in deployment ID and select license type
5. Click "Generate License"
6. Check your email inbox (and spam folder)

### Method 2: Python Test Script

Create `test_email.py`:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your config
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your-email@gmail.com"
sender_password = "your-app-password"
recipient = "test@example.com"

# Create message
message = MIMEMultipart()
message["Subject"] = "PGAIView License Portal - Test Email"
message["From"] = sender_email
message["To"] = recipient

body = "This is a test email from PGAIView License Portal!"
message.attach(MIMEText(body, "plain"))

# Send
try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, message.as_string())
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
```

Run:
```bash
python test_email.py
```

## Common Issues & Solutions

### Issue: "Authentication failed"
**Solution**: 
- Gmail: Make sure you're using an **app password**, not your regular Gmail password
- Outlook: Try enabling "Less secure app access" or use app password
- Check username is the full email address

### Issue: "Connection refused" or "Timeout"
**Solution**:
- Check SMTP server address is correct
- Verify port number (usually 587 for TLS, 465 for SSL)
- Check firewall isn't blocking outgoing connections
- Try `telnet smtp.gmail.com 587` to test connectivity

### Issue: Email not received
**Solution**:
- Check spam/junk folder
- Verify recipient email is correct
- Check backend logs: `tail -f backend/license_portal.log`
- Ensure `email.enabled: true` in config.yml

### Issue: "SMTP AUTH extension not supported"
**Solution**:
- Make sure using port 587 (not 25)
- Enable TLS/STARTTLS support
- Use `smtp.gmail.com` not `smtp.googlemail.com`

## Email Template Customization

Want to customize the email? Edit `backend/main.py`:

```python
def send_license_email(email: str, license_key: str, license_info: dict):
    # Find this section in the function:
    message["Subject"] = f"Your Custom Subject Here"
    
    # Customize HTML template:
    html = f"""
    <html>
      <body>
        <!-- Your custom HTML here -->
      </body>
    </html>
    """
```

## Security Best Practices

✅ **DO:**
- Use app-specific passwords (not regular passwords)
- Store credentials in `config.yml` with restricted permissions: `chmod 600 config.yml`
- Use environment variables in production: `EMAIL_PASSWORD=xxx`
- Enable 2-factor authentication on email accounts
- Use dedicated email account for sending (not personal account)

❌ **DON'T:**
- Commit passwords to version control (add `config.yml` to `.gitignore`)
- Share config.yml file with others
- Use same password for multiple services
- Store passwords in plain text in public repositories

## Production Deployment

For production, use environment variables:

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="noreply@yourcompany.com"
export SENDER_PASSWORD="your-app-password"
```

Update backend to read from environment:

```python
smtp_server = os.environ.get('SMTP_SERVER') or email_config.get('smtp_server')
sender_email = os.environ.get('SENDER_EMAIL') or email_config.get('sender_email')
sender_password = os.environ.get('SENDER_PASSWORD') or email_config.get('sender_password')
```

## Email Rate Limits

| Provider | Free Tier Limit | Notes |
|----------|----------------|-------|
| Gmail | 500/day | Per account |
| Outlook | 300/day | Per account |
| SendGrid | 100/day | Free tier |
| Mailgun | 100/day | Free tier |
| AWS SES | 200/day | After verification |

For high-volume needs, consider:
- Dedicated email service (SendGrid, Mailgun, AWS SES)
- Queue system for email delivery
- Multiple sender accounts

## Disable Email Feature

To turn off email notifications:

```yaml
email:
  enabled: false
```

Licenses will still be generated and displayed on screen, but won't be emailed.

## Support

If you're still having issues:
1. Check backend console for error messages
2. Review `config.yml` settings
3. Test with the Python script above
4. Check email provider's documentation
5. Open an issue on GitHub with error logs

---

**Last Updated**: 2025-11-02
