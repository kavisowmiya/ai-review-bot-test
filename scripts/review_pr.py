import os
import requests
import openai

# GitHub provides these automatically inside the workflow environment
repo = os.environ.get("GITHUB_REPOSITORY")
pr_number = os.environ.get("GITHUB_REF", "").split("/")[-1]

gh_token = os.environ["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"]
openai.api_key = os.environ["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"]

headers = {
    "Authorization": f"token {gh_token}",
    "Accept": "application/vnd.github.v3+json"
}

# 1. Get PR files and their patches
files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
files = requests.get(files_url, headers=headers).json()

# Build a single diff text to send to GPT
diff_text = ""
for f in files:
    patch = f.get("patch")
    if patch:
        diff_text += f"File: {f['filename']}\n{patch}\n\n"

# 2. Send to GPT for review
prompt = f"Review this code diff and point out any potential problems:\n\n{diff_text[:10000]}"
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
review_comment = response.choices[0].message["content"]

# 3. Post comment back to the PR
comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
requests.post(comments_url, headers=headers, json={"body": review_comment})
