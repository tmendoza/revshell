# Reverse Shell AI Command Executor

This repository contains a Python-based command execution tool that leverages an AI (via the OpenAI API) to issue and execute specific UNIX commands or generate standalone Python scripts to fulfill a high-level task. **Unlike traditional systems where users specify exact commands, this tool "flips" the interaction model**: the user provides a high-level task description, and the AI autonomously determines the necessary commands and code to achieve the goal.

With this setup, the AI becomes the "operator," issuing precise UNIX commands or Python scripts in response to real-time feedback from each execution, thus iterating and refining its approach as needed.

---

## Key Features

- **High-Level Task Interpretation**: The user provides a broad task description, and the AI breaks it down into actionable UNIX commands or Python scripts.
- **Python Script Generation**: If the task requires complex logic, the AI generates a standalone Python script, which is saved, executed, and deleted automatically after completion.
- **Error Detection and Adjustment**: If a command or script fails, the AI receives the error details and can adjust its approach, retrying with modified commands if needed.
- **Seamless Switching Between UNIX and Python**: The tool can distinguish whether a response is a UNIX command or Python script, ensuring the appropriate execution environment.
- **Autonomous Execution Loop**: The AI issues commands, evaluates feedback, and continues iterating until the task is completed.

---

## Concept: Flipping the Interaction Model

In most systems, users manually break down tasks and issue individual commands. Here, we reverse this relationship:

1. **User Provides High-Level Task**: Instead of specifying step-by-step commands, the user describes an outcome, like “Create a chart of NVIDIA's stock price over the last 3 months.”
   
2. **AI as Command Generator**: The AI determines whether each step requires a simple UNIX command or a standalone Python script, issuing each in response to real-time feedback.
   
3. **Iterative Feedback and Refinement**: After each execution, the tool captures the output or error message, allowing the AI to refine its approach based on feedback.

4. **Closed-Loop Control**: The AI continues generating commands and code until it indicates the task is complete, ensuring that high-level goals are met without micromanagement.

This interaction model is flexible, allowing the AI to solve complex tasks through autonomous command generation, script execution, and error-handling.

---

## How It Works

This tool operates as a closed-loop system, consisting of several components:

### 1. **Loading the OpenAI API Key**

The `load_api_key` function reads the OpenAI API key from a file named `API.txt` in the project root directory. This key is necessary for authenticating requests to OpenAI’s API.

### 2. **Generating the Initial Prompt**

The `get_initial_prompt` function defines the initial task, specifying that the AI should respond only with:

- **A UNIX command** for simple tasks, such as installing a library or executing system commands.
- **A standalone Python script** for complex operations that require programming logic. 

The AI is instructed to provide a single, complete response for each step, either as a UNIX command or as a monolithic Python script.

### 3. **AI Response Processing**

The `get_ai_response` function:

- Queries the OpenAI API with the task and conversation history.
- Determines whether the AI response is a UNIX command (e.g., installing a package) or a Python script based on response content.
- If the AI response starts with standard UNIX command prefixes (like `sudo`, `pip`, etc.), it treats it as a UNIX command; otherwise, it defaults to Python code.

### 4. **Executing the Command or Python Code**

The `execute_unix_command` and `save_and_execute_python_code` functions manage execution:

- **For UNIX commands**: The function runs the command in a shell environment and captures output and errors.
- **For Python scripts**: The function saves the AI-generated code to a temporary file, executes it, captures output, and deletes the file.

In each case, the output and any errors are combined and returned to the AI as feedback.

### 5. **Formatting Output for AI Feedback**

The `format_output` function structures the response with the command type, content, output, exit code, and timestamp. This formatted feedback provides the AI with full context for each execution step, allowing it to adjust commands intelligently.

### 6. **Iterative Command Execution Loop**

The `main_loop` function controls the interaction loop:

1. **Task Request and AI Command Generation**: Sends the task prompt to the AI and receives commands or code to execute.
2. **Execution and Feedback**: Executes each command or code, captures the output, and logs the results.
3. **Retry Mechanism**: If a command or script fails, it retries up to a maximum number of attempts (default is 10).
4. **Completion Check**: The loop exits when the AI indicates that the task is fully completed, or the retry limit is reached.

---

## Example Usage

Run the tool by specifying a high-level task description:

HINT: Letting the AI know what type of system you are on can make things run smoother.

### Retrieving Stock Data
```bash
python3 revshell.py "I am on a modern macOS system.  Download NVIDIA's stock data for the past 3 months and generate a line chart."
```

### Generate a process report and then display it in a spreadsheet application.
```bash
python3 revshell9.py "I am on a modern macOS laptop. Generate a list of all of the processes running this machine.  Place the output into a CSV file.  Place the file in my home directory.  Then open the file for viewing."
```

