import React, { useState } from 'react';
import Homepage from './pages/HomePage.jsx';

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
        <Homepage onAnalyze={handleAnalyze} />
      ) : (
        <div style={{ padding: '2rem', color: '#003052' }}>
          <h2>Analyzing repo: {repo}</h2>
          {/* You can replace this with the repo analysis screen */}
        </div>
      )}
    </>
  );
}

export default App;
