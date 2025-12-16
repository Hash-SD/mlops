"""Test GitHub API connection."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_github_connection():
    """Test GitHub API connection with configured credentials."""
    from ui.cicd_management import GitHubIntegration
    
    token = os.getenv('GITHUB_TOKEN', '')
    repo = os.getenv('GITHUB_REPO', '')
    
    print(f"\n{'='*50}")
    print("GitHub Connection Test")
    print(f"{'='*50}")
    print(f"Token configured: {'Yes' if token else 'No'}")
    print(f"Repo configured: {repo if repo else 'No'}")
    
    if not token or not repo:
        print("\n❌ GITHUB_TOKEN atau GITHUB_REPO belum diisi di .env")
        print("\nContoh isi .env:")
        print("GITHUB_TOKEN=ghp_xxxxxxxxxxxx")
        print("GITHUB_REPO=Hash-SD/insightextrepo")
        return False
    
    gh = GitHubIntegration(token, repo)
    
    print(f"\nTesting connection to: {repo}")
    success, message = gh.test_connection()
    
    if success:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False


if __name__ == "__main__":
    test_github_connection()
