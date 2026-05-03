import { useState } from "react";
import HomeScreen from "./components/HomeScreen.jsx";
import ExtendedSession from "./components/ExtendedSession.jsx";
import MCQSession from "./components/MCQSession.jsx";
import SessionSummary from "./components/SessionSummary.jsx";

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-white">
      <main>{children}</main>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("home");
  // Extended session state
  const [extendedSession, setExtendedSession] = useState(null);
  const [extendedResults, setExtendedResults] = useState(null);
  // MCQ session state
  const [mcqSession, setMcqSession] = useState(null);
  const [mcqResults, setMcqResults] = useState(null);

  function handleExtendedStart(session) {
    setExtendedSession(session);
    setExtendedResults(null);
    setView("extended");
  }

  function handleExtendedDone(results) {
    setExtendedResults(results);
    setView("summary-extended");
  }

  function handleMcqStart(session) {
    setMcqSession(session);
    setMcqResults(null);
    setView("mcq");
  }

  function handleMcqDone(results) {
    setMcqResults(results);
    setView("summary-mcq");
  }

  function goHome() {
    setView("home");
    setExtendedSession(null);
    setMcqSession(null);
    setExtendedResults(null);
    setMcqResults(null);
  }

  const viewContent = (() => {
    if (view === "home") {
      return (
        <HomeScreen
          onExtendedStart={handleExtendedStart}
          onMcqStart={handleMcqStart}
        />
      );
    }
    if (view === "extended") {
      return (
        <ExtendedSession
          session={extendedSession}
          onDone={handleExtendedDone}
          onHome={goHome}
        />
      );
    }
    if (view === "mcq") {
      return (
        <MCQSession
          session={mcqSession}
          onDone={handleMcqDone}
          onHome={goHome}
        />
      );
    }
    if (view === "summary-extended") {
      return (
        <SessionSummary
          type="extended"
          topicName={extendedSession?.topic_name}
          results={extendedResults}
          onTryAgain={goHome}
          onHome={goHome}
        />
      );
    }
    if (view === "summary-mcq") {
      return (
        <SessionSummary
          type="mcq"
          topicName={mcqSession?.topic_name}
          results={mcqResults}
          onTryAgain={goHome}
          onHome={goHome}
        />
      );
    }
    return null;
  })();

  return <Layout>{viewContent}</Layout>;
}
