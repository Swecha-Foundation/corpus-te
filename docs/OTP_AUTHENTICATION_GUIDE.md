# OTP Authentication API Documentation

## Overview

The OTP (One-Time Password) authentication system provides a secure, phone number-based authentication mechanism for the Telugu corpus collections backend. Users can authenticate using their phone number by receiving an OTP via SMS.

## Features

- **SMS-based OTP delivery** using integrated SMS service
- **Rate limiting** to prevent abuse (configurable)
- **Secure OTP storage** with HMAC-based hashing
- **Automatic user creation** on successful OTP verification
- **JWT token generation** for authenticated sessions
- **Attempt tracking** and maximum retry limits
- **Expiry management** for OTP codes

## Environment Configuration

Add the following variables to your `.env` file:

```env
# OTP Service Configuration
OTP_USER_NAME=your_sms_service_username
OTP_ENTITY_ID=your_entity_id
OTP_TEMPLATE_ID=your_template_id
OTP_API_KEY=your_sms_api_key
OTP_SENDER_ID=SWECHA
OTP_SERVICE_URL=https://api.example.com/sendsms
OTP_SMS_TEXT=Your OTP code is: {otp}. Valid for 5 minutes.

# OTP Settings
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RATE_LIMIT_MINUTES=1
OTP_RATE_LIMIT_MAX_REQUESTS=3
```

## API Endpoints

### 1. Send OTP

**POST** `/api/v1/auth/send-otp`

Sends an OTP to the specified phone number.

**Request Body:**
```json
{
  "phone_number": "<PHONE_NUMBER>"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "OTP sent successfully",
  "reference_id": "<REFERENCE_ID>"
}
```

**Error Responses:**
- `429` - Rate limit exceeded
- `500` - SMS delivery failure

### 2. Verify OTP

**POST** `/api/v1/auth/verify-otp`

Verifies the OTP code and returns a JWT token on success.

**Request Body:**
```json
{
  "phone_number": "<PHONE_NUMBER>",
  "otp_code": "<OTP_CODE>"
}
```

**Response:**
```json
{
  "access_token": "<ACCESS_TOKEN>",
  "token_type": "bearer",
  "user_id": "<USER_ID>",
  "phone_number": "<PHONE_NUMBER>"
}
```

**Error Responses:**
- `400` - Invalid or expired OTP
- `400` - Maximum attempts exceeded

### 3. Resend OTP

**POST** `/api/v1/auth/resend-otp`

Resends a new OTP to the phone number (invalidates previous OTP).

**Request Body:**
```json
{
  "phone_number": "<PHONE_NUMBER>"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "OTP resent successfully",
  "reference_id": "<REFERENCE_ID>"
}
```

## Usage Examples

### Python Example

```python
import requests

# Send OTP
response = requests.post(
    "http://localhost:8000/api/v1/auth/send-otp",
    json={"phone_number": "<PHONE_NUMBER>"}
)

if response.status_code == 200:
    print("OTP sent successfully")
    
    # Get OTP from user
    otp_code = input("Enter OTP: ")
    
    # Verify OTP
    verify_response = requests.post(
        "http://localhost:8000/api/v1/auth/verify-otp",
        json={
            "phone_number": "+<PHONE_NUMBER>",
            "otp_code": otp_code
        }
    )
    
    if verify_response.status_code == 200:
        token_data = verify_response.json()
        access_token = token_data["access_token"]
        
        # Use token for authenticated requests
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(
            "http://localhost:8000/api/v1/auth/me",
            headers=headers
        )
        
        print("User info:", user_response.json())
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function authenticateWithOTP(phoneNumber, otpCode) {
    try {
        // Send OTP
        const sendResponse = await axios.post(
            'http://localhost:8000/api/v1/auth/send-otp',
            { phone_number: phoneNumber }
        );
        
        console.log('OTP sent:', sendResponse.data.message);
        
        // Verify OTP
        const verifyResponse = await axios.post(
            'http://localhost:8000/api/v1/auth/verify-otp',
            {
                phone_number: phoneNumber,
                otp_code: otpCode
            }
        );
        
        const { access_token } = verifyResponse.data;
        
        // Use token for authenticated requests
        const userResponse = await axios.get(
            'http://localhost:8000/api/v1/auth/me',
            {
                headers: {
                    'Authorization': `Bearer ${access_token}`
                }
            }
        );
        
        console.log('User info:', userResponse.data);
        
    } catch (error) {
        console.error('Authentication error:', error.response?.data || error.message);
    }
}
```

## Security Features

