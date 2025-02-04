import streamlit as st
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
import nltk
from nltk.corpus import stopwords

# Page configuration
st.set_page_config(
    page_title="Phishing Site Detector",
    layout="wide"
)

# CSS styling ------------------------------------------------------------------------------------------------------------
st.markdown("""
<style>
            
[data-testid="stMetric"] {
    background-color: #e8e9eb;
    text-align: center;
    padding: 15px 0;
    border: 1px solid #000;
}
            
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

</style>
""", unsafe_allow_html=True)

# Model integration ------------------------------------------------------------------------------------------------------------
def predict_website_status(user_input):
    try:
        # Wrap the user input in a list
        website_status = classifier.predict([user_input])
        # For debugging - display status on terminal
        print(f"Predicted status: {website_status}")
        return website_status
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

# Page title & header
st.title("Phishing Website Detector")
st.markdown("A machine learning application used to identify a malicious website from its link. Input a link to get started!")

# Get user input
user_input = st.text_input("Enter a website link here")
st.markdown(f"Your input is: {user_input}")

# Load phishing detector model
try:
    with open("phishing.pkl", "rb") as pickle_in:
        classifier = pickle.load(pickle_in)
except Exception as e:
    st.error(f"Error loading model: {e}")

# Pass data to model & produce output
result = None
if st.button("Predict"):
    result = predict_website_status(user_input)

# Produce output and show in output section
if result is not None:
    if result[0] == 'good':  # Assuming 'good' means safe
        st.success("This website is safe")
    elif result[0] == 'bad':  # Assuming 'bad' means malicious
        st.warning("This website is malicious!")
else:
    st.error("Unable to predict the status of the website.")

# Dashboard ---------------------------------------------------------------------------------------------------------------
# Load the dataset
phish_data = pd.read_csv('phishing_site_urls.csv')

# Row 1
row1_col = st.columns((8, 4), gap='medium')

with row1_col[0]:
    # Dataset used
    st.write("### Dataset Used")
    st.write("Scroll through the dataset:")
    st.write(phish_data)

with row1_col[1]:
    # URL Counts from Dataset
    st.write("### URL Counts from Dataset")
    st.write("This dataset contains phishing urls (bad) and legitimate urls (good)")
    num_bad_urls = phish_data[phish_data['Label'] == 'bad'].shape[0]
    num_good_urls = phish_data[phish_data['Label'] == 'good'].shape[0]
    
    st.metric(label="Bad URL", value=num_bad_urls, delta=None)
    st.metric(label="Good URL", value=num_good_urls, delta=None)

# Row 2
row2_col = st.columns((6, 5), gap='medium')

with row2_col[0]:
    # TLD information
    st.write("### Top Level Domain Used in Phishing and Legitimate URL")
    bad_sites = phish_data[phish_data['Label'] == 'bad']
    good_sites = phish_data[phish_data['Label'] == 'good']

    top_tlds_phish = bad_sites['URL'].apply(lambda x: x.split('.')[-1])
    top_tlds_good = good_sites['URL'].apply(lambda x: x.split('.')[-1])

    plt.figure(figsize=(10, 6))
    sns.countplot(y=top_tlds_phish, order=top_tlds_phish.value_counts().index[:10], color='red', alpha=1.0, label='Phishing')
    sns.countplot(y=top_tlds_good, order=top_tlds_good.value_counts().index[:10], color='yellow', alpha=1.0, label='Legitimate')

    plt.title('Top 10 TLDs for Phishing and Legitimate URLs')
    plt.xlabel('Frequency')
    plt.ylabel('Top-Level Domain (TLD)')
    plt.legend()
    st.pyplot(plt)

with row2_col[1]:
    # Keyword Frequency in Phishing and Legitimate URLs
    st.write("### Keyword Frequency in Phishing and Legitimate URLs")
    def count_keywords(urls, keyword):
        return sum(url.count(keyword) for url in urls)
    
    keywords = ['login', 'bank', 'search', 'secure', 'account']

    keyword_counts_good = {keyword: count_keywords(good_sites['URL'], keyword) for keyword in keywords}
    keyword_counts_bad = {keyword: count_keywords(bad_sites['URL'], keyword) for keyword in keywords}

    plt.figure(figsize=(10, 6))
    plt.bar(keyword_counts_good.keys(), keyword_counts_good.values(), color='yellow', alpha=0.7, label='Good Sites')
    plt.bar(keyword_counts_bad.keys(), keyword_counts_bad.values(), color='red', alpha=0.7, label='Bad Sites')
    plt.title('Keyword Frequency in Good and Bad Sites')
    plt.xlabel('Keyword')
    plt.ylabel('Frequency')
    plt.legend()
    st.pyplot(plt)

# Row 3
row3_col = st.columns((3, 3.5, 6), gap='medium')

with row3_col[0]:
    # Calculate URL length statistics
    url_length_stats = phish_data.groupby('Label')['URL'].apply(lambda x: x.str.len().describe()).unstack()

    # Separate statistics for good and bad URLs
    url_length_stats_bad = url_length_stats.loc['bad']
    url_length_stats_good = url_length_stats.loc['good']

    # Create DataFrames for good and bad URL length statistics
    df_bad = pd.DataFrame(url_length_stats_bad).reset_index().rename(columns={'index': 'Statistic', 'bad': 'Value'})
    df_good = pd.DataFrame(url_length_stats_good).reset_index().rename(columns={'index': 'Statistic', 'good': 'Value'})
    
    # Display the statistics for bad URLs
    st.write("### Bad URL Statistics")
    st.dataframe(df_bad,
                 column_order=("Statistic", "Value"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "Statistic": st.column_config.TextColumn("Statistic"),
                    "Value": st.column_config.NumberColumn("Value", format="%f")
                 })

with row3_col[1]:
    # Display the statistics for good URLs
    st.write("### Good URL Statistics")
    st.dataframe(df_good,
                 column_order=("Statistic", "Value"),
                 hide_index=True,
                 width=None,
                 column_config={
                    "Statistic": st.column_config.TextColumn("Statistic"),
                    "Value": st.column_config.NumberColumn("Value", format="%f")
                 })

with row3_col[2]:
    # Define function to count special characters in a URL
    def count_special_characters(url):
        special_characters = set(string.punctuation)  # All special characters
        return sum(1 for char in url if char in special_characters)

    # Count special characters in phishing and legitimate URLs
    phish_data['special_char_count'] = phish_data['URL'].apply(count_special_characters)
    special_char_counts_phishing = phish_data[phish_data['Label'] == 'bad']['special_char_count']
    special_char_counts_legitimate = phish_data[phish_data['Label'] == 'good']['special_char_count']

    # Compare the mean special character count between phishing and legitimate URLs
    mean_special_char_count_phishing = special_char_counts_phishing.mean()
    mean_special_char_count_legitimate = special_char_counts_legitimate.mean()

    st.write("### Mean Special Character Count")
    # Create a bar plot to compare mean special character count for phishing and legitimate URLs
    plt.figure(figsize=(8, 5))
    bars = plt.bar(['Phishing', 'Legitimate'], [mean_special_char_count_phishing, mean_special_char_count_legitimate], color=['red', 'blue'])
    plt.xlabel('Label')
    plt.ylabel('Mean Special Character Count')
    
    # Annotate the bar chart with the mean values
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.05, round(yval, 2), ha='center', va='bottom')

    st.pyplot(plt)