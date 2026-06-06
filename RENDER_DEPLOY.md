# Render Deployment Guide

## Step 1: Deploy via Blueprint (Easiest)
1. Push your code to GitHub (make sure `render.yaml` is in root)
2. Go to [Render.com](https://render.com) and log in
3. Click "New +" → "Blueprint"
4. Connect your GitHub repo and select the branch with `render.yaml`
5. Follow the prompts! You'll need to set:
   - `OPENAI_API_KEY`: Your OpenAI API key
6. Wait for both services to deploy!

## Step 2: Verify Deployment
1. Backend: Check the health endpoint at `https://your-backend-name.onrender.com/health`
2. Frontend: Open `https://your-frontend-name.onrender.com` and test ingest/chat!

## Notes for Render Free Tier
- **ChromaDB persistence**: Free tier disk resets on redeploy. For persistent storage, either:
  - Use a hosted vector DB like Qdrant Cloud
  - Or re-ingest videos after each redeploy
- **Whisper RAM usage**: Free tier has 512MB RAM. Use Whisper "tiny" model instead of "base" for better performance!
- **Cold starts**: Free services sleep after 15 minutes of inactivity. Wake them up before your demo!
