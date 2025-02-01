import os
import PIL
from flask import Flask, request, render_template, send_from_directory
import google.generativeai as genai
import json
from dotenv import load_dotenv
from PIL import Image
import io
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get the API key from environment variables
api_key = os.getenv("GEMINI_API_KEY")

# Configure the generative AI client with the API key
genai.configure(api_key=api_key)

# Define the directory where uploaded files will be saved
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Path to your JSON file containing trash items
json_file_path = "trash.json"  # Replace with the actual file path

# Function to read JSON from a file
def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to extract all item names and prices from the JSON
def extract_items_and_prices(data):
    items_and_prices = {}
    for category in data['trash_items'].values():
        for item in category:
            item_name = item['item']
            price = item['price_per_unit']
            items_and_prices[item_name] = price
    return items_and_prices

# Read JSON content from file
data = read_json_from_file(json_file_path)

# Extract all items and their corresponding prices
items_and_prices = extract_items_and_prices(data)

# Prepare the list of all items as text
all_items_text = "\n".join(items_and_prices.keys())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "No file part", 400
    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    try:
        # Save the image to the static/uploads folder
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        userfile = PIL.Image.open(filename)

        # Create the prompt for the model
        prompt = "Find various objects present in this image."

        # Choose a Gemini model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

        # Generate content from the LLM with the image in byte array format
        response = model.generate_content([prompt, userfile])

        # Assuming response['content'] contains the text output (adjust based on your API's response structure)
        response_text = response.text

        # Prepare the prompt to match the items in the image
        prompt_to_match_items = f"""
        I have a list of items below, and a description of objects found in an image.
        Please match the items from the list that appear in the description and count how many times each item appears.
        If an item appears multiple times, count it accordingly.
        The list of items:
        {all_items_text}

        Here is the description:
        {response_text}

        Provide the result in the format:
        Item: Count
        """

        # Generate the result with the LLM
        result = model.generate_content([prompt_to_match_items])

        # Parse the result and create a table-friendly structure
        result_text = result.text
        print("Result Text:", result_text)

        # Initialize the dictionary to store item counts
        item_counts = {}

        # Split the result text into lines
        lines = result_text.splitlines()

        # Process each line to extract the item name and count
        for line in lines:
            line = line.replace("*", "").strip()

            # Skip lines that don't contain a colon (i.e., they don't follow the "Item: Count" structure)
            if ":" not in line:
                continue

            # Split the line into item name and count
            try:
                item_name, count = line.split(":")
                count = count.split('(')[0].strip()  # Remove the contents in parentheses (if any)
                count = int(count)  # Convert to integer

                # Store the item and its count in the dictionary
                item_counts[item_name] = count
            except ValueError:
                # Skip lines that don't match the expected "Item: Count" format
                continue

        # Calculate the total price based on the item counts
        total_price = 0
        item_details = {}

        for item_name, count in item_counts.items():
            if item_name in items_and_prices:
                price_str = items_and_prices[item_name]
                
                # Extract the price value (strip any currency symbols and 'per' parts)
                price_value = re.findall(r"[\d.]+", price_str)
                if price_value:
                    price = float(price_value[0])

                    # Calculate the total price for this item (price * count)
                    total_price += price * count

                    item_details[item_name] = {
                        "count": count,
                        "price_per_unit": price_str,
                        "total_price": price * count
                    }

        # Round the total price to two decimal places
        total_price = round(total_price, 2)

        # Return the result page with image, item counts, item details, and total price
        return render_template('results.html', item_counts=item_counts, item_details=item_details, image_filename=file.filename, total_price=total_price)

    except Exception as e:
        return f"Error processing the image: {e}", 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
