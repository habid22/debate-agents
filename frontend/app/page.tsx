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
const agentColors: Record<string, { bg: string; text: string; border: string }> = {
  Alex: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-l-emerald-500" },
  Morgan: { bg: "bg-red-500/10", text: "text-red-400", border: "border-l-red-500" },
  Jordan: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-l-blue-500" },
  Sam: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-l-amber-500" },
  Casey: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-l-purple-500" },
  Riley: { bg: "bg-pink-500/10", text: "text-pink-400", border: "border-l-pink-500" },
  Moderator: { bg: "bg-neutral-500/10", text: "text-white", border: "border-l-neutral-500" },
};

const getAgentColor = (name: string) => {
  return agentColors[name] || { bg: "bg-neutral-500/10", text: "text-neutral-400", border: "border-l-neutral-500" };
};

// Section configuration for synthesis parsing
const sectionConfig = [
  { key: "Synthesis", icon: "○", color: "text-neutral-400", borderColor: "border-neutral-700" },
  { key: "Points of Agreement", icon: "○", color: "text-emerald-400", borderColor: "border-emerald-900" },
  { key: "Points of Contention", icon: "○", color: "text-amber-400", borderColor: "border-amber-900" },
  { key: "Key Insights", icon: "○", color: "text-blue-400", borderColor: "border-blue-900" },
  { key: "Conclusion", icon: "○", color: "text-purple-400", borderColor: "border-purple-900" },
  { key: "Confidence", icon: "○", color: "text-pink-400", borderColor: "border-pink-900" },
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
  const sections: { title: string; content: string[]; icon: string; color: string; borderColor: string }[] = [];
  
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
        borderColor: config.borderColor,
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
    <div className="space-y-3">
      {sections.map((section, idx) => (
        <div key={idx} className={`border-l-2 ${section.borderColor} pl-4 py-2`}>
          <div className="flex items-center gap-2 mb-2">
            <h4 className={`text-xs font-medium uppercase tracking-wider ${section.color}`}>{section.title}</h4>
          </div>
          
          {section.content.length === 1 ? (
            <p className="text-neutral-400 leading-relaxed text-sm">
              {section.content[0]}
            </p>
          ) : (
            <ul className="space-y-1.5">
              {section.content.map((bullet, bulletIdx) => (
                <li key={bulletIdx} className="text-neutral-400 text-sm leading-relaxed flex items-start gap-2">
                  <span className={`mt-2 w-1 h-1 rounded-full flex-shrink-0 ${section.color.replace('text-', 'bg-')}`} />
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
          className="text-center mb-12"
        >
          <h1 className="text-3xl md:text-4xl font-medium tracking-tight text-white mb-2">
            discourse
          </h1>
          <p className="text-neutral-500 text-sm tracking-wide">
            multi-agent debate
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6 mb-8"
        >
          {/* Topic Input */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Topic
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isLoading && startDebate()}
                placeholder="What should we debate?"
                className="flex-1 px-4 py-3 bg-black rounded-md border border-neutral-800 focus:border-neutral-600 text-white placeholder-neutral-600 transition-colors"
                disabled={isLoading}
              />
              <button
                onClick={startDebate}
                disabled={isLoading}
                className="px-6 py-3 bg-white text-black hover:bg-neutral-200 disabled:bg-neutral-800 disabled:text-neutral-500 disabled:cursor-not-allowed rounded-md font-medium transition-colors"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Running
                  </span>
                ) : (
                  "Start"
                )}
              </button>
            </div>
          </div>

          {/* Sample Topics */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Suggestions
            </label>
            <div className="flex flex-wrap gap-2">
              {sampleTopics.map((sampleTopic) => (
                <button
                  key={sampleTopic}
                  onClick={() => setTopic(sampleTopic)}
                  className="px-3 py-1.5 text-xs text-neutral-400 border border-neutral-800 hover:border-neutral-600 hover:text-white rounded-md transition-colors"
                >
                  {sampleTopic}
                </button>
              ))}
            </div>
          </div>

          {/* Agent Selection */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Agents
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries({
                optimist: { name: "Alex", label: "Optimist" },
                skeptic: { name: "Morgan", label: "Skeptic" },
                pragmatist: { name: "Jordan", label: "Pragmatist" },
                innovator: { name: "Sam", label: "Innovator" },
                veteran: { name: "Casey", label: "Veteran" },
                devils_advocate: { name: "Riley", label: "Contrarian" },
              }).map(([key, { name, label }]) => {
                const isSelected = selectedTemplates.includes(key);
                const colors = getAgentColor(name);
                return (
                  <button
                    key={key}
                    onClick={() => toggleTemplate(key)}
                    className={`px-3 py-2 rounded-md text-xs font-medium transition-all ${
                      isSelected
                        ? `${colors.bg} ${colors.text} border border-current`
                        : "border border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-300"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Rounds Selection */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Rounds
            </label>
            <div className="flex gap-2">
              {[1, 2, 3].map((num) => (
                <button
                  key={num}
                  onClick={() => setRounds(num)}
                  className={`px-4 py-2 rounded-md text-xs font-medium transition-colors ${
                    rounds === num
                      ? "bg-white text-black"
                      : "border border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-300"
                  }`}
                >
                  {num}
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
              className="mb-6 p-4 border border-neutral-800 rounded-md text-neutral-400"
            >
              <span className="text-red-400">{error}</span>
              <p className="text-xs mt-2 text-neutral-600">
                Backend: <code className="text-neutral-500">uvicorn server:app --reload --port 8000</code>
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Debate Display */}
        {argumentEntries.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card p-6"
          >
            {/* Debate Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-neutral-800">
              <div>
                <h2 className="text-lg font-medium text-white">
                  {debates.find((d) => d.type === "start")?.topic || topic}
                </h2>
                <p className="text-xs text-neutral-500 mt-1">
                  {isLoading ? `Round ${currentRound}` : "Complete"}
                </p>
              </div>
              {!isLoading && (
                <div className="text-xs text-neutral-600">
                  {argumentEntries.length} responses
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
                      className={`p-4 rounded-md border-l-2 ${
                        isSynthesis
                          ? "bg-neutral-900/30 border-l-neutral-600"
                          : `${colors.border}`
                      }`}
                    >
                      {/* Agent Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`text-sm font-medium ${isSynthesis ? "text-white" : colors.text}`}>
                          {entry.agent}
                        </div>
                        <div className="text-xs text-neutral-600">
                          {entry.role} {!isSynthesis && `· R${entry.round}`}
                        </div>
                      </div>

                      {/* Message */}
                      {isSynthesis ? (
                        <div className="mt-2">
                          <SynthesisCard message={entry.message || ""} />
                        </div>
                      ) : (
                        <p className="text-neutral-400 text-sm leading-relaxed">
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
                  className="flex items-center gap-3 p-4 border border-neutral-800 rounded-md"
                >
                  <div className="flex gap-1">
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                  </div>
                  <span className="text-neutral-500 text-xs">Thinking...</span>
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
            className="text-center py-20"
          >
            <p className="text-neutral-600 text-sm">Enter a topic to begin</p>
          </motion.div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-xs text-neutral-700">
          Local AI · No external data
        </div>
      </div>
    </main>
  );
}
