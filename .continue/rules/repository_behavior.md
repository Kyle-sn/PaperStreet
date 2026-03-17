# Repository Interaction Rules

These rules define how the agent should explore and interact with the repository.

The goal is to ensure responses are based only on the actual project code.

---

# File Discovery

When asked about files or code:

1. Identify the relevant directory.
2. List the files in that directory.
3. Open and inspect the relevant files.
4. Base responses only on code that exists in the repository.

Never assume file contents without opening the file.

---

# Do Not Hallucinate Files

Never invent:

- files
- modules
- functions
- classes
- directories

If something is not present in the repository, clearly state that it does not exist.

Example:

Correct:
"The repository does not contain a config module."

Incorrect:
"The config module probably handles settings."

---

# Reading Code Before Answering

Before explaining behavior:

- open the relevant file
- read the implementation
- identify dependencies
- confirm how functions are actually used

Do not infer behavior from filenames alone.

---

# When Modifying Code

When suggesting code changes:

- prefer minimal modifications
- avoid rewriting entire files
- preserve the existing architecture
- reuse existing utilities

Do not introduce new modules unless explicitly requested.

---

# Dependency Awareness

Before creating new functionality:

1. Check whether the functionality already exists.
2. Search common utility locations such as:

- `utils/`
- shared helper modules
- existing broker interfaces

Prefer using existing utilities rather than creating new ones.

---

# Handling Missing Information

If the repository does not provide enough information:

- say that the information is not available
- ask the user for clarification

Do not guess how the system works.

---

# Explaining Code

When explaining repository code:

1. Reference the actual file.
2. Reference the relevant function or class.
3. Explain how the code behaves based on the implementation.
