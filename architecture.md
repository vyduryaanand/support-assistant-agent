# Architecture Diagram – Support Assistant Agent

```mermaid
flowchart TD

A[User Interface - Streamlit Support Chat] --> B[User Inputs Support Query]

B --> C[Query Processing Layer]

C --> D[OpenRouter GPT API]
D --> E[AI Response Generation]

E --> F{Confidence Check / Complexity Check}

F -->|Simple| G[Return FAQ Resolution to User]
F -->|Complex| H[Generate Structured Escalation Summary]

H --> I[Log / Escalate to Human AI Support Team]

```

---

### Explanation

* User asks a support question
* AI processes query and generates answer
* If the answer is confident → agent replies
* If query is unclear/complex → escalates
* Optional: Escalation can be sent to email / CRM if implemented
