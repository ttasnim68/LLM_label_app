import streamlit as st
import pandas as pd
import json
import os
import numpy as np  # Import NumPy to handle NaN values

# CSV File Path
CSV_FILE = "label_Charles.csv"

# Function to Load CSV Data
@st.cache_data
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["body", "label", "reason"])

    df = pd.read_csv(CSV_FILE)

    # Extract "html_url" safely from JSON in "body" column
    def extract_url(json_str):
        try:
            data = json.loads(json_str)  # Use json.loads instead of ast.literal_eval
            return data.get("html_url", "")
        except (json.JSONDecodeError, TypeError):
            return ""  # Return empty if JSON is invalid

    df["html_url"] = df["body"].apply(extract_url)

    # Ensure label and reason columns exist
    if "label" not in df.columns:
        df["label"] = None  # Empty for checkboxes
    if "reason" not in df.columns:
        df["reason"] = ""  # Empty for text input

    # Fix: Replace NaN in "reason" with an empty string
    df["reason"] = df["reason"].fillna("")

    return df

# Load the data
df = load_data()

# Initialize session state for checkboxes & text areas
if "label" not in st.session_state:
    st.session_state["label"] = {i: df.at[i, "label"] for i in df.index}
if "reason" not in st.session_state:
    st.session_state["reason"] = {i: df.at[i, "reason"] if pd.notna(df.at[i, "reason"]) else "" for i in df.index}

# Function to Save Data
def save_data():
    for index in df.index[:110]:  # Save only first 110 rows
        df.at[index, "label"] = st.session_state["label"][index]
        df.at[index, "reason"] = st.session_state["reason"][index] if st.session_state["reason"][index] != "" else np.nan  # Save empty as NaN

    df.to_csv(CSV_FILE, index=False)
    st.success("Data saved successfully!")  # Show success message

# Streamlit UI
st.title("Issue Report Label")
st.write(f"Displaying {min(110, len(df))} records.")

# Display Table with Editable Fields
for index in df.index[:110]:  # Show first 110 rows
    col1, col2, col3, col4 = st.columns([1, 3, 2, 3])

    with col1:
        st.write(index + 1)  # Serial Number

    with col2:
        if df.at[index, "html_url"]:  # Ensure the link is not empty
            st.markdown(f"[Issue Link]({df.at[index, 'html_url']})")  # Clickable Link
        else:
            st.write("No Link Available")

    with col3:
        # Classification Checkboxes (Mutually Exclusive)
        if st.checkbox("Standard", key=f"std_{index}", value=(df.at[index, "label"] == 1)):
            st.session_state["label"][index] = 1
        elif st.checkbox("Not Standard", key=f"not_std_{index}", value=(df.at[index, "label"] == 0)):
            st.session_state["label"][index] = 0

    with col4:
        # Text Area for Reason (Default Empty Instead of NaN)
        reason_text = st.text_area(f"Reason {index}", value=st.session_state["reason"][index], key=f"reason_{index}")
        st.session_state["reason"][index] = reason_text

# Button to Save Data
if st.button("Save Data"):
    save_data()  # Now correctly runs inside Streamlit's context
