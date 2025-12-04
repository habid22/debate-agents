"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Types
interface DebateEntry {
  type: string;
  round?: number | string;
  agent?: string;
  role?: string;
  message?: string;
  topic?: string;
  agents?: Array<{ name: string; role: string }>;
}

interface AgentTemplate {
  name: string;
  role: string;
  personality: string;
  stance: string;
}

// Agent color mapping
const agentColors: Record<string, { bg: string; text: string; glow: string }> = {
  Alex: { bg: "bg-emerald-500/20", text: "text-emerald-400", glow: "shadow-emerald-500/20" },
  Morgan: { bg: "bg-red-500/20", text: "text-red-400", glow: "shadow-red-500/20" },
  Jordan: { bg: "bg-blue-500/20", text: "text-blue-400", glow: "shadow-blue-500/20" },
  Sam: { bg: "bg-amber-500/20", text: "text-amber-400", glow: "shadow-amber-500/20" },
  Casey: { bg: "bg-purple-500/20", text: "text-purple-400", glow: "shadow-purple-500/20" },
  Riley: { bg: "bg-pink-500/20", text: "text-pink-400", glow: "shadow-pink-500/20" },
  Moderator: { bg: "bg-indigo-500/20", text: "text-indigo-400", glow: "shadow-indigo-500/20" },
};

const getAgentColor = (name: string) => {
  return agentColors[name] || { bg: "bg-gray-500/20", text: "text-gray-400", glow: "shadow-gray-500/20" };
};

// Section configuration for synthesis parsing
const sectionConfig = [
  { key: "Synthesis", icon: "📋", color: "text-indigo-400", bgColor: "bg-indigo-500/10" },
  { key: "Points of Agreement", icon: "🤝", color: "text-emerald-400", bgColor: "bg-emerald-500/10" },
  { key: "Points of Contention", icon: "⚔️", color: "text-amber-400", bgColor: "bg-amber-500/10" },
  { key: "Key Insights", icon: "💡", color: "text-blue-400", bgColor: "bg-blue-500/10" },
  { key: "Conclusion", icon: "🎯", color: "text-purple-400", bgColor: "bg-purple-500/10" },
  { key: "Confidence", icon: "📊", color: "text-pink-400", bgColor: "bg-pink-500/10" },
];

// Clean up markdown formatting from text
const cleanMarkdown = (text: string): string => {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1") // Remove bold markers **text**
    .replace(/^:\s*/, "") // Remove leading colons
    .trim();
};

// Parse content into bullet points if it contains * markers
const parseContentIntoBullets = (content: string): string[] => {
  // Split by bullet pattern: newline or start followed by * and space
  // This handles: "* item1 * item2" and "* item1\n* item2"
  const bulletPattern = /(?:^|\n)\s*\*\s+/;
  
  // Check if content has bullet-like structure
  if (!content.includes("* ")) {
    // No bullets, return cleaned content as single item
    return [cleanMarkdown(content)];
  }
  
  // Split content by bullet markers, handling both inline and newline bullets
  // First normalize: replace " * " with "\n* " for consistent splitting
  const normalized = content.replace(/\s+\*\s+/g, "\n* ");
  const parts = normalized.split(bulletPattern).filter(p => p.trim());
  
  if (parts.length > 1) {
    return parts.map(p => cleanMarkdown(p));
  }
  
  // Fallback: return cleaned content as single item
  return [cleanMarkdown(content)];
};

// Parse synthesis message into structured sections
const parseSynthesis = (message: string) => {
  const sections: { title: string; content: string[]; icon: string; color: string; bgColor: string }[] = [];
  
  // Build regex to find all sections
  const sectionKeys = sectionConfig.map(s => s.key).join("|");
  const sectionRegex = new RegExp(`\\*\\*(${sectionKeys}):?\\*\\*`, "gi");
  
  // Find all section positions
  const sectionMatches: { key: string; index: number; endIndex: number }[] = [];
  let match;
  
  while ((match = sectionRegex.exec(message)) !== null) {
    sectionMatches.push({
      key: match[1],
      index: match.index,
      endIndex: match.index + match[0].length,
    });
  }
  
  // Extract content for each section
  for (let i = 0; i < sectionMatches.length; i++) {
    const current = sectionMatches[i];
    const nextIndex = i + 1 < sectionMatches.length ? sectionMatches[i + 1].index : message.length;
    const rawContent = message.substring(current.endIndex, nextIndex).trim();
    
    const config = sectionConfig.find(s => s.key.toLowerCase() === current.key.toLowerCase());
    if (config && rawContent) {
      sections.push({
        title: config.key,
        content: parseContentIntoBullets(rawContent),
        icon: config.icon,
        color: config.color,
        bgColor: config.bgColor,
      });
    }
  }
  
  return sections;
};

