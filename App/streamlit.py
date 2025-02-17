import streamlit as st
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

# Okta configuration
OKTA_DOMAIN = "dev-moyfp4odxs5s2o2w.us.auth0.com"
CLIENT_ID = "RfAX1npgT2Pteq6KOBp8KTZ9ZxI3n6q1"
CLIENT_SECRET = "tm5gDHPt7nnQJG8ArpJ8vr2V-wv2NFa_dw6dX5-IXfcJQ6jWPDEuqLZk6ebLXFgy"
REDIRECT_URI = "http://localhost:8501/callback"
AUTHORIZATION_URL = f"{OKTA_DOMAIN}/oauth2/default/v1/authorize"
TOKEN_URL = f"{OKTA_DOMAIN}/oauth2/default/v1/token"
USERINFO_URL = f"{OKTA_DOMAIN}/oauth2/default/v1/userinfo"

# Initialize OAuth2 session
oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=["openid", "profile", "email"])

# Okta authentication functions
def login():
    authorization_url, state = oauth.authorization_url(AUTHORIZATION_URL)
    st.session_state['oauth_state'] = state
    st.write(f"Please log in [here]({authorization_url}).")

def callback():
    try:
        # Use st.query_params instead of st.experimental_get_query_params
        query_params = st.query_params
        token = oauth.fetch_token(
            TOKEN_URL,
            authorization_response=query_params["url"],
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        )
        st.session_state['oauth_token'] = token
        st.success("Successfully logged in!")
    except Exception as e:
        st.error(f"Error during login: {e}")

def get_user_info():
    if 'oauth_token' in st.session_state:
        oauth.token = st.session_state['oauth_token']
        user_info = oauth.get(USERINFO_URL).json()
        st.write("User Info:", user_info)
    else:
        st.warning("Not logged in.")

def logout():
    if 'oauth_token' in st.session_state:
        del st.session_state['oauth_token']
        st.success("Successfully logged out!")
    else:
        st.warning("Not logged in.")

# Cold Mail Generator function
def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Cold Mail Generator")
    url_input = st.text_input("Enter a URL:", value="P")
    submit_button = st.button("Submit")

    if submit_button:
        try:
            loader = WebBaseLoader(url_input)
            data = clean_text(loader.load().pop().page_content)
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)
            for job in jobs:
                skills = job.get('skills', [])
                links = portfolio.query_links(skills)
                email = llm.write_mail(job, links)
                st.code(email, language='markdown')
        except Exception as e:
            st.error(f"An Error Occurred: {e}")

# Main app logic
def main():
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")

    # Check if the user is authenticated
    if 'oauth_token' not in st.session_state:
        st.title("OUTREACH PRO - Cold Mail Generator")
        if st.button("Login"):
            login()
        # Use st.query_params instead of st.experimental_get_query_params
        if st.query_params.get("code"):
            callback()
        if st.button("Get User Info"):
            get_user_info()
        if st.button("Logout"):
            logout()
    else:
        # If authenticated, show the Cold Mail Generator
        chain = Chain()
        portfolio = Portfolio()
        create_streamlit_app(chain, portfolio, clean_text)

if __name__ == "__main__":
    main()