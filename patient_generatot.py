import numpy as np

# Define the distributions and probabilities
patient_types = ["A", "B", "EM"]
diagnoses_A = ["A1", "A2", "A3", "A4"]
diagnoses_B = ["B1", "B2", "B3", "B4"]
probabilities_A = [1 / 2, 1 / 4, 1 / 8, 1 / 8]
probabilities_B = [1 / 2, 1 / 4, 1 / 8, 1 / 8]


# Function to simulate the arrival of a single patient
def simulate_patient():
    patient_type = np.random.choice(
        patient_types, p=[1 / 3, 1 / 3, 1 / 3]
    )  # Assuming equal probability for simplicity

    if patient_type == "A":
        diagnosis = np.random.choice(diagnoses_A, p=probabilities_A)
        if diagnosis == "A1":
            operation_time = np.random.normal(4, 0.5)
            nursing_time = None
            complications_prob = 0.01
        elif diagnosis == "A2":
            operation_time = np.random.normal(1, 0.25)
            nursing_time = np.random.normal(8, 2)
            complications_prob = 0.01
        elif diagnosis == "A3":
            operation_time = np.random.normal(2, 0.5)
            nursing_time = np.random.normal(16, 2)
            complications_prob = 0.02
        elif diagnosis == "A4":
            operation_time = np.random.normal(4, 0.5)
            nursing_time = np.random.normal(16, 2)
            complications_prob = 0.02

    elif patient_type == "B":
        diagnosis = np.random.choice(diagnoses_B, p=probabilities_B)
        if diagnosis == "B1":
            operation_time = None
            nursing_time = np.random.normal(8, 2)
            complications_prob = 0.001
        elif diagnosis == "B2":
            operation_time = None
            nursing_time = np.random.normal(16, 2)
            complications_prob = 0.01
        elif diagnosis == "B3":
            operation_time = np.random.normal(4, 0.5)
            nursing_time = np.random.normal(16, 4)
            complications_prob = 0.02
        elif diagnosis == "B4":
            operation_time = np.random.normal(4, 1)
            nursing_time = np.random.normal(16, 4)
            complications_prob = 0.02

    elif patient_type == "EM":
        diagnosis = None
        operation_time = None
        nursing_time = None
        complications_prob = None

    return {
        "patient_type": patient_type,
        "diagnosis": diagnosis,
        "operation_time": operation_time,
        "nursing_time": nursing_time,
        "complications_prob": complications_prob,
    }


# Function to simulate multiple patients
def simulate_patients(num_patients):
    patients = []
    for _ in range(num_patients):
        patient = simulate_patient()
        patients.append(patient)
    return patients


# Example usage
num_patients_to_simulate = 10
simulated_patients = simulate_patients(num_patients_to_simulate)

for i, patient in enumerate(simulated_patients):
    print(f"Patient {i+1}: {patient}")
