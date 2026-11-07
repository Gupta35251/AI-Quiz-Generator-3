// import React from "react";
// import { useEffect, useMemo, useState } from "react";
// import {
//   Activity, ArrowLeft, ArrowRight, BookOpen, Brain, Check, CheckCircle2,
//   ChevronDown, CircleHelp, Clock3, Code2, FileText, Flame, History,
//   LayoutDashboard, LoaderCircle, Menu, RotateCcw, Sparkles, Target,
//   Trophy, XCircle, Zap,
// } from "lucide-react";
// import {
//   api,
//   saveLogin,
//   clearLogin,
//   getSavedUser,
// } from "./api.js";

// const TYPE_LABELS = {
//   mcq: "Multiple choice",
//   multiple_answer: "Select all that apply",
//   code: "Coding",
//   theory: "Theory",
// };

// function formatDate(value) {
//   if (!value) return "Unknown date";
//   const date = new Date(value);
//   return Number.isNaN(date.getTime())
//     ? value
//     : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
// }

// function App() {
//   const [user, setUser] = useState(getSavedUser);
//   const [authMode, setAuthMode] = useState("login");
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const [authLoading, setAuthLoading] = useState(false);
//   const [page, setPage] = useState("create");
//   const [view, setView] = useState("setup");
//   const [content, setContent] = useState("");
//   const [count, setCount] = useState(5);
//   const [level, setLevel] = useState("medium");
//   const [sessionId, setSessionId] = useState(null);
//   const [quiz, setQuiz] = useState(null);
//   const [answers, setAnswers] = useState({});
//   const [results, setResults] = useState([]);
//   const [score, setScore] = useState(0);
//   const [history, setHistory] = useState([]);
//   const [historyDetail, setHistoryDetail] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [questionIndex, setQuestionIndex] = useState(0);
//   const [mobileMenu, setMobileMenu] = useState(false);
//   const [apiOnline, setApiOnline] = useState(false);

//   async function handleAuth(event) {
//   event.preventDefault();
//   setError("");
//   setAuthLoading(true);

//   try {
//     const data =
//       authMode === "login"
//         ? await api.login({ email, password })
//         : await api.signup({ email, password });

//     saveLogin(data);
//     setUser(data.user);
//     setEmail("");
//     setPassword("");
//   } catch (err) {
//     setError(err.message);
//   } finally {
//     setAuthLoading(false);
//   }
// }

// function handleLogout() {
//   clearLogin();
//   setUser(null);
//   setPassword("");
//   setPage("create");
//   setView("setup");
//   setHistory([]);
//   setHistoryDetail(null);
//   setQuiz(null);
//   setResults([]);
//   setError("");
// }
//   useEffect(() => {
//   function handleSessionExpired() {
//     setUser(null);
//     setPage("create");
//     setView("setup");
//     setError("Your session expired. Please log in again.");
//   }

//   window.addEventListener("quizwise:logout", handleSessionExpired);

//   return () => {
//     window.removeEventListener(
//       "quizwise:logout",
//       handleSessionExpired
//     );
//   };
//   }, []);

//   useEffect(() => {
//     api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
//   }, []);

//   const currentQuestion = quiz?.questions?.[questionIndex];
//   const currentAnswers = answers[questionIndex] || [];
//   const percentage = results.length ? Math.round((score / results.length) * 100) : 0;

//   const completedCount = useMemo(
//     () => quiz?.questions?.filter((_, i) => (answers[i] || []).some((a) => a.trim())).length || 0,
//     [quiz, answers]
//   );

//   async function loadHistory() {
//     setLoading(true);
//     setError("");
//     try {
//       const data = await api.history();
//       setHistory(data.items || []);
//       setPage("history");
//       setView("history");
//       setHistoryDetail(null);
//     } catch (e) {
//       setError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   }

//   async function startQuiz(event) {
//     event.preventDefault();
//     setError("");
//     if (!content.trim()) {
//       setError("Add a topic or describe what you learned first.");
//       return;
//     }
//     setLoading(true);
//     try {
//       const data = await api.generateQuiz({
//         content: content.trim(),
//         no_of_questions: Number(count),
//         level,
//       });
//       setQuiz(data.quiz);
//       setSessionId(data.session_id);
//       setAnswers({});
//       setResults([]);
//       setScore(0);
//       setQuestionIndex(0);
//       setView("taking");
//       setPage("create");
//     } catch (e) {
//       setError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   }

//   function setSingleAnswer(value) {
//     setAnswers((old) => ({ ...old, [questionIndex]: [value] }));
//   }

//   function toggleMultipleAnswer(value) {
//     setAnswers((old) => {
//       const selected = old[questionIndex] || [];
//       const next = selected.includes(value)
//         ? selected.filter((item) => item !== value)
//         : [...selected, value];
//       return { ...old, [questionIndex]: next };
//     });
//   }

//   async function submitQuiz() {
//     setError("");
//     setLoading(true);
//     try {
//       const data = await api.submitQuiz({
//         session_id: sessionId,
//         answers: quiz.questions.map((_, i) => answers[i] || []),
//       });
//       setResults(data.results || []);
//       setScore(data.score || 0);
//       setView("results");
//       setPage("create");
//     } catch (e) {
//       setError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   }

//   async function openHistoryItem(id) {
//     setError("");
//     setLoading(true);
//     try {
//       const data = await api.historyItem(id);
//       setHistoryDetail(data);
//       setView("historyDetail");
//     } catch (e) {
//       setError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   }

//   function goCreate() {
//     setPage("create");
//     setView("setup");
//     setError("");
//     setMobileMenu(false);
//   }

//   const nav = (
//     <>
//       <button className={`nav-item ${page === "create" ? "active" : ""}`} onClick={goCreate}>
//         <LayoutDashboard size={18} /> <span>New quiz</span>
//       </button>
//       <button className={`nav-item ${page === "history" ? "active" : ""}`} onClick={() => { loadHistory(); setMobileMenu(false); }}>
//         <History size={18} /> <span>Quiz history</span>
//       </button>
//     </>
//   );

//   return (
//     if (!user) {
//       return (
//         <div className="auth-page">
//           <div className="auth-card">
//             <div className="auth-logo">
//               <Brain size={28} />
//             </div>

//             <h1>Welcome to Quizwise</h1>
//             <p>Your personal AI-powered learning space.</p>

