import os
import requests
import openai

# Get required environment variables safely
gh_token = os.getenv("GH_TOKEN")
openai_api_key = os.getenv("OPEN_API_KEY")
repo = os.getenv("GITHUB_REPOSITORY")
pr_number = os.getenv("GITHUB_REF", "").split("/")[-1]

# Fail fast if anything important is missing
if not gh_token:
    raise EnvironmentError("❌ GH_TOKEN environment variable is not set.")

if not openai_api_key:
    raise EnvironmentError("❌ OPEN_API_KEY environment variable is not set.")

if not repo or not pr_number:
    raise EnvironmentError("❌ GitHub repo or PR number not found in environment variables.")

# Set OpenAI API key
openai.api_key = openai_api_key

# Headers for GitHub API
headers = {
    "Authorization": f"token {gh_token}",
    "Accept": "application/vnd.github.v3+json"
}

# 1. Get PR files and their patches
files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
files_response = requests.get(files_url, headers=headers)

if files_response.status_code != 200:
    raise Exception(f"❌ Failed to fetch PR files: {files_response.status_code} - {files_response.text}")

files = files_response.json()

# Build a single diff text to send to GPT
diff_text = ""
for f in files:
    patch = f.get("patch")
    if patch:
        diff_text += f"File: {f['filename']}\n{patch}\n\n"

if not diff_text:
    print("ℹ️ No diffs to review in this PR.")
    exit(0)

# 2. Send to GPT for review
prompt = f"Review this code diff and point out any potential problems:\n\n{diff_text[:10000]}"
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a code reviewer."},
        {"role": "user", "content": prompt}
    ]
)
review_comment = response.choices[0].message["content"]

# 3. Post comment back to the PR
comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
post_response = requests.post(comments_url, headers=headers, json={"body": review_comment})

if post_response.status_code == 201:
    print("✅ Successfully posted review comment.")
else:
    print(f"❌ Failed to post comment: {post_response.status_code} - {post_response.text}")
