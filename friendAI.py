import gradio as gr
import openai
from googletrans import Translator
from newsapi import NewsApiClient

# Set your OpenAI API key
openai.api_key = "OpenAI-API-key"

# Set your NewsAPI key
newsapi = NewsApiClient(api_key="NewsAPI-Key")

# Initialize memory
user_memory = {}
conversation_log = []
translator = Translator()

# Jokes and Trivia Lists
jokes = [
    "Why don’t scientists trust atoms? Because they make up everything!",
    "Why did the math book look sad? Because it had too many problems.",
    "What do you call fake spaghetti? An impasta!",
    "What do you call a pony with a cough? A little horse!",
    "What did one hat say to the other? You wait here. I’ll go on a head!",
    "What do you call a magic dog? A labracadabrador!",
    "What did the shark say when he ate the clownfish? This tastes a little funny..."
]

trivia = [
    "Did you know? The Eiffel Tower can be 15 cm taller during the summer.",
    "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.",
    "Did you know? A group of flamingos is called a 'flamboyance.'",
    "Did you know? A cloud weighs around a million tonnes.",
    "Did you know? Giraffes are 30 times more likely to get hit by lightning than people.",
    "Did you know? Identical twins don’t have the same fingerprints.",
    "Did you know? Earth’s rotation is changing speed. It's actually slowing down. Every century, the days get ~1.8 seconds longer!"
]

# Function to manage user memory
def manage_memory(user_input, user_name):
    global user_memory

    # Normalize user input for easier processing
    normalized_input = user_input.lower().replace("whats", "what's")

    # Initialize memory for the user if not already present
    if user_name not in user_memory:
        user_memory[user_name] = {}

    if "what's my" in normalized_input:
        # Extract the key by splitting the input
        key = normalized_input.split("what's my")[-1].strip().rstrip("?")
        # Check if the key exists in user's memory
        if key in user_memory[user_name]:
            return f"Your {key} is {user_memory[user_name][key]}."
        else:
            return f"I don't know your {key} yet. You can tell me by saying, 'My {key} is...'."

    if "my" in normalized_input and "is" in normalized_input:
        # Parse input to extract key-value pair
        parts = normalized_input.split("my", 1)[-1].split("is", 1)
        if len(parts) == 2:
            key = parts[0].strip().lower()  # Normalize the key to lowercase
            value = parts[1].strip()
            # Store the value in the user's memory
            user_memory[user_name][key] = value
            return f"Got it! I'll remember that your {key} is {value}."

    # Default response if no memory-related action is needed
    return None

# Function to handle calculations
def calculate(expression):
    """
    Simple calculator function to evaluate basic math expressions.
    """
    try:
        result = eval(expression)
        return f"The answer is {result}."
    except Exception as e:
        return "I couldn't calculate that. Please make sure your math expression is valid."

# Function to handle unit conversion
def convert_units(user_input):
    """
    Converts units based on user input.
    """
    conversion_factors = {
        "meters to feet": 3.28084,
        "feet to meters": 0.3048,
        "kilograms to pounds": 2.20462,
        "pounds to kilograms": 0.453592,
        "liters to gallons": 0.264172,
        "gallons to liters": 3.78541
    }

    try:
        parts = user_input.lower().split("convert")[-1].strip().split(" to ")
        value, source_unit = parts[0].split()[0], " ".join(parts[0].split()[1:])
        target_unit = parts[1]
        key = f"{source_unit} to {target_unit}"

        if key in conversion_factors:
            converted_value = float(value) * conversion_factors[key]
            return f"{value} {source_unit} is equal to {converted_value:.2f} {target_unit}."
        else:
            return "Sorry, I can't convert those units yet."
    except Exception as e:
        return "I couldn't understand your conversion request. Please use the format 'Convert [value] [source unit] to [target unit]'."

# Function to handle translations
def translate_text(user_input):
    try:
        if "translate" in user_input.lower():
            parts = user_input.lower().split("translate")[-1].strip().split(" to ")
            text_to_translate = parts[0].strip("'").strip("\"")
            target_language = parts[1].strip()

            translated = translator.translate(text_to_translate, dest=target_language)
            return f"'{text_to_translate}' in {target_language} is '{translated.text}'."
        else:
            return None
    except Exception as e:
        return "I couldn't understand your translation request. Please use the format 'Translate [text] to [language]'."

# Function to fetch news
def fetch_news(topic=None):
    try:
        if topic:
            articles = newsapi.get_everything(q=topic, language='en', sort_by='relevancy', page_size=5)
        else:
            articles = newsapi.get_top_headlines(language='en', page_size=5)

        if articles['status'] == 'ok' and articles['totalResults'] > 0:
            news_list = [f"- {article['title']} (Source: {article['source']['name']})" for article in articles['articles']]
            return "\n".join(news_list)
        else:
            return "I couldn't find any news on that topic right now."
    except Exception as e:
        return "Sorry, I encountered an error while fetching news."

# Function to generate AI response
def generate_response(user_input, user_name, ai_personality):
    global user_memory

    if any(op in user_input for op in ['+', '-', '*', '/']):
        expression = user_input.replace("calculate", "").replace("what's", "").replace("?", "").strip()
        return calculate(expression)

    if "convert" in user_input.lower():
        return convert_units(user_input)

    if "translate" in user_input.lower():
        return translate_text(user_input)

    if "news" in user_input.lower():
        topic = user_input.lower().replace("news about", "").replace("news", "").strip()
        return fetch_news(topic if topic else None)

    memory_response = manage_memory(user_input, user_name)
    if memory_response:
        return memory_response

    if "tell me a joke" in user_input.lower():
        import random
        return random.choice(jokes)

    if "tell me trivia" in user_input.lower():
        import random
        return random.choice(trivia)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ai_personality},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response.choices[0].message.content.strip()

        # Return the reply without appending to the conversation log
        return reply
    except Exception as e:
        return "Sorry, I encountered an error while generating a response."

# Gradio interface
def chat_with_ai(user_name, ai_personality, user_input, avatar):
    if not user_name:
        return "Please enter your name."
    if not user_input:
        return "Please enter a message."

    response = generate_response(user_input, user_name, ai_personality)

    # Append user input and AI response to the conversation log
    conversation_log.append({"user": user_input, "ai": response})

    # Build conversation history as a formatted string
    history = "\n".join([f"You: {log['user']}\nAI: {log['ai']}" for log in conversation_log])

    return history, avatar

# Gradio app layout
with gr.Blocks() as demo:
    gr.Markdown("# Your Personal AI Friend")
    gr.Markdown("Talk to an AI friend you can personalize! Your AI friend is just in front of you!")
    with gr.Row():
        with gr.Column(scale=1):
            avatar = gr.Image(label="Your Avatar", type="pil")
            user_name = gr.Textbox(label="Your Name", placeholder="Enter your name (e.g.: Alice)...")
            ai_personality = gr.Textbox(label="Friend's Personality", placeholder="Enter your AI friend's personality (e.g.: 'You are a sweet friend')")
        with gr.Column(scale=2):
            conversation_history = gr.Textbox(label="Conversation", placeholder="Conversation will appear here...", interactive=False)
            user_input = gr.Textbox(label="Your Message", placeholder="Enter your message. Out of ideas? Ask for a joke or some trivia...")
            send_button = gr.Button("Send")
    
    send_button.click(
        chat_with_ai,
        inputs=[user_name, ai_personality, user_input, avatar],
        outputs=[conversation_history, avatar]
    )

# Launch Gradio app
demo.launch(share=True)