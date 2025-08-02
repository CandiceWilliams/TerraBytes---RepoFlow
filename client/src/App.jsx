import { useState } from 'react'
import RepoLink from './repoLink.jsx';
import axios from 'axios';
import WorkSpace from './workspace.jsx';


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
