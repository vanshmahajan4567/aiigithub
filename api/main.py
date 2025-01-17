"""
FastAPI backend for GitHub candidate finder application.
"""
import os
import logging
import re
from typing import Optional, List, Dict
from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github, Auth
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    """
    Request model for candidate search endpoint.
    """
    requirement: str

class GithubCandidateFinder:
    """
    Class to handle GitHub candidate searching and scoring.
    """
    def __init__(self):
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        
        logger.info("Initializing GitHub client with token length: %d", len(token))
        logger.info("Token prefix: %s", token[:10])
        logger.info("Token suffix: %s", token[-10:])
        
        try:
            self.github = Github(auth=Auth.Token(token))
            user = self.github.get_user()
            logger.info("Successfully authenticated as: %s", user.login)
        except Exception as e:
            logger.error("Failed to initialize GitHub client: %s", str(e))
            raise

        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver successfully initialized")
        except Exception as e:
            logger.error("Failed to initialize Chrome WebDriver: %s", str(e))
            raise

    def __del__(self):
        """Cleanup method to ensure WebDriver is closed."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception:
                pass

    def get_user_languages(self, username: str) -> Dict[str, int]:
        """Get the programming languages used by a user."""
        try:
            user = self.github.get_user(username)
            repos = user.get_repos()
            languages = Counter()
            
            for repo in repos:
                if repo.language:
                    languages[repo.language] += 1
            
            return dict(languages)
        except Exception as e:
            logger.error("Error getting user languages: %s", str(e))
            return {}

    def get_contribution_count(self, username: str) -> int:
        """Get the contribution count for a user."""
        try:
            url = f"https://github.com/{username}"
            self.driver.get(url)
            
            # Wait for the contributions graph to load
            wait = WebDriverWait(self.driver, 10)
            h2_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.f4.text-normal.mb-2"))
            )
            
            # Extract contribution count
            text = h2_element.text
            match = re.search(r'\d+', text)
            return int(match.group()) if match else 0
        except Exception as e:
            logger.error("Error getting contribution count: %s", str(e))
            return 0

    def calculate_score(self, user_data: Dict) -> float:
        """Calculate a score for a candidate based on their GitHub data."""
        score = 0
        
        # Score based on public repositories (max 20 points)
        repos = min(user_data['public_repos'], 50)
        score += (repos / 50) * 20
        
        # Score based on followers (max 15 points)
        followers = min(user_data['followers'], 1000)
        score += (followers / 1000) * 15
        
        # Score based on contributions (max 25 points)
        contributions = min(user_data['contributions'], 1000)
        score += (contributions / 1000) * 25
        
        # Score based on language diversity (max 20 points)
        language_count = len(user_data['languages'])
        score += min((language_count / 10) * 20, 20)
        
        # Score based on having a bio and location (max 10 points)
        if user_data['bio']:
            score += 5
        if user_data['location']:
            score += 5
        
        # Score based on pinned repositories (max 10 points)
        pinned_count = len(user_data['pinned_repos'])
        score += (pinned_count / 6) * 10
        
        return round(min(score, 100), 2)

    def get_user_details(self, username: str) -> Dict:
        """Get detailed information about a GitHub user."""
        try:
            user = self.github.get_user(username)
            
            # Get pinned repositories
            url = f"https://github.com/{username}"
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)
            pinned_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.pinned-item-list-item-content span.repo"))
            )
            pinned_repos = [elem.text for elem in pinned_elements]
            
            # Get contribution streak
            streak_element = self.driver.find_element(By.CSS_SELECTOR, ".js-yearly-contributions h2")
            contribution_streak = streak_element.text if streak_element else "No contributions"
            
            return {
                'name': user.name or username,
                'bio': user.bio or "",
                'location': user.location or "",
                'languages': self.get_user_languages(username),
                'contributions': self.get_contribution_count(username),
                'public_repos': user.public_repos,
                'followers': user.followers,
                'pinned_repos': pinned_repos,
                'contribution_streak': contribution_streak,
                'profile_url': user.html_url
            }
        except Exception as e:
            logger.error("Error getting user details: %s", str(e))
            raise

    def search_candidates(self, requirement: str) -> List[Dict]:
        """Search for GitHub candidates based on requirements."""
        try:
            # Convert requirement to search query
            query = f"{requirement} type:user"
            users = self.github.search_users(query)
            candidates = []
            
            # Process top 10 users
            for user in users[:10]:
                try:
                    details = self.get_user_details(user.login)
                    score = self.calculate_score(details)
                    
                    candidate = {
                        **details,
                        'score': score,
                        'explanation': f"Matched based on {requirement}"
                    }
                    candidates.append(candidate)
                except Exception as e:
                    logger.error("Error processing user %s: %s", user.login, str(e))
                    continue
            
            # Sort candidates by score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            return candidates
            
        except Exception as e:
            logger.error("Error searching candidates: %s", str(e))
            raise

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/search")
async def search_candidates(request: SearchRequest):
    """
    Endpoint to search for GitHub candidates based on requirements.
    """
    try:
        finder = GithubCandidateFinder()
        candidates = finder.search_candidates(request.requirement)
        return {"candidates": candidates}
    except Exception as e:
        logger.error("Error during candidate search: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"} 