# agents/automl_agent/agent.py
import time
import os
import datarobot as dr
# Ensure your DATAROBOT_API_TOKEN and DATAROBOT_ENDPOINT env vars are set

# Assuming a2a_utils is available
try:
    from a2a_utils import TaskStatus, send_a2a_message
except ImportError:
     # Fallback
     class TaskStatus:
        SUBMITTED = "submitted"
        WORKING = "working"
        INPUT_REQUIRED = "input-required"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELED = "canceled"
     TaskStatus = type('TaskStatus', (object,), {k:k.lower() for k in ['SUBMITTED', 'WORKING', 'INPUT_REQUIRED', 'COMPLETED', 'FAILED', 'CANCELED']})()

     # Dummy send_a2a_message if a2a_utils not fully available
    # sender_id -> id of previous agent (e.g. dataprepagent) 
    # receiver_id -> id of the current agent (e.g. auto_ml_agent)
    def send_a2a_message(sender_id, receiver_id, verb, payload, task_id=None):
         print(f"\n[SIM A2A - Dummy] {sender_id} -> {receiver_id} ({verb}) | Task: {task_id or 'New'}")
         print(f"  Payload: {json.dumps(payload, indent=2)}")
         # In a real setup, this would route to the receiver's agent.py
         # For this dummy, it just prints.
         pass


# Simple in-memory task status tracking
task_states = {}
task_results = {} # To store final artifacts

# Agent ID (should match agent.json)
AGENT_ID = "automl.v1"
COMPLIANCE_AGENT_ID = "compliance.v1" # Assuming this ID for A2A call

def process_task(task_id, verb, payload):
    """Simulates processing an A2A task by interacting with DataRobot."""
    print(f"  AutoMLAgent: Received verb '{verb}' for task {task_id}")

    if verb == "CALL":
        if task_id not in task_states or task_states[task_id] == TaskStatus.SUBMITTED:
            task_states[task_id] = TaskStatus.WORKING
            print(f"  AutoMLAgent: Starting AutoML run for task {task_id}...")
            # Simulate receiving payload
            message_parts = payload.get("parts", [])
            processed_data_path = None
            target_feature = None
            for part in message_parts:
                if part.get("type") == "data":
                    content = part.get("content", {})
                    processed_data_path = content.get("processed_data_path")
                    target_feature = content.get("target_feature")
                    if processed_data_path and target_feature:
                         break

            if not processed_data_path or not os.path.exists(processed_data_path) or not target_feature:
                 task_states[task_id] = TaskStatus.FAILED
                 message = "Error: Missing processed_data_path or target_feature in payload, or file not found."
                 print(f"  AutoMLAgent: {message}")
                 return task_states[task_id], message, {}

            try:
                # --- SIMULATING MCP CALLS TO DATAROBOT API ---
                print(f"  AutoMLAgent (via MCP): Calling DataRobot API to upload dataset from {processed_data_path}...")
                # In a real scenario, this would use the DataRobot client
                # upload = dr.Dataset.create(file_path=processed_data_path)
                # print(f"  AutoMLAgent (via MCP): Dataset uploaded, ID: {upload.id}. Creating project...")
                # project = dr.Project.create_from_dataset(dataset_id=upload.id, project_name=f"Agent_AutoML_{task_id[:8]}", target=target_feature, wait_for_completion=False) # Use wait_for_completion=False if you want to simulate polling/streaming progress
                # print(f"  AutoMLAgent (via MCP): Project created, ID: {project.id}. Starting Autopilot...")
                # project.wait_for_autopilot() # Blocks until complete. For streaming demo, you'd poll project status.

                # --- Simplified Simulation of DataRobot Interaction ---
                print("  AutoMLAgent (via MCP): ...Simulating dataset upload and project creation...")
                time.sleep(5) # Simulate API calls and initial processing
                simulated_dataset_id = f"sim_ds_{task_id[:8]}"
                simulated_project_id = f"sim_proj_{task_id[:8]}"
                print(f"  AutoMLAgent (via MCP): ...Simulating Autopilot run...")
                time.sleep(15) # Simulate AutoML running time

                # Find a "champion" model (simulated)
                simulated_champion_model_id = f"sim_model_{task_id[:8]}_rank1"
                print(f"  AutoMLAgent (via MCP): DataRobot AutoML completed. Simulated champion model ID: {simulated_champion_model_id}")
                # --- End Simplified Simulation ---


                message = "DataRobot AutoML completed."
                artifacts = {
                    "automl_results": {
                        "type": "data",
                        "content": {
                           "project_id": simulated_project_id,
                           "champion_model_id": simulated_champion_model_id
                        }
                    }
                }
                task_states[task_id] = TaskStatus.COMPLETED
                task_results[task_id] = artifacts # Store results

                print(f"  AutoMLAgent: Task {task_id} completed successfully.")

                # --- SIMULATING A2A CALL TO NEXT AGENT ---
                # After completing its task, the AutoMLAgent initiates the next step
                # by sending an A2A message to the ComplianceAgent.
                print(f"  AutoMLAgent: Notifying {COMPLIANCE_AGENT_ID} to review the model...")
                compliance_payload = {
                     "parts": [
                         {"type": "text", "content": f"Review model {simulated_champion_model_id} from project {simulated_project_id}."},
                         {"type": "data", "content": {
                             "project_id": simulated_project_id,
                             "model_id": simulated_champion_model_id
                             }}
                     ]
                 }
                # Note: In a real system, send_a2a_message here would not block like in run_workflow.py
                # It would send the message asynchronously. For this simple demo, we'll just print.
                send_a2a_message(AGENT_ID, COMPLIANCE_AGENT_ID, "CALL", compliance_payload)
                # End of simulated A2A call

                return task_states[task_id], message, artifacts

            except dr.errors.ClientError as e:
                 task_states[task_id] = TaskStatus.FAILED
                 message = f"DataRobot API error: {e}"
                 print(f"  AutoMLAgent: {message}")
                 return task_states[task_id], message, {}
            except Exception as e:
                task_states[task_id] = TaskStatus.FAILED
                message = f"AutoML processing failed: {e}"
                print(f"  AutoMLAgent: {message}")
                return task_states[task_id], message, {}

        elif task_states[task_id] == TaskStatus.WORKING:
             return task_states[task_id], "Task already in progress.", {}
        elif task_states[task_id] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
             # Return stored results if task is finished
             return task_states[task_id], "Task already finished.", task_results.get(task_id, {})

    elif verb == "GET_STATUS":
         return task_states.get(task_id, TaskStatus.SUBMITTED), "Current status requested.", task_results.get(task_id, {}) # Return results if available

    else:
        task_states[task_id] = TaskStatus.FAILED
        message = f"Unsupported verb: {verb}"
        print(f"  AutoMLAgent: {message}")
        return task_states[task_id], message, {}