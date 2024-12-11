# **LLM Shell Manual**

## **Introduction**
LLM Shell (llmshell) is an interactive shell for evaluating Lisp-like expressions. It combines traditional Lisp-like constructs with modern capabilities such as interacting with LLMs, managing variables, working with contexts, and executing system commands.

---

## **Command Reference**

### **1. Variable Management**

- **`(var.set "name" value)`**  
  Set a variable to a specific value.  
  **Example:** `(var.set "greeting" "Hello, World!")`

- **`(var.get "name")`**  
  Retrieve the value of a variable.  
  **Example:** `(var.get "greeting")`

- **`(var.list)`**  
  List all variables.  
  **Example:**  
  ```plaintext
  {"greeting": "Hello, World!"}
  ```

- **`(var.delete "name")`**  
  Delete a variable.  
  **Example:** `(var.delete "greeting")`

---

### **2. Context Management**

- **`(context.append "item")`**  
  Add an item to the shared context.  
  **Example:** `(context.append "This is context data.")`

- **`(context.view)`**  
  View the current context.  
  **Example Output:**  
  ```plaintext
  This is context data.
  ```

- **`(context.clear)`**  
  Clear the context.  
  **Example:** `(context.clear)`

- **`(context.slice start end)`**  
  Retrieve a slice of the context.  
  **Example:** `(context.slice 0 1)`

- **`(context.save "filepath")`**  
  Save the current context to a file.  
  **Example:** `(context.save "context.json")`

- **`(context.load "filepath")`**  
  Load the context from a file.  
  **Example:** `(context.load "context.json")`

---

### **3. String Manipulation**

- **`(concat "string1" "string2" ...)`**  
  Concatenate multiple strings.  
  **Example:** `(concat "Hello, " "World!")`

- **`(uppercase "string")`**  
  Convert a string to uppercase.  
  **Example:** `(uppercase "hello")`

- **`(lowercase "string")`**  
  Convert a string to lowercase.  
  **Example:** `(lowercase "HELLO")`

- **`(split "string" "delimiter")`**  
  Split a string by a delimiter.  
  **Example:** `(split "a,b,c" ",")`

---

### **4. Arithmetic Operations**

- **`(add num1 num2 ...)`**  
  Add numbers.  
  **Example:** `(add 1 2 3)` → `6`

- **`(sub num1 num2 ...)`**  
  Subtract numbers.  
  **Example:** `(sub 10 2 3)` → `5`

- **`(mul num1 num2 ...)`**  
  Multiply numbers.  
  **Example:** `(mul 2 3 4)` → `24`

- **`(div num1 num2 ...)`**  
  Divide numbers.  
  **Example:** `(div 12 2 2)` → `3`

---

### **5. Logical Operations**

- **`(and expr1 expr2 ...)`**  
  Logical AND operation.  
  **Example:** `(and true false)` → `false`

- **`(or expr1 expr2 ...)`**  
  Logical OR operation.  
  **Example:** `(or true false)` → `true`

- **`(not expr)`**  
  Logical NOT operation.  
  **Example:** `(not true)` → `false`

---

### **6. Control Structures**

- **`(if condition true_branch false_branch)`**  
  Conditional evaluation.  
  **Example:** `(if true "Yes" "No")` → `"Yes"`

- **`(repeat count expression)`**  
  Repeat an expression multiple times.  
  **Example:** `(repeat 3 (concat "Hello " "World"))`

- **`(for variable list body)`**  
  Iterate over a list and evaluate the body for each element.  
  **Example:** `(for "x" [1 2 3] (add x 1))` → `[2, 3, 4]`

---

### **7. LLM Interaction**

- **`(llm.prompt "prompt_text")`**  
  Send a prompt to the LLM and return the response.  
  **Example:** `(llm.prompt "What is AI?")`

- **`(llm.config "key" value ...)`**  
  Configure the LLM client.  
  **Example:** `(llm.config "temperature" 0.5 "max_tokens" 150)`

- **`(llm.with-context "prompt_text")`**  
  Send a prompt with the current context to the LLM.  
  **Example:** `(llm.with-context "Provide feedback on this context.")`

- **`(llm.cost)`**  
  Display the total tokens used and estimated cost.  
  **Example Output:**  
  ```plaintext
  Total tokens used: 1000, Cost: $0.02
  ```

---

### **8. System Commands**

- **`(system.info)`**  
  Get system information.  
  **Example Output:**  
  ```plaintext
  OS: Darwin, Architecture: x86_64, CPU Count: 8
  ```

- **`(system.cwd)`**  
  Get the current working directory.  
  **Example:** `(system.cwd)`

- **`(system.ls)`**  
  List files in the current directory.  
  **Example:** `(system.ls)`

- **`(system.disk)`**  
  Display disk usage information.  
  **Example Output:**  
  ```plaintext
  Total: 500GB, Used: 300GB, Free: 200GB
  ```

- **`(system.time)`**  
  Get the current system time.  
  **Example:** `(system.time)`

- **`(system.exec "command")`**  
  Execute a shell command and return the output.  
  **Example:** `(system.exec "ls -la")`

---

### **9. Session Management**

- **`(session.save "filepath")`**  
  Save the current session (variables, context, templates) to a file.  
  **Example:** `(session.save "session.json")`

- **`(session.load "filepath")`**  
  Load a session from a file.  
  **Example:** `(session.load "session.json")`

---

### **10. Help**

- **`(help)`**  
  Display help for all commands.  
  **Example:** `(help)`

- **`(help "command_name")`**  
  Display help for a specific command.  
  **Example:** `(help "var.set")`

---

## **Example Workflow**

```lisp
; Set some variables
(var.set "name" "Alice")
(var.set "age" 30)

; Add data to the context
(context.append (concat "Name: " (var.get "name")))
(context.append (concat "Age: " (var.get "age")))

; Get system information
(context.append (system.info))

; Use the LLM with context
(llm.with-context "Summarize the user's profile and system information.")

; Save the session
(session.save "profile_session.json")
```

---

## **Version**
LLM Shell 1.0.0

---

## **License**
MIT License