This result of this command was a CSV file located in my home directory and then it opened the CSV file in macOS Numbers without me having to tell it which program to use.  Here is the output

```bash
(env) tmendoza@Tonys-MacBook-Pro revshell % python3 revshell.py "I am on a modern macOS laptop. Generate a list of all of the processes running this machine.  Place the output into a CSV file.  Place the file in my home directory.  Then open the file for viewing."

Starting reverse shell with OpenAI Assistant API...

--- Executing Python code ---
import csv
import os
import subprocess

def list_processes():
    # Use 'ps' command to fetch list of processes
    process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
    output, error = process.communicate()
    
    # Split the output into lines and parse
    lines = output.splitlines()
    data = [line.split(None, 10) for line in lines]
    
    # Define the path for the CSV file in the home directory
    home_dir = os.path.expanduser('~')
    csv_file_path = os.path.join(home_dir, 'processes.csv')
    
    # Write data to CSV
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    # Open the CSV file
    subprocess.run(['open', csv_file_path])

if __name__ == "__main__":
    list_processes()

--- Response to AI ---
Python Code:
import csv
import os
import subprocess

def list_processes():
    # Use 'ps' command to fetch list of processes
    process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
    output, error = process.communicate()
    
    # Split the output into lines and parse
    lines = output.splitlines()
    data = [line.split(None, 10) for line in lines]
    
    # Define the path for the CSV file in the home directory
    home_dir = os.path.expanduser('~')
    csv_file_path = os.path.join(home_dir, 'processes.csv')
    
    # Write data to CSV
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    # Open the CSV file
    subprocess.run(['open', csv_file_path])

if __name__ == "__main__":
    list_processes()
Output:

Exit Code: 0
Timestamp: 2024-11-10T23:51:13.354661+00:00
AI indicated task completion. Exiting session.
```

### Expected Flow:

1. **AI Recognizes Libraries Needed**: Generates a command to install required libraries (e.g., `pip install yfinance matplotlib`).
2. **AI Generates Python Script**: The AI generates a full Python script using `yfinance` and `matplotlib` to download stock data and plot it.
3. **Error Detection and Adjustment**: If any errors occur during execution (e.g., missing libraries or syntax issues), the AI receives the error output and adjusts the code.
4. **Completion**: The AI eventually indicates “Task completed,” signaling the end of the interaction.

---

## Logging

All interactions are logged in `revshell_debug.log`, including:

- **Commands and Scripts Issued**: Each step generated by the AI is recorded.
- **Output and Errors**: Full details of each execution are logged, helping diagnose any issues in AI command generation.
- **Retries**: If a command fails and is retried, each attempt is logged.
- **Completion Status**: Whether the task completed successfully or reached the retry limit is logged for easy review.

This log provides complete traceability and debugging insights for each interaction.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tmendoza/revshell.git
   cd revshell
   ```

2. Install dependencies:
   ```bash
   pip install openai
   ```

3. Set up your OpenAI API key:
   - Place your API key in a file named `API.txt` in the root directory of the project.

---

## Novelty of the Approach

This tool leverages an innovative interaction model, reversing the typical command-control relationship:

1. **AI as the Operator**: Instead of receiving direct instructions, the AI autonomously decides what commands or code to execute based on a high-level goal.
2. **Feedback Loop**: Each step produces feedback, which the AI uses to refine its approach. This closed-loop control enables the AI to adapt dynamically.
3. **Python Integration**: The AI can generate Python scripts as part of its instructions, enhancing flexibility for complex tasks that require programmatic logic rather than simple shell commands.
4. **Error-Handling and Retry Logic**: The tool integrates retry mechanisms and logs feedback, enabling the AI to handle errors intelligently and attempt different strategies if initial attempts fail.

The result is an interesting, flexible tool that can autonomously solve high-level tasks through AI-directed command and code execution. It is especially suited for tasks that require both shell commands and lightweight scripting, such as data processing, system diagnostics, or integration with external APIs.

## Experimental

This code is experimental and designed to validate an idea: Can we get an LLM to act as an orchestrator and submit commands to a executor repeatedly in an attempt to complete a high-level task and guide itself to the right solution without any human intervention.  

Though it has a few warts and is a bit ugly, this appears to work.  This feels important because I was able to get the AI to drive the session with the Python program just acting as a sort of job runner and output reporter back to the LLM, which, based on the returned output, can decide what to do next.

This was all done with less than 200 lines of code total.  All in one file and very easy to read.  And... was completely written by ChatGPT.  Took about an hour or two of interaction with ChatGPT to get it to work reasonably well.  Give it a try but I am sure it will have bugs.  But then all YOU have to do is pop this README, the errors and this code into ChatGPT and have it fix it for you.

My next version will be more feature rich and more modular and manageable.