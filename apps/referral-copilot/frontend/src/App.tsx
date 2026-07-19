import { Route, Routes } from "react-router-dom";
import { useAppState } from "./state/AppState";
import { GovernedCopyProvider } from "./i18n/governed";
import { STRINGS } from "./i18n/copy";
import { Header } from "./components/Header";
import { Landing } from "./pages/Landing";
import { Intake } from "./pages/Intake";
import { Confirm } from "./pages/Confirm";
import { Results } from "./pages/Results";
import { AskData } from "./pages/AskData";
import { Profile } from "./pages/Profile";

function App() {
  const { language } = useAppState();
  const strings = STRINGS[language];

  return (
    <GovernedCopyProvider language={language}>
      <div className="app-shell">
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/intake" element={<Intake />} />
          <Route path="/confirm" element={<Confirm />} />
          <Route path="/results" element={<Results />} />
          <Route path="/ask" element={<AskData />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        <footer className="footer">
          <p className="footer-boundary">🛡️ {strings.boundary}</p>
        </footer>
      </div>
    </GovernedCopyProvider>
  );
}

export default App;
