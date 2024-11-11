import os
import openai
import subprocess
from datetime import datetime, timezone
import time
import sys
import logging

# Setup logging to a file for debugging and error output
logging.basicConfig(filename="revshell_debug.log", level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# Load the OpenAI API key from a file named API.txt
def load_api_key():
    """
    Loads the OpenAI API key from a file named 'API.txt' in the same directory.
    """
    try:
        with open("API.txt", "r") as file:
            api_key = file.read().strip()
            return api_key
    except FileNotFoundError:
        logging.error("API.txt file not found. Exiting.")
        exit(1)

# Initialize the OpenAI client instance with the API key
api_key = load_api_key()
client = openai.OpenAI(api_key=api_key)

def get_initial_prompt(task_description):
    """
    Constructs the initial prompt with the provided task description.
    """
    return (
        f"I want you to generate a complete, standalone Python program that can be saved to a single file and run from the command line. "
        "If any libraries or tools are required to run the program, provide UNIX commands to install them (e.g., using 'pip install'). "
        "Each response should be either a single UNIX command or a monolithic Python script to solve the entire task, including imports, functions, and logic. "
        "Respond ONLY with the code or command, and no explanations or additional text.\n\n"
        "If an error occurs during execution, I will send you the error message, and you should adjust the code or command to resolve it. "
        f"Once the task is fully completed, respond with 'Task completed' to indicate completion.\n\n"
        f"Here is the task: {task_description}"
    )

def get_ai_response(conversation_history):
    """
    Queries OpenAI's Assistant API for the next command or Python code based on the conversation history.
    """
    messages = conversation_history
    logging.debug("\n--- Sending request to OpenAI ---")
    logging.debug(messages)

    # Make the API call using the new client structure
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=300,  # Increased tokens to allow for larger code blocks
        temperature=0.3
    )
    
    logging.debug("\n--- Received response from OpenAI ---")
    logging.debug(response)

    # Extract and clean the response
    response_text = response.choices[0].message.content.strip()
    
    # Detect if response contains Python code or a UNIX command
    if response_text.startswith("```python"):
        code_text = response_text.split("```python")[1].split("```")[0].strip()
        return "python", code_text
    elif response_text.startswith("```bash") or response_text.startswith("sudo") or response_text.startswith("apt-get") or response_text.startswith("pip"):
        command_text = response_text.split("```bash")[1].split("```")[0].strip() if "```bash" in response_text else response_text
        return "unix", command_text
    else:
        return "python", response_text  # Default to Python code if unclassified

def save_and_execute_python_code(code):
    """
    Saves the Python code to a temporary file and executes it from the command line.
    Captures both stdout and stderr.
    """
    temp_file = "temp_code.py"
    with open(temp_file, "w") as f:
        f.write(code)

    logging.info(f"Executing Python code saved in {temp_file}")

    # Execute the Python file and capture output
    process = subprocess.Popen(f"python3 {temp_file}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    exit_code = process.returncode

    # Clean up the temp file after execution
    os.remove(temp_file)

    output = stdout + stderr  # Combine both stdout and stderr
    return output, exit_code

def execute_unix_command(command):
    """
    Executes a UNIX command (such as a package installation) on the shell.
    """
    logging.info(f"Executing UNIX command: {command}")

    # Run the UNIX command asynchronously and capture output
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    exit_code = process.returncode

    output = stdout + stderr  # Combine both stdout and stderr
    return output, exit_code

def format_output(command_type, command, output, exit_code):
    """
    Formats the output of executed commands or code.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    response = f"{'Python Code' if command_type == 'python' else 'UNIX Command'}:\n{command}\nOutput:\n{output}\nExit Code: {exit_code}\nTimestamp: {timestamp}"
    logging.debug(response)
    return response

def main_loop(task_description):
    print("Starting reverse shell with OpenAI Assistant API...")

    # Initialize conversation history with the task prompt
    conversation_history = [{"role": "user", "content": get_initial_prompt(task_description)}]
    previous_output = None
    retry_count = 0
    max_retries = 10  # Limit retries for any command to avoid infinite loop
    
    while True:
        # Step 1: Get the next command or code from the AI
        if previous_output:
            # Add the previous output to the conversation history
            conversation_history.append({"role": "assistant", "content": previous_output})

        command_type, command_text = get_ai_response(conversation_history)

        # Check if the AI indicates task completion
        if "task completed" in command_text.lower():
            print("AI indicated task completion. Exiting session.")
            logging.info("Session ended by AI indicating task completion.")
            break

        # Step 2: Execute the command or Python code
        if command_type == "python":
            print(f"\n--- Executing Python code ---\n{command_text}")
            output, exit_code = save_and_execute_python_code(command_text)
        else:
            print(f"\n--- Executing UNIX command ---\n{command_text}")
            output, exit_code = execute_unix_command(command_text)

        # Step 3: Check for execution success or failure
        if exit_code == 0:
            retry_count = 0  # Reset retry counter on success
            feedback_message = f"The {command_type} executed successfully. Output:\n{output}"
        else:
            retry_count += 1
            feedback_message = f"The {command_type} failed with exit code {exit_code}. Error output:\n{output}"
            if retry_count >= max_retries:
                print(f"{command_type.capitalize()} failed {max_retries} times. Exiting to avoid infinite loop.")
                logging.error(f"{command_type.capitalize()} '{command_text}' failed {max_retries} times. Ending session.")
                break

        # Step 4: Format the output as plain text and store it in the conversation history
        formatted_output = format_output(command_type, command_text, output, exit_code)
        print(f"\n--- Response to AI ---\n{formatted_output}")
        
        # Add feedback message to conversation history to prompt the assistant for an adjustment
        conversation_history.append({"role": "user", "content": feedback_message})

        # Update previous_output to guide AI in the next iteration
        previous_output = formatted_output

        # Optional: Add delay between commands to simulate response time
        time.sleep(2)

# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 revshell.py '<task_description>'")
        sys.exit(1)

    task_description = sys.argv[1]
    main_loop(task_description)
