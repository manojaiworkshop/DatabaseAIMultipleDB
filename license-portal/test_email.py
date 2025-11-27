#!/usr/bin/env python3
"""
Email Debug Script for PGAIView License Portal
Tests SMTP configuration and email sending
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml
from pathlib import Path

def load_config():
    """Load config.yml"""
    config_path = Path(__file__).parent / 'config.yml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_smtp_connection(config):
    """Test SMTP connection"""
    print("=" * 60)
    print("🔍 Testing SMTP Connection")
    print("=" * 60)
    
    email_config = config.get('email', {})
    
    print(f"\n📧 Configuration:")
    print(f"   Enabled: {email_config.get('enabled')}")
    print(f"   SMTP Server: {email_config.get('smtp_server')}")
    print(f"   SMTP Port: {email_config.get('smtp_port')}")
    print(f"   Sender Email: {email_config.get('sender_email')}")
    print(f"   Password: {'*' * len(email_config.get('sender_password', ''))}")
    
    if not email_config.get('enabled'):
        print("\n⚠️  WARNING: Email is DISABLED in config.yml")
        print("   Set 'email.enabled: true' to enable email notifications")
        return False
    
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    sender_email = email_config.get('sender_email')
    sender_password = email_config.get('sender_password')
    
    if not all([smtp_server, sender_email, sender_password]):
        print("\n❌ Error: Incomplete email configuration")
        return False
    
    try:
        print("\n🔌 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        print("   ✅ Connected")
        
        print("\n🔐 Starting TLS...")
        server.starttls()
        print("   ✅ TLS started")
        
        print("\n🔑 Authenticating...")
        server.login(sender_email, sender_password)
        print("   ✅ Authentication successful")
        
        server.quit()
        print("\n✅ SMTP connection test PASSED!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you're using an App Password, not your regular Gmail password")
        print("   2. Generate App Password at: https://myaccount.google.com/apppasswords")
        print("   3. Remove spaces from the app password in config.yml")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify SMTP server and port are correct")
        print("   3. Check if firewall is blocking port 587")
        return False

def send_test_email(config, recipient):
    """Send a test email"""
    print("\n" + "=" * 60)
    print("📨 Sending Test Email")
    print("=" * 60)
    
    email_config = config.get('email', {})
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    sender_email = email_config.get('sender_email')
    sender_password = email_config.get('sender_password')
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "PGAIView License Portal - Test Email"
    message["From"] = sender_email
    message["To"] = recipient
    
    # Text version
    text = """
Hello!

This is a test email from PGAIView License Portal.

If you received this email, your SMTP configuration is working correctly!

Test Details:
- SMTP Server: {}
- Port: {}
- From: {}
- To: {}

Best regards,
PGAIView License Portal
    """.format(smtp_server, smtp_port, sender_email, recipient)
    
    # HTML version
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
      <h2 style="color: #0ea5e9;">✅ Email Test Successful!</h2>
      <p>Hello!</p>
      <p>This is a test email from <strong>PGAIView License Portal</strong>.</p>
      <p>If you received this email, your SMTP configuration is working correctly! 🎉</p>
      
      <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #0369a1;">Test Details</h3>
        <ul style="list-style: none; padding: 0;">
          <li><strong>SMTP Server:</strong> {smtp_server}</li>
          <li><strong>Port:</strong> {smtp_port}</li>
          <li><strong>From:</strong> {sender_email}</li>
          <li><strong>To:</strong> {recipient}</li>
        </ul>
      </div>
      
      <p style="font-size: 12px; color: #666;">
        Best regards,<br>
        <strong>PGAIView License Portal</strong>
      </p>
    </div>
  </body>
</html>
    """
    
    # Attach parts
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        print(f"\n📤 Sending email to: {recipient}")
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, message.as_string())
        
        print("\n✅ Email sent successfully!")
        print(f"\n📬 Check your inbox: {recipient}")
        print("   (Also check spam/junk folder)")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        return False

def main():
    """Main function"""
    print("\n" + "🔧" * 30)
    print("PGAIView License Portal - Email Debug Tool")
    print("🔧" * 30 + "\n")
    
    try:
        # Load config
        config = load_config()
        
        # Test connection
        if not test_smtp_connection(config):
            print("\n⚠️  Fix the issues above and try again")
            return
        
        # Ask for recipient
        print("\n" + "-" * 60)
        recipient = input("\n📧 Enter recipient email to send test message: ").strip()
        
        if not recipient:
            print("❌ No recipient provided")
            return
        
        # Send test email
        send_test_email(config, recipient)
        
        print("\n" + "=" * 60)
        print("✅ Email Debug Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Check your email inbox (and spam folder)")
        print("2. If you received the email, your configuration is correct")
        print("3. Make sure 'email.enabled: true' in config.yml")
        print("4. Restart the license portal: ./start.sh")
        
    except FileNotFoundError:
        print("❌ Error: config.yml not found")
        print("   Make sure you're running this from the license-portal directory")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
