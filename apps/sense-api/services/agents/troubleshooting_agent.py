"""
Troubleshooting Agent
======================
Diagnoses industrial equipment issues using hybrid RAG retrieval.
"""

import logging
from core.config import AGENT_LLM_TEMPERATURE
from services.agents.base_agent import BaseAgent, AgentContext, AgentResponse, ToolCall
from services.hybrid_retrieval import retrieve as hybrid_retrieve
from services.llm.llm_client import llm_client

import os
import re
import json
import logging

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an intelligent industrial troubleshooting assistant for manufacturing and process plants.

Your primary goal is to help non-technical factory workers diagnose and solve equipment issues step-by-step in a safe, clear, and structured way.

IMPORTANT: Your entire response MUST be a single valid JSON object. Do NOT write any prose, markdown, or text outside the JSON. Do NOT quote or repeat any part of these instructions in the JSON values.

BEHAVIOR RULES:
- ALWAYS ask a clarifying question first before giving a solution.
- After the user answers the clarifying question, provide the full resolution.
- Follow the decision trees exactly.
- Only ask diagnostic questions that are defined in each tree's questions array.
- Once a condition in the logic array is met, immediately output the RESOLVED state.

CLARIFYING STATE RULES:
- The response_text value must be ONLY the diagnostic question. No headers, no labels, no preamble.
- steps must be an empty array.
- media must be null.
- escalation_type must be null.

