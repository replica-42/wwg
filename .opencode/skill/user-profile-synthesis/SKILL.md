---
name: user-profile-synthesis
description: Merges multiple time-period behavior summaries into a unified current user profile. Use when synthesizing a complete user profile from different time periods for personalized emotional companionship and behavior analysis.
---

When synthesizing a unified user profile from multiple time-period summaries, always:

1. **Load and parse the user-provided file**
   - The agent MUST load the specified input file.
   - The file contains a JSON array of summary objects (chronologically ordered from oldest to newest).
   - Each object has the schema:
     ```json
     {
       "time_period": "...",
       "profile": ["..."],
       "preferences": [
         {"name": "...", "type": "...", "duration": "short/medium/long", "reason": "..."}
       ],
       "personality": ["..."],
       "language_style": "...",
       "key_events": ["..."]
     }
     ```
   - The chronological order of the array reflects real time progression.

2. **Interpret each field semantically**
   - `time_period`: the target period analyzed.
   - `profile`: inferred labels (age, occupation, identity tags).
   - `preferences`: list of preference objects with strength and inference reasons.
   - `personality`: inferred emotional/behavior traits.
   - `language_style`: linguistic habits, including tone and punctuation.

 3. **Time-Weighted Fusion Across Periods**
    - Apply exponential decay weighting (λ=0.9/month) to all features, giving higher weight to recent periods.
    - For preferences, require both frequency AND duration evidence: core preferences must appear in ≥3 months with "long" duration tags.
    - Track personality and preference evolution using key_events as contextual anchors.
    - Differentiate stable traits (language style, core values) from volatile traits (temporary interests).

4. **Conflict Resolution**
   - When traits (e.g., personality, preferences) conflict between periods:
     - Default to the most recent expression.
     - If change is meaningful (e.g., from anxious to calm), label it as **Personality Evolution: from X → Y**.
   - Where relevant, record transitions and note the approximate time of change.

5. **Output TWO Results**
   - **Output 1: Consolidated JSON Profile (for debugging/archiving)**
     - This JSON uses the same schema as individual summaries but aggregated into a single object representing the current user.
   - **Output 2: Natural Language Prompt (for Chatbot System Prompt)**
     - A coherent, readable description of the user suitable for injection into a personal chatbot.
   - The language used in the generated results must match the input corpus.

---

 ## Output 1: Consolidated JSON Profile (strict schema)

 ```json
 {
   "current_state": {
     "time_period": "latest period (e.g., 2024-12)",
     "profile": ["current identity label1", "current identity label2"],
     "preferences": [
       {
         "name": "core preference",
         "type": "strong/neutral",
         "stability": "core/temporary",
         "reason": "aggregated inference with duration evidence"
       }
     ],
     "personality": ["current dominant trait"],
     "language_style": "description of overall linguistic style"
   },
   "evolution_trajectory": {
     "personality_shifts": [
       {"from": "anxious", "to": "calm", "approximate_period": "2024-Q2"}
     ],
     "preference_transitions": [
       {"from": "topic_A", "to": "topic_B", "trigger_event": "career_change"}
     ]
   }
 }
 ```

---

## Output 2: Natural Language User Summary (System Prompt)

You MUST generate a natural language summary with the following sections:

### **Who the User Is**

* A concise description using core identity labels.
* For example: *“The user is a [标签], likely aged [age range], with interests and habits that suggest [occupation/role].”*

### **Personality & Values**

* Describe current emotional baseline and value orientation.
* If there has been evolution, present it clearly:
  *“Previously, the user tended to be [past trait], but now shows [current trait], indicating [growth/shift].”*

### **Interest Map**

* Summarize *core interests*, distinguishing between:

  * **Strong preferences**
  * **Neutral mentions**
  * **Dislikes**
* For evolving interests, include a brief transition narrative:
  *“Interest shifted from X in earlier periods to Y more recently.”*

### **Speaking Style**

* 2–3 actionable suggestions on how the chatbot should mimic the user’s linguistic style:

  * Common phrases
  * Typical punctuation or emojis
  * Tone (e.g., “concise and humorous”)

---

## Additional Instructions

* **Preserve Temporal Dynamics**: The summary must reflect how the user changed over time, not just static snapshots.
* **Do not drop any dimension**: All fields from the input summaries must be consolidated—do not ignore profile, preferences, personality, or language style.
* **Maintain clarity**: Both the JSON and natural language outputs must be clean, concise, and directly usable.

---
