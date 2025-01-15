import os
import json
from github import Github
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests
from collections import Counter
import re

# Load environment variables
load_dotenv()

class GithubCandidateFinder:
    def __init__(self):
        self.github = Github(os.getenv('GITHUB_TOKEN'))
        
    def calculate_score(self, user_data, requirement):
        """Calculate candidate score based on various metrics."""
        score = 0
        explanation = []
        
        # Convert requirement to lowercase for matching
        requirement_lower = requirement.lower()
        
        # Parse key terms from requirement
        key_terms = set(re.findall(r'\w+', requirement_lower))
        
        # Score based on bio match (if bio contains relevant keywords)
        if user_data['bio']:
            bio_terms = set(re.findall(r'\w+', user_data['bio'].lower()))
            matching_terms = key_terms.intersection(bio_terms)
            if matching_terms:
                term_score = len(matching_terms) * 10
                score += term_score
                explanation.append(f"Bio matches {len(matching_terms)} key terms (+{term_score})")
        
        # Score based on relevant languages
        lang_score = min(len(user_data['languages']) * 5, 25)
        score += lang_score
        explanation.append(f"Uses {len(user_data['languages'])} languages (+{lang_score})")
        
        # Score based on contributions
        contrib_score = min(user_data['contributions'] // 100, 25)
        score += contrib_score
        explanation.append(f"Has {user_data['contributions']} contributions (+{contrib_score})")
        
        # Score based on public repos
        repo_score = min(user_data['public_repos'] * 2, 25)
        score += repo_score
        explanation.append(f"Has {user_data['public_repos']} public repos (+{repo_score})")
        
        # Score based on followers (as a measure of influence)
        follower_score = min(user_data['followers'] // 10, 25)
        score += follower_score
        explanation.append(f"Has {user_data['followers']} followers (+{follower_score})")
        
        # Normalize score to 0-100 range
        final_score = min(score, 100)
        
        return {
            'score': final_score,
            'explanation': ' | '.join(explanation)
        }

    def get_user_languages(self, username):
        """Get programming languages used by the user."""
        try:
            user = self.github.get_user(username)
            languages = Counter()
            
            for repo in user.get_repos():
                repo_langs = repo.get_languages()
                for lang, bytes_count in repo_langs.items():
                    languages[lang] += bytes_count
                    
            # Get top 5 languages
            return dict(languages.most_common(5))
        except:
            return {}

    def get_contribution_count(self, username):
        """Scrape user's contribution count from GitHub profile."""
        try:
            url = f"https://github.com/{username}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            contributions = soup.find('h2', class_='f4 text-normal mb-2').text.strip()
            return int(''.join(filter(str.isdigit, contributions)))
        except:
            return 0

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
                user_data = {
                    'login': user.login,
                    'name': user.name or user.login,
                    'bio': user.bio,
                    'location': user.location,
                    'public_repos': user.public_repos,
                    'followers': user.followers,
                    'languages': self.get_user_languages(user.login),
                    'contributions': self.get_contribution_count(user.login),
                    'profile_url': f"https://github.com/{user.login}"
                }
                
                analysis = self.calculate_score(user_data, requirement)
                user_data.update(analysis)
                candidates.append(user_data)
                
            except Exception as e:
                print(f"Error processing user {user.login}: {str(e)}")
                continue
                
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