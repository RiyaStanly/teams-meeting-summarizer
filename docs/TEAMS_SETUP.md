# Microsoft Teams Integration Setup Guide

Complete guide to setting up Microsoft Teams API integration for accessing live meetings and calendar events.

---

## Overview

This guide covers:
1. Azure AD app registration
2. API permissions configuration
3. Authentication setup
4. Testing Teams connectivity

**Time Required:** ~15 minutes

---

## Prerequisites

- Microsoft 365 account (work/school or developer account)
- Azure AD admin access (or developer tenant)
- Teams Meeting Summarizer installed

---

## Step 1: Get Microsoft 365 Developer Account (Optional)

If you don't have a work/school Microsoft 365 account:

1. **Join Microsoft 365 Developer Program:**
   - Visit: https://developer.microsoft.com/microsoft-365/dev-program
   - Click **"Join now"**
   - Sign in with Microsoft account
   - Complete profile

2. **Create Developer Tenant:**
   - Set up instant sandbox (E5 subscription)
   - Choose admin username and password
   - **Save credentials** - you'll need these

3. **Access Admin Portal:**
   - Go to https://admin.microsoft.com/
   - Sign in with developer account

---

## Step 2: Register Application in Azure AD

1. **Navigate to Azure Portal:**
   - Go to https://portal.azure.com/
   - Sign in with Microsoft 365 account

2. **Open Azure Active Directory:**
   - Search for **"Azure Active Directory"**
   - Click to open

3. **Register New Application:**
   - Click **"App registrations"** in left menu
   - Click **"+ New registration"**

4. **Configure Application:**
   ```
   Name: Teams Meeting Summarizer
   Supported account types: 
     ○ Accounts in this organizational directory only (Single tenant)
     ● Accounts in any organizational directory (Multi-tenant)
   
   Redirect URI:
     Platform: Web
     URL: http://localhost:8000/auth/callback
   ```

5. **Click "Register"**

6. **Copy Application Details:**
   - **Application (client) ID** - Save this
   - **Directory (tenant) ID** - Save this

---

## Step 3: Create Client Secret

1. **In your app registration:**
   - Click **"Certificates & secrets"** in left menu

2. **Create New Secret:**
   - Click **"+ New client secret"**
   - Description: "Teams Summarizer Secret"
   - Expires: 24 months (recommended)
   - Click **"Add"**

3. **Copy Secret Value:**
   - **IMPORTANT:** Copy the **Value** immediately
   - You won't be able to see it again
   - **Save this securely**

---

## Step 4: Configure API Permissions

1. **Click "API permissions"** in left menu

2. **Add Permissions:**
   - Click **"+ Add a permission"**
   - Select **"Microsoft Graph"**
   - Select **"Delegated permissions"**

3. **Select Required Permissions:**
   
   **For Meeting Access:**
   - `OnlineMeetings.Read` - Read online meetings
   - `OnlineMeetings.ReadWrite` - Read and create meetings
   
   **For Calendar:**
   - `Calendars.Read` - Read user calendars
   - `Calendars.ReadWrite` - Read and write calendars (optional)
   
   **For User Info:**
   - `User.Read` - Sign in and read user profile
   
   **For Attendance (Optional):**
   - `OnlineMeetingArtifact.Read.All` - Read meeting artifacts

4. **Click "Add permissions"**

5. **Grant Admin Consent:**
   - Click **"✓ Grant admin consent for [Your Organization]"**
   - Click **"Yes"** to confirm
   - Status should show green checkmarks

---

## Step 5: Configure Application

1. **Copy `.env.example` to `.env`** (if not already done):
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   # Microsoft Teams Integration
   TEAMS_CLIENT_ID=your_application_client_id_from_step_2
   TEAMS_CLIENT_SECRET=your_client_secret_from_step_3
   TEAMS_TENANT_ID=your_directory_tenant_id_from_step_2
   TEAMS_REDIRECT_URI=http://localhost:8000/auth/callback
   ```

3. **Save file**

---

## Step 6: Install Dependencies

```bash
# Install required packages
pip install msal msgraph-sdk azure-identity

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 7: Test Authentication

### Test 1: Device Code Flow

```python
from src.teams_integration import TeamsAuthManager

# Initialize auth manager
auth = TeamsAuthManager(use_device_code=True)

# Authenticate (will prompt for device code)
token = auth.authenticate()

print(f"✓ Successfully authenticated!")
print(f"Token: {token[:50]}...")
```

**Expected Output:**
```
=============================================================
MICROSOFT TEAMS AUTHENTICATION
=============================================================

To sign in, use a web browser to open the page https://microsoft.com/devicelogin 
and enter the code ABC12DEF to authenticate.

=============================================================
```

**Follow the prompts**, then you should see:
```
✓ Authentication successful!
```

### Test 2: List Meetings