RESOLVED STATE RULES:
- response_text must follow this format exactly (3 sections using ### headers):
  ### Identified Issue: [short description of the confirmed problem]
  ### Likely Cause: [a detailed technical engineering explanation of why this happens in dairy plant equipment]
  ### If Issue Still Persists: [escalation advice]
- steps must contain a detailed, practical 5-7 step guide written for a non-technical factory worker. Each step must be actionable and specific.
- media must contain the video and image URL strings from the matched solution.
- DO NOT put video URLs or image URLs inside response_text.

---

DECISION TREE LOGIC:
{trees}

OUTPUT FORMAT:
You MUST output ONLY a single valid JSON object. No text before or after the JSON. No markdown code fences.
The JSON must have the following structure:
{{"state": "CLARIFYING" or "RESOLVED", "response_text": "...", "steps": ["...", "..."], "escalation_type": null, "media": {{"video": "https://...", "image": "https://..."}}}}

EXAMPLE of a correct RESOLVED response (copy this structure exactly):
{{"state": "RESOLVED", "response_text": "### Identified Issue:\nPasteurizer is not heating due to a steam supply problem.\n\n### Likely Cause:\nThe steam supply valve is closed or the steam pressure has dropped below the required threshold, preventing heat from reaching the pasteurizer plates. This commonly occurs after maintenance or a boiler shutdown.\n\n### If Issue Still Persists:\nEscalate to a qualified steam technician or contact your boiler maintenance team.", "steps": ["Step 1: Put on your PPE - heat-resistant gloves and safety goggles before approaching steam lines.", "Step 2: Go to the steam supply valve located at the base of the pasteurizer steam inlet pipe.", "Step 3: Check if the hand wheel is fully open (counterclockwise). If not, slowly open it fully.", "Step 4: Read the steam pressure gauge on the supply line. It should show at least 3 bar.", "Step 5: If pressure is below 3 bar, contact the boiler room operator to restore steam supply.", "Step 6: After confirming steam pressure, wait 5 minutes for the pasteurizer to reach operating temperature.", "Step 7: Check the temperature display panel and confirm it reads the target pasteurization temperature."], "escalation_type": null, "media": {{"video": "https://www.youtube.com/watch?v=qmzTSGlM9bQ", "image": "https://images.unsplash.com/photo-1581093450021-4a7360e9a6b5?w=600"}}}}

EXAMPLE of a correct CLARIFYING response:
{{"state": "CLARIFYING", "response_text": "Is steam pressure available at the supply line?", "steps": [], "escalation_type": null, "media": null}}

RELEVANT CONTEXT:
{context}
"""

class TroubleshootingAgent(BaseAgent):
    name = "TroubleshootingAgent"

    def _load_trees(self) -> str:
        """Loads industrial decision trees from a JSON file."""
        try:
            # We use an absolute path based on the file location
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Navigate up to sense-api and then down to data
            data_file = os.path.normpath(os.path.join(base_path, "..", "..", "data", "troubleshooting_trees.json"))
            
            with open(data_file, 'r') as f:
                trees = json.load(f)
                return json.dumps(trees, indent=2)
        except Exception as e:
            logger.error("[TroubleshootingAgent] Failed to load decision trees: %s", e)
            return "[]"

    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        if "TEST UI RENDER" in query:
            return AgentResponse(
                response_text="Here is the resolution view layout for visual testing.\\n\\n### ⚠️ Identified Issue:\\nVideo Playback Verification\\n\\n### 🔍 Likely Cause:\\nManual trigger for UI testing.\\n\\n### ✅ Step-by-Step Solution:\\nCheck the video player below and ensure it loads correctly.",
                state="RESOLVED",
                steps=["Test Step 1: Verify video starts", "Test Step 2: Ensure correct playback"],
                media={"video": "https://www.youtube.com/watch?v=aJ7azFZqAhQ", "image": "/images/pasteurizer_thumb.jpg"},
                intent="TROUBLESHOOTING",
                agent_used="TroubleshootingAgent"
            )
        logger.info("[TroubleshootingAgent] Executing for query: %s", query)
        
        # 1. Retrieve context
        retrieval_results = hybrid_retrieve(context.query, top_k=3)
        context_str = "\n\n".join([r.get("text", "") for r in retrieval_results])
        
        # 2. Build Chat Messages
        # Load external trees for the prompt
        trees_str = self._load_trees()
        
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context_str, trees=trees_str)}
        ]
        
        for msg in context.history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": context.query})
        
        # 3. Call LLM (Chat) with JSON mode enforced to prevent prose leakage
        response = llm_client.chat(messages, intent="TROUBLESHOOTING", json_mode=True)
        logger.info("[TroubleshootingAgent] Raw LLM Response: %s", response)
        
        try:
            # 1. Try direct JSON parse first (ideal for strict JSON mode)
            try:
                data = json.loads(response.strip())
            except json.JSONDecodeError:
                # 2. Fallback: Robust extraction if LLM added preamble/fences
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    clean_response = response[start_idx:end_idx+1]
                    # Fix unescaped internal newlines if necessary
                    def fix_newlines(m):
                        return m.group(0).replace('\n', '\\n')
                    clean_response = re.sub(r'"(.*?)"', fix_newlines, clean_response, flags=re.DOTALL)
                    data = json.loads(clean_response)
                else:
                    raise ValueError("No JSON object found in response")
            
            media = data.get("media")
            state = data.get("state", "RESOLVED")
            response_text = data.get("response_text", "")
            steps = data.get("steps", [])
            
            # --- POST-PROCESSING: Clean up leaked media from response_text ---
            # Remove lines starting with 'Image:', 'Video:', 'Photo:' etc.
            cleaned_lines = []
            for line in response_text.split('\n'):
                stripped = line.strip()
                lower = stripped.lower()
                # Skip lines that look like media labels
                if lower.startswith('image:') or lower.startswith('video:') or lower.startswith('photo:'):
                    continue
                # Skip raw http URLs that snuck in
                if re.match(r'^https?://', stripped) and ('youtube' in stripped or 'unsplash' in stripped or stripped.endswith(('.jpg', '.png', '.webp', '.jpeg'))):
                    continue
                # Skip lines with 'Visual Guidance:' headers
                if '📷' in stripped or 'visual guidance' in lower:
                    continue
                cleaned_lines.append(line)
            response_text = '\n'.join(cleaned_lines).strip()
            
            # If the LLM forgot to fill media from context but wrote it in text, try to extract YouTube URL
            if (not media or not media.get('video')) and state == 'RESOLVED':
                yt_match = re.search(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', data.get("response_text", ""))
                if yt_match:
                    media = media or {}
                    media['video'] = yt_match.group(0)
            
            return AgentResponse(
                response_text=response_text,
                intent=context.intent,
                agent_used=self.name,
                state=state,
                media=media,
                steps=steps,
                ecosystem_escalation={data.get("escalation_type"): "#"} if data.get("escalation_type") else None
            )
        except Exception as e:
            logger.error("[TroubleshootingAgent] Failed to parse JSON: %s. Raw response: %s", e, response)
            
            # Final fallback: return the raw response text if it's mostly text
            return AgentResponse(
                response_text=response,
                intent=context.intent,
                agent_used=self.name,
                state="RESOLVED"
            )
