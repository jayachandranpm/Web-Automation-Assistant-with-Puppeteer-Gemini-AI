# Web Automation Assistant with Puppeteer and Gemini AI

This project is a web-based automation tool that generates and executes Puppeteer scripts using Google Gemini AI. It allows users to automate browser tasks such as navigation, interaction with web elements, and handling common dialogs by simply providing a text prompt.

## Features
- **AI-Powered Script Generation**: Uses Google Gemini AI to generate Node.js Puppeteer scripts based on user prompts.
- **Flask Backend**: Handles user requests, generates scripts, and executes them using subprocesses.
- **Responsive Frontend**: Built with Tailwind CSS and CodeMirror for a clean and interactive user interface.
- **Logging and Error Handling**: Ensures robust script execution and provides detailed logs for debugging.
- **User-Friendly**: Simplifies complex web automation tasks with minimal user input.

## Technologies Used
- **Backend**: Python, Flask
- **AI Integration**: Google Gemini API
- **Automation**: Puppeteer (Node.js)
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS, CodeMirror
- **Logging**: Python logging module

## How It Works
1. The user inputs a prompt describing the browser automation task (e.g., "Go to Google, search for 'web automation', and take a screenshot").
2. The Flask backend sends the prompt to the Gemini API, which generates a Puppeteer script.
3. The backend executes the script using Node.js and returns the results (logs, output, or errors) to the frontend.
4. The user can view the generated script, execution logs, and output in the browser.

## Installation
1. Clone the repository:
   ```bash
   git clone [[https://github.com/your-username/web-automation-assistant](https://github.com/jayachandranpm/Web-Automation-Assistant-with-Puppeteer-Gemini-AI)](https://github.com/jayachandranpm/Web-Automation-Assistant-with-Puppeteer-Gemini-AI.git
   cd web-automation-assistant```
