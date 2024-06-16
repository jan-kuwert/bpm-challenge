import numpy as np
import requests

# Define the distributions and probabilities
PATIENT_TYPES = ["A", "B", "EM"]
TYPES_PROBABILITIES = [0.4, 0.4, 0.2]
DIAGNOSE_A = ["A1", "A2", "A3", "A4"]
DIAGNOSE_B = ["B1", "B2", "B3", "B4"]
PROBABILITIES_A = [0.5, 0.25, 0.125, 0.125]
PROBABILITIES_B = [0.5, 0.25, 0.125, 0.125]

INSTANCE_TYPES = ["fork_running", "fork_ready", "wait_running", "wait_ready"]


# Function to simulate the arrival of a single patient
def generate_patient():
    patient_type = np.random.choice(PATIENT_TYPES, p=TYPES_PROBABILITIES)

    if patient_type == "A":
        diagnosis = np.random.choice(DIAGNOSE_A, p=PROBABILITIES_A)

    elif patient_type == "B":
        diagnosis = np.random.choice(DIAGNOSE_B, p=PROBABILITIES_B)

    elif patient_type == "EM":
        # emergency patients need to divide probs by 2 since they can have either diagnosis
        diagnosis = np.random.choice(
            DIAGNOSE_A + DIAGNOSE_B,
            p=[a / 2 for a in PROBABILITIES_A] + [b / 2 for b in PROBABILITIES_B],
        )
    return {
        "type": patient_type,
        "diagnosis": diagnosis,
    }


# Function to simulate multiple patients
def simulate_patients(num_patients):
    patients = []
    for _ in range(num_patients):
        patient = generate_patient()
        create_instance(patient)
        patients.append(patient)
    return patients


# creates new process instance
def create_instance(patientData, behavior="fork_running"):
    try:
        if not patientData["type"]:
            raise ValueError("Patient type invalid: " + patientData["type"])
        if not patientData["diagnosis"]:
            raise ValueError("Patient diagnosis invalid: " + patientData["diagnosis"])
        if behavior not in INSTANCE_TYPES:
            raise ValueError("Instance Type invalid:" + behavior)
        url = "https://cpee.org/flow/start/url/"
        xml_url = "https://cpee.org/hub/server/Teaching.dir/Prak.dir/Challengers.dir/Jan_Kuwert.dir/hospital_test.xml"
        data = {
            "behavior": behavior,
            "url": xml_url,
            "init": '{"type": "'
            + patientData["type"]
            + '", "diagnosis": "'
            + patientData["diagnosis"]
            + '"}',
        }

        response = requests.post(url, data=data)
        # instanceData = {}
        # instanceData["instance"] = response.forms.get("CPEE-INSTANCE")
        # instanceData["url"] = response.fomrms.get("CPEE-INSTANCE-URL")
        # instanceData["id"] = response.forms.get("CPEE-INSTANCE-UUID")
        # instanceData["beahvior"] = response.forms.get("CPEE-BEHAVIOR")
        # print("Instance Data:", instanceData)
        print("Response:", response)
        return response
    except Exception as e:
        print("create_instance_error: ", e)
        return e


num_patients_to_simulate = 10
simulated_patients = simulate_patients(num_patients_to_simulate)

for i, patient in enumerate(simulated_patients):
    print(f"Patient {i+1}: {patient}")
