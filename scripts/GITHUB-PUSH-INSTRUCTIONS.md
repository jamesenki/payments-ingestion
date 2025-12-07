# Instructions for Pushing to GitHub

## Issue: Token Authentication Failed

The provided token appears to be invalid or expired. Here's how to fix it:

## Option 1: Generate a New Personal Access Token (Recommended)

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/tokens
   - Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Create New Token:**
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name: "payments-ingestion-push"
   - Select expiration (or "No expiration" for long-term use)
   - **Required scopes:**
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (if you need to update GitHub Actions)

3. **Generate and Copy Token:**
   - Click "Generate token"
   - **IMPORTANT:** Copy the token immediately (you won't see it again)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **Push Using Token:**
   ```bash
   # Replace YOUR_NEW_TOKEN with the token you just created
   export GITHUB_TOKEN=YOUR_NEW_TOKEN
   git push https://${GITHUB_TOKEN}@github.com/jamesenki/payments-ingestion.git main
   ```

## Option 2: Use GitHub CLI (gh)

1. **Install GitHub CLI:**
   ```bash
   # macOS
   brew install gh
   
   # Or download from: https://cli.github.com/
   ```

2. **Authenticate:**
   ```bash
   gh auth login
   # Follow the prompts to authenticate
   ```

3. **Push:**
   ```bash
   git push jamesenki main
   ```

## Option 3: Use SSH (Most Secure for Long-term)

1. **Generate SSH Key (if you don't have one):**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Optionally set a passphrase
   ```

2. **Add SSH Key to GitHub:**
   ```bash
   # Copy your public key
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste your public key
   - Click "Add SSH key"

3. **Update Remote to Use SSH:**
   ```bash
   git remote set-url jamesenki git@github.com:jamesenki/payments-ingestion.git
   git push jamesenki main
   ```

## Create Repository First (if it doesn't exist)

If the repository doesn't exist on GitHub:

1. **Via Web Interface:**
   - Go to: https://github.com/new
   - Repository name: `payments-ingestion`
   - Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license
   - Click "Create repository"

2. **Or Use GitHub CLI:**
   ```bash
   gh repo create payments-ingestion --public --source=. --remote=jamesenki --push
   ```

## Quick Push Script

After you have a valid token, you can use the helper script:

```bash
# Make script executable (if not already)
chmod +x scripts/push-to-jamesenki.sh

# Run with your token
./scripts/push-to-jamesenki.sh YOUR_NEW_TOKEN
```

## Security Notes

⚠️ **Important Security Practices:**
- Never commit tokens to git
- Never share tokens publicly
- Use environment variables or credential helpers
- Consider using SSH keys for long-term authentication
- Rotate tokens regularly

## Current Status

- ✅ Remote "jamesenki" is configured
- ✅ All code is committed locally
- ⚠️ Need valid token to push
- ⚠️ Repository may need to be created on GitHub

