import streamlit as st
import pandas as pd
import os

# 🔗 Set page title
st.set_page_config(page_title="LeadPulse Dashboard", page_icon="📈")

# 📅 Title
st.title("📊 Lead Dashboard")
st.markdown("Track all the leads captured by LeadPulse in one place.")

# 📃 Define path to the leads file
leads_file = "leads.txt"

# 🔍 Check if file exists
if os.path.exists(leads_file):
    with open(leads_file, "r") as f:
        lines = f.readlines()

    # 📂 Parse the data
    leads = [line.strip().split(" | ") for line in lines if line.strip()]
    df = pd.DataFrame(leads, columns=["Name", "Email", "Interest"])

    # 🌀 Display the DataFrame
    st.dataframe(df, use_container_width=True)

    # 🔀 Add filters (optional)
    search = st.text_input("Search by name or interest")
    if search:
        df_filtered = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        st.dataframe(df_filtered, use_container_width=True)
else:
    st.warning("No leads found yet. Start chatting in LeadPulse to collect leads!")
        # 📥 Add a download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Leads as CSV",
        data=csv,
        file_name='leadpulse_leads.csv',
        mime='text/csv',
    )

