import streamlit as st
import pandas as pd
import json
import os
import numpy as np
import requests
from io import StringIO
from dotenv import load_dotenv
import base64

# Define available datasets
DATASETS = {
    # "Charles": "dataset/label_Charles.csv",
    "Iury": "dataset/label_Iury.csv",
    "Jessica": "dataset/label_Jessica.csv",
    # "Jose": "dataset/label_Jose.csv",
    # "Lukas": "dataset/label_Lukas.csv",
}

# Streamlit UI
st.title("Issue Report Labeling System")


# Display two textboxes on top
st.text_area("Criteria for Standard:", """
Cell contains most of the following key values:

1. Issue triggering steps
2. Stack traces (for crashes/errors)
3. Product/component version
4. Hardware/configuration info
5. Clear, descriptive title/summary
6. Related software versions
7. Test cases demonstrating the issue
8. Code examples showing the problem
9. Precise, unambiguous language
10. Operating system details

""", height=350)

st.text_area("Criteria for Not Standard: Missing the above criteria. Such as:", """
Missing or unclear reproduction steps.
Unclear core issue.
Lacks technical evidence.
Vague or ambiguous language.
""", height=200)


# User Selection Dropdown
selected_user = st.selectbox("Select User:", list(DATASETS.keys()))

# print(path)
# Load the selected dataset
CSV_FILE = DATASETS[selected_user]

# @st.cache_data
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

# Update the session state for reason based on the new dataset
# st.session_state["reason"] = {i: df.at[i, "reason"] for i in df.index}

# Initialize session state
# if "label" not in st.session_state:
st.session_state["label"] = {i: df.at[i, "label"] for i in df.index}
# if "reason" not in st.session_state:
st.session_state["reason"] = {i: df.at[i, "reason"] for i in df.index}