//             <div className="auth-tabs">
//               <button
//                 type="button"
//                 className={authMode === "login" ? "selected" : ""}
//                 onClick={() => {
//                   setAuthMode("login");
//                   setError("");
//                 }}
//               >
//                 Log in
//               </button>

//               <button
//                 type="button"
//                 className={authMode === "signup" ? "selected" : ""}
//                 onClick={() => {
//                   setAuthMode("signup");
//                   setError("");
//                 }}
//               >
//                 Sign up
//               </button>
//             </div>

//             {error && (
//               <div className="error-banner" role="alert">
//                 {error}
//               </div>
//             )}

//             <form onSubmit={handleAuth}>
//               <label className="field-label" htmlFor="auth-email">
//                 Email address
//               </label>

//               <input
//                 id="auth-email"
//                 type="email"
//                 autoComplete="email"
//                 value={email}
//                 onChange={(e) => setEmail(e.target.value)}
//                 required
//               />

//               <label className="field-label" htmlFor="auth-password">
//                 Password
//               </label>

//               <input
//                 id="auth-password"
//                 type="password"
//                 autoComplete={
//                   authMode === "login"
//                     ? "current-password"
//                     : "new-password"
//                 }
//                 value={password}
//                 onChange={(e) => setPassword(e.target.value)}
//                 minLength={authMode === "signup" ? 8 : 1}
//                 required
//               />

//               {authMode === "signup" && (
//                 <small>
//                   Use at least 8 characters, including a letter and a number.
//                 </small>
//               )}

//               <button
//                 className="primary-button auth-submit"
//                 type="submit"
//                 disabled={authLoading}
//               >
//                 {authLoading
//                   ? "Please wait..."
//                   : authMode === "login"
//                     ? "Log in"
//                     : "Create account"}
//               </button>
//             </form>

//             <p className="auth-switch">
//               {authMode === "login"
//                 ? "New to Quizwise?"
//                 : "Already have an account?"}{" "}
//               <button
//                 type="button"
//                 onClick={() => {
//                   setAuthMode(
//                     authMode === "login" ? "signup" : "login"
//                   );
//                   setError("");
//                 }}
//               >
//                 {authMode === "login" ? "Sign up" : "Log in"}
//               </button>
//             </p>
//           </div>
//         </div>
//       );
//     }
//     <div className="app-shell">
//       <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
//         <button className="brand" onClick={goCreate} aria-label="Quizwise home">
//           <span className="brand-mark"><Brain size={22} /></span>
//           <span>quizwise<span className="brand-dot">.</span><small>YOUR LEARNING SPACE</small></span>
//         </button>
//         <div className="side-label">WORKSPACE</div>
//         <nav>{nav}</nav>
//         <div className="sidebar-spacer" />
//         <div className="side-tip">
//           <div className="tip-icon"><Sparkles size={17} /></div>
//           <strong>Little by little.</strong>
//           <p>Every question is a chance to understand something better.</p>
//         </div>
//         <div className="sidebar-footer">
//           <span className={`status-dot ${apiOnline ? "online" : ""}`} />
//           <span>{apiOnline ? "Backend connected" : "Backend not connected"}</span>
//         </div>
//       </aside>

//       {mobileMenu && <button className="mobile-scrim" onClick={() => setMobileMenu(false)} aria-label="Close menu" />}

//       <main className="main-area">
//         <header className="topbar">
//           <button className="icon-button mobile-menu-button" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Toggle menu"><Menu size={20} /></button>
//           <div className="breadcrumb">Workspace <span>/</span> <strong>{page === "history" ? "Quiz history" : view === "results" ? "Quiz results" : view === "taking" ? "Taking quiz" : "Create a quiz"}</strong></div>
          
// <div className="topbar-right">
//   <span className="top-pill">
//     <span className="live-dot" /> {user.email}
//   </span>
//   <button
//     className="secondary-button"
//     type="button"
//     onClick={handleLogout}
//   >
//     Log out
//   </button>
// </div>

//         </header>

//         <div className="page-content">
//           {error && (
//             <div className="error-banner" role="alert">
//               <XCircle size={18} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><XCircle size={16} /></button>
//             </div>
//           )}

//           {page === "create" && view === "setup" && (
//             <section className="setup-page">
//               <div className="welcome-row">
//                 <div>
//                   <div className="eyebrow"><Sparkles size={14} /> YOUR PERSONAL AI TUTOR</div>
//                   <h1>Learn it today.<br /><span>Know it for good.</span></h1>
//                   <p className="hero-copy">Turn what you've learned into a focused quiz. Find gaps, understand mistakes, and build real confidence.</p>
//                 </div>
//                 <div className="hero-art" aria-hidden="true">
//                   <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
//                   <div className="art-card art-card-back"><BookOpen size={21} /></div>
//                   <div className="art-card art-card-front"><Brain size={35} /><span>Think deeper</span><div className="art-bars"><i /><i /><i /><i /><i /></div></div>
//                   <div className="floating-star star-one"><Sparkles size={17} /></div>
//                   <div className="floating-star star-two"><Zap size={16} /></div>
//                 </div>
//               </div>

//               <div className="stats-strip">
//                 <div className="stat-item"><span className="stat-icon lavender"><Target size={18} /></span><div><strong>Learn your way</strong><small>Built around your topics</small></div></div>
//                 <div className="stat-item"><span className="stat-icon mint"><Activity size={18} /></span><div><strong>Understand mistakes</strong><small>Explanations that teach</small></div></div>
//                 <div className="stat-item"><span className="stat-icon peach"><History size={18} /></span><div><strong>Keep your progress</strong><small>Revisit past quizzes</small></div></div>
//               </div>

//               <form className="create-card" onSubmit={startQuiz}>
//                 <div className="section-heading">
//                   <div><span className="step-tag">01</span><h2>Create your quiz</h2></div>
//                   <span className="required-note">All fields required</span>
//                 </div>
//                 <label className="field-label" htmlFor="topic">What have you been learning?</label>
//                 <textarea id="topic" className="topic-input" rows="3" value={content} onChange={(e) => setContent(e.target.value)} placeholder="e.g. Python functions, loops, and lists — focus on the basics and common mistakes..." />
//                 <div className="field-hint"><CircleHelp size={14} /> Add a topic, notes, or concepts you want to practise.</div>

