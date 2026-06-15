import os
import re
import json
import requests
import tempfile
from weasyprint import HTML
import streamlit as st
from groq import Groq

# ✅ Initialize Groq client
client = Groq(api_key=os.environ.get("career"))

# ✅ YouTube API Key
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# ✅ Global system prompt
system_prompt = "You are a career expert helping users explore jobs based on their background."

# ✅ YouTube Search using API
def search_youtube(query, max_results=5):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results,
        "type": "video"
    }

    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return [{"title": "Unable to fetch videos", "link": ""}]
    
    data = response.json()
    videos = []
    for item in data.get("items", []):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"title": title, "link": video_url})
    return videos


# ✅ Streamlit UI
st.set_page_config(page_title="Career Guide", layout="centered")
st.title("🎯 Career Guide – Your AI Career Companion")
st.markdown("Helping you explore career paths, learn the skills, and land the job.")

# ✅ Session state setup
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""
if "career_titles" not in st.session_state:
    st.session_state.career_titles = []

# ✅ Step 1: User Input
with st.form("career_form"):
    name = st.text_input("Your Name")
    education = st.selectbox("Education Level", ["High School", "Undergraduate", "Graduate", "Other"])
    interests = st.text_area("What are your interests or favorite subjects?")
    skills = st.text_area("List your current skills")
    preferences = st.selectbox("Preferred Work Style", ["Remote", "On-site", "Hybrid", "Flexible"])
    submitted = st.form_submit_button("Suggest Careers")

if submitted:
    with st.spinner("🔍 Analyzing your profile..."):
        user_prompt = f"""
        Name: {name}
        Education: {education}
        Interests: {interests}
        Skills: {skills}
        Preferences: {preferences}

        Suggest exactly 3 career paths suitable for this user. For each, format as:
        **Career Title**
        - One-line description
        - Salary Range (add $ sign and mention based in US)
        - Future Demand (growth percentage in coming years)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        chat = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        ai_response = chat.choices[0].message.content

        # Store in session
        st.session_state.submitted = True
        st.session_state.ai_response = ai_response
        st.session_state.career_titles = re.findall(r"\*\*(.*?)\*\*", ai_response)

# ✅ Show career suggestions
if st.session_state.submitted:
    st.subheader("🔍 Suggested Career Paths")
    st.markdown(st.session_state.ai_response)

    if st.session_state.career_titles:
        selected_career = st.selectbox("Choose a career to explore further:", ["-- Select a career --"] + st.session_state.career_titles)

        if selected_career != "-- Select a career --":
            with st.spinner("Generating personalized career resources..."):
                # ✅ Roadmap
                roadmap_prompt = f"Give a 3-stage (Beginner, Intermediate, Advanced) learning roadmap to become a {selected_career}."
                roadmap_chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": roadmap_prompt}
                    ]
                )
                raw_roadmap = roadmap_chat.choices[0].message.content
                st.subheader("🧭 Learning Roadmap")
                st.markdown(raw_roadmap)

                # ✅ YouTube Tutorials
                st.subheader("▶️ YouTube Tutorials")
                videos = search_youtube(f"{selected_career} tutorial")
                for vid in videos:
                    st.markdown(f"[{vid['title']}]({vid['link']})")

                # ✅ Courses
                st.subheader("📚 Recommended Online Courses")
                st.markdown(f"- [Intro to {selected_career} on Coursera](https://www.coursera.org)")
                st.markdown(f"- [{selected_career} Bootcamp on Udemy](https://www.udemy.com)")
                st.markdown(f"- [Advanced {selected_career} on edX](https://www.edx.org)")

                # ✅ Jobs
                st.subheader("💼 Job Listings")
                st.markdown(f"[Search {selected_career} jobs on LinkedIn](https://www.linkedin.com/jobs/search/?keywords={selected_career})")
                st.markdown(f"[Remote {selected_career} jobs on Remotive](https://remotive.io/remote-{selected_career.lower().replace(' ', '-')}-jobs)")

                # ✅ PDF Download
                st.subheader("📥 Download Career Plan")
                clean_roadmap = re.sub(r"[*_]{1,2}", "", raw_roadmap)
                roadmap_html = clean_roadmap.replace('\n', '<br>')
                pdf_html = f"""
                <html>
                <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                    h2 {{ color: #2E86C1; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
                    h3 {{ color: #117A65; margin-top: 20px; }}
                </style>
                </head>
                <body>
                    <h2>{selected_career} Career Plan</h2>
                    <h3>Learning Roadmap</h3>
                    <p>{roadmap_html}</p>
                    <h3>YouTube Tutorials</h3>
                    <ul>
                        {''.join([f"<li><a href='{vid['link']}'>{vid['title']}</a></li>" for vid in videos])}
                    </ul>
                    <h3>Recommended Courses</h3>
                    <ul>
                        <li>Intro to {selected_career} on Coursera</li>
                        <li>{selected_career} Bootcamp on Udemy</li>
                        <li>Advanced {selected_career} on edX</li>
                    </ul>
                    <h3>Job Listings</h3>
                    <ul>
                        <li><a href='https://www.linkedin.com/jobs/search/?keywords={selected_career}'>LinkedIn Jobs</a></li>
                        <li><a href='https://remotive.io/remote-{selected_career.lower().replace(' ', '-')}-jobs'>Remote Jobs</a></li>
                    </ul>
                </body>
                </html>
                """
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    pdf_path = f.name
                    HTML(string=pdf_html).write_pdf(pdf_path)
                    with open(pdf_path, "rb") as file:
                        st.download_button("Download PDF", data=file, file_name=f"{selected_career}_plan.pdf", mime="application/pdf")
