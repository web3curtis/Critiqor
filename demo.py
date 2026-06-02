from critiqor import Critiqor

class MyAgent:
    def run(self, prompt: str) -> str:
        if "Hallucination:" in prompt:
            return (
                "Hallucination: 70\n"
                "Reasoning: 72\n"
                "Tool Reliability: 68\n"
                "Consistency: 74\n"
                "Task Completion: 66\n"
                "Confidence Calibration: 62\n"
                "Execution Efficiency: 70\n"
                "Evidence Level: response_only\n"
                "Summary: Partially useful, but too thin to be fully trusted.\n"
                "Findings:\n"
                "- The answer does not include enough detail to confirm task completion."
            )
        return "This is my agent's answer."

base_agent = MyAgent()
agent = Critiqor(base_agent)

result = agent.run("Explain vector databases in one paragraph.")

print(result.answer)
print(result.confidence)
print(result.trust_level)
print(result.critique)
