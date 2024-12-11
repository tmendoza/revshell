import json
import re
import openai
import logging
import platform
import os
import shutil
import subprocess
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
import random
import time

# Help Text
HELP_TEXT = {
    "var.set": {"description": "Set a variable with the given name and value.", "usage": '(var.set "name" "value")'},
    "var.get": {"description": "Retrieve the value of a variable by its name.", "usage": '(var.get "name")'},
    "var.list": {"description": "List all defined variables as a dictionary.", "usage": '(var.list)'},
    "var.delete": {"description": "Delete a variable by its name.", "usage": '(var.delete "name")'},
    "context.append": {"description": "Append a value to the shared context.", "usage": '(context.append "value")'},
    "context.view": {"description": "View all values currently in the context.", "usage": '(context.view)'},
    "context.clear": {"description": "Clear all values from the context.", "usage": '(context.clear)'},
    "context.slice": {"description": "Retrieve a slice of the context using start and end indices.", "usage": '(context.slice start end)'},
    "context.save": {"description": "Save the current context to a file.", "usage": '(context.save "filepath")'},
    "context.load": {"description": "Load a context from a specified file.", "usage": '(context.load "filepath")'},
    "template.create": {"description": "Create a named template with placeholders.", "usage": '(template.create "name" "template_content")'},
    "template.use": {"description": "Render a template by its name using current variables.", "usage": '(template.use "name")'},
    "template.list": {"description": "List all defined templates.", "usage": '(template.list)'},
    "template.delete": {"description": "Delete a template by its name.", "usage": '(template.delete "name")'},
    "llm.prompt": {"description": "Send a prompt to the OpenAI API and retrieve the response.", "usage": '(llm.prompt "prompt_text")'},
    "llm.config": {"description": "Configure the LLM client with key-value pairs.", "usage": '(llm.config "key" "value" ...)'},
    "llm.with-context": {"description": "Send a prompt to the OpenAI API with the current context included.", "usage": '(llm.with-context "prompt_text")'},
    "llm.cost": {"description": "Display the total tokens used and estimated API cost.", "usage": '(llm.cost)'},
    "system.info": {"description": "Display general system information (OS, architecture, CPU count).", "usage": '(system.info)'},
    "system.cwd": {"description": "Display the current working directory.", "usage": '(system.cwd)'},
    "system.ls": {"description": "List files and directories in the current working directory.", "usage": '(system.ls)'},
    "system.disk": {"description": "Display disk usage information (total, used, free).", "usage": '(system.disk)'},
    "system.env": {"description": "Display all environment variables or a specific one.", "usage": '(system.env) or (system.env "VAR_NAME")'},
    "system.time": {"description": "Display the current system time.", "usage": '(system.time)'},
    "system.exec": {"description": "Execute a shell command and capture its output.", "usage": '(system.exec "command")'},
    "if": {"description": "Evaluate a condition and execute the true or false branch.", "usage": '(if condition true_branch false_branch)'},
    "for": {"description": "Iterate over an iterable, assigning each item to a variable, and execute a body for each iteration.", "usage": '(for "variable" ["item1" "item2"] (body))'},
    "debug.start": {"description": "Enable debug mode to display detailed logs.", "usage": '(debug.start)'},
    "debug.stop": {"description": "Disable debug mode.", "usage": '(debug.stop)'},
    "session.save": {"description": "Save the current session (variables, context, templates) to a file.", "usage": '(session.save "filepath")'},
    "session.load": {"description": "Load a session from a specified file.", "usage": '(session.load "filepath")'},
    "system.load-script": {"description": "Load and execute an LLM-Shell script from a file.","usage": '(system.load-script "filepath")'},
    "help": {"description": "Display help for all commands or a specific command.", "usage": '(help) or (help "command_name")'},

    "add": {
        "description": "Add numbers together.",
        "usage": '(add 1 2 3)'
    },
    "sub": {
        "description": "Subtract numbers.",
        "usage": '(sub 10 3 2)'
    },
    "mul": {
        "description": "Multiply numbers.",
        "usage": '(mul 2 3 4)'
    },
    "div": {
        "description": "Divide numbers.",
        "usage": '(div 20 5 2)'
    },
    "concat": {
        "description": "Concatenate strings.",
        "usage": '(concat "Hello, " "World!")'
    },
    "uppercase": {
        "description": "Convert a string to uppercase.",
        "usage": '(uppercase "hello")'
    },
    "lowercase": {
        "description": "Convert a string to lowercase.",
        "usage": '(lowercase "HELLO")'
    },
    "split": {
        "description": "Split a string by a delimiter.",
        "usage": '(split "a,b,c" ",")'
    },
    "and": {
        "description": "Logical AND operation.",
        "usage": '(and true false true)'
    },
    "or": {
        "description": "Logical OR operation.",
        "usage": '(or false false true)'
    },
    "not": {
        "description": "Logical NOT operation.",
        "usage": '(not false)'
    },
    "type": {
        "description": "Get the type of a value.",
        "usage": '(type 123)'
    },
    "is-number": {
        "description": "Check if a value is a number.",
        "usage": '(is-number 123)'
    },
    "is-string": {
        "description": "Check if a value is a string.",
        "usage": '(is-string "hello")'
    },
    "repeat": {
        "description": "Repeat a command multiple times.",
        "usage": '(repeat 3 (concat "hello" " "))'
    },
    "env.get": {
        "description": "Get the value of an environment variable.",
        "usage": '(env.get "HOME")'
    },
    "env.set": {
        "description": "Set the value of an environment variable.",
        "usage": '(env.set "MY_VAR" "value")'
    },
    "env.list": {
        "description": "List all environment variables.",
        "usage": '(env.list)'
    },
    "random": {
        "description": "Generate a random number between two values.",
        "usage": '(random 1 10)'
    },
    "time": {
        "description": "Measure the time taken to execute a command.",
        "usage": '(time (add 1 2 3))'
    },
    "dotimes": {
        "description": "Repeat a body of code a fixed number of times, assigning the counter variable to the current iteration index.",
        "usage": '(dotimes "counter" count body)'
    },
    "print": {
        "description": "Print one or more evaluated arguments to the console.",
        "usage": '(print arg1 arg2 ...)'
    }
}