### 1. OTP Hashing
- OTPs are hashed using HMAC-SHA256 before storage
- Phone number is used as salt for additional security
- Stored hashes cannot be reversed to get original OTP

### 2. Rate Limiting
- Configurable rate limits prevent abuse
- Default: 3 requests per minute per phone number
- Applies to both send and resend operations

### 3. Attempt Tracking
- Maximum verification attempts per OTP (default: 3)
- OTP becomes invalid after max attempts reached
- Forces new OTP request after exhausting attempts

### 4. Expiry Management
- OTPs expire after configured time (default: 5 minutes)
- Expired OTPs are automatically invalid
- Cleanup of old OTP records

## Database Schema

The OTP system uses the following database table:

```sql
CREATE TABLE otp (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR NOT NULL,
    otp_hash VARCHAR NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    reference_id VARCHAR NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_otp_phone_number ON otp (phone_number);
```

## Configuration Details

### SMS Service Integration

The system integrates with SMS services using the following format:

```python
{
    "userName": "your_username",
    "entityId": "your_entity_id", 
    "templateId": "your_template_id",
    "apiKey": "your_api_key",
    "senderId": "SWECHA",
    "smsText": "Your OTP code is: {otp}. Valid for 5 minutes.",
    "mobile": "<PHONE_NUMBER>",
}
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OTP_USER_NAME` | SMS service username | - | Yes |
| `OTP_ENTITY_ID` | SMS service entity ID | - | Yes |
| `OTP_TEMPLATE_ID` | SMS template ID | - | Yes |
| `OTP_API_KEY` | SMS service API key | - | Yes |
| `OTP_SENDER_ID` | SMS sender ID | `<SENDER_ID>` | No |
| `OTP_SERVICE_URL` | SMS service endpoint | - | Yes |
| `OTP_SMS_TEXT` | OTP SMS template | `Your OTP code is: {otp}. Valid for 5 minutes.` | No |
| `OTP_EXPIRY_MINUTES` | OTP expiry time | `5` | No |
| `OTP_MAX_ATTEMPTS` | Max verification attempts | `3` | No |
| `OTP_RATE_LIMIT_MINUTES` | Rate limit window | `1` | No |
| `OTP_RATE_LIMIT_MAX_REQUESTS` | Max requests per window | `3` | No |

## Testing

Use the provided test script:

```bash
python test_otp_api.py
```

This script will:
1. Send an OTP to the configured phone number
2. Prompt for the received OTP code
3. Verify the OTP and get a JWT token
4. Test accessing an authenticated endpoint
5. Test the resend functionality

## Error Handling

The API provides detailed error responses:

### Common Error Codes

- `400` - Bad Request (invalid OTP, max attempts exceeded)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (SMS service failure, database error)

### Error Response Format

```json
{
  "detail": "Invalid or expired OTP"
}
```

## Integration with Frontend

### Flutter/Dart Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class OTPService {
  static const String baseUrl = 'http://localhost:8000/api/v1/auth';
  
  static Future<bool> sendOTP(String phoneNumber) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/send-otp'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'phone_number': phoneNumber}),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Error sending OTP: $e');
      return false;
    }
  }
  
  static Future<String?> verifyOTP(String phoneNumber, String otpCode) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/verify-otp'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'phone_number': phoneNumber,
          'otp_code': otpCode,
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['access_token'];
      }
      
      return null;
    } catch (e) {
      print('Error verifying OTP: $e');
      return null;
    }
  }
}
```

## Monitoring and Logging

The system provides comprehensive logging:

- OTP generation and sending events
- Verification attempts and results
- Rate limiting triggers
- SMS service responses
- Database operations

Log levels:
- `INFO` - Normal operations
- `ERROR` - Failures and exceptions
- `DEBUG` - Detailed operation flow (development only)

## Best Practices

1. **Environment Security**: Keep SMS service credentials secure
2. **Rate Limiting**: Configure appropriate limits for your use case
3. **Monitoring**: Monitor SMS delivery rates and costs
4. **Cleanup**: Regularly clean up expired OTP records
5. **Testing**: Use test phone numbers during development
6. **Backup**: Implement fallback authentication methods

## Troubleshooting

### Common Issues

1. **SMS not received**: Check SMS service configuration and credits
2. **Rate limit errors**: Adjust rate limiting settings
3. **Database connection**: Ensure PostgreSQL is running
4. **Invalid OTP**: Check OTP expiry and attempt limits

### Debug Mode

Enable debug logging in development:

```python
import logging
logging.getLogger("app.services.otp_service").setLevel(logging.DEBUG)
```

This will show generated OTP codes in logs for testing purposes.
