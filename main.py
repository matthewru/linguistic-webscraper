import requests
from bs4 import BeautifulSoup
import csv
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import string

def scrape_cambridge_dictionary(word):
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
    }
    # print(f"Fetching data for {word} from {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for {word}")
        return [], [], []  # Return empty lists for entries, definitions, and redundant definitions
    
    soup = BeautifulSoup(response.text, 'html.parser')
    entries = []   
    definitions = []
    redundant_definitions = []
    
    # Locate the section containing definitions
    definition_sections = soup.find_all("div", class_="sense-body")
    if not definition_sections:
        print(f"Definitions not found for {word}")
        return [], [], []  # Return empty lists if no definitions are found
    
    # print(f"\nProcessing word: {word}")
    
    # Extract definitions
    for section in definition_sections:
        part_of_speech_tag = section.find_previous("span", class_="pos")
        part_of_speech = part_of_speech_tag.get_text() if part_of_speech_tag else "Unknown"
        # print(f"\nFound part of speech: {part_of_speech}")
        
        definition_list = section.find_all("div", class_="def-block")
        for definition in definition_list:
            def_tag = definition.find("div", class_="def")
            if def_tag:
                definition_text = def_tag.get_text()
                definition_text = ' '.join(definition_text.split())  # Normalize spaces
                definition_text = remove_articles(definition_text)  # Remove articles
                definition_text = remove_punctuation(definition_text)  # Remove punctuation
                definitions.append(definition_text)
            else:
                print("Definition tag not found.")
                continue
            
            example_sentence = ""
            if word.lower() in definition_text.lower():
                redundant_definitions.append((word, definition_text))
            
            # Find example sentence if available
            example_tag = definition.find("div", class_="examp")
            if example_tag:
                example_sentence = example_tag.get_text()
                example_sentence = ' '.join(example_sentence.split())  # Normalize spaces
            
            entries.append([word, part_of_speech, definition_text, example_sentence])
            # print(f"Added definition: {definition_text[:50]}...")
    
    # print(f"\nTotal entries found for {word}: {len(entries)}")
    return entries, definitions, redundant_definitions

def save_to_csv(data, filename="cambridge_dictionary_data.csv"):
    if not data:
        print("No data to save!")
        return
        
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Part of Speech", "Definition", "Example"])
        writer.writerows(data)
    print(f"Data saved to {filename}")

def generate_word_cloud(definitions, highlight_word=None):
    text = " ".join(definition[2] for definition in definitions)
    text = remove_articles(text)
    word_frequencies = {}
    for word in text.split():
        word_frequencies[word] = word_frequencies.get(word, 1) + 1
    
    if highlight_word and highlight_word in word_frequencies:
        word_frequencies[highlight_word] *= 5  # Increase weight of highlighted word
    
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_frequencies)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    
def analyze_redundancy(redundant_definitions):
    if redundant_definitions:
        print("Words with redundant definitions:")
        for word, definition in redundant_definitions:
            print(f"{word}: {definition}")
    else:
        print("No redundant definitions found.")

def remove_articles(text):
    articles = {"a", "an", "the", "or", "to", "and", "in", "it"}
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in articles]
    return ' '.join(filtered_words)

def remove_punctuation(text):
    # Create a translation table that maps each punctuation character to None
    translator = str.maketrans('', '', string.punctuation)
    # Use the translate method to remove punctuation
    return text.translate(translator)

def scrape_article(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to fetch the article")
        return ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the main content of the article
    # This will depend on the structure of the page; you may need to inspect the HTML to find the right tags
    article_body = soup.find('div', class_='article-body-commercial-selector article-body-viewer-selector dcr-11jq3zt')  # Example class name
    if not article_body:
        print("Article content not found")
        return ""
    
    # Extract text from the article body
    paragraphs = article_body.find_all('p')
    article_text = ' '.join(paragraph.get_text() for paragraph in paragraphs)
    
    return article_text

# Example usage
word_list = []  # Initial word list
data = []
definitions = []
redundant_definitions = []
url = "https://www.theguardian.com/commentisfree/2025/mar/31/trump-logging-us-forests"
article_text = scrape_article(url)
print("Scraped article")
# print(article_text)

# Extract words from the article and add them to the word list
article_text = remove_punctuation(article_text)
article_words = article_text.split()
word_list.extend(article_words)  # Add words from the article to the word list
word_list = list(set(word_list))  # Remove duplicates


print("Updated word list:")
print(word_list)
print("Starting scraping process...")
for word in word_list:
    entries, word_defs, redundant_defs = scrape_cambridge_dictionary(word) 
    data.extend(entries)
    definitions.extend(word_defs)
    redundant_definitions.extend(redundant_defs)
print(f"\nTotal entries collected: {len(data)}")
if data:
    save_to_csv(data)
    print("Data saved to cambridge_dictionary_data.csv")
    analyze_redundancy(redundant_definitions)
    # generate_word_cloud(data)
else:
    print("No data to save")

def read_csv(filename="cambridge_dictionary_data.csv"):
    data = []
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            data.append(row)  # Append each row to the data list
    return data

# Example usage
data = read_csv()
generate_word_cloud(data)
