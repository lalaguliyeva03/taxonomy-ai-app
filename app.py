import streamlit as st
import pandas as pd
from groq import Groq
import time

# --- INITIALIZATION ---
# Initialize the Groq Client
client = Groq(api_key="GROQ_API_KEY")

# --- CORE AI FUNCTION ---
def categorize_product(messy_name, allowed_categories):
    system_prompt = f"""
    You are an expert E-commerce Catalog Manager. 
    Your job is to map a raw, messy product name to the single most accurate category from the provided list.
    
    Allowed Categories:
    {allowed_categories}
    
    Rules:
    1. You must ONLY reply with the exact name of the category from the list.
    2. Do not add any extra text, punctuation, or explanations.
    3. If the product does not fit any category, reply with "Uncategorized".
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Categorize this product: {messy_name}"}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0
        )
        result = chat_completion.choices[0].message.content
        if result:
            return result.strip()
        return "Uncategorized"
    except Exception as e:
        return f"Error: {e}"

# --- WEB INTERFACE (FRONT-END) ---
st.set_page_config(page_title="Taxonomy AI", page_icon="🛒", layout="centered")

st.title("🛒 E-Commerce Taxonomy AI")
st.write("Upload your messy supplier data and let AI categorize it in seconds.")

# 1. Provide the taxonomy tree (Users can edit this in the text area!)
default_taxonomy = """Electronics > Audio > Headphones
Electronics > TV & Video > Televisions
Apparel > Men > Shoes
Home & Kitchen > Appliances > Coffee Makers
Beauty > Skincare > Serums
Grocery > Pantry > Honey & Syrups"""

st.markdown("### 1. Define Your Taxonomy Tree")
user_taxonomy = st.text_area("Edit your allowed categories (one per line):", value=default_taxonomy, height=150)
taxonomy_list = [cat.strip() for cat in user_taxonomy.split('\n') if cat.strip()]

# 2. File Uploader
st.markdown("### 2. Upload Messy Data (CSV)")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    # Read the uploaded CSV
    df = pd.read_csv(uploaded_file)
    
    st.write("👀 **Data Preview (First 5 rows):**")
    st.dataframe(df.head())
    
    # Let the user select which column contains the messy names
    messy_column = st.selectbox("Which column contains the messy product names?", df.columns)
    
    # 3. The Action Button
    if st.button("🚀 Categorize Data"):
        st.write("Processing... Please wait.")
        
        # Create a progress bar
        progress_bar = st.progress(0)
        clean_categories = []
        total_rows = len(df)
        
        # Loop through the data and update the progress bar
        for i, (index, row) in enumerate(df.iterrows()):
            messy_item = str(row[messy_column])
            mapped_category = categorize_product(messy_item, taxonomy_list)
            clean_categories.append(mapped_category)
            
            # Update progress
            progress_bar.progress((i + 1) / total_rows)
            # A tiny sleep to prevent hitting API rate limits too quickly
            time.sleep(0.5) 
            
        # Add the results to the dataframe
        df['AI_Category'] = clean_categories
        
        st.success("✅ Categorization Complete!")
        
        # Show the final editable dataframe (Human-in-the-loop!)
        st.write("✍️ **Review and Edit Results:**")
        edited_df = st.data_editor(df)
        
        # 4. Export Button
        st.markdown("### 3. Download Clean Data")
        csv_export = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Clean CSV",
            data=csv_export,
            file_name='clean_taxonomy_data.csv',
            mime='text/csv',
        )