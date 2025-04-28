from dataclasses import dataclass

class Message:  # ultra‑light A2A stand‑in
    def __init__(self, sender, intent, payload=None):
        self.sender, self.intent, self.payload = sender, intent, payload or {}

# ── Agents ───────────────────────────────────────────────────────────
@dataclass
class DataPrepAgent:
    name: str = "DataPrepAgent"

    def process(self, batch_path):
        print("[DataPrep] validating & encoding", batch_path)
        # …stub…
        return {"encoded_path": batch_path.replace("raw", "enc")}

@dataclass
class AutoMLAgent:
    name: str = "AutoMLAgent"

    def train(self, dataset):
        print("[AutoML] running Autopilot on", dataset)
        # pretend we call DataRobot here
        return {"model_id": "mdl_123", "bias": 0.07}

@dataclass
class ComplianceAgent:
    name: str = "ComplianceAgent"
    bias_threshold: float = 0.05

    def review(self, metrics):
        print("[Compliance] bias =", metrics["bias"])
        if metrics["bias"] > self.bias_threshold:
            return Message(self.name, "RETRAIN", {"reason": "bias"})
        return Message(self.name, "APPROVE")

# ── Orchestration (mimic A2A runtime) ───────────────────────────────
prep   = DataPrepAgent()
automl = AutoMLAgent()
comp   = ComplianceAgent()

batch = prep.process("data/raw/2025‑04‑25.csv")
metrics = automl.train(batch)
reply = comp.review(metrics)

if reply.intent == "RETRAIN":
    print("→ Compliance requested retrain… looping!")
    metrics = automl.train(batch)  # second pass (could adjust params)
print("→ Workflow complete. Model ID:", metrics["model_id"])