import { useState } from 'react'
import RepoLink from './repoLink.jsx';


function App() {
  const [repoReceived, setRepoReceived] = useState(false);

  return (
    <>
      {!repoReceived ? (
        <RepoLink /> 
      ) : (
        <div>Next Stage Goes Here</div>
      )}
    </>
  );
}

export default App
