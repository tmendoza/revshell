### Experimenting with Agentic Behavior Using OpenAI: A Lightweight Approach to Autonomy

In the evolving world of artificial intelligence, the quest to build autonomous, agent-like systems has led to the development of complex agent frameworks. Libraries like LangChain, Haystack, and similar tools are designed to enable "agentic" behavior—programs that can act independently, interpret user instructions, and adapt their behavior in response to errors or feedback. However, these frameworks come with their own challenges: steep learning curves, heavy dependencies, and often a level of complexity that may be overkill for simple use cases.

The **revshell** project on [GitHub](https://github.com/tmendoza/revshell) takes a different, more experimental approach. Instead of a heavyweight framework, it explores how agent-like behavior can be achieved using a lightweight Python script with minimal dependencies. This project is an experiment in reversing the typical human-AI interaction model to empower the AI as the primary driver of action. It explores whether we can achieve true autonomy in a compact and understandable way without additional agent libraries. However, **caveat emptor**—this is an experimental setup and comes with limitations and quirks that make it an exploratory tool rather than a production-ready system.

In this article, we’ll walk through how revshell works, highlighting the exploratory nature of the project and discussing both its potential and its limitations.

---

### Project Overview: A Reversed Interaction Model

In traditional automation, the user provides a step-by-step breakdown, and the system executes each command with minimal autonomy. **revshell** flips this model around: instead of the user providing specific instructions, they provide a high-level task description. The AI, powered by OpenAI’s language model, then interprets this task, breaks it down into steps, and issues commands directly to the system.

For example, a user might request: “Generate a chart of NVIDIA’s stock price over the last three months.” Rather than guiding the AI step-by-step, revshell hands over control, allowing the AI to decide which packages to install, which Python code to write, and how to handle any errors that arise. This hands-off, reversed approach brings autonomy but also introduces an element of unpredictability—a characteristic that may appeal to experimenters and early adopters but also poses risks in a production setting.

### Key Components of the revshell Code

#### 1. **Simple Setup and Configuration**

The revshell script is designed to be easy to set up. It requires only an OpenAI API key, which is read from a local file (`API.txt`). Additionally, logging captures debug output in `revshell_debug.log` for easy troubleshooting and post-execution analysis.

```python
def load_api_key():
    try:
        with open("API.txt", "r") as file:
            api_key = file.read().strip()
            return api_key
    except FileNotFoundError:
        logging.error("API.txt file not found. Exiting.")
        exit(1)
```

#### 2. **Directing the AI with a Carefully Crafted Prompt**

The key to revshell’s autonomy lies in its prompt design. By providing clear instructions on output format and expected behavior, the AI is primed to respond with executable commands rather than natural language explanations. This is essential to keep the system non-interactive.

```python
def get_initial_prompt(task_description):
    return (
        f"I want you to generate a complete, standalone Python program that can be saved to a single file and run from the command line. "
        "If any libraries or tools are required to run the program, provide UNIX commands to install them (e.g., using 'pip install'). "
        "Each response should be either a single UNIX command or a monolithic Python script to solve the entire task, including imports, functions, and logic. "
        "Respond ONLY with the code or command, and no explanations or additional text.\n\n"
        "If an error occurs during execution, I will send you the error message, and you should adjust the code or command to resolve it. "
        f"Once the task is fully completed, respond with 'Task completed' to indicate completion.\n\n"
        f"Here is the task: {task_description}"
    )
```

This prompt shifts responsibility onto the AI, encouraging it to adapt based on feedback. The novelty here is in the experimentation: rather than the AI simply providing assistance, it’s responsible for solving issues, issuing installation commands, and adjusting its responses autonomously.

#### 3. **Parsing and Executing AI Responses**

The `get_ai_response` function captures responses from OpenAI and determines whether the output is a Python script or a UNIX command. The script classifies responses and executes them accordingly, parsing markdown formatting (` ```python `, ` ```bash `) when necessary.

```python
def get_ai_response(conversation_history):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=conversation_history,
        max_tokens=300,
        temperature=0.3
    )

    response_text = response.choices[0].message.content.strip()
    
    if response_text.startswith("```python"):
        code_text = response_text.split("```python")[1].split("```")[0].strip()
        return "python", code_text
    elif response_text.startswith("```bash") or response_text.startswith("sudo") or response_text.startswith("apt-get") or response_text.startswith("pip"):
        command_text = response_text.split("```bash")[1].split("```")[0].strip() if "```bash" in response_text else response_text
        return "unix", command_text
    else:
        return "python", response_text
```

This method allows revshell to differentiate between code and commands effectively, issuing UNIX commands when dependencies are missing and running Python scripts to achieve the user’s task. By iterating on failed commands, the AI adjusts its responses, simulating agentic behavior in a simple feedback loop.

#### 4. **Feedback Loop for Error Handling and Adjustments**

The core of revshell’s adaptability lies in its feedback loop. If a command or script fails, the AI receives the error message as context in the next prompt. This nudges the AI to reconsider its strategy and issue an adjusted command, creating a cycle of experimentation and adaptation.

```python
def main_loop(task_description):
    conversation_history = [{"role": "user", "content": get_initial_prompt(task_description)}]
    previous_output = None
    retry_count = 0
    max_retries = 10  # Limit retries for any command to avoid infinite loop
    
    while True:
        if previous_output:
            conversation_history.append({"role": "assistant", "content": previous_output})

        command_type, command_text = get_ai_response(conversation_history)

        if "task completed" in command_text.lower():
            print("AI indicated task completion. Exiting session.")
            logging.info("Session ended by AI indicating task completion.")
            break

        if command_type == "python":
            output, exit_code = save_and_execute_python_code(command_text)
        else:
            output, exit_code = execute_unix_command(command_text)

        feedback_message = f"The {command_type} executed successfully." if exit_code == 0 else f"The {command_type} failed with exit code {exit_code}."
        
        # Feedback added to conversation history
        conversation_history.append({"role": "user", "content": feedback_message})
        previous_output = feedback_message
```

This approach is not without risks; as the AI iterates, it may issue commands that change the environment in unpredictable ways. **Caveat emptor**: the experimental nature of this loop means that running it on a production system could lead to unexpected results.

---

### Experiment in Action: Generating a Stock Price Chart

As a proof of concept, consider a high-level task: **“Produce a PNG chart of NVIDIA’s stock price over the last three months.”** When this request is given to revshell, the AI:

1. Issues a `pip install` command for the required libraries, `yfinance` and `matplotlib`.
2. Generates a Python script to retrieve NVIDIA’s stock data and plot it.
3. Runs the script and presents the output.

Throughout this process, if an error occurs, the system automatically provides feedback to the AI to generate a revised command or code snippet. The AI iterates until the task is successfully completed, marking the end of the session with “Task completed.”

### Experimental Benefits and Limitations

The revshell project is an experimental look at what’s possible when we strip down agentic behavior to its essentials. Here’s what makes it both promising and challenging:

- **Simplicity**: Without needing external agent libraries, revshell achieves surprising autonomy, capable of adjusting its behavior based on errors.
- **Minimal Dependencies**: By relying only on the OpenAI API and standard Python libraries, revshell minimizes dependency management and deployment complexities.
- **Error-Driven Adaptability**: The feedback loop makes the AI responsible for solving problems autonomously, a novel approach that brings surprising flexibility.

But the project also has some critical limitations:

- **Risk of Unpredictable Behavior**: Since the AI makes decisions based on limited context, there’s always a risk it may issue commands with unintended side effects.
- **Limited Error Handling**: The system relies on AI-based corrections, which may not always correctly interpret error messages.
- **Not Production-Ready**: As an experimental tool, revshell should be used with caution, ideally in sandboxed or non-critical environments.

---

### Conclusion

The [revshell project on GitHub](https://github.com/tmendoza/revshell) is a novel and experimental tool that explores agentic behavior without the need for heavyweight libraries. By flipping the interaction model around and enabling the AI to take charge of issuing commands, it introduces a lightweight approach to building adaptive, autonomous systems. 

While this project shows that agentic behavior can be achieved with a minimal setup, it also highlights the risks and challenges of such an approach. As AI systems continue to evolve, projects like revshell offer a glimpse into what’s possible when we rethink the way we interact with intelligent systems.