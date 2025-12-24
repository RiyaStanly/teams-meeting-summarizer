# Azure Speech-to-Text Setup Guide

Complete guide to setting up Azure Cognitive Services Speech-to-Text for the Teams Meeting Summarizer.

---

## Prerequisites

- Azure account (free tier available)
- Credit card for verification (no charges with free tier)
- Python environment set up

---

## Step 1: Create Azure Account

1. **Go to** https://azure.microsoft.com/free/
2. **Click** "Start free"
3. **Sign in** with Microsoft account or create new
4. **Complete** verification (requires credit card, but won't be charged)
5. **Activate** free credits ($200 for 30 days + 12 months of free services)

---

## Step 2: Create Speech Service Resource

1. **Navigate to Azure Portal**: https://portal.azure.com/

2. **Create Resource:**
   - Click **"Create a resource"**
   - Search for **"Speech"**
   - Select **"Speech"** (by Microsoft)
   - Click **"Create"**

3. **Configure Speech Service:**
   ```
   Subscription: Your subscription
   Resource Group: Create new → "teams-summarizer-rg"
   Region: East US (or nearest to you)
   Name: "teams-summarizer-speech"
   Pricing Tier: Free F0 (5 hours/month) or Standard S0
   ```

4. **Review + Create:**
   - Click **"Review + create"**
   - Click **"Create"**
   - Wait for deployment (~1 minute)

---

## Step 3: Get API Keys

1. **Go to Resource:**
   - Click **"Go to resource"** after deployment
   - Or find it in **"All resources"**

2. **Copy Keys:**
   - In left menu, click **"Keys and Endpoint"**
   - Copy **KEY 1** (or KEY 2)
   - Copy **REGION** (e.g., "eastus")

   **Important:** Keep these secret! Don't commit to GitHub.

---

## Step 4: Configure Application

1. **Copy `.env.example` to `.env`:**
   ```bash
   cd "/Users/riyastanly/Desktop/Teams meeting Summarization"
   cp .env.example .env
   ```

2. **Edit `.env` file:**
   ```bash
   # Add your Azure credentials
   AZURE_SPEECH_KEY=your_key_here_from_step_3
   AZURE_SPEECH_REGION=eastus
   AZURE_SPEECH_LANGUAGE=en-US
   AZURE_SPEECH_ENABLE_DIARIZATION=true
   ```

3. **Save file**

---

## Step 5: Install Azure SDK

```bash
# Install Python package
pip install azure-cognitiveservices-speech==1.35.0

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 6: Test Setup

### Test 1: Verify Installation

```bash
python -c "import azure.cognitiveservices.speech as speechsdk; print('✓ Azure Speech SDK installed')"
```

### Test 2: Test with Sample Audio

```bash
# Download sample audio (or use your own)
# Create test file
echo "This is a test" | say -o test.aiff
ffmpeg -i test.aiff test.wav

# Transcribe
python scripts/transcribe_audio.py --audio test.wav --output outputs/test
```

**Expected Output:**
```
Transcribing audio file: test.wav
Transcription complete: XX characters
✓ Saved transcript: outputs/test/test_transcript.txt
```

### Test 3: Test via API

```bash
# Start API server
make api

# In another terminal, upload audio
curl -X POST "http://localhost:8000/meetings/upload-audio" \
  -F "file=@test.wav" \
  -F "meeting_id=test_001"
```

---

## Features Enabled

Once configured, you can use:

### ✅ Audio File Transcription
```bash
python scripts/transcribe_audio.py --audio meeting.wav
```

### ✅ Real-Time Microphone Transcription
```python
from src.transcription.azure_stt import AzureSpeechTranscriber

transcriber = AzureSpeechTranscriber(
    on_transcribed=lambda text, final: print(f"{'FINAL' if final else 'interim'}: {text}")
)
transcriber.start_continuous_recognition()
# Speak into microphone...
# transcriber.stop_continuous_recognition()
```

### ✅ Speaker Diarization (Who said what)
Automatically enabled when `AZURE_SPEECH_ENABLE_DIARIZATION=true`

### ✅ API Audio Upload
```bash
curl -X POST "http://localhost:8000/meetings/upload-audio" -F "file=@audio.wav"
```

---

## Pricing & Limits

### Free Tier (F0)
- **Cost:** $0/month
- **Limit:** 5 audio hours/month
- **Features:** Standard transcription
- **Best for:** Development, testing, small projects

### Standard Tier (S0)
- **Cost:** ~$1/hour of audio
- **Limit:** Unlimited
- **Features:** All features including custom models
- **Best for:** Production

**Pricing Page:** https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/

---

## Troubleshooting

### Error: "Invalid subscription key"
- **Solution:** Check `AZURE_SPEECH_KEY` in `.env` matches Azure portal
- Ensure no extra spaces or quotes

### Error: "Region not found"
- **Solution:** Check `AZURE_SPEECH_REGION` matches resource region (e.g., "eastus", not "East US")

### Error: "Module 'azure.cognitiveservices.speech' not found"
- **Solution:** `pip install azure-cognitiveservices-speech`

### No audio transcribed
- **Solution:** Check audio format (WAV works best)
- Ensure audio has clear speech
- Try with different audio file

### Rate limit exceeded
- **Solution:** Upgrade to Standard tier or wait for monthly reset

---

## Advanced Configuration

### Change Language

```bash
# In .env
AZURE_SPEECH_LANGUAGE=es-ES  # Spanish
AZURE_SPEECH_LANGUAGE=fr-FR  # French
AZURE_SPEECH_LANGUAGE=de-DE  # German
```

**Supported:** 100+ languages
**List:** https://learn.microsoft.com/azure/cognitive-services/speech-service/language-support

### Enable Custom Models

For domain-specific vocabulary (medical, legal, technical):
1. Create Custom Speech project in Speech Studio
2. Upload training data
3. Train custom model
4. Update model ID in configuration

---

## Security Best Practices

1. **Never commit `.env` file** to Git (already in .gitignore)
2. **Rotate keys** periodically (Azure portal → Keys)
3. **Use managed identities** in production (Azure-hosted apps)
4. **Monitor usage** in Azure portal to prevent unexpected charges

---

## Resources

- **Azure Portal:** https://portal.azure.com/
- **Speech Studio:** https://speech.microsoft.com/
- **Documentation:** https://learn.microsoft.com/azure/cognitive-services/speech-service/
- **Pricing:** https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/
- **Code Samples:** https://github.com/Azure-Samples/cognitive-services-speech-sdk

---

## Next Steps

After Azure Speech is configured:
1. ✅ Test transcription with your meeting recordings
2. ✅ Integrate with existing summarization pipeline
3. [ ] Configure Microsoft Teams integration (see [TEAMS_SETUP.md](TEAMS_SETUP.md))
4. [ ] Deploy to production with Docker

---

**Setup Complete!** You can now transcribe audio files and receive real-time summaries. 🎉