logging.basicConfig(
    filename="lisp_shell_debug.log", 
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log_debug(self, message):
    """Logs debug messages when debug mode is enabled."""
    if self.debug_mode:
        logging.debug(message)

# Tokenizer
def tokenize(input_string):
    """Converts raw input into tokens, including handling lists."""
    return re.findall(r'"[^"]*"|\[.*?\]|\(|\)|[^\s()]+', input_string)


def parse(tokens):
    """Parses tokens into an Abstract Syntax Tree (AST)."""
    if not tokens:
        raise SyntaxError("Unexpected EOF while reading")
    token = tokens.pop(0)
    if token == '(':
        ast = []
        while tokens[0] != ')':
            ast.append(parse(tokens))
        tokens.pop(0)  # Remove closing ')'
        return ast
    elif token == ')':
        raise SyntaxError("Unexpected )")
    else:
        return atom(token)

def atom(token):
    """Converts a token into an atom (string, number, boolean, or None)."""
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]  # Remove surrounding double quotes
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            if token == "true":
                return True
            elif token == "false":
                return False
            return token  # Return as a string


class LispShell:
    def __init__(self):
        self.variables = {}
        self.context = []
        self.templates = {}
        self.history = []
        self.llm_client = LLMClient()
        self.llm_config = {"model": "gpt-4", "temperature": 0.7}
        self.debug_mode = False
        self.total_tokens_used = 0
        self.cost_per_token = 0.02 / 1000

    def log_debug(self, message):
        """Logs debug messages when debug mode is enabled."""
        if self.debug_mode:
            logging.debug(message)

    def eval(self, expr):
        """Main evaluation entry point."""
        try:
            self.log_debug(f"Evaluating expression: {expr}")

            if isinstance(expr, str):
                return self.variables.get(expr, expr)
            if not isinstance(expr, list):
                return expr

            command, *args = expr
            args = [self.eval(arg) for arg in args]

            # Dispatch to specific command handler
            handlers = {
                "var.set": self.handle_var_set,
                "var.get": self.handle_var_get,
                "var.list": self.handle_var_list,
                "var.delete": self.handle_var_delete,
                "add": self.handle_add,
                "sub": self.handle_sub,
                "mul": self.handle_mul,
                "div": self.handle_div,
                "concat": self.handle_concat,
                "uppercase": self.handle_uppercase,
                "lowercase": self.handle_lowercase,
                "split": self.handle_split,
                "and": self.handle_and,
                "or": self.handle_or,
                "not": self.handle_not,
                "type": self.handle_type,
                "is-number": self.handle_is_number,
                "is-string": self.handle_is_string,
                "repeat": self.handle_repeat,
                "env.get": self.handle_env_get,
                "env.set": self.handle_env_set,
                "env.list": self.handle_env_list,
                "random": self.handle_random,
                "time": self.handle_time,
                "context.append": self.handle_context_append,
                "context.view": self.handle_context_view,
                "context.clear": self.handle_context_clear,
                "context.slice": self.handle_context_slice,
                "context.save": self.handle_context_save,
                "context.load": self.handle_context_load,
                "template.create": self.handle_template_create,
                "template.use": self.handle_template_use,
                "template.list": self.handle_template_list,
                "template.delete": self.handle_template_delete,
                "llm.prompt": self.handle_llm_prompt,
                "llm.config": self.handle_llm_config,
                "llm.with-context": self.handle_llm_with_context,
                "llm.cost": self.handle_llm_cost,
                "system.info": self.handle_system_info,
                "system.cwd": self.handle_system_cwd,
                "system.ls": self.handle_system_ls,
                "system.disk": self.handle_system_disk,
                "system.env": self.handle_system_env,
                "system.time": self.handle_system_time,
                "system.exec": self.handle_system_exec,
                "if": self.handle_if,
                "for": self.handle_for,
                "debug.start": self.handle_debug_start,
                "debug.stop": self.handle_debug_stop,
                "session.save": self.handle_session_save,
                "session.load": self.handle_session_load,
                "system.load-script": self.run_script,
                "system.env": self.handle_system_env,
                "session.save": self.handle_session_save,
                "session.load": self.handle_session_load,
                "help": self.handle_help,
                "print": self.handle_print,
                "dotimes": self.handle_dotimes,
            }

            if command in handlers:
                return handlers[command](args)
            else:
                raise ValueError(f"Unknown command: {command}")
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_help(self, args):
        """Provide help information for all commands or a specific command."""
        if len(args) == 0:
            # General help: List all commands with descriptions
            return "\n".join([f"{cmd}: {info['description']}" for cmd, info in HELP_TEXT.items()])
        elif len(args) == 1:
            # Specific help: Show details for a single command
            command = args[0]
            if command in HELP_TEXT:
                info = HELP_TEXT[command]
                return f"{command}:\n  Description: {info['description']}\n  Usage: {info['usage']}"
            else:
                return f"Unknown command: {command}"
        else:
            raise ValueError("help expects zero or one argument.")

    # ---------------------------
    # Variable Management
    # ---------------------------
    def handle_var_set(self, args):
        """Set a variable."""
        self.variables[args[0]] = args[1]
        self.log_debug(f"Set variable {args[0]} to {self.variables[args[0]]}")
        return f"{args[0]} set to {args[1]}"

    def handle_var_get(self, args):
        """Get a variable's value."""
        return self.variables.get(args[0], "Undefined")

    def handle_var_list(self, args):
        """List all variables."""
        return self.variables

    def handle_var_delete(self, args):
        """Delete a variable."""
        self.variables.pop(args[0], None)

    # ---------------------------
    # Arithmetic Operations
    # ---------------------------
    def handle_add(self, args):
        """Add all arguments."""
        return sum(args)

    def handle_sub(self, args):
        """Subtract all subsequent arguments from the first."""
        return args[0] - sum(args[1:])

    def handle_mul(self, args):
        """Multiply all arguments."""
        result = 1
        for arg in args:
            result *= arg
        return result

    def handle_div(self, args):
        """Divide the first argument by subsequent arguments."""
        result = args[0]
        for divisor in args[1:]:
            if divisor == 0:
                raise ValueError("Division by zero is not allowed.")
            result /= divisor
        return result

    # ---------------------------
    # String Manipulation
    # ---------------------------
    def handle_concat(self, args):
        """Concatenate arguments into a single string."""
        return "".join(map(str, args))

    def handle_uppercase(self, args):
        """Convert a string to uppercase."""
        return args[0].upper()

    def handle_lowercase(self, args):
        """Convert a string to lowercase."""
        return args[0].lower()

    def handle_split(self, args):
        """Split a string by a delimiter."""
        return args[0].split(args[1])

    # ---------------------------
    # Logical Operations
    # ---------------------------
    def handle_and(self, args):
        """Logical AND operation."""
        return all(args)

    def handle_or(self, args):
        """Logical OR operation."""
        return any(args)

    def handle_not(self, args):
        """Logical NOT operation."""
        return not args[0]

    # ---------------------------
    # Type Checking
    # ---------------------------
    def handle_type(self, args):
        """Get the type of a value."""
        return type(args[0]).__name__

    def handle_is_number(self, args):
        """Check if a value is a number."""
        return isinstance(args[0], (int, float))

    def handle_is_string(self, args):
        """Check if a value is a string."""
        return isinstance(args[0], str)

    # ---------------------------
    # Repetition and Loops
    # ---------------------------
    def handle_repeat(self, args):
        """Repeat an expression a number of times."""
        count = args[0]
        body = args[1]
        results = []
        for _ in range(count):
            results.append(self.eval(body))
        return results

    def handle_for(self, args):
        """Iterate over a list and evaluate an expression for each element."""
        results = []
        for item in args[1]:
            self.variables[args[0]] = item
            results.append(self.eval(args[2]))
        return results

    def handle_if(self, args):
        """Evaluate a condition and return the result of the true or false branch."""
        condition, true_branch, false_branch = args
        if condition:
            return self.eval(true_branch)
        else:
            return self.eval(false_branch)

    # ---------------------------
    # Environment Interaction
    # ---------------------------
    def handle_env_get(self, args):
        """Get an environment variable."""
        return os.getenv(args[0], "Undefined")

    def handle_env_set(self, args):
        """Set an environment variable."""
        os.environ[args[0]] = args[1]
        return f"{args[0]} set to {args[1]}"

    def handle_env_list(self, args):
        """List all environment variables."""
        return "\n".join([f"{k}={v}" for k, v in os.environ.items()])

    # ---------------------------
    # Random Number Generation
    # ---------------------------
    def handle_random(self, args):
        """Generate a random integer between two bounds."""
        return random.randint(args[0], args[1])

    # ---------------------------
    # Timing Commands
    # ---------------------------
    def handle_time(self, args):
        """Time the evaluation of an expression."""
        start_time = time.time()
        result = self.eval(args[0])
        elapsed_time = time.time() - start_time
        return f"Result: {result}, Time taken: {elapsed_time:.4f} seconds"

    # ---------------------------
    # Context Management
    # ---------------------------
    def handle_context_append(self, args):
        """Append a string to the context."""
        entry = args[0]
        self.context.append(str(entry))
        self.log_debug(f"Appended to context: {entry}")

    def handle_context_view(self, args):
        """View the current context."""
        return "\n".join(self.context)

    def handle_context_clear(self, args):
        """Clear the context."""
        self.context.clear()

    def handle_context_slice(self, args):
        """Get a slice of the context."""
        return self.context[args[0]:args[1]]

    def handle_context_save(self, args):
        """Save the context to a file."""
        with open(args[0], "w") as f:
            json.dump(self.context, f)

    def handle_context_load(self, args):
        """Load the context from a file."""
        with open(args[0], "r") as f:
            self.context = json.load(f)

    # ---------------------------
    # Template Management
    # ---------------------------
    def handle_template_create(self, args):
        """Create a template."""
        self.templates[args[0]] = args[1]

    def handle_template_use(self, args):
        """Render a template with variables."""
        template = self.templates.get(args[0], "")
        return template.format(**self.variables)

    def handle_template_list(self, args):
        """List all templates."""
        return self.templates

    def handle_template_delete(self, args):
        """Delete a template."""
        self.templates.pop(args[0], None)

    # ---------------------------
    # LLM Interaction
    # ---------------------------
    def handle_llm_prompt(self, args):
        """Send a prompt to the LLM."""
        result, tokens = self.llm_client.prompt(args[0])
        self.total_tokens_used += tokens
        return result

    def handle_llm_config(self, args):
        """Update the LLM configuration."""
        for i in range(0, len(args), 2):
            self.llm_config[args[i]] = args[i + 1]
        self.llm_client.set_config(**self.llm_config)

    def handle_llm_with_context(self, args):
        """Send a prompt to the LLM with the current context."""
        prompt = "\n".join(self.context) + "\n" + args[0]
        result, tokens = self.llm_client.prompt(prompt)
        self.total_tokens_used += tokens
        return result

    def handle_llm_cost(self, args):
        """Calculate the total cost of tokens used."""
        total_cost = self.total_tokens_used * self.cost_per_token
        return f"Total tokens used: {self.total_tokens_used}, Cost: ${total_cost:.4f}"

    # ---------------------------
    # System Commands
    # ---------------------------
    def handle_system_info(self, args):
        """Get system information."""
        return f"OS: {platform.system()}, Architecture: {platform.architecture()[0]}, CPU Count: {os.cpu_count()}"

    def handle_system_cwd(self, args):
        """Get the current working directory."""
        return os.getcwd()

    def handle_system_ls(self, args):
        """List files in the current directory."""
        return "\n".join(os.listdir(os.getcwd()))

    def handle_system_disk(self, args):
        """Get disk usage information."""
        total, used, free = shutil.disk_usage("/")
        return f"Total: {total // (1024**3)}GB, Used: {used // (1024**3)}GB, Free: {free // (1024**3)}GB"

    def handle_system_time(self, args):
        """Get the current system time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def handle_system_exec(self, args):
        """Execute a shell command and return the output."""
        result = subprocess.run(args[0], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Error: {result.stderr.strip()}"

    # ---------------------------
    # Debugging
    # ---------------------------
    def handle_debug_start(self, args):
        """Enable debug mode."""
        self.debug_mode = True
        print("Debug mode enabled.")

    def handle_debug_stop(self, args):
        """Disable debug mode."""
        self.debug_mode = False
        print("Debug mode disabled.")

    def handle_system_env(self, args):
        """List all environment variables or get a specific one."""
        if len(args) == 0:
            # List all environment variables
            return "\n".join([f"{key}={value}" for key, value in os.environ.items()])
        elif len(args) == 1:
            # Get a specific environment variable
            return os.environ.get(args[0], "Variable not found")
        else:
            raise ValueError("Invalid usage of system.env. Use (system.env) or (system.env 'VARIABLE_NAME').")

    def handle_session_save(self, args):
        """Save the current session (variables, context, templates) to a file."""
        if len(args) != 1:
            raise ValueError("session.save expects a single file path as an argument.")
        
        session_data = {
            "variables": self.variables,
            "context": self.context,
            "templates": self.templates,
        }
        with open(args[0], "w") as f:
            json.dump(session_data, f)
        self.log_debug(f"Session saved to {args[0]}")
        return f"Session saved to {args[0]}"

    def handle_session_load(self, args):
        """Load a session from a file."""
        if len(args) != 1:
            raise ValueError("session.load expects a single file path as an argument.")
        
        with open(args[0], "r") as f:
            session_data = json.load(f)
            self.variables = session_data.get("variables", {})
            self.context = session_data.get("context", [])
            self.templates = session_data.get("templates", {})
        self.log_debug(f"Session loaded from {args[0]}")
        return f"Session loaded from {args[0]}"

    def handle_print(self, args):
        """Print the evaluated arguments to the console."""
        evaluated_args = [self.eval(arg) for arg in args]
        output = " ".join(map(str, evaluated_args))
        print(output)  # Print to the console
        return output  # Return the printed output for consistency

    def handle_dotimes(self, args):
        """
        Execute a body of code a fixed number of times.
        Args:
            args[0]: Counter variable name (string)
            args[1]: Iteration count (integer)
            args[2]: Body expression (list)
        """
        if len(args) != 3:
            raise ValueError("dotimes requires exactly 3 arguments: counter, count, and body.")
        
        counter_name = args[0]
        iteration_count = self.eval(args[1])
        body = args[2]

        if not isinstance(counter_name, str):
            raise ValueError("First argument to dotimes must be a variable name.")
        if not isinstance(iteration_count, int):
            raise ValueError("Second argument to dotimes must evaluate to an integer.")

        results = []
        for i in range(iteration_count):
            self.variables[counter_name] = i  # Set the counter variable in the shell's variables
            result = self.eval(body)         # Evaluate the body expression
            results.append(result)

        # Clean up the counter variable after the loop
        self.variables.pop(counter_name, None)
        
        return results


    # ---------------------------
    # Script Execution
    # ---------------------------
    def run_script(self, args):
        """Execute an LLM-Shell script."""
        script_path = args[0]
        if not os.path.isfile(script_path):
            raise ValueError(f"Script file '{script_path}' does not exist or is not accessible.")

        results = []
        try:
            with open(script_path, "r") as script_file:
                for line_number, line in enumerate(script_file, start=1):
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith(";"):  # Skip comments
                        continue
                    try:
                        tokens = tokenize(line)
                        parsed = parse(tokens)
                        result = self.eval(parsed)
                        if result is not None:
                            results.append(result)
                    except Exception as e:
                        error_message = f"Error on line {line_number}: {str(e)}"
                        logging.error(error_message)
                        results.append(error_message)
        except Exception as e:
            raise ValueError(f"Failed to execute script: {str(e)}")

        return "\n".join(str(result) for result in results)


class LLMClient:
    def __init__(self):
        # Load the API key from API.txt
        self.api_key = self.load_api_key()
        self.client = openai.OpenAI(api_key=self.api_key)
        self.config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2048,  # Increased token limit
            "top_p": 1.0,        # Full range of token probabilities
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }

    def load_api_key(self):
        """Load the OpenAI API key from a file named 'API.txt'."""
        try:
            with open("API.txt", "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError("API.txt file not found. Please provide an API key.")

    def set_config(self, **kwargs):
        """Update the configuration for API calls."""
        self.config.update(kwargs)

    def prompt(self, text):
        """Send a text prompt to the OpenAI API and return the response."""
        try:
            logging.debug(f"Raw prompt received: {text}")
            if not isinstance(text, str) or len(text.strip()) == 0:
                raise ValueError("Prompt text must be a non-empty string.")

            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "user", "content": text.strip()},
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                top_p=self.config["top_p"],
                frequency_penalty=self.config["frequency_penalty"],
                presence_penalty=self.config["presence_penalty"],
            )

            # Extract message and token usage
            message_content = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens

            logging.debug(f"Received response: {message_content}")
            return message_content, tokens_used
        except openai.OpenAIError as e:
            logging.error(f"OpenAI API Error: {str(e)}")
            return f"Error: {e}", 0
        except ValueError as e:
            logging.error(f"Invalid prompt: {str(e)}")
            return f"Error: {e}", 0

# Main entry point
if __name__ == "__main__":
    import sys

    session = PromptSession(history=InMemoryHistory())
    shell = LispShell()

    if len(sys.argv) > 1:
        # Script execution mode
        script_path = sys.argv[1]
        try:
            output = shell.run_script(script_path)
            if output:
                print(output)
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Interactive mode
        print("Welcome to the LLM Shell. Type 'exit' to leave.")
        while True:
            try:
                user_input = session.prompt("llmshell> ")
                if user_input.lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break
                tokens = tokenize(user_input)
                parsed = parse(tokens)
                result = shell.eval(parsed)
                if result is not None:
                    print(result)
            except Exception as e:
                print(f"Error: {e}")