// Component to render formatted synthesis
const SynthesisCard = ({ message }: { message: string }) => {
  const sections = parseSynthesis(message);
  
  // If parsing failed, fall back to simple display
  if (sections.length === 0) {
    return <p className="text-gray-200 leading-relaxed">{message}</p>;
  }

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => (
        <div key={idx} className={`rounded-lg p-4 ${section.bgColor}`}>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">{section.icon}</span>
            <h4 className={`font-semibold text-base ${section.color}`}>{section.title}</h4>
          </div>
          
          {section.content.length === 1 ? (
            <p className="text-gray-300 leading-relaxed text-sm pl-8">
              {section.content[0]}
            </p>
          ) : (
            <ul className="space-y-2 pl-8">
              {section.content.map((bullet, bulletIdx) => (
                <li key={bulletIdx} className="text-gray-300 text-sm leading-relaxed flex items-start gap-2">
                  <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${section.color.replace('text-', 'bg-')}`} />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
};

// Sample debate topics
const sampleTopics = [
  "Should developers use AI coding assistants?",
  "Is remote work better than office work?",
  "Tabs vs Spaces - which is superior?",
  "Should startups use microservices or monoliths?",
  "Is college necessary for a career in tech?",
  "Should we regulate AI development?",
];

export default function Home() {
  const [topic, setTopic] = useState("");
  const [debates, setDebates] = useState<DebateEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRound, setCurrentRound] = useState<number>(0);
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(["optimist", "skeptic", "pragmatist"]);
  const [rounds, setRounds] = useState(2);
  const debateEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    debateEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [debates]);

  const startDebate = async () => {
    if (!topic.trim()) {
      setError("Please enter a debate topic");
      return;
    }

    setIsLoading(true);
    setError(null);
    setDebates([]);
    setCurrentRound(0);

    try {
      const response = await fetch("http://localhost:8000/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          rounds,
          agent_templates: selectedTemplates,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start debate");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === "round_start") {
                setCurrentRound(data.round);
              }
              
              setDebates((prev) => [...prev, data]);
            } catch (e) {
              console.error("Failed to parse:", line);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTemplate = (template: string) => {
    setSelectedTemplates((prev) => {
      if (prev.includes(template)) {
        if (prev.length <= 2) return prev; // Minimum 2 agents
        return prev.filter((t) => t !== template);
      }
      if (prev.length >= 4) return prev; // Maximum 4 agents
      return [...prev, template];
    });
  };

  const argumentEntries = debates.filter((d) => d.type === "argument" || d.type === "synthesis");

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-3 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            🎭 AI Debate Arena
          </h1>
          <p className="text-gray-400 text-lg">
            Watch AI agents debate any topic from multiple perspectives
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="gradient-border p-6 mb-6"
        >
          {/* Topic Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Debate Topic
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isLoading && startDebate()}
                placeholder="Enter a topic to debate..."
                className="flex-1 px-4 py-3 bg-black/50 rounded-lg border border-gray-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all"
                disabled={isLoading}
              />
              <button
                onClick={startDebate}
                disabled={isLoading}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed rounded-lg font-medium transition-all hover:shadow-lg hover:shadow-indigo-500/25"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Debating...
                  </span>
                ) : (
                  "Start Debate"
                )}
              </button>
            </div>
          </div>

          {/* Sample Topics */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Or try a sample topic:
            </label>
            <div className="flex flex-wrap gap-2">
              {sampleTopics.map((sampleTopic) => (
                <button
                  key={sampleTopic}
                  onClick={() => setTopic(sampleTopic)}
                  className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 rounded-full transition-colors"
                >
                  {sampleTopic}
                </button>
              ))}
            </div>
          </div>

          {/* Agent Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Select Agents (2-4)
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries({
                optimist: { name: "Alex", label: "Optimist", emoji: "😊" },
                skeptic: { name: "Morgan", label: "Skeptic", emoji: "🤔" },
                pragmatist: { name: "Jordan", label: "Pragmatist", emoji: "⚖️" },
                innovator: { name: "Sam", label: "Innovator", emoji: "💡" },
                veteran: { name: "Casey", label: "Veteran", emoji: "🎖️" },
                devils_advocate: { name: "Riley", label: "Devil's Advocate", emoji: "😈" },
              }).map(([key, { name, label, emoji }]) => {
                const isSelected = selectedTemplates.includes(key);
                const colors = getAgentColor(name);
                return (
                  <button
                    key={key}
                    onClick={() => toggleTemplate(key)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      isSelected
                        ? `${colors.bg} ${colors.text} ring-1 ring-current`
                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                  >
                    {emoji} {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Rounds Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Number of Rounds
            </label>
            <div className="flex gap-2">
              {[1, 2, 3].map((num) => (
                <button
                  key={num}
                  onClick={() => setRounds(num)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    rounds === num
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                >
                  {num} {num === 1 ? "Round" : "Rounds"}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400"
            >
              ⚠️ {error}
              <p className="text-sm mt-1 text-red-400/70">
                Make sure the backend is running: <code className="bg-black/30 px-1 rounded">uvicorn server:app --reload --port 8000</code>
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Debate Display */}
        {argumentEntries.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="gradient-border p-6"
          >
            {/* Debate Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  {debates.find((d) => d.type === "start")?.topic || topic}
                </h2>
                <p className="text-sm text-gray-400 mt-1">
                  {isLoading ? `Round ${currentRound} in progress...` : "Debate complete"}
                </p>
              </div>
              {!isLoading && (
                <div className="text-sm text-gray-400">
                  {argumentEntries.length} arguments
                </div>
              )}
            </div>

            {/* Arguments */}
            <div className="space-y-4">
              <AnimatePresence>
                {argumentEntries.map((entry, i) => {
                  const colors = getAgentColor(entry.agent || "");
                  const isSynthesis = entry.type === "synthesis";

                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.05 }}
                      className={`p-4 rounded-xl ${
                        isSynthesis
                          ? "bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/30"
                          : `${colors.bg} border border-gray-800`
                      }`}
                    >
                      {/* Agent Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
                            isSynthesis ? "bg-indigo-500/30" : colors.bg
                          }`}
                        >
                          {isSynthesis ? "📊" : entry.agent?.charAt(0)}
                        </div>
                        <div>
                          <div className={`font-semibold ${isSynthesis ? "text-indigo-400" : colors.text}`}>
                            {entry.agent}
                          </div>
                          <div className="text-xs text-gray-500">
                            {entry.role} {!isSynthesis && `• Round ${entry.round}`}
                          </div>
                        </div>
                      </div>

                      {/* Message */}
                      {isSynthesis ? (
                        <div className="mt-4">
                          <SynthesisCard message={entry.message || ""} />
                        </div>
                      ) : (
                        <p className="text-gray-200 leading-relaxed pl-13">
                          {entry.message}
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </AnimatePresence>

              {/* Loading Indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-3 p-4 bg-gray-800/50 rounded-xl"
                >
                  <div className="flex gap-1">
                    <span className="typing-dot w-2 h-2 bg-indigo-400 rounded-full" />
                    <span className="typing-dot w-2 h-2 bg-indigo-400 rounded-full" />
                    <span className="typing-dot w-2 h-2 bg-indigo-400 rounded-full" />
                  </div>
                  <span className="text-gray-400 text-sm">Agent is thinking...</span>
                </motion.div>
              )}

              <div ref={debateEndRef} />
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {debates.length === 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-center py-16 text-gray-500"
          >
            <div className="text-6xl mb-4">🎭</div>
            <p className="text-lg">Enter a topic and start a debate!</p>
            <p className="text-sm mt-2">
              Watch AI agents argue from different perspectives
            </p>
          </motion.div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          Powered by local AI • No data sent to external servers
        </div>
      </div>
    </main>
  );
}
