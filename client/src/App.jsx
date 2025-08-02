import { useState } from 'react'
import RepoLink from './RepoLink.jsx';
import WorkSpace from './workspace.jsx';


function App() {
  const [repoReceived, setRepoReceived] = useState(false);

  return (
    <>
      {!repoReceived ? (
        <RepoLink /> 
      ) : (
        <WorkSpace />
      )}
    </>
  );
}

export default App;
