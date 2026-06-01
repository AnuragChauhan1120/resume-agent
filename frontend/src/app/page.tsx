"use client";

import { useState, useRef } from "react";

const API = "http://localhost:8000";

type Tab = "upload" | "ask" | "jobs" | "improve";

interface Job {
  title: string;
  url: string;
  snippet: string;
  query_used: string;
}

interface ChunkResult {
  score: number;
  text: string;
  section: string;
  filename: string;
}

interface AskResponse {
  question: string;
  answer: string;
  sources: ChunkResult[];
}

export default function Home() {
  const [tab, setTab] = useState<Tab>("upload");
  const [filename, setFilename] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<any>(null);

  // Ask state
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askResult, setAskResult] = useState<AskResponse | null>(null);

  // Jobs state
  const [findingJobs, setFindingJobs] = useState(false);
  const [jobResult, setJobResult] = useState<any>(null);

  // Improve state
  const [jobDesc, setJobDesc] = useState("");
  const [improving, setImproving] = useState(false);
  const [improveResult, setImproveResult] = useState<any>(null);

  const fileRef = useRef<HTMLInputElement>(null);

async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
  const file = e.target.files?.[0];
  if (!file) return;
  setUploading(true);
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch(`${API}/resume/upload`, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) {
      alert(data.detail);
      return;           // stops here, never reaches setTab
    }
    setFilename(data.filename);
    setUploadInfo(data);
    setTab("ask");      // only runs on success
  } catch (err) {
    alert("Upload failed");
  } finally {
    setUploading(false);
  }
}

  async function handleAsk() {
    if (!question.trim() || !filename) return;
    setAsking(true);
    setAskResult(null);
    try {
      const res = await fetch(`${API}/resume/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, filename, top_k: 3 }),
      });
      const data = await res.json();
      setAskResult(data);
    } catch (err) {
      alert("Ask failed");
    } finally {
      setAsking(false);
    }
  }

  async function handleFindJobs() {
    if (!filename) return;
    setFindingJobs(true);
    setJobResult(null);
    try {
      const res = await fetch(`${API}/resume/find-jobs?filename=${filename}`, { method: "POST" });
      const data = await res.json();
      setJobResult(data);
    } catch (err) {
      alert("Job search failed");
    } finally {
      setFindingJobs(false);
    }
  }

  async function handleImprove() {
    if (!filename || !jobDesc.trim()) return;
    setImproving(true);
    setImproveResult(null);
    try {
      const res = await fetch(`${API}/resume/improve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, job_description: jobDesc }),
      });
      const data = await res.json();
      setImproveResult(data);
    } catch (err) {
      alert("Improve failed");
    } finally {
      setImproving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white font-mono">
      {/* Header */}
      <div className="border-b border-zinc-800 px-8 py-5 flex items-center justify-between">
        <div>
          <span className="text-green-400 text-xs tracking-widest uppercase">resume</span>
          <h1 className="text-xl font-bold tracking-tight">agent_</h1>
        </div>
        {filename && (
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
            {filename}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-zinc-800 px-8 flex gap-0">
        {(["upload", "ask", "jobs", "improve"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-3 text-xs tracking-widest uppercase transition-all border-b-2 ${
              tab === t
                ? "border-green-400 text-green-400"
                : "border-transparent text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="px-8 py-8 max-w-3xl">
        {/* UPLOAD TAB */}
        {tab === "upload" && (
          <div>
            <p className="text-zinc-500 text-sm mb-8">drop your resume to get started</p>
            <div
              onClick={() => fileRef.current?.click()}
              className="border border-dashed border-zinc-700 rounded p-16 text-center cursor-pointer hover:border-green-400 hover:bg-zinc-900 transition-all group"
            >
              <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">📄</div>
              <p className="text-zinc-400 text-sm">
                {uploading ? "uploading..." : "click to upload PDF"}
              </p>
              <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
            </div>

            {uploadInfo && (
              <div className="mt-8 border border-zinc-800 rounded p-6 space-y-2">
                <p className="text-green-400 text-xs tracking-widest uppercase mb-4">upload complete</p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-zinc-500 text-xs">chunks created</p>
                    <p className="text-white font-bold">{uploadInfo.num_chunks}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-xs">sections found</p>
                    <p className="text-white font-bold">{uploadInfo.sections_found?.join(", ")}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ASK TAB */}
        {tab === "ask" && (
          <div>
            <p className="text-zinc-500 text-sm mb-8">ask anything about your resume</p>
            {!filename && <p className="text-red-400 text-sm">upload a resume first</p>}
            <div className="flex gap-3">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAsk()}
                placeholder="what are my strongest skills?"
                className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-4 py-3 text-sm focus:outline-none focus:border-green-400 placeholder-zinc-600"
              />
              <button
                onClick={handleAsk}
                disabled={asking || !filename}
                className="px-5 py-3 bg-green-400 text-black text-sm font-bold rounded hover:bg-green-300 disabled:opacity-40 transition-all"
              >
                {asking ? "..." : "ask"}
              </button>
            </div>

            {askResult && (
              <div className="mt-8 space-y-6">
                <div className="border border-zinc-800 rounded p-6">
                  <p className="text-green-400 text-xs tracking-widest uppercase mb-3">answer</p>
                  <p className="text-zinc-200 text-sm leading-relaxed whitespace-pre-wrap">{askResult.answer}</p>
                </div>

                <div className="border border-zinc-800 rounded p-6">
                  <p className="text-zinc-500 text-xs tracking-widest uppercase mb-4">sources</p>
                  <div className="space-y-3">
                    {askResult.sources.map((s, i) => (
                      <div key={i} className="border border-zinc-800 rounded p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs text-zinc-400 uppercase">{s.section}</span>
                          <span className="text-xs text-green-400">{(s.score * 100).toFixed(0)}% match</span>
                        </div>
                        <p className="text-zinc-500 text-xs leading-relaxed line-clamp-3">{s.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* JOBS TAB */}
        {tab === "jobs" && (
          <div>
            <p className="text-zinc-500 text-sm mb-8">find jobs matching your resume</p>
            {!filename && <p className="text-red-400 text-sm">upload a resume first</p>}
            <button
              onClick={handleFindJobs}
              disabled={findingJobs || !filename}
              className="px-6 py-3 bg-green-400 text-black text-sm font-bold rounded hover:bg-green-300 disabled:opacity-40 transition-all"
            >
              {findingJobs ? "searching..." : "find matching jobs"}
            </button>
             {jobResult && jobResult.jobs.length === 0 && (
                <p className="mt-4 text-yellow-400 text-sm">
                  No jobs found. Make sure you uploaded a resume PDF.
                </p>
              )}

            {jobResult && (
              <div className="mt-8 space-y-4">
                <div className="border border-zinc-800 rounded p-4">
                  <p className="text-zinc-500 text-xs uppercase tracking-widest mb-2">profile extracted</p>
                  <p className="text-zinc-300 text-xs whitespace-pre-wrap">{jobResult.profile}</p>
                </div>

                <p className="text-green-400 text-xs tracking-widest uppercase">{jobResult?.jobs?.length ?? 0} jobs found</p>

                {jobResult.jobs.map((job: Job, i: number) => (
                  <div key={i} className="border border-zinc-800 rounded p-5 hover:border-zinc-600 transition-all">
                    <a href={job.url} target="_blank" rel="noopener noreferrer"
                      className="text-white text-sm font-bold hover:text-green-400 transition-colors">
                      {job.title}
                    </a>
                    <p className="text-zinc-500 text-xs mt-2 leading-relaxed">{job.snippet}</p>
                    <p className="text-zinc-600 text-xs mt-3">via: {job.query_used}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* IMPROVE TAB */}
        {tab === "improve" && (
          <div>
            <p className="text-zinc-500 text-sm mb-8">paste a job description to improve your resume</p>
            {!filename && <p className="text-red-400 text-sm">upload a resume first</p>}
            <textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="paste job description here..."
              rows={8}
              className="w-full bg-zinc-900 border border-zinc-700 rounded px-4 py-3 text-sm focus:outline-none focus:border-green-400 placeholder-zinc-600 resize-none"
            />
            <button
              onClick={handleImprove}
              disabled={improving || !filename || !jobDesc.trim()}
              className="mt-4 px-6 py-3 bg-green-400 text-black text-sm font-bold rounded hover:bg-green-300 disabled:opacity-40 transition-all"
            >
              {improving ? "analyzing..." : "analyze & improve"}
            </button>

            {improveResult && (
              <div className="mt-8 space-y-6">
                {[
                  { label: "gap analysis", key: "gap_analysis" },
                  { label: "suggestions", key: "suggestions" },
                  { label: "rewritten experience", key: "rewritten_experience" },
                ].map(({ label, key }) => (
                  <div key={key} className="border border-zinc-800 rounded p-6">
                    <p className="text-green-400 text-xs tracking-widest uppercase mb-3">{label}</p>
                    <p className="text-zinc-300 text-sm leading-relaxed whitespace-pre-wrap">{improveResult[key]}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}