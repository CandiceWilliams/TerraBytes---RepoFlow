import axios from "axios";
import { useState } from "react";
import "@fontsource/poppins";


export default function RepoLink({ onRepoSubmitted }) {

    const [repoUrl, setRepoUrl] = useState('');
    const [message, setMessage] = useState('');
    const [isError, setIsError] = useState(false);
    
      // Handles changes to the input field, updating the state
      const handleInputChange = (event) => {
        setRepoUrl(event.target.value);
      };
    
      // Handles the form submission
      const handleSubmit = async (event) => {
        event.preventDefault();
        setMessage('Analyzing repository...');
        setIsError(false);

        if (!repoUrl.trim()) {
          setMessage('Please enter a GitHub repository URL.');
          setIsError(true);
          return;
        }

        try {
          const response = await axios.post('http://127.0.0.1:8000/api/receive-repo', { repoUrl: repoUrl }, {
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          if (!response.data.err) {
            setMessage('Repository URL received successfully!');
            // Call the prop function to notify the parent component
            onRepoSubmitted(); 
          } else {
            setMessage('Repository URL is not valid. Please enter a valid GitHub repository URL.');
            setIsError(true);
          }
        } catch (error) {
          console.error("Error submitting URL:", error);
          setMessage('An error occurred. Please check the console for more details.');
          setIsError(true);
        }
      };

  return (/*
     <>
       <div className="bg-dark text-light min-vh-200 d-flex align-items-center justify-content-center p-4">*/
      <div>
      {/* Main title of the application
        <div className="d-flex align-items-center justify-content-center mb-4">
           <h1 className="display-4 fw-bold text-light text-center">
               RepoFlow
             </h1>
           </div> */}

           {/* Descriptive text for the user */}
           {/* <p className="text-center text-white mb-5 lead">
             Paste your GitHub Repository link and we’ll analyze it for you! 
           </p> */}

           {/* Display messages to the user */}
           {message && (
             <div className={`alert ${isError ? 'alert-danger' : 'alert-info'}`} role="alert">
               {message}
             </div>
           )}

                 <form onSubmit={handleSubmit}>
                 <div className="mb-3">
                   <label htmlFor="repo-url" className="form-label visually-hidden">
                   GitHub Repository URL
                   </label>
                   <input
                   id="repo-url"
                   type="text"
                   placeholder="https://github.com/owner/repository"
                   value={repoUrl}
                   onChange={handleInputChange}
                   className="form-control form-control-lg bg-secondary text-white border-0"
                   required
                   size={50} // Set the length of the text box
                   style={{ ...styles.input, width: 'auto' }} // Optional: override width if needed
                   />
                 </div>

                 {/* Submit button */}
             <button
             style={styles.button}
               type="submit"
               className="btn btn-primary btn-lg w-40 fw-bold shadow-sm"
             >
               Analyze Repo
             </button>
           </form>
         </div>
      //  </div>
    //  </>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#012A4A', // Dark blue background
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
    textAlign: 'center',
    fontFamily: '"Poppins", sans-serif',
  },
  logo: {
    width: 160, // Adjust size as per screenshot
    height: 160, // Adjust size as per screenshot
    marginBottom: 24,
    objectFit: 'cover',
  },
  title: {
    fontSize: 48, // Large font size for "RepoFlow"
    fontWeight: 'bold',
    marginBottom: 8,
  },
  // subtitle: {
  //   fontSize: 18, // Increased font size for subtitle
  //   fontWeight: 'normal', // Can be 'bold' or 'normal' based on preference
  //   marginBottom: 24,
  //   color: '#D0D6DB', // This color looks good for contrast
  // },
  input: {
    width: '100%',
    maxWidth: 600,
    padding: '14px 20px',
    borderRadius: 30, // More rounded corners
    backgroundColor: '#4A6173', // Darker input background
    border: 'none',
    color: 'white',
    fontSize: 16,
    marginBottom: 24,
    outline: 'none',
    textAlign: 'center', // Center placeholder text
  },
  button: {
    padding: '14px 32px',
    backgroundColor: '#89C2D9', // Light blue button color
    color: '#012A4A', // Dark blue text on button
    fontWeight: 'bold',
    fontSize: 16,
    border: 'none',
    borderRadius: 12, // Rounded button
    cursor: 'pointer',
  },
};