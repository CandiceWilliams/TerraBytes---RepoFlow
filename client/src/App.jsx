import React, { useState } from 'react';
import Homepage from './pages/HomePage.jsx';
import ChoicePage from './pages/ChoicePage.jsx';

function App() {
  const [repo, setRepo] = useState(null);

  const handleAnalyze = (repoUrl) => {
    console.log('Repo URL received in App:', repoUrl);
    setRepo(repoUrl);

    // You could route to another screen here or call FastAPI
  };

  return (
    <>
      {!repo ? (
        // 1️⃣ Show your existing HomePage
        <Homepage onAnalyze={handleAnalyze} />
      ) : (
        // 2️⃣ Once the button is clicked, show ChoicePage
        <ChoicePage
          onSelect={(choice) => {
            console.log('User wants to edit:', choice);
            // later: set another state (e.g. `section`) to drive WorkSpace
          }}
        />
      )}
    </>
  );
}

export default App;
