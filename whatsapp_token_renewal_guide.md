# 🔧 WhatsApp Access Token Renewal Guide

## 🚨 Current Issue
```
Error: "(#10) Application does not have permission for this action"
Cause: Access token expired or invalid
Solution: Generate new access token
```

## 📋 Step-by-Step Token Renewal

### Step 1: Access Facebook Developers Console
1. Go to: **https://developers.facebook.com/apps/**
2. Log in with your Facebook account
3. Find and click on your WhatsApp Business app

### Step 2: Navigate to WhatsApp Settings
1. In the left sidebar, click **"WhatsApp"**
2. Click **"API Setup"** or **"Getting Started"**
3. You should see your phone number ID: `668182639718247`

### Step 3: Generate New Access Token
1. Look for **"Access Token"** section
2. Click **"Generate Token"** button
3. Copy the entire token (starts with `EAA...`)
4. **Important**: This is a 24-hour temporary token

### Step 4: Update Your .env File
```bash
# Edit your .env file
nano .env

# Replace this line:
WHATSAPP_TOKEN=EAAKFEQYC7xgBPFIZBb4P7O27IEnZCnyEigZAeH4CQ7Dy9nXw99sB5ukHqGShpyv04TxgPY6e6l76Ka7kFsKyCl327GoXAoD3iPesJ1z2cHCPHlbP22oWh0wdSuxWJHWlxUkTm9nfjCVe0Bshm345JWxEZAPTGdZACAdvkAxqsdFnbJFlniGuz70jXZBKBtxqrpchytwwbcPrqXHOoPYkRZAklrKB91AtFl2nVkDUo9gXQZDZD

# With your new token:
WHATSAPP_TOKEN=your_new_token_here
```

## 🔄 Alternative: Get Permanent Token (Recommended)

### For Production Use:
1. In Facebook Developers, go to **"App Settings" → "Basic"**
2. Click **"Generate System User Token"**
3. Select permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
4. Set expiration to **"Never"**
5. Generate and copy token

## ✅ Verification Steps

### Test 1: Check Token Validity
```bash
curl -X GET "https://graph.facebook.com/v18.0/me?access_token=YOUR_NEW_TOKEN"
```

### Test 2: Check Phone Number Access
```bash
curl -X GET "https://graph.facebook.com/v18.0/668182639718247?access_token=YOUR_NEW_TOKEN"
```

### Test 3: Run Diagnostic Script
```bash
python3 diagnose_whatsapp_api.py
```

## 🚨 Common Issues

### Issue 1: Token Still Invalid
- **Solution**: Make sure you copied the entire token
- **Check**: Token should be 200+ characters long

### Issue 2: Permission Denied
- **Solution**: Ensure your app has `whatsapp_business_messaging` permission
- **Check**: App Review section in Facebook Developers

### Issue 3: Phone Number Not Found
- **Solution**: Verify phone number is added to your WhatsApp Business account
- **Check**: Business Manager → WhatsApp Accounts

## 📞 Quick Fix Commands

```bash
# 1. Test current token
python3 diagnose_whatsapp_api.py

# 2. After updating token, test again
python3 diagnose_whatsapp_api.py

# 3. Test your app
python3 app.py
```

## 🎯 Expected Results After Fix

✅ **Before (Current Error):**
```
Status Code: 401
Error: Session has expired
```

✅ **After (Fixed):**
```
Status Code: 200
✅ Phone number accessible
✅ Messaging permissions active
``` 