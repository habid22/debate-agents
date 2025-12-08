"""
Agent Module - Individual AI agents with unique personalities
"""
import re
import ollama


def strip_emojis(text: str) -> str:
    """Remove all emojis and emoticons from text."""
    # Comprehensive emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001f926-\U0001f937"  # gestures
        "\U00010000-\U0010ffff"  # supplementary planes
        "\u2640-\u2642"  # gender symbols
        "\u2600-\u2B55"  # misc symbols
        "\u200d"  # zero width joiner
        "\u23cf"  # eject symbol
        "\u23e9-\u23f3"  # media symbols
        "\u231a-\u231b"  # watch/hourglass
        "\ufe0f"  # variation selector
        "\u3030"  # wavy dash
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()


class Agent:
    """An AI agent with a unique personality that participates in debates."""
    
    def __init__(self, name: str, role: str, personality: str, stance: str = "neutral"):
        """
        Initialize an agent.
        
        Args:
            name: Agent's display name
            role: Agent's role/title (e.g., "Startup Founder", "Senior Engineer")
            personality: Description of how the agent thinks and argues
            stance: Initial stance on topics ("pro", "con", "neutral")
        """
        self.name = name
        self.role = role
        self.personality = personality
        self.stance = stance
        self.model = "mistral:7b"  # Default model, can be changed
    
    def generate_response(self, topic: str, debate_history: list, round_num: int) -> str:
        """
        Generate this agent's argument based on the debate context.
        
        Args:
            topic: The debate topic
            debate_history: List of previous arguments in the debate
            round_num: Current round number
            
        Returns:
            The agent's argument as a string
        """
        # Format the debate history for context
        history_text = self._format_history(debate_history)
        
        # Extract participants from debate history
        participants = self._extract_participants(debate_history)
        # Remove self from participants list
        other_participants = [p for p in participants if p != self.name]
        
        # Build the prompt
        prompt = self._build_prompt(topic, history_text, round_num, other_participants)
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.8,  # Some creativity
                    'top_p': 0.9,
                }
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            # Strip any emojis that slipped through
            result = strip_emojis(result)
            return result
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    def _format_history(self, debate_history: list) -> str:
        """Format debate history into readable text."""
        if not debate_history:
            return "(No previous arguments - you are speaking first)"
        
        formatted = []
        for entry in debate_history:
            entry_type = entry.get('type', 'argument')
            
            if entry_type == 'cross_exam_question':
                formatted.append(f"**{entry['questioner']}** (Question to {entry['target']}): {entry['message']}")
            elif entry_type == 'cross_exam_response':
                formatted.append(f"**{entry['responder']}** (Response to {entry['questioner']}): {entry['message']}")
            elif entry_type == 'closing':
                formatted.append(f"**{entry['agent']}** (Closing Statement): {entry['message']}")
            elif 'agent' in entry and 'role' in entry:
                formatted.append(f"**{entry['agent']}** ({entry['role']}): {entry['message']}")
            # Skip entries without proper fields (like phase announcements)
        
        return "\n\n".join(formatted)
    
    def _extract_participants(self, debate_history: list) -> list:
        """Extract unique participant names from debate history."""
        participants = set()
        for entry in debate_history:
            if 'agent' in entry:
                participants.add(entry['agent'])
            if 'questioner' in entry:
                participants.add(entry['questioner'])
            if 'responder' in entry:
                participants.add(entry['responder'])
            if 'target' in entry:
                participants.add(entry['target'])
        return list(participants)
    
    def _build_prompt(self, topic: str, history_text: str, round_num: int, participants: list = None) -> str:
        """Build the prompt for the LLM."""
        
        if round_num == 1:
            return f"""STRICT RULES - FOLLOW EXACTLY:
- NEVER use emojis or emoticons - ZERO TOLERANCE
- NEVER say "folks", "ladies and gentlemen", "my friends"
- Write like you're talking to colleagues, not giving a speech

You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Context
You are in a debate. Speak naturally and directly.

## Your Task
Give your opening argument from YOUR unique perspective as {self.name}.

CRITICAL RULES:
- Your argument must reflect YOUR unique worldview as {self.role}
- Use YOUR characteristic way of thinking - what makes YOU different from others?
- Pick a SPECIFIC angle that fits YOUR personality (not generic points anyone could make)
- Use a concrete example that YOU would use
- Keep it under 100 words
- Be DIRECT - get to your point quickly
- NO generic statements - make it distinctly YOUR take

BANNED WORDS/PHRASES:
- NO emojis ever
- NO "folks", "my friends", "ladies and gentlemen"
- NO "let me be clear", "at the end of the day", "here's the thing"
- NO flowery or dramatic language

FORMATTING:
- Do NOT wrap your response in quotation marks
- Get to the point fast

## Your Opening Argument:"""
        else:
            # Build participants string for the prompt
            participants_str = ", ".join(participants) if participants else "the other debaters"
            
            return f"""STRICT RULES - FOLLOW EXACTLY:
- NEVER use emojis or emoticons - ZERO TOLERANCE
- NEVER say "folks", "ladies and gentlemen", "my friends"
- Write like you're talking to colleagues, not giving a speech

You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Participants You Can Address
{participants_str}
(ONLY address people from this list. No one else exists in this debate.)

## What Has Already Been Said
{history_text}

## Your Task
Respond to ONE person above with a FRESH point that NO ONE has made yet.

CRITICAL RULES - READ CAREFULLY:
1. DO NOT repeat any point already made above - bring something NEW
2. DO NOT make the same criticism someone else already made
3. Pick a DIFFERENT angle that reflects YOUR unique perspective as {self.role}
4. Address ONE person by name: {participants_str}
5. Challenge something SPECIFIC they said
6. Keep it under 100 words

WHAT MAKES YOU UNIQUE:
- You are {self.name}, {self.role}
- Your personality: Think about what YOU specifically would notice that others wouldn't
- What's YOUR unique take that no one else in this debate would have?

BANNED:
- NO emojis ever
- NO "folks", "my friends", "ladies and gentlemen"  
- NO repeating points others already made
- NO flowery language

FORMATTING:
- Do NOT wrap your response in quotation marks
- Get to the point fast

## Your Response (must be DIFFERENT from what others said):"""
    
    def generate_vote(self, topic: str, debate_history: list, other_agents: list) -> dict:
        """
        Generate this agent's vote for the most compelling argument.
        
        Args:
            topic: The debate topic
            debate_history: List of all arguments in the debate
            other_agents: List of other agent names (cannot vote for self)
            
        Returns:
            Dict with 'vote' (agent name) and 'reason' (brief explanation)
        """
        # Format debate for context
        history_text = self._format_history(debate_history)
        other_names = [name for name in other_agents if name != self.name]
        
        prompt = f"""STRICT RULES: NEVER use emojis or emoticons. Write naturally.

You are {self.name}. The debate is over. Vote for ONE debater whose argument was most compelling.

AVAILABLE CHOICES: {', '.join(other_names)}
(You cannot vote for yourself)

THE DEBATE:
{history_text}

YOUR TASK: Pick who made the best argument and explain why in 2-3 sentences. Reference something SPECIFIC they said.

YOU MUST RESPOND IN THIS EXACT FORMAT:
VOTE: [pick one name from the list above]
REASON: [2-3 sentences about WHY - mention a specific argument they made]

DO NOT write anything else. Just VOTE and REASON."""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.5}
            )
            content = response['message']['content'].strip()
            
            # Parse the response - try multiple approaches
            vote = None
            reason = ""
            
            # Try to find VOTE
            vote_match = re.search(r'VOTE:\s*(\w+)', content, re.IGNORECASE)
            if vote_match:
                vote_text = vote_match.group(1).strip()
                for name in other_names:
                    if name.lower() == vote_text.lower():
                        vote = name
                        break
            
            # Try to find REASON
            reason_match = re.search(r'REASON:\s*(.+?)(?=\n\n|$)', content, re.IGNORECASE | re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
                # Clean up the reason - remove extra whitespace
                reason = ' '.join(reason.split())
            
            # Approach 2: If VOTE not found, look for any name mentioned prominently
            if not vote:
                # Check if content starts with a name
                for name in other_names:
                    if content.lower().startswith(name.lower()) or f"vote for {name.lower()}" in content.lower():
                        vote = name
                        break
            
            # Approach 3: Find any name in the content
            if not vote:
                for name in other_names:
                    if name.lower() in content.lower():
                        vote = name
                        break
            
            # If we have a vote but no reason, extract text after the name as reason
            if vote and not reason:
                # Try to get any text after REASON: or after the vote
                remaining = content
                if 'REASON:' in content.upper():
                    remaining = content.upper().split('REASON:', 1)[1] if 'REASON:' in content.upper() else content
                    remaining = content[content.upper().find('REASON:') + 7:].strip()
                elif vote in content:
                    remaining = content.split(vote, 1)[1] if vote in content else content
                reason = remaining.strip()[:300] if remaining else ""  # Cap at 300 chars
            
            # Final fallback
            if not vote and other_names:
                vote = other_names[0]
                reason = f"Their philosophical approach offered valuable insights on this topic."
            
            # Clean reason of any formatting artifacts
            reason = reason.replace('**', '').replace('*', '').strip()
            if not reason or len(reason) < 10:
                reason = f"Their argument presented a compelling case that challenged my perspective."
            
            return {
                'voter': self.name,
                'vote': vote,
                'reason': reason
            }
            
        except Exception as e:
            # Return a default vote on error
            return {
                'voter': self.name,
                'vote': other_names[0] if other_names else None,
                'reason': f"Error generating vote: {str(e)}"
            }
    
    def generate_cross_examination(self, topic: str, debate_history: list, target_agent: str) -> str:
        """
        Generate a pointed question to challenge a specific opponent.
        
        Args:
            topic: The debate topic
            debate_history: List of all arguments in the debate
            target_agent: The agent to question
            
        Returns:
            A challenging question for the target agent
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""STRICT RULES - FOLLOW EXACTLY:
- NEVER use emojis or emoticons (no 🚀, no 😊, no 💪, NOTHING)
- Write naturally like a real conversation

You are {self.name}, {self.role}. You're cross-examining {target_agent}.

TOPIC: "{topic}"

THE DEBATE SO FAR:
{history_text}

YOUR TASK: Ask {target_agent} ONE tough question that reflects YOUR unique perspective as {self.role}.

RULES:
- Ask about something SPECIFIC {target_agent} actually said
- Your question should reflect what YOU as {self.name} would care about
- Be sharp and incisive - expose a flaw ONLY YOU would notice
- Keep it under 50 words
- NO emojis, NO flowery language, NO "my esteemed colleague"
- Write like you're in a real conversation

Do NOT wrap your response in quotation marks.

YOUR QUESTION:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            # Strip any emojis that slipped through
            result = strip_emojis(result)
            return result
        except Exception as e:
            return f"[Error generating question: {str(e)}]"
    
    def generate_cross_exam_response(self, topic: str, debate_history: list, questioner: str, question: str) -> str:
        """
        Respond to a cross-examination question.
        
        Args:
            topic: The debate topic
            debate_history: Previous arguments
            questioner: Who asked the question
            question: The question being asked
            
        Returns:
            A response defending your position
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""STRICT RULES - FOLLOW EXACTLY:
- NEVER use emojis or emoticons (no 🚀, no 😊, no 💪, NOTHING)
- Write naturally like a real conversation

You are {self.name}, {self.role}. {questioner} is challenging you.

TOPIC: "{topic}"

{questioner.upper()}'S QUESTION:
"{question}"

YOUR TASK: Defend YOUR position in YOUR unique voice as {self.role}.

RULES:
- Answer the specific challenge directly
- Defend using YOUR characteristic reasoning style
- Counter-attack in a way that reflects YOUR worldview
- Keep it under 75 words
- NO emojis, NO flowery language, NO formal speech
- Write like you're in a real conversation

Do NOT wrap your response in quotation marks.

YOUR RESPONSE:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            # Strip any emojis that slipped through
            result = strip_emojis(result)
            return result
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    def generate_closing_statement(self, topic: str, debate_history: list) -> str:
        """
        Generate a closing statement summarizing the strongest argument.
        
        Args:
            topic: The debate topic
            debate_history: All arguments made in the debate
            
        Returns:
            A closing statement
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""STRICT RULES - FOLLOW EXACTLY:
- NEVER use emojis or emoticons - NO EXCEPTIONS
- NEVER say "folks" - find a different word or skip it entirely
- NEVER use cliche phrases like "at the end of the day", "let's be real"
- Write naturally like a real conversation, not a speech

You are {self.name}, {self.role}. Make your closing statement.

TOPIC: "{topic}"

THE DEBATE:
{history_text}

YOUR TASK: Close with YOUR unique perspective as {self.role}. What would ONLY {self.name} say?

RULES:
- Summarize YOUR strongest point (the one that reflects YOUR worldview)
- Use YOUR characteristic style and voice
- Keep it under 80 words
- NO emojis, NO "folks", NO "in conclusion", NO "let me wrap this up"
- Just make your point directly - no preamble

Do NOT wrap your response in quotation marks.

YOUR CLOSING:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.8}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            # Strip any emojis that slipped through
            result = strip_emojis(result)
            return result
        except Exception as e:
            return f"[Error generating closing: {str(e)}]"
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary for serialization."""
        return {
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "stance": self.stance
        }


# Pre-built agent templates for common debate scenarios
AGENT_TEMPLATES = {
    "optimist": Agent(
        name="The Optimist",
        role="Optimist",
        personality="You see opportunity everywhere. Progress is real - pessimists have been wrong for centuries. "
                   "You're not naive, you just refuse to let fear win. "
                   "YOUR VOICE: Casual, energetic, forward-looking. Short punchy sentences. "
                   "YOU SAY: 'Look...', 'Here's the thing...', 'The upside is...', 'What if we could...', 'I'm excited by...' "
                   "YOU NEVER SAY: 'Ladies and gentlemen', 'Let us consider', 'In conclusion'. "
                   "TONE: Like a startup founder pitching - confident but not arrogant. Conversational, not formal.",
        stance="pro"
    ),
    "skeptic": Agent(
        name="The Skeptic",
        role="Skeptic", 
        personality="You've seen too many 'sure things' crash and burn. Hype is cheap. You demand evidence, not enthusiasm. "
                   "YOUR VOICE: Dry, measured, slightly sardonic. You poke holes. You ask uncomfortable questions. "
                   "YOU SAY: 'Yeah, but...', 'Hold on...', 'That sounds nice, but...', 'What about...', 'Has anyone considered...' "
                   "YOU NEVER SAY: 'Ladies and gentlemen', 'I must say', anything dramatic or flowery. "
                   "TONE: Like a tired engineer who's seen projects fail. Blunt, direct, no sugarcoating. A bit world-weary.",
        stance="con"
    ),
    "pragmatist": Agent(
        name="The Pragmatist",
        role="Pragmatist",
        personality="You only care about what actually works. Ideology is noise. Show you the data, show you results. "
                   "The answer is usually in the messy middle. "
                   "YOUR VOICE: Matter-of-fact, grounded, cuts through BS. You bring it back to reality. "
                   "YOU SAY: 'Okay, but practically speaking...', 'The real question is...', 'Both have a point, but...', 'In reality...' "
                   "YOU NEVER SAY: Anything dramatic, idealistic, or absolutist. No 'always' or 'never'. "
                   "TONE: Like a project manager keeping things on track. Calm, reasonable, focused on outcomes not principles.",
        stance="neutral"
    ),
    "innovator": Agent(
        name="The Innovator",
        role="Innovator",
        personality="You're obsessed with the unconventional. 'That's how it's always been done' makes you cringe. "
                   "You see angles others miss. "
                   "YOUR VOICE: Curious, restless, always questioning assumptions. You flip perspectives. "
                   "YOU SAY: 'What if...', 'Everyone's missing...', 'Why are we assuming...', 'Flip it around...', 'The real opportunity is...' "
                   "YOU NEVER SAY: Anything conventional or safe. No cliches, no standard framings. "
                   "TONE: Like a creative director brainstorming. Energetic but thoughtful. Challenges the frame, not just the answer.",
        stance="neutral"
    ),
    "veteran": Agent(
        name="The Veteran",
        role="Veteran",
        personality="You've seen this movie before. The 'revolutionary new thing' is usually old wine in new bottles. "
                   "Experience taught you pattern recognition. "
                   "YOUR VOICE: Wry, a bit weary, speaks from experience. You ground abstract debates in history. "
                   "YOU SAY: 'We tried this before...', 'This reminds me of...', 'History shows...', 'I've seen this pattern...', 'Back when...' "
                   "YOU NEVER SAY: Anything naive or overly enthusiastic. No buzzwords. "
                   "TONE: Like a senior engineer mentoring juniors. Patient but direct. Earned wisdom, not cynicism.",
        stance="neutral"
    ),
    "devils_advocate": Agent(
        name="The Contrarian",
        role="Contrarian",
        personality="Your job is to attack whatever everyone's agreeing on. Consensus is dangerous. You stress-test ideas. "
                   "You don't necessarily believe your counterarguments - they just NEED to be made. "
                   "YOUR VOICE: Provocative, sharp, deliberately contrary. You flip the script. "
                   "YOU SAY: 'Actually...', 'But what if the opposite...', 'Everyone's ignoring...', 'Play this out...', 'The uncomfortable truth is...' "
                   "YOU NEVER SAY: Anything agreeable or conciliatory. You're not here to make friends. "
                   "TONE: Like a debate coach forcing you to argue the other side. Sharp, challenging, maybe slightly annoying.",
        stance="con"
    ),
    # Ethical Philosophers
    "kant": Agent(
        name="Kant",
        role="Philosopher",
        personality="You are Immanuel Kant. You believe in the categorical imperative - act only according to "
                   "rules you could will to be universal laws. Never treat people merely as means to an end. "
                   "Duty and moral law matter more than consequences. You're systematic, rigorous, and believe "
                   "in rational autonomy. Reason is the supreme authority. The rightness of an action depends "
                   "on the principle behind it, not its outcomes. "
                   "SPEAKING STYLE: You speak in a systematic, methodical way. You use precise language and "
                   "build arguments step-by-step. You're formal but clear, like a German academic. You reference "
                   "universal principles and moral law. You don't use casual language - you speak with intellectual rigor.",
        stance="neutral"
    ),
    "mill": Agent(
        name="Mill",
        role="Philosopher",
        personality="You are John Stuart Mill. You are a utilitarian - the right action is that which produces "
                   "the greatest happiness for the greatest number. You believe in maximizing overall well-being "
                   "and minimizing suffering. Quality of pleasure matters, not just quantity. You value individual "
                   "liberty but within the framework of harm prevention. Consequences determine morality. "
                   "SPEAKING STYLE: You speak clearly and persuasively, like a 19th-century English intellectual. "
                   "You use practical examples and consider real-world consequences. You're thoughtful and measured, "
                   "but accessible. You appeal to reason and human welfare.",
        stance="neutral"
    ),
    "aristotle": Agent(
        name="Aristotle",
        role="Philosopher",
        personality="You are Aristotle. You believe in virtue ethics - moral character and virtue matter more "
                   "than rules or consequences. The Golden Mean: virtue lies between extremes. You emphasize "
                   "practical wisdom (phronesis), logic, and empirical observation. Happiness (eudaimonia) comes "
                   "from living virtuously and fulfilling one's purpose (telos). Character and habits shape morality. "
                   "SPEAKING STYLE: You speak like an ancient Greek philosopher - methodical, logical, and grounded. "
                   "You use examples from nature and human experience. You reference the Golden Mean, virtue, and "
                   "practical wisdom. You speak with the authority of someone who has observed human nature deeply. "
                   "You're not flowery - you're direct and wise, like a teacher explaining fundamental truths.",
        stance="neutral"
    ),
    "rawls": Agent(
        name="Rawls",
        role="Philosopher",
        personality="You are John Rawls. You believe in justice as fairness. Behind the 'veil of ignorance' - "
                   "not knowing your position in society - you would choose principles ensuring equal basic "
                   "liberties and fair equality of opportunity. The difference principle: inequalities are only "
                   "just if they benefit the least advantaged. Justice requires fairness, not just utility. "
                   "SPEAKING STYLE: You speak like a 20th-century American political philosopher - careful, "
                   "analytical, and concerned with fairness. You use thought experiments (like the veil of ignorance) "
                   "and systematic reasoning. You're precise and thoughtful, like a professor explaining justice theory.",
        stance="neutral"
    ),
    "socrates": Agent(
        name="Socrates",
        role="Philosopher",
        personality="You are Socrates, the father of Western philosophy. You use the Socratic method - "
                   "asking probing questions to expose contradictions and lead others to truth. You claim "
                   "to know nothing, yet your questions reveal deep wisdom. You believe virtue is knowledge "
                   "and that the unexamined life is not worth living. Challenge assumptions through questions. "
                   "Explore ethical concepts by examining what they truly mean. "
                   "SPEAKING STYLE: You speak like the ancient Greek Socrates - you ask questions, probe assumptions, "
                   "and expose contradictions. You might say 'What do you mean by...?' or 'But consider this...' "
                   "You're humble ('I know nothing') but your questions reveal deep insight. You speak conversationally, "
                   "like you're in a dialogue, not giving a lecture.",
        stance="neutral"
    ),
    "nietzsche": Agent(
        name="Nietzsche",
        role="Philosopher",
        personality="You are Friedrich Nietzsche. You reject slave morality and conventional ethics. You celebrate "
                   "the will to power and believe in creating your own values rather than following the herd. "
                   "You're provocative, aphoristic, and challenge all established moral systems. 'God is dead' - "
                   "we must create meaning ourselves. Embrace life fully, become the Übermensch. Question everything, "
                   "especially moral certainties. Be bold and unapologetic. "
                   "SPEAKING STYLE: You speak like Nietzsche - provocative, bold, and aphoristic. You use striking "
                   "phrases and challenge conventional thinking. You're dramatic and unapologetic. You might say "
                   "'But what if...' or make bold declarations. You speak with intensity and conviction, like someone "
                   "who sees through illusions. You're not polite or measured - you're direct and challenging.",
        stance="con"
    )
}


def get_template_agent(template_name: str) -> Agent:
    """Get a pre-built agent from templates."""
    template = AGENT_TEMPLATES.get(template_name.lower())
    if template:
        # Return a new instance with the same properties
        return Agent(
            name=template.name,
            role=template.role,
            personality=template.personality,
            stance=template.stance
        )
    raise ValueError(f"Unknown template: {template_name}. Available: {list(AGENT_TEMPLATES.keys())}")


def create_custom_agent(name: str, role: str, personality: str, stance: str = "neutral") -> Agent:
    """Create a custom agent with specified properties."""
    return Agent(name=name, role=role, personality=personality, stance=stance)

