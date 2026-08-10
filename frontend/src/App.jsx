import './App.css';
import AppShell from './components/layout/AppShell.jsx';
import ComplaintForm from './components/complaint/ComplaintForm.jsx';
import CopilotPanel from './components/copilot/CopilotPanel.jsx';

function App() {
  return (
    <AppShell>
      <ComplaintForm />
      <CopilotPanel />
    </AppShell>
  );
}

export default App;
