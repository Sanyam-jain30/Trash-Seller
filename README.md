# Trash Seller

## Overview:
Trash Seller uses image recognition and AI to detect trash items from uploaded images and estimate their price based on predefined unit rates. It creates a marketplace for users to sell trash, promoting recycling and reducing pollution.

## Setup Instructions:
1. Clone the repository:

    ``` bash
    git clone https://github.com/yourusername/trash-seller.git
    ```

2. Install dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

3. Set up your ```.env``` file with the necessary API key:

    ``` bash
    GEMINI_API_KEY=your-api-key-here
    ```

4. Run the Flask app:

    ``` bash
    python server.py
    ```

5. Visit ```http://127.0.0.1:5000/``` in your browser to upload images.

