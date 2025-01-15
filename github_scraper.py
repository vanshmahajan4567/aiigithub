import os
import json
import logging
import requests
from github import Github
from github.GithubException import BadCredentialsException, RateLimitExceededException
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests
from collections import Counter
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv(find_dotenv())

class GithubCandidateFinder:
    def __init__(self):
        try:
            # Force reload environment variables
            load_dotenv(find_dotenv(), override=True)
            
            # Get and clean token
            token = os.getenv('GITHUB_TOKEN', '').strip()
            if not token:
                raise ValueError("GitHub token not found in environment variables")
            
            # Log token details for debugging
            logging.info(f"Token length: {len(token)}")
            logging.info(f"Token prefix: {token[:10]}")
            logging.info(f"Token suffix: {token[-10:]}")
            logging.info(f"Token format valid: {token.startswith('ghp_')}")
            
            # Store cleaned token
            self.token = token
            
            # Test token with direct API call first
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Python'
            }
            
            logging.info("Making API request...")
            response = requests.get('https://api.github.com/user', headers=headers)
            
            if response.status_code != 200:
                logging.error(f"API Response: {response.text}")
                logging.error(f"Response headers: {dict(response.headers)}")
                raise BadCredentialsException(f"GitHub API test failed with status {response.status_code}")
            
            user_data = response.json()
            logging.info(f"Direct API call successful, authenticated as: {user_data['login']}")
            
            # Now initialize Github client
            self.github = Github(self.token)
            logging.info("Successfully initialized GitHub client")
            
        except BadCredentialsException as e:
            error_msg = f"GitHub authentication failed: {str(e)}"
            st.error(error_msg)
            logging.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error initializing GitHub client: {str(e)}"
            st.error(error_msg)
            logging.error(error_msg)
            raise
            
        self.driver = None
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Use system ChromeDriver
            service = Service('/usr/bin/chromedriver')
            
            # Initialize WebDriver with explicit wait
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Test the connection
            self.driver.get("https://github.com")
            logging.info("Successfully initialized Chrome WebDriver")
            
        except Exception as e:
            error_msg = f"Failed to initialize Chrome: {str(e)}"
            st.error(error_msg)
            logging.error(error_msg)
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            self.driver = None
            raise

    def __del__(self):
        """Cleanup Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def calculate_score(self, user_data, requirement):
        """Calculate candidate score based on various metrics."""
        score = 0
        explanation = []
        
        # Convert requirement to lowercase for matching
        requirement_lower = requirement.lower()
        
        # Parse key terms from requirement
        key_terms = set(re.findall(r'\w+', requirement_lower))
        
        # Score based on bio match
        if user_data['bio']:
            bio_terms = set(re.findall(r'\w+', user_data['bio'].lower()))
            matching_terms = key_terms.intersection(bio_terms)
            if matching_terms:
                term_score = len(matching_terms) * 10
                score += term_score
                explanation.append(f"Bio matches {len(matching_terms)} key terms (+{term_score})")
        
        # Score based on languages
        lang_score = min(len(user_data['languages']) * 5, 25)
        score += lang_score
        explanation.append(f"Uses {len(user_data['languages'])} languages (+{lang_score})")
        
        # Score based on contributions
        contrib_score = min(user_data['contributions'] // 100, 25)
        score += contrib_score
        explanation.append(f"Has {user_data['contributions']} contributions (+{contrib_score})")
        
        # Score based on repositories
        repo_score = min(user_data['public_repos'] * 2, 25)
        score += repo_score
        explanation.append(f"Has {user_data['public_repos']} public repos (+{repo_score})")
        
        # Score based on followers
        follower_score = min(user_data['followers'] // 10, 25)
        score += follower_score
        explanation.append(f"Has {user_data['followers']} followers (+{follower_score})")
        
        return {
            'score': min(score, 100),
            'explanation': ' | '.join(explanation)
        }

    def get_user_languages(self, username):
        """Get programming languages used by the user using Selenium."""
        try:
            url = f"https://github.com/{username}?tab=repositories"
            self.driver.get(url)
            time.sleep(2)  # Wait for content to load
            
            languages = Counter()
            
            # Find repository language elements
            lang_elements = self.driver.find_elements(By.CSS_SELECTOR, '[itemprop="programmingLanguage"]')
            for elem in lang_elements:
                lang = elem.text.strip()
                if lang:
                    languages[lang] += 1
                    
            return dict(languages.most_common(5))
        except Exception as e:
            print(f"Error getting languages for {username}: {str(e)}")
            return {}

    def get_contribution_count(self, username):
        """Get contribution count using Selenium."""
        try:
            url = f"https://github.com/{username}"
            self.driver.get(url)
            
            # Wait for the contributions graph to load
            wait = WebDriverWait(self.driver, 10)
            contrib_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-yearly-contributions h2"))
            )
            
            contributions_text = contrib_element.text
            # Extract numbers from text like "1,250 contributions in the last year"
            contributions = ''.join(filter(str.isdigit, contributions_text))
            return int(contributions) if contributions else 0
            
        except Exception as e:
            logging.error(f"Error getting contributions for {username}: {str(e)}")
            return 0

    def get_user_details(self, username):
        """Get additional user details using Selenium."""
        try:
            url = f"https://github.com/{username}"
            self.driver.get(url)
            time.sleep(2)
            
            # Get pinned repositories
            pinned_repos = []
            try:
                pinned_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-hovercard-type="repository"]')
                pinned_repos = [elem.text for elem in pinned_elements[:6]]  # Get up to 6 pinned repos
            except:
                pass
            
            # Get contribution streak
            streak = "N/A"
            try:
                streak_element = self.driver.find_element(By.CSS_SELECTOR, '.js-yearly-contributions h2')
                streak = streak_element.text
            except:
                pass
            
            return {
                'pinned_repos': pinned_repos,
                'contribution_streak': streak
            }
        except Exception as e:
            print(f"Error getting details for {username}: {str(e)}")
            return {'pinned_repos': [], 'contribution_streak': "N/A"}

    def search_candidates(self, requirement, location=None, language=None, limit=50):
        """Search for candidates based on requirements."""
        query = f"{requirement}"
        if location:
            query += f" location:{location}"
        if language:
            query += f" language:{language}"
            
        users = self.github.search_users(query)
        candidates = []
        
        for user in users[:limit]:
            try:
                # Basic info from GitHub API
                user_data = {
                    'login': user.login,
                    'name': user.name or user.login,
                    'bio': user.bio,
                    'location': user.location,
                    'public_repos': user.public_repos,
                    'followers': user.followers,
                    'profile_url': f"https://github.com/{user.login}"
                }
                
                # Enhanced data from Selenium
                user_data['languages'] = self.get_user_languages(user.login)
                user_data['contributions'] = self.get_contribution_count(user.login)
                
                # Additional details
                details = self.get_user_details(user.login)
                user_data.update(details)
                
                # Calculate score
                analysis = self.calculate_score(user_data, requirement)
                user_data.update(analysis)
                candidates.append(user_data)
                
            except Exception as e:
                print(f"Error processing user {user.login}: {str(e)}")
                continue
                
        # Clean up
        self.driver.quit()
        return sorted(candidates, key=lambda x: x['score'], reverse=True)

def main():
    st.title("Sphynx - Git the perfect candidate")
    
    # User input
    requirement = st.text_input(
        "Describe the candidate you're looking for (eg. Python developer with experience in AI and machine learning)..."
    )
    
    if st.button("SEARCH"):
        if not requirement:
            st.error("Please enter search requirements")
            return
            
        finder = GithubCandidateFinder()
        
        with st.spinner('Searching for candidates...'):
            candidates = finder.search_candidates(requirement)
            
            # Display results
            st.subheader(f"Found {len(candidates)} matching candidates")
            
            for candidate in candidates:
                with st.expander(f"{candidate['name']} - Score: {candidate['score']}/100"):
                    st.write(f"**Bio:** {candidate['bio']}")
                    st.write(f"**Location:** {candidate['location']}")
                    st.write(f"**Top Languages:** {', '.join(candidate['languages'].keys())}")
                    st.write(f"**Contributions:** {candidate['contributions']}")
                    st.write(f"**Public Repos:** {candidate['public_repos']}")
                    st.write(f"**Followers:** {candidate['followers']}")
                    st.write(f"**Pinned Repositories:**")
                    for repo in candidate['pinned_repos']:
                        st.write(f"- {repo}")
                    st.write(f"**Contribution Streak:** {candidate['contribution_streak']}")
                    st.write(f"**Match Details:** {candidate['explanation']}")
                    st.write(f"**Profile:** {candidate['profile_url']}")

    # Display previous searches
    st.header("Previous Searches")
    if os.path.exists('previous_searches.json'):
        with open('previous_searches.json', 'r') as f:
            searches = json.load(f)
            
        df = pd.DataFrame(searches)
        st.table(df)

if __name__ == "__main__":
    main() 