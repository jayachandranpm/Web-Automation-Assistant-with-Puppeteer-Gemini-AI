from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import subprocess
import os
import logging
import re
from datetime import datetime

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
log_file = 'automation.log'
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def remove_markdown_code_fences(text):
    """Removes markdown code fences from the given text."""
    # Regex to remove ```javascript or ```js or ``` and any other text between those.
    pattern = r'```(?:javascript|js)?\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        # Use the last match which will be the code within the markdown fences
        return matches[-1].strip()
    else:
       return text.strip()


def generate_puppeteer_script(user_prompt):
    logger.info(f"Generating Puppeteer script with Gemini for: {user_prompt}")
    
    prompt = f"""
    You are an expert in writing Puppeteer automation scripts.  
    Your task is to write a Node.js script using Puppeteer to automate a web browser according to the user's instructions.
    The script should:
    - Launch a Chrome browser with the following arguments:
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--window-position=0,0',
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        '--disable-notifications',
        '--disable-popup-blocking'
    - **It must launch a visible browser. This is mandatory. The browser must not be headless**
    - Create a new page, set its viewport to 1280x800 and default navigation timeout to 60 seconds.
    - Handle any common dialogs or modals (like "Stay signed out" or cookie consent) that might appear on major sites.
    - Perform the actions specified in the user's request (like clicking elements, entering text, etc).
    - Ensure proper error handling, logging any error to the console and taking a screenshot on error.
    - Use try/catch blocks for error handling and logging all actions to console.
    - Finally, make sure to close the browser instance in a 'finally' block.
    - Make sure to include timeout to avoid any infinite waiting.
    - **Crucially, before attempting to interact with the search input**, use `await page.waitForSelector('input[name="q"], input[title="Search"], textarea[name="q"]', {{ visible: true, timeout: 30000 }})`. The `visible: true` option *must* be inside the object passed to `waitForSelector`. **Make sure the timeout is greater than 30 seconds.**
    - Make sure to use `await page.goto()` to navigate to any page.
    - Make sure you use all three of the search input selectors `input[name="q"], input[title="Search"], textarea[name="q"]` when attempting to interact with the search input.
    - Make sure to wait for the search result to load before closing the browser.
     - You MUST declare the 'browser' and 'page' variables outside the 'try' block and initialize to `null`, to ensure they are accessible in `catch` and `finally` blocks.
    - Use `console.log()` to log any action during script execution.

    User request: {user_prompt}
    
    Respond ONLY with the Node.js Puppeteer code. Ensure the code runs directly, includes `const puppeteer = require('puppeteer');`. **Do not include any markdown code formatting or any other text. Just provide the javascript code.** Make sure that your response is a full and executable javascript file that runs correctly with the command 'node script.js'.
    """


    try:
        response = model.generate_content(prompt)
        script = response.text
        logger.info(f"Generated Puppeteer script with Gemini: {script}")
        return script
    except Exception as e:
        logger.error(f"Error generating script from Gemini: {e}")
        return None



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')
        
        if not user_prompt:
            logger.error("No prompt provided")
            return jsonify({'status': 'error', 'message': 'No prompt provided'}), 400

        logger.info(f"Processing new automation request: {user_prompt}")

        # Generate Puppeteer script
        puppeteer_code = generate_puppeteer_script(user_prompt)
        if not puppeteer_code:
            logger.error("Failed to generate Puppeteer script")
            return jsonify({'status': 'error', 'message': 'Failed to generate script'}), 500
        
        # Remove markdown code fences
        puppeteer_code = remove_markdown_code_fences(puppeteer_code)
    

        # Create timestamp for this run
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create directory for this run's artifacts
        run_dir = os.path.join('runs', timestamp)
        os.makedirs(run_dir, exist_ok=True)

        # Save script to file
        script_path = os.path.join(run_dir, 'puppeteer_script.js')
        with open(script_path, 'w') as f:
            f.write(puppeteer_code)
        
        logger.info(f"Saved Puppeteer script to {script_path}")

        # Execute Puppeteer script
        logger.info("Executing Puppeteer script")
        result = subprocess.run(
            ['node', script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Log the results
        if result.returncode == 0:
            logger.info("Script executed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Script execution failed: {result.stderr}")

        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': result.stderr,
                'code': puppeteer_code,
                'logs': get_recent_logs()
            })

        return jsonify({
            'status': 'success',
            'message': result.stdout,
            'code': puppeteer_code,
            'logs': get_recent_logs()
        })

    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out")
        return jsonify({
            'status': 'error',
            'message': 'Script execution timed out after 5 minutes',
            'logs': get_recent_logs()
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}',
            'logs': get_recent_logs()
        }), 500

def get_recent_logs(lines=50):
    try:
        with open(log_file, 'r') as f:
            return f.readlines()[-lines:]
    except Exception as e:
        return [f"Error reading logs: {str(e)}"]

if __name__ == '__main__':
    os.makedirs('runs', exist_ok=True)
    app.run(debug=True)