```python
from src.teams_integration import TeamsAuthManager, TeamsMeetingsClient

# Authenticate
auth = TeamsAuthManager(use_device_code=True)
auth.authenticate()

# Create client
client = TeamsMeetingsClient(auth)

# List meetings
meetings = client.list_user_meetings(limit=5)

print(f"Found {len(meetings)} upcoming meetings:")
for meeting in meetings:
    print(f"- {meeting.get('subject', 'No subject')}")
```

### Test 3: Check Calendar Events

```python
from datetime import datetime, timedelta

events = client.list_calendar_events(
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=7)
)

print(f"Found {len(events)} Teams meetings in next 7 days")
```

---

## Features Enabled

Once configured, you can:

### ✅ Authenticate with Teams
```python
from src.teams_integration import TeamsAuthManager

auth = TeamsAuthManager()
auth.authenticate()  # Device code flow
```

### ✅ List Upcoming Meetings
```python
client = TeamsMeetingsClient(auth)
meetings = client.list_user_meetings()
```

### ✅ Access Meeting Details
```python
meeting = client.get_meeting_details(meeting_id)
print(meeting['subject'], meeting['startDateTime'])
```

### ✅ Get Participants
```python
participants = client.get_meeting_participants(meeting_id)
for p in participants:
    print(p['identity']['displayName'])
```

---

## API Endpoints (Future Enhancement)

The following endpoints are planned for future releases:

- `POST /meetings/join` - Join Teams meeting and start transcription
- `GET /meetings/active` - List active transcription sessions
- `DELETE /meetings/leave/{id}` - Stop transcription and leave meeting

---

## Authentication Flows

### Device Code Flow (Recommended for CLI)
- **Use when:** Running scripts locally, CLI tools
- **User experience:** Opens browser, enters code
- **Security:** User authenticates directly with Microsoft

### Client Credentials Flow (For App-Only Access)
- **Use when:** Backend services, automated tasks
- **User experience:** No user interaction
- **Security:** App authenticates as itself
- **Requires:** Admin-consented app permissions

---

## Troubleshooting

### Error: "AADSTS7000215: Invalid client secret"
- **Solution:** Regenerate client secret in Azure portal
- Update `TEAMS_CLIENT_SECRET` in `.env`

### Error: "AADSTS65001: Consent required"
- **Solution:** Grant admin consent in Azure portal
- API permissions → Grant admin consent

### Error: "Insufficient privileges to complete the operation"
- **Solution:** Add required API permissions
- Ensure admin consent granted

### Error: "Device code expired"
- **Solution:** Re-run authentication
- Complete device code flow within 15 minutes

### No meetings returned
- **Solution:** Ensure you have Teams meetings scheduled
- Check account has Teams license
- Try listing calendar events instead

---

## Security Best Practices

1. **Protect Client Secret:**
   - Never commit to Git
   - Rotate regularly (every 6-12 months)
   - Use Azure Key Vault in production

2. **Minimize Permissions:**
   - Only request permissions you need
   - Use least-privilege principle

3. **Token Management:**
   - Don't log tokens
   - Implement token refresh
   - Validate token expiration

4. **Production Deployment:**
   - Use managed identities when possible
   - Enable conditional access policies
   - Monitor authentication logs

---

## Permissions Reference

| Permission | Type | Description | Required For |
|-----------|------|-------------|--------------|
| `User.Read` | Delegated | Read user profile | Authentication |
| `OnlineMeetings.Read` | Delegated | Read meetings | List meetings |
| `OnlineMeetings.ReadWrite` | Delegated | Create/modify meetings | Join meetings |
| `Calendars.Read` | Delegated | Read calendar | Find meetings |
| `OnlineMeetingArtifact.Read.All` | Application | Read artifacts | Attendance reports |

**Documentation:** https://learn.microsoft.com/graph/permissions-reference

---

## Resources

- **Azure Portal:** https://portal.azure.com/
- **Graph Explorer:** https://developer.microsoft.com/graph/graph-explorer
- **Teams API Docs:** https://learn.microsoft.com/graph/api/resources/onlinemeeting
- **MSAL Python:** https://github.com/AzureAD/microsoft-authentication-library-for-python
- **Developer Program:** https://developer.microsoft.com/microsoft-365/dev-program

---

## Limitations & Known Issues

1. **Meeting Audio Access:**
   - Requires Teams bot framework for real-time audio
   - Currently supports: transcript parsing from exports
   - Future: Live audio stream capture

2. **Rate Limits:**
   - Graph API: ~2,000 requests/app/second
   - Throttling applies to heavy usage

3. **Permissions:**
   - Some features require admin consent
   - Personal accounts have limited access

---

## Next Steps

After Teams integration is configured:

1. ✅ Test listing your scheduled meetings
2. ✅ Parse Teams meeting exports (JSON format)
3. [ ] Implement real-time meeting bot (advanced)
4. [ ] Deploy with Azure App Service for production

---

**Setup Complete!** You can now access Teams meetings via Microsoft Graph API. 🎉

For issues or questions, see the troubleshooting section or open an issue on GitHub.