def save_data_to_github(df_to_save, token, repo, path):
    headers = {"Authorization": f"token {token}"}

    # Convert the updated dataframe to CSV string
    updated_csv = df_to_save.to_csv(index=False)

    # Get file sha before updating it
    sha_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    sha_response = requests.get(sha_url, headers=headers)
    
    try:
        sha_data = sha_response.json()
        sha = sha_data.get('sha')
    except requests.exceptions.JSONDecodeError as e:
        st.error(f"⚠️ Error decoding JSON in SHA response: {str(e)}")
        st.write(f"Raw SHA Response: {sha_response.text}")
        return
    
    if not sha:
        st.error(f"⚠️ SHA not found in the response. Please check the file path.")
        return

    # Prepare the payload to update the file in GitHub
    update_payload = {
        "message": "Update dataset with new labels and reasons",
        "content": base64.b64encode(updated_csv.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }

    # Send PUT request to update the file
    update_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    update_response = requests.put(update_url, headers=headers, json=update_payload)

    if update_response.status_code in [200, 201]:
        st.success("✅ Data saved successfully to GitHub!")
    else:
        st.error(f"⚠️ Error saving data: {update_response.json().get('message', 'Unknown error')}")
        st.write(update_response.json())



def save_data_to_github_old(csv_file, token, repo, path):
    # Construct the URL to get the raw file from GitHub
    url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
    
    # Display the URL to fetch the file for debugging
    # st.write(f"Fetching from URL: {url}")
    
    headers = {"Authorization": f"token {token}"}
    
    # Send GET request to download the raw CSV file
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Read the CSV content into a pandas DataFrame
            df = pd.read_csv(StringIO(response.text))  # Load CSV directly from text
            
            # Display the first few rows of the DataFrame for inspection
            # st.write(f"Displaying data for {path}")
            # st.write(df.head())
            
            # Update the 'label' and 'reason' columns from the session state (assuming it's already populated)
            for index in df.index[:110]:  # Update first 110 rows
                classification_value = st.session_state["label"].get(index)
                df.at[index, "label"] = classification_value if classification_value is not None else np.nan
                df.at[index, "reason"] = st.session_state["reason"][index] if st.session_state["reason"][index] != "" else np.nan
            

            # Save the modified DataFrame back to CSV
            updated_csv = df.to_csv(index=False)

            # Prepare the payload to update the file in GitHub
            update_payload = {
                "message": "Update dataset with new labels and reasons",
                "content": base64.b64encode(updated_csv.encode('utf-8')).decode('utf-8')
            }

            # GitHub API URL to update the file
            update_url = f"https://api.github.com/repos/{repo}/contents/{path}"

            # Get file sha before updating it
            sha_url = f"https://api.github.com/repos/{repo}/contents/{path}"
            sha_response = requests.get(sha_url, headers=headers)
            
            # Check if the sha_response is in JSON format
            try:
                sha_data = sha_response.json()
                sha = sha_data.get('sha')
            except requests.exceptions.JSONDecodeError as e:
                st.error(f"⚠️ Error decoding JSON in SHA response: {str(e)}")
                st.write(f"Raw SHA Response: {sha_response.text}")
                return
            
            if not sha:
                st.error(f"⚠️ SHA not found in the response. Please check the file path.")
                return

            update_payload["sha"] = sha

            # Send PUT request to update the file
            update_response = requests.put(update_url, headers=headers, json=update_payload)

            # Display response status and message
            if update_response.status_code == 200:
                st.success("✅ Data saved successfully!")
            else:
                st.error(f"⚠️ Error saving data: {update_response.json()['message']}")
                st.write(f"Update Response JSON: {update_response.json()}")
        except requests.exceptions.JSONDecodeError as e:
            st.error(f"⚠️ Error decoding CSV response: {str(e)}")
            st.write(f"Raw Response: {response.text}")  # Display raw response for debugging
    else:
        st.error(f"⚠️ Error fetching file: {response.status_code}")
        st.write(f"Error Response: {response.text}")



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

for index in df.index[:200]:  # Show first 100 rows
    col1, col2, col3, col4 = st.columns([1, 3, 2, 3])

    with col1:
        st.write(index + 1)

    with col2:
        if df.at[index, "html_url"]:  
            st.markdown(f"[Issue Link]({df.at[index, 'html_url']})")  
        else:
            st.write("No Link Available")

    with col3:
        # For the "Standard" checkbox
        standard_checked = st.checkbox("Standard", key=f"std_{index}", value=(df.at[index, "label"] == 1))
        
        # For the "Not Standard" checkbox
        not_standard_checked = st.checkbox("Not Standard", key=f"not_std_{index}", value=(df.at[index, "label"] == 0))
        
        # Logic to clear the label in session_state when both checkboxes are unchecked
        if not standard_checked and not not_standard_checked:
            st.session_state["label"][index] = np.nan  # Clear the label when both checkboxes are unchecked
        elif standard_checked:
            st.session_state["label"][index] = 1  # Assign "Standard" when checked
        elif not_standard_checked:
            st.session_state["label"][index] = 0  # Assign "Not Standard" when checked


    with col4:
        reason_text = st.text_area(f"Reason {index+1}", value=st.session_state["reason"][index], key=f"reason_{index}")
        st.session_state["reason"][index] = reason_text
   
# Save Button
#if st.button("Save Data"):
#    save_data()
if st.button("Save Data"):
    token = st.secrets["GITHUB_TOKEN"]
    if not token:
        st.error("⚠️ GitHub token not found. Please set the GITHUB_TOKEN secret.")
        st.stop()

    # Update df from session state before saving
    for index in df.index[:200]:
        df.at[index, "label"] = st.session_state["label"].get(index, np.nan)
        df.at[index, "reason"] = st.session_state["reason"].get(index, "")

    repo = "ttasnim68/LLM_label_app"
    path = "dataset/label_" + selected_user + ".csv"
    save_data_to_github(df, token, repo, path)

