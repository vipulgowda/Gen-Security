import os
import subprocess

def run_terminal_command(command):
  """
  Runs the provided command in the terminal.

  Args:
    command: The command to be executed.
  """
  try:
    # Use subprocess.run for capturing output and error messages (optional)
    # result = subprocess.run(command, capture_output=True, text=True)
    # print(result.stdout)
    # print(result.stderr)

    # Simpler option for just running the command
    subprocess.run(command.split(), check=True)  # Exit script on non-zero exit code
  except subprocess.CalledProcessError as e:
    print(f"Error running command: {e}")

if __name__ == "__main__":
  command = input("Enter the command to run: ")
  run_terminal_command(command)