//                 <div className="form-grid">
//                   <div>
//                     <label className="field-label" htmlFor="count">Number of questions</label>
//                     <div className="count-control">
//                       <button type="button" onClick={() => setCount((n) => Math.max(1, Number(n) - 1))} aria-label="Decrease questions">−</button>
//                       <input id="count" type="number" min="1" max="30" value={count} onChange={(e) => setCount(Math.min(30, Math.max(1, Number(e.target.value) || 1)))} />
//                       <button type="button" onClick={() => setCount((n) => Math.min(30, Number(n) + 1))} aria-label="Increase questions">+</button>
//                     </div>
//                     <div className="field-hint">Choose between 1 and 30</div>
//                   </div>
//                   <div>
//                     <label className="field-label">Difficulty level</label>
//                     <div className="level-options">
//                       {[
//                         { value: "easy", label: "Easy", note: "Build basics", icon: "🌱" },
//                         { value: "medium", label: "Medium", note: "Apply ideas", icon: "⚡" },
//                         { value: "hard", label: "Hard", note: "Go deeper", icon: "🔥" },
//                       ].map((item) => (
//                         <button type="button" key={item.value} className={`level-card ${level === item.value ? "selected" : ""}`} onClick={() => setLevel(item.value)}>
//                           <span>{item.icon}</span><strong>{item.label}</strong><small>{item.note}</small>{level === item.value && <Check size={14} className="level-check" />}
//                         </button>
//                       ))}
//                     </div>
//                   </div>
//                 </div>
//                 <button className="primary-button create-button" type="submit" disabled={loading}>
//                   {loading ? <><LoaderCircle className="spin" size={18} /> Creating your quiz...</> : <><Sparkles size={18} /> Generate my quiz <ArrowRight size={17} /></>}
//                 </button>
//                 <p className="privacy-note"><Zap size={13} /> AI-generated practice, made for your learning goals.</p>
//               </form>
//             </section>
//           )}

//           {page === "create" && view === "taking" && currentQuestion && (
//             <section className="quiz-page">
//               <button className="back-link" onClick={() => { setView("setup"); setError(""); }}><ArrowLeft size={16} /> Leave quiz</button>
//               <div className="quiz-header">
//                 <div><div className="eyebrow"><BookOpen size={14} /> YOUR PRACTICE SESSION</div><h1>{quiz.topic}</h1><p>Take your time. Focus on what you understand.</p></div>
//                 <div className="question-count"><strong>{questionIndex + 1}<span> / {quiz.questions.length}</span></strong><small>QUESTION</small></div>
//               </div>
//               <div className="progress-track"><div style={{ width: `${((questionIndex + 1) / quiz.questions.length) * 100}%` }} /></div>
//               <div className="quiz-layout">
//                 <div className="question-card">
//                   <div className="question-meta"><span className="question-number">QUESTION {String(questionIndex + 1).padStart(2, "0")}</span><span className={`type-pill type-${currentQuestion.type}`}>{TYPE_LABELS[currentQuestion.type] || currentQuestion.type}</span></div>
//                   <h2>{currentQuestion.question}</h2>
//                   {currentQuestion.type === "mcq" && currentQuestion.options?.length > 0 && (
//                     <div className="answer-options">
//                       {currentQuestion.options.map((option, i) => (
//                         <button type="button" key={option} className={`answer-option ${currentAnswers.includes(option) ? "chosen" : ""}`} onClick={() => setSingleAnswer(option)}>
//                           <span className="option-letter">{String.fromCharCode(65 + i)}</span><span>{option}</span>{currentAnswers.includes(option) && <CheckCircle2 className="option-check" size={18} />}
//                         </button>
//                       ))}
//                     </div>
//                   )}
//                   {currentQuestion.type === "multiple_answer" && currentQuestion.options?.length > 0 && (
//                     <>
//                       <p className="select-hint">Select every answer you think is correct.</p>
//                       <div className="answer-options">
//                         {currentQuestion.options.map((option, i) => (
//                           <button type="button" key={option} className={`answer-option ${currentAnswers.includes(option) ? "chosen" : ""}`} onClick={() => toggleMultipleAnswer(option)}>
//                             <span className={`option-letter checkbox-letter ${currentAnswers.includes(option) ? "checked" : ""}`}>{currentAnswers.includes(option) ? <Check size={14} /> : String.fromCharCode(65 + i)}</span><span>{option}</span>
//                           </button>
//                         ))}
//                       </div>
//                     </>
//                   )}
//                   {(currentQuestion.type === "code" || currentQuestion.type === "theory" || !currentQuestion.options?.length) && (
//                     <div className="written-answer">
//                       <label className="field-label" htmlFor="written-answer">{currentQuestion.type === "code" ? "Write your code or answer" : "Your answer"}</label>
//                       <textarea id="written-answer" rows={currentQuestion.type === "code" ? 7 : 5} value={currentAnswers[0] || ""} onChange={(e) => setSingleAnswer(e.target.value)} placeholder={currentQuestion.type === "code" ? "Write your code here..." : "Explain your answer in your own words..."} />
//                     </div>
//                   )}
//                   <div className="question-footer">
//                     <button className="secondary-button" disabled={questionIndex === 0} onClick={() => setQuestionIndex((i) => i - 1)}><ArrowLeft size={16} /> Previous</button>
//                     {questionIndex < quiz.questions.length - 1 ? (
//                       <button className="primary-button" onClick={() => setQuestionIndex((i) => i + 1)}>Next question <ArrowRight size={16} /></button>
//                     ) : (
//                       <button className="primary-button" disabled={loading} onClick={submitQuiz}>{loading ? <LoaderCircle size={17} className="spin" /> : <CheckCircle2 size={17} />} Submit quiz</button>
//                     )}
//                   </div>
//                 </div>
//                 <aside className="quiz-side-card">
//                   <div className="side-card-icon"><Target size={20} /></div><h3>Stay curious</h3><p>It's okay if you're unsure. Your results will help you find what to practise next.</p>
//                   <div className="mini-progress"><div><span>Answered</span><strong>{completedCount}/{quiz.questions.length}</strong></div><div className="mini-track"><div style={{ width: `${(completedCount / quiz.questions.length) * 100}%` }} /></div></div>
//                   <div className="question-jump"><span>JUMP TO QUESTION</span><div>{quiz.questions.map((_, i) => <button key={i} className={`${i === questionIndex ? "current" : ""} ${(answers[i] || []).some((a) => a.trim()) ? "answered" : ""}`} onClick={() => setQuestionIndex(i)}>{i + 1}</button>)}</div></div>
//                 </aside>
//               </div>
//             </section>
//           )}

