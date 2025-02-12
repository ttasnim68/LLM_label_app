import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import requests
from io import StringIO
from dotenv import load_dotenv

# Define available datasets
DATASETS = {
    "Charles": "dataset/label_Charles.csv",
    "Iury": "dataset/label_Iury.csv",
    "Jessica": "dataset/label_Jessica.csv",
    "Jose": "dataset/label_Jose.csv",
    "Lukas": "dataset/label_Lukas.csv",
    "test":"dataset/test.csv",
}

# Streamlit UI
st.title("Issue Report Labeling System")


# Display two textboxes on top
st.text_area("Criteria for Standard:", """
Cell contains most of the following key values:

Quality Requirements:
Clear title, precise language, complete information.

Steps to Reproduce:
Clear, numbered steps showing how to trigger the issue.
Expected vs. actual results.

Technical Information:
Test cases, code examples, error logs, software versions.
""", height=350)

st.text_area("Criteria for Not Standard:", """
Missing or unclear reproduction steps.
Unclear core issue.
Lacks technical evidence.
Vague or ambiguous language.
""", height=200)


# User Selection Dropdown
selected_user = st.selectbox("Select User:", list(DATASETS.keys()))

# Load the selected dataset
CSV_FILE = DATASETS[selected_user]

@st.cache_data
def load_data(csv_file):
    if not os.path.exists(csv_file):
        st.error(f"⚠️ File {csv_file} not found!")
        return pd.DataFrame(columns=["body", "label", "reason"])

    df = pd.read_csv(csv_file)

    # Extract "html_url" safely from JSON in "body" column
    def extract_url(json_str):
        try:
            data = json.loads(json_str)  
            return data.get("html_url", "")
        except (json.JSONDecodeError, TypeError):
            return ""  

    df["html_url"] = df["body"].apply(extract_url)

    # Ensure label and reason columns exist
    df["label"] = df.get("label", np.nan)
    df["reason"] = df.get("reason", "").fillna("")

    return df

df = load_data(CSV_FILE)

# Initialize session state
if "label" not in st.session_state:
    st.session_state["label"] = {i: df.at[i, "label"] for i in df.index}
if "reason" not in st.session_state:
    st.session_state["reason"] = {i: df.at[i, "reason"] for i in df.index}




# Function to save data to GitHub
def save_data_to_github(csv_file, token, repo, path):
    # Load current CSV from GitHub
    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    
    headers = {"Authorization": f"token {token}"}
    # Get the file contents
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"⚠️ Error fetching file: {response.json()['message']}")
        return

    # Parse the file content (base64 encoded)
    file_content = response.json()['content']
    file_content_decoded = requests.utils.base64.b64decode(file_content).decode('utf-8')
    
    # Load the CSV into DataFrame
    df = pd.read_csv(StringIO(file_content_decoded))

    # Update data in the dataframe
    for index in df.index[:110]:  # Update first 110 rows
        classification_value = st.session_state["label"].get(index)
        df.at[index, "label"] = classification_value if classification_value is not None else np.nan
        df.at[index, "reason"] = st.session_state["reason"][index] if st.session_state["reason"][index] != "" else np.nan

    # Save the dataframe to CSV
    updated_csv = df.to_csv(index=False)

    # Prepare the payload to update the file in GitHub
    update_payload = {
        "message": "Update dataset with new labels and reasons",
        "content": requests.utils.base64.b64encode(updated_csv.encode('utf-8')).decode('utf-8'),
        "sha": response.json()['sha']
    }

    # Send the update request to GitHub
    update_response = requests.put(url, headers=headers, json=update_payload)
    if update_response.status_code == 200:
        st.success("✅ Data saved to GitHub successfully!")
    else:
        st.error(f"⚠️ Error saving data: {update_response.json()['message']}")

def save_data_to_github(csv_file, token, repo, path):
    file_name = path.split("/")[-1]  # This gives the file name (e.g., label_Charles.csv)
    repo_path = f"dataset/{file_name}"  # Form the full path in the GitHub repo (example: dataset/label_Charles.csv)

    # GitHub URL to access file contents
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"


    headers = {"Authorization": f"token {token}"}
    
    # Get the file contents
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"⚠️ Error fetching file: {response.json()['message']}")
        return

    # Parse the file content (base64 encoded)
    file_content = response.json()['content']
    file_content_decoded = requests.utils.base64.b64decode(file_content).decode('utf-8')

    # Load the CSV into DataFrame
    df = pd.read_csv(StringIO(file_content_decoded))

    # Update data in the dataframe
    for index in df.index[:110]:  # Update first 110 rows
        classification_value = st.session_state["label"].get(index)
        df.at[index, "label"] = classification_value if classification_value is not None else np.nan
        df.at[index, "reason"] = st.session_state["reason"][index] if st.session_state["reason"][index] != "" else np.nan

    # Save the dataframe to CSV
    updated_csv = df.to_csv(index=False)

    # Prepare the payload to update the file in GitHub
    update_payload = {
        "message": "Update dataset with new labels and reasons",
        "content": requests.utils.base64.b64encode(updated_csv.encode('utf-8')).decode('utf-8'),
        "sha": response.json()['sha']
    }

    # Send the update request to GitHub
    update_response = requests.put(url, headers=headers, json=update_payload)
    if update_response.status_code == 200:
        st.success("✅ Data saved to GitHub successfully!")
    else:
        st.error(f"⚠️ Error saving data: {update_response.json()['message']}")

# Function to Save Data
#def save_data():
#    for index in df.index[:110]:  # Save only first 110 rows
#        classification_value = st.session_state["label"].get(index)
#        df.at[index, "label"] = classification_value if classification_value is not None else np.nan
#        df.at[index, "reason"] = st.session_state["reason"][index] if st.session_state["reason"][index] != "" else np.nan

#    df.to_csv(CSV_FILE, index=False)
#    st.success("✅ Data saved successfully!")

# Display Table with Editable Fields
st.write(f"📊 Displaying Data for: **{selected_user}**")

for index in df.index[:110]:  # Show first 110 rows
    col1, col2, col3, col4 = st.columns([1, 3, 2, 3])

    with col1:
        st.write(index + 1)

    with col2:
        if df.at[index, "html_url"]:  
            st.markdown(f"[Issue Link]({df.at[index, 'html_url']})")  
        else:
            st.write("No Link Available")

    with col3:
        if st.checkbox("Standard", key=f"std_{index}", value=(df.at[index, "label"] == 1)):
            st.session_state["label"][index] = 1
        elif st.checkbox("Not Standard", key=f"not_std_{index}", value=(df.at[index, "label"] == 0)):
            st.session_state["label"][index] = 0

    with col4:
        reason_text = st.text_area(f"Reason {index+1}", value=st.session_state["reason"][index], key=f"reason_{index}")
        st.session_state["reason"][index] = reason_text

# Save Button
#if st.button("Save Data"):
#    save_data()
if st.button("Save Data to GitHub"):
    token = st.secrets["GITHUB_TOKEN"]  # Access the token from Streamlit Secrets
    if not token:
        st.error("⚠️ GitHub token not found. Please set the GITHUB_TOKEN secret.")
        st.stop()  # Stop execution if the token is missing

    repo = "ttasnim/LLM_label_app"  # Replace with your actual GitHub repo
    path = DATASETS[selected_user]  # Path to the CSV file in the repo
    save_data_to_github(path, token, repo, path)