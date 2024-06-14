import os
from atomic_operator import AtomicOperator

def run_atomic_tests(techniques, atomics_path):
    """
    Run atomic tests for given techniques.

    :param techniques: List of technique IDs (e.g., ['T1040', 'T1059'])
    :param atomics_path: Path to the atomic red team directory
    :return: None
    """
    operator = AtomicOperator()
    results = operator.run(techniques=techniques, atomics_path=atomics_path)
    print(results)

def atomic_operator():
    try:
        # Ensure ATOMICS_PATH is set in the environment
        atomics_path = os.getenv('ATOMICS_PATH')
        if not atomics_path:
            raise EnvironmentError("ATOMICS_PATH environment variable is not set. Please set it and rerun the script.")
        
        # Input for techniques
        techniques_input = input("Enter the technique IDs separated by commas (e.g., T1040,T1059): ")
        techniques = [tech.strip() for tech in techniques_input.split(',')]
        
        # Running the tests
        run_atomic_tests(techniques, atomics_path)
        
    except Exception as e:
        print(f"An error occurred: {e}")