//           {page === "create" && view === "results" && (
//             <section className="results-page">
//               <div className="results-hero">
//                 <div className="result-trophy"><Trophy size={34} /></div>
//                 <div className="eyebrow">QUIZ COMPLETE</div>
//                 <h1>{percentage >= 80 ? "Fantastic work!" : percentage >= 50 ? "Good progress!" : "Every attempt teaches you."}</h1>
//                 <p>You finished <strong>{quiz?.topic}</strong>. Review the explanations below to make the concepts stick.</p>
//                 <div className="score-ring" style={{ "--score": `${percentage}%` }}><div><strong>{percentage}%</strong><small>YOUR SCORE</small></div></div>
//                 <div className="result-stats"><div><strong>{score}/{results.length}</strong><span>Correct answers</span></div><div><strong>{results.length - score}</strong><span>To review</span></div><div><strong>{quiz?.questions.length || 0}</strong><span>Total questions</span></div></div>
//               </div>
//               <div className="results-heading"><div><div className="eyebrow">LEARN FROM EVERY ANSWER</div><h2>Answer review</h2></div><button className="secondary-button" onClick={goCreate}><RotateCcw size={16} /> New quiz</button></div>
//               <div className="review-list">
//                 {results.map((result, i) => (
//                   <article className={`review-card ${result.is_correct ? "review-correct" : "review-wrong"}`} key={`${i}-${result.question}`}>
//                     <div className="review-status">{result.is_correct ? <CheckCircle2 size={19} /> : <XCircle size={19} />}</div>
//                     <div className="review-body"><div className="review-kicker">QUESTION {String(i + 1).padStart(2, "0")} · {result.is_correct ? "CORRECT" : "KEEP PRACTISING"}</div><h3>{result.question}</h3>
//                       <div className="answer-comparison"><div><span>Your answer</span><p>{(result.user_answer || []).join(", ") || "No answer provided"}</p></div><div><span>Correct answer</span><p>{(result.correct_answer || []).join(", ")}</p></div></div>
//                       <div className="explanation"><Sparkles size={16} /><div><strong>Explanation</strong><p>{result.description}</p></div></div>
//                     </div>
//                   </article>
//                 ))}
//               </div>
//               <div className="bottom-cta"><div><strong>Ready to keep learning?</strong><p>A short practice session can make a big difference.</p></div><button className="primary-button" onClick={goCreate}>Create another quiz <ArrowRight size={16} /></button></div>
//             </section>
//           )}

//           {page === "history" && view === "history" && (
//             <section className="history-page">
//               <div className="page-title-row"><div><div className="eyebrow"><History size={14} /> YOUR LEARNING JOURNEY</div><h1>Quiz history</h1><p>Every attempt is progress. Revisit what you've practised.</p></div><button className="primary-button" onClick={goCreate}><Sparkles size={17} /> New quiz</button></div>
//               <div className="history-summary"><div className="history-summary-icon"><BookOpen size={20} /></div><div><strong>{history.length} saved {history.length === 1 ? "quiz" : "quizzes"}</strong><p>Your completed practice sessions, all in one place.</p></div></div>
//               {loading && !history.length ? <div className="loading-state"><LoaderCircle className="spin" size={25} /><span>Loading your history...</span></div> : history.length === 0 ? (
//                 <div className="empty-state"><div><History size={28} /></div><h2>Your learning story starts here</h2><p>Complete your first quiz and it will appear here for future review.</p><button className="primary-button" onClick={goCreate}>Create your first quiz <ArrowRight size={16} /></button></div>
//               ) : (
//                 <div className="history-table">
//                   <div className="history-table-head"><span>QUIZ TOPIC</span><span>DATE</span><span>SCORE</span><span /></div>
//                   {history.map((item) => <button className="history-row" key={item.id} onClick={() => openHistoryItem(item.id)}>
//                     <span className="history-topic"><span className="history-topic-icon"><BookOpen size={17} /></span><span><strong>{item.topic || "Quiz"}</strong><small>{item.question_count} questions</small></span></span>
//                     <span className="history-date">{formatDate(item.date)}</span>
//                     <span className="history-score"><strong>{item.score}/{item.total}</strong><small>{item.total ? Math.round((item.score / item.total) * 100) : 0}%</small></span>
//                     <span className="history-open"><ArrowRight size={17} /></span>
//                   </button>)}
//                 </div>
//               )}
//             </section>
//           )}

//           {page === "history" && view === "historyDetail" && historyDetail && (
//             <section className="results-page">
//               <button className="back-link" onClick={() => { setView("history"); setHistoryDetail(null); }}><ArrowLeft size={16} /> Back to history</button>
//               <div className="page-title-row detail-title"><div><div className="eyebrow">PAST QUIZ · {formatDate(historyDetail.date)}</div><h1>{historyDetail.quiz.topic}</h1><p>Review your answers and the explanations from this attempt.</p></div><div className="detail-score"><strong>{historyDetail.score}/{historyDetail.results.length}</strong><span>Score</span></div></div>
//               <div className="review-list">
//                 {historyDetail.results.map((result, i) => (
//                   <article className={`review-card ${result.is_correct ? "review-correct" : "review-wrong"}`} key={`${i}-${result.question}`}>
//                     <div className="review-status">{result.is_correct ? <CheckCircle2 size={19} /> : <XCircle size={19} />}</div>
//                     <div className="review-body"><div className="review-kicker">QUESTION {String(i + 1).padStart(2, "0")} · {result.is_correct ? "CORRECT" : "KEEP PRACTISING"}</div><h3>{result.question}</h3>
//                       <div className="answer-comparison"><div><span>Your answer</span><p>{(result.user_answer || []).join(", ") || "No answer provided"}</p></div><div><span>Correct answer</span><p>{(result.correct_answer || []).join(", ")}</p></div></div>
//                       <div className="explanation"><Sparkles size={16} /><div><strong>Explanation</strong><p>{result.description}</p></div></div>
//                     </div>
//                   </article>
//                 ))}
//               </div>
//             </section>
//           )}
//         </div>
//       </main>
//     </div>
//   );
// }

// export default App;

import React from "react";
import { useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowLeft, ArrowRight, BookOpen, Brain, Check, CheckCircle2,
  ChevronDown, CircleHelp, Clock3, Code2, FileText, Flame, History,
  LayoutDashboard, LoaderCircle, Menu, RotateCcw, Sparkles, Search, Target,
  Trophy, XCircle, Zap,
} from "lucide-react";
import {
  api,
  saveLogin,
  clearLogin,
  getSavedUser,
  subscribeToAuth,
} from "./api.js";

const TYPE_LABELS = {
  mcq: "Multiple choice",
  multiple_answer: "Select all that apply",
  code: "Coding",
  theory: "Theory",
};

function formatDate(value) {
  if (!value) return "Unknown date";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function App() {
  const [user, setUser] = useState(getSavedUser);
  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [page, setPage] = useState("create");
  const [view, setView] = useState("setup");
  const [content, setContent] = useState("");
  const [count, setCount] = useState(5);
  const [level, setLevel] = useState("medium");
  const [sessionId, setSessionId] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState([]);
  const [score, setScore] = useState(0);
  const [history, setHistory] = useState([]);
  const [historySearch, setHistorySearch] = useState("");
  const [historyDetail, setHistoryDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);

  async function handleAuth(event) {
  event.preventDefault();
  setError("");
  setAuthLoading(true);

  try {
    const data =
      authMode === "login"
        ? await api.login({ email, password })
        : await api.signup({ email, password });

    saveLogin(data);
    setUser(data.user);
    setEmail("");
    setPassword("");
  } catch (err) {
    setError(err.message);
  } finally {
    setAuthLoading(false);
  }
}
async function handleGoogleLogin() {
  setError("");
  setAuthLoading(true);

  try {
    const data = await api.googleLogin();
    saveLogin(data);
    setUser(data.user);
  } catch (err) {
    setError(err.message);
  } finally {
    setAuthLoading(false);
  }
}

async function handleLogout() {
  try {
    await clearLogin();
    setUser(null);
    setPassword("");
    setPage("create");
    setView("setup");
    setHistory([]);
    setHistoryDetail(null);
    setQuiz(null);
    setResults([]);
    setError("");
  } catch (err) {
    setError(err.message);
  }
}
  useEffect(() => {
  const unsubscribe = subscribeToAuth((firebaseUser) => {
    setUser(firebaseUser);

    if (firebaseUser) {
      saveLogin({ user: firebaseUser });
    } else {
      localStorage.removeItem("quizwise_user");
    }
  });

  return () => unsubscribe();
}, []);
  useEffect(() => {
  function handleSessionExpired() {
    setUser(null);
    setPage("create");
    setView("setup");
    setError("Your session expired. Please log in again.");
  }

  window.addEventListener("quizwise:logout", handleSessionExpired);

  return () => {
    window.removeEventListener(
      "quizwise:logout",
      handleSessionExpired
    );
  };
  }, []);

  useEffect(() => {
    api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
  }, []);

  const currentQuestion = quiz?.questions?.[questionIndex];
  const currentAnswers = answers[questionIndex] || [];
  const percentage = results.length ? Math.round((score / results.length) * 100) : 0;
  const filteredHistory = history.filter((item) => {
  const search = historySearch.trim().toLowerCase();

  if (!search) return true;

  const topic = item.quiz?.topic || item.topic || "";
  const questions = (item.quiz?.questions || [])
    .map((question) => question.question || "")
    .join(" ");

  const date = formatDate(item.date);
  const scoreText = `${item.score ?? 0}/${(item.results || []).length}`;

  return `${topic} ${questions} ${date} ${scoreText}`
    .toLowerCase()
    .includes(search);
});

  const completedCount = useMemo(
    () => quiz?.questions?.filter((_, i) => (answers[i] || []).some((a) => a.trim())).length || 0,
    [quiz, answers]
  );

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const data = await api.history();
      setHistory(data.items || []);
      setPage("history");
      setView("history");
      setHistoryDetail(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function startQuiz(event) {
    event.preventDefault();
    setError("");
    if (!content.trim()) {
      setError("Add a topic or describe what you learned first.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.generateQuiz({
        content: content.trim(),
        no_of_questions: Number(count),
        level,
      });
      setQuiz(data.quiz);
      setSessionId(data.session_id);
      setAnswers({});
      setResults([]);
      setScore(0);
      setQuestionIndex(0);
      setView("taking");
      setPage("create");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function setSingleAnswer(value) {
    setAnswers((old) => ({ ...old, [questionIndex]: [value] }));
  }

  function toggleMultipleAnswer(value) {
    setAnswers((old) => {
      const selected = old[questionIndex] || [];
      const next = selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value];
      return { ...old, [questionIndex]: next };
    });
  }

  async function submitQuiz() {
    setError("");
    setLoading(true);
    try {
      const data = await api.submitQuiz({
        session_id: sessionId,
        answers: quiz.questions.map((_, i) => answers[i] || []),
      });
      setResults(data.results || []);
      setScore(data.score || 0);
      setView("results");
      setPage("create");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function openHistoryItem(id) {
    setError("");
    setLoading(true);
    try {
      const data = await api.historyItem(id);
      setHistoryDetail(data);
      setView("historyDetail");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function goCreate() {
    setPage("create");
    setView("setup");
    setError("");
    setMobileMenu(false);
  }

  const nav = (
    <>
      <button className={`nav-item ${page === "create" ? "active" : ""}`} onClick={goCreate}>
        <LayoutDashboard size={18} /> <span>New quiz</span>
      </button>
      <button className={`nav-item ${page === "history" ? "active" : ""}`} onClick={() => { loadHistory(); setMobileMenu(false); }}>
        <History size={18} /> <span>Quiz history</span>
      </button>
    </>
  );

  if (!user) {
    return (
        <div className="auth-page">
          <div className="auth-card">
            <div className="auth-logo">
              <Brain size={28} />
            </div>

            <h1>Welcome to Quizwise</h1>
            <p>Your personal AI-powered learning space.</p>

            <div className="auth-tabs">
              <button
                type="button"
                className={authMode === "login" ? "selected" : ""}
                onClick={() => {
                  setAuthMode("login");
                  setError("");
                }}
              >
                Log in
              </button>

              <button
                type="button"
                className={authMode === "signup" ? "selected" : ""}
                onClick={() => {
                  setAuthMode("signup");
                  setError("");
                }}
              >
                Sign up
              </button>
            </div>

            {error && (
              <div className="error-banner" role="alert">
                {error}
              </div>
            )}

            <form onSubmit={handleAuth}>
              <label className="field-label" htmlFor="auth-email">
                Email address
              </label>

              <input
                id="auth-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <label className="field-label" htmlFor="auth-password">
                Password
              </label>

              <input
                id="auth-password"
                type="password"
                autoComplete={
                  authMode === "login"
                    ? "current-password"
                    : "new-password"
                }
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={authMode === "signup" ? 8 : 1}
                required
              />

              {authMode === "signup" && (
                <small>
                  Use at least 8 characters, including a letter and a number.
                </small>
              )}

              <button
                className="primary-button auth-submit"
                type="submit"
                disabled={authLoading}
              >
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Log in"
                    : "Create account"}
              </button>
            </form>
            <button
              type="button"
              className="secondary-button auth-submit"
              onClick={handleGoogleLogin}
              disabled={authLoading}
            >
              Continue with Google
            </button>
            <p className="auth-switch">
              {authMode === "login"
                ? "New to Quizwise?"
                : "Already have an account?"}{" "}
              <button
                type="button"
                onClick={() => {
                  setAuthMode(
                    authMode === "login" ? "signup" : "login"
                  );
                  setError("");
                }}
              >
                {authMode === "login" ? "Sign up" : "Log in"}
              </button>
            </p>
          </div>
        </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <button className="brand" onClick={goCreate} aria-label="Quizwise home">
          <span className="brand-mark"><Brain size={22} /></span>
          <span>quizwise<span className="brand-dot">.</span><small>YOUR LEARNING SPACE</small></span>
        </button>
        <div className="side-label">WORKSPACE</div>
        <nav>{nav}</nav>
        <div className="sidebar-spacer" />
        <div className="side-tip">
          <div className="tip-icon"><Sparkles size={17} /></div>
          <strong>Little by little.</strong>
          <p>Every question is a chance to understand something better.</p>
        </div>
        <div className="sidebar-footer">
          <span className={`status-dot ${apiOnline ? "online" : ""}`} />
          <span>{apiOnline ? "Backend connected" : "Backend not connected"}</span>
        </div>
      </aside>

      {mobileMenu && <button className="mobile-scrim" onClick={() => setMobileMenu(false)} aria-label="Close menu" />}

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu-button" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Toggle menu"><Menu size={20} /></button>
          <div className="breadcrumb">Workspace <span>/</span> <strong>{page === "history" ? "Quiz history" : view === "results" ? "Quiz results" : view === "taking" ? "Taking quiz" : "Create a quiz"}</strong></div>
          
<div className="topbar-right">
  <span className="top-pill">
    <span className="live-dot" /> {user.email}
  </span>
  <button
    className="secondary-button"
    type="button"
    onClick={handleLogout}
  >
    Log out
  </button>
</div>

        </header>

        <div className="page-content">
          {error && (
            <div className="error-banner" role="alert">
              <XCircle size={18} /><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><XCircle size={16} /></button>
            </div>
          )}

          {page === "create" && view === "setup" && (
            <section className="setup-page">
              <div className="welcome-row">
                <div>
                  <div className="eyebrow"><Sparkles size={14} /> YOUR PERSONAL AI TUTOR</div>
                  <h1>Learn it today.<br /><span>Know it for good.</span></h1>
                  <p className="hero-copy">Turn what you've learned into a focused quiz. Find gaps, understand mistakes, and build real confidence.</p>
                </div>
                <div className="hero-art" aria-hidden="true">
                  <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
                  <div className="art-card art-card-back"><BookOpen size={21} /></div>
                  <div className="art-card art-card-front"><Brain size={35} /><span>Think deeper</span><div className="art-bars"><i /><i /><i /><i /><i /></div></div>
                  <div className="floating-star star-one"><Sparkles size={17} /></div>
                  <div className="floating-star star-two"><Zap size={16} /></div>
                </div>
              </div>

              <div className="stats-strip">
                <div className="stat-item"><span className="stat-icon lavender"><Target size={18} /></span><div><strong>Learn your way</strong><small>Built around your topics</small></div></div>
                <div className="stat-item"><span className="stat-icon mint"><Activity size={18} /></span><div><strong>Understand mistakes</strong><small>Explanations that teach</small></div></div>
                <div className="stat-item"><span className="stat-icon peach"><History size={18} /></span><div><strong>Keep your progress</strong><small>Revisit past quizzes</small></div></div>
              </div>

              <form className="create-card" onSubmit={startQuiz}>
                <div className="section-heading">
                  <div><span className="step-tag">01</span><h2>Create your quiz</h2></div>
                  <span className="required-note">All fields required</span>
                </div>
                <label className="field-label" htmlFor="topic">What have you been learning?</label>
                <textarea id="topic" className="topic-input" rows="3" value={content} onChange={(e) => setContent(e.target.value)} placeholder="e.g. Python functions, loops, and lists — focus on the basics and common mistakes..." />
                <div className="field-hint"><CircleHelp size={14} /> Add a topic, notes, or concepts you want to practise.</div>

                <div className="form-grid">
                  <div>
                    <label className="field-label" htmlFor="count">Number of questions</label>
                    <div className="count-control">
                      <button type="button" onClick={() => setCount((n) => Math.max(1, Number(n) - 1))} aria-label="Decrease questions">−</button>
                      <input id="count" type="number" min="1" max="30" value={count} onChange={(e) => setCount(Math.min(30, Math.max(1, Number(e.target.value) || 1)))} />
                      <button type="button" onClick={() => setCount((n) => Math.min(30, Number(n) + 1))} aria-label="Increase questions">+</button>
                    </div>
                    <div className="field-hint">Choose between 1 and 30</div>
                  </div>
                  <div>
                    <label className="field-label">Difficulty level</label>
                    <div className="level-options">
                      {[
                        { value: "easy", label: "Easy", note: "Build basics", icon: "🌱" },
                        { value: "medium", label: "Medium", note: "Apply ideas", icon: "⚡" },
                        { value: "hard", label: "Hard", note: "Go deeper", icon: "🔥" },
                      ].map((item) => (
                        <button type="button" key={item.value} className={`level-card ${level === item.value ? "selected" : ""}`} onClick={() => setLevel(item.value)}>
                          <span>{item.icon}</span><strong>{item.label}</strong><small>{item.note}</small>{level === item.value && <Check size={14} className="level-check" />}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <button className="primary-button create-button" type="submit" disabled={loading}>
                  {loading ? <><LoaderCircle className="spin" size={18} /> Creating your quiz...</> : <><Sparkles size={18} /> Generate my quiz <ArrowRight size={17} /></>}
                </button>
                <p className="privacy-note"><Zap size={13} /> AI-generated practice, made for your learning goals.</p>
              </form>
            </section>
          )}

          {page === "create" && view === "taking" && currentQuestion && (
            <section className="quiz-page">
              <button className="back-link" onClick={() => { setView("setup"); setError(""); }}><ArrowLeft size={16} /> Leave quiz</button>
              <div className="quiz-header">
                <div><div className="eyebrow"><BookOpen size={14} /> YOUR PRACTICE SESSION</div><h1>{quiz.topic}</h1><p>Take your time. Focus on what you understand.</p></div>
                <div className="question-count"><strong>{questionIndex + 1}<span> / {quiz.questions.length}</span></strong><small>QUESTION</small></div>
              </div>
              <div className="progress-track"><div style={{ width: `${((questionIndex + 1) / quiz.questions.length) * 100}%` }} /></div>
              <div className="quiz-layout">
                <div className="question-card">
                  <div className="question-meta"><span className="question-number">QUESTION {String(questionIndex + 1).padStart(2, "0")}</span><span className={`type-pill type-${currentQuestion.type}`}>{TYPE_LABELS[currentQuestion.type] || currentQuestion.type}</span></div>
                  <h2>{currentQuestion.question}</h2>
                  {currentQuestion.type === "mcq" && currentQuestion.options?.length > 0 && (
                    <div className="answer-options">
                      {currentQuestion.options.map((option, i) => (
                        <button type="button" key={option} className={`answer-option ${currentAnswers.includes(option) ? "chosen" : ""}`} onClick={() => setSingleAnswer(option)}>
                          <span className="option-letter">{String.fromCharCode(65 + i)}</span><span>{option}</span>{currentAnswers.includes(option) && <CheckCircle2 className="option-check" size={18} />}
                        </button>
                      ))}
                    </div>
                  )}
                  {currentQuestion.type === "multiple_answer" && currentQuestion.options?.length > 0 && (
                    <>
                      <p className="select-hint">Select every answer you think is correct.</p>
                      <div className="answer-options">
                        {currentQuestion.options.map((option, i) => (
                          <button type="button" key={option} className={`answer-option ${currentAnswers.includes(option) ? "chosen" : ""}`} onClick={() => toggleMultipleAnswer(option)}>
                            <span className={`option-letter checkbox-letter ${currentAnswers.includes(option) ? "checked" : ""}`}>{currentAnswers.includes(option) ? <Check size={14} /> : String.fromCharCode(65 + i)}</span><span>{option}</span>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                  {(currentQuestion.type === "code" || currentQuestion.type === "theory" || !currentQuestion.options?.length) && (
                    <div className="written-answer">
                      <label className="field-label" htmlFor="written-answer">{currentQuestion.type === "code" ? "Write your code or answer" : "Your answer"}</label>
                      <textarea id="written-answer" rows={currentQuestion.type === "code" ? 7 : 5} value={currentAnswers[0] || ""} onChange={(e) => setSingleAnswer(e.target.value)} placeholder={currentQuestion.type === "code" ? "Write your code here..." : "Explain your answer in your own words..."} />
                    </div>
                  )}
                  <div className="question-footer">
                    <button className="secondary-button" disabled={questionIndex === 0} onClick={() => setQuestionIndex((i) => i - 1)}><ArrowLeft size={16} /> Previous</button>
                    {questionIndex < quiz.questions.length - 1 ? (
                      <button className="primary-button" onClick={() => setQuestionIndex((i) => i + 1)}>Next question <ArrowRight size={16} /></button>
                    ) : (
                      <button className="primary-button" disabled={loading} onClick={submitQuiz}>{loading ? <LoaderCircle size={17} className="spin" /> : <CheckCircle2 size={17} />} Submit quiz</button>
                    )}
                  </div>
                </div>
                <aside className="quiz-side-card">
                  <div className="side-card-icon"><Target size={20} /></div><h3>Stay curious</h3><p>It's okay if you're unsure. Your results will help you find what to practise next.</p>
                  <div className="mini-progress"><div><span>Answered</span><strong>{completedCount}/{quiz.questions.length}</strong></div><div className="mini-track"><div style={{ width: `${(completedCount / quiz.questions.length) * 100}%` }} /></div></div>
                  <div className="question-jump"><span>JUMP TO QUESTION</span><div>{quiz.questions.map((_, i) => <button key={i} className={`${i === questionIndex ? "current" : ""} ${(answers[i] || []).some((a) => a.trim()) ? "answered" : ""}`} onClick={() => setQuestionIndex(i)}>{i + 1}</button>)}</div></div>
                </aside>
              </div>
            </section>
          )}

          {page === "create" && view === "results" && (
            <section className="results-page">
              <div className="results-hero">
                <div className="result-trophy"><Trophy size={34} /></div>
                <div className="eyebrow">QUIZ COMPLETE</div>
                <h1>{percentage >= 80 ? "Fantastic work!" : percentage >= 50 ? "Good progress!" : "Every attempt teaches you."}</h1>
                <p>You finished <strong>{quiz?.topic}</strong>. Review the explanations below to make the concepts stick.</p>
                <div className="score-ring" style={{ "--score": `${percentage}%` }}><div><strong>{percentage}%</strong><small>YOUR SCORE</small></div></div>
                <div className="result-stats"><div><strong>{score}/{results.length}</strong><span>Correct answers</span></div><div><strong>{results.length - score}</strong><span>To review</span></div><div><strong>{quiz?.questions.length || 0}</strong><span>Total questions</span></div></div>
              </div>
              <div className="results-heading"><div><div className="eyebrow">LEARN FROM EVERY ANSWER</div><h2>Answer review</h2></div><button className="secondary-button" onClick={goCreate}><RotateCcw size={16} /> New quiz</button></div>
              <div className="review-list">
                {results.map((result, i) => (
                  <article className={`review-card ${result.is_correct ? "review-correct" : "review-wrong"}`} key={`${i}-${result.question}`}>
                    <div className="review-status">{result.is_correct ? <CheckCircle2 size={19} /> : <XCircle size={19} />}</div>
                    <div className="review-body"><div className="review-kicker">QUESTION {String(i + 1).padStart(2, "0")} · {result.is_correct ? "CORRECT" : "KEEP PRACTISING"}</div><h3>{result.question}</h3>
                      <div className="answer-comparison"><div><span>Your answer</span><p>{(result.user_answer || []).join(", ") || "No answer provided"}</p></div><div><span>Correct answer</span><p>{(result.correct_answer || []).join(", ")}</p></div></div>
                      <div className="explanation"><Sparkles size={16} /><div><strong>Explanation</strong><p>{result.description}</p></div></div>
                    </div>
                  </article>
                ))}
              </div>
              <div className="bottom-cta"><div><strong>Ready to keep learning?</strong><p>A short practice session can make a big difference.</p></div><button className="primary-button" onClick={goCreate}>Create another quiz <ArrowRight size={16} /></button></div>
            </section>
          )}

          {page === "history" && view === "history" && (
            <section className="history-page">
              <div className="page-title-row">
                <div>
                  <div className="eyebrow">
                    <History size={14} /> YOUR LEARNING JOURNEY
                  </div>
                  <h1>Quiz history</h1>
                  <p>Every attempt is progress. Revisit what you've practised.</p>
                </div>

                <button className="primary-button" onClick={goCreate}>
                  <Sparkles size={17} /> New quiz
                </button>
              </div>

              <div className="history-summary">
                <div className="history-summary-icon">
                  <BookOpen size={20} />
                </div>
                <div>
                  <strong>
                    {history.length} saved{" "}
                    {history.length === 1 ? "quiz" : "quizzes"}
                  </strong>
                  <p>Your completed practice sessions, all in one place.</p>
                </div>
              </div>

              <div className="history-search">
                <Search size={19} />
                <input
                  type="search"
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  placeholder="Search by topic, question, date or score..."
                  aria-label="Search quiz history"
                />

                {historySearch && (
                  <button
                    type="button"
                    onClick={() => setHistorySearch("")}
                    aria-label="Clear search"
                  >
                    <XCircle size={17} />
                  </button>
                )}
              </div>

              {loading && !history.length ? (
                <div className="loading-state">
                  <LoaderCircle className="spin" size={25} />
                  <span>Loading your history...</span>
                </div>
              ) : history.length === 0 ? (
                <div className="empty-state">
                  <div><History size={28} /></div>
                  <h2>Your learning story starts here</h2>
                  <p>
                    Complete your first quiz and it will appear here for future review.
                  </p>
                  <button className="primary-button" onClick={goCreate}>
                    Create your first quiz <ArrowRight size={16} />
                  </button>
                </div>
              ) : filteredHistory.length === 0 ? (
                <div className="empty-state">
                  <div><Search size={28} /></div>
                  <h2>No matching quizzes found</h2>
                  <p>
                    Try another topic or question, or clear your search.
                  </p>
                  <button
                    className="secondary-button"
                    onClick={() => setHistorySearch("")}
                  >
                    Clear search
                  </button>
                </div>
              ) : (
                <div className="history-table">
                  <div className="history-table-head">
                    <span>QUIZ TOPIC</span>
                    <span>DATE</span>
                    <span>SCORE</span>
                    <span />
                  </div>

                  {filteredHistory.map((item) => {
                    const topic =
                      item.quiz?.topic || item.topic || "Untitled quiz";

                    const total =
                      item.results?.length ?? item.total ?? item.question_count ?? 0;

                    return (
                      <button
                        className="history-row"
                        key={item.id}
                        onClick={() => openHistoryItem(item.id)}
                      >
                        <span className="history-topic">
                          <span className="history-topic-icon">
                            <BookOpen size={17} />
                          </span>
                          <span>
                            <strong>{topic}</strong>
                            <small>{total} questions</small>
                          </span>
                        </span>

                        <span className="history-date">
                          {formatDate(item.date)}
                        </span>

                        <span className="history-score">
                          <strong>{item.score ?? 0}/{total}</strong>
                          <small>
                            {total
                              ? Math.round(((item.score ?? 0) / total) * 100)
                              : 0}%
                          </small>
                        </span>

                        <span className="history-open">
                          <ArrowRight size={17} />
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>
          )}

          {page === "history" && view === "historyDetail" && historyDetail && (
            <section className="results-page">
              <button className="back-link" onClick={() => { setView("history"); setHistoryDetail(null); }}><ArrowLeft size={16} /> Back to history</button>
              <div className="page-title-row detail-title"><div><div className="eyebrow">PAST QUIZ · {formatDate(historyDetail.date)}</div><h1>{historyDetail.quiz.topic}</h1><p>Review your answers and the explanations from this attempt.</p></div><div className="detail-score"><strong>{historyDetail.score}/{historyDetail.results.length}</strong><span>Score</span></div></div>
              <div className="review-list">
                {historyDetail.results.map((result, i) => (
                  <article className={`review-card ${result.is_correct ? "review-correct" : "review-wrong"}`} key={`${i}-${result.question}`}>
                    <div className="review-status">{result.is_correct ? <CheckCircle2 size={19} /> : <XCircle size={19} />}</div>
                    <div className="review-body"><div className="review-kicker">QUESTION {String(i + 1).padStart(2, "0")} · {result.is_correct ? "CORRECT" : "KEEP PRACTISING"}</div><h3>{result.question}</h3>
                      <div className="answer-comparison"><div><span>Your answer</span><p>{(result.user_answer || []).join(", ") || "No answer provided"}</p></div><div><span>Correct answer</span><p>{(result.correct_answer || []).join(", ")}</p></div></div>
                      <div className="explanation"><Sparkles size={16} /><div><strong>Explanation</strong><p>{result.description}</p></div></div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
