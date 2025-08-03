import React from "react";

/* Adjust styles for textarea and button row */
const textareaContainerStyle = {
  position: "relative",
  width: "100%",
  maxWidth: "600px",
  marginBottom: "1.5rem",
};

const textareaStyle = {
  width: "100%",
  height: "300px",
  padding: "1rem 3rem 1rem 1.2rem",
  borderRadius: "16px",
  fontSize: "1rem",
  backgroundColor: "#294b63",
  color: "white",
  border: "none",
  outline: "none",
  resize: "vertical",
  boxSizing: "border-box",
};

const buttonRowStyle = {
  display: "flex",
  gap: "1rem",
  width: "100%",
  maxWidth: "600px",
  marginTop: "1.5rem",
};

const PromptPage = () => {
  return (
    <div
      style={{
        backgroundColor: "#001F3F",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <h1
        style={{
          color: "white",
          fontSize: "2.5rem",
          fontWeight: "bold",
          textAlign: "center",
          marginBottom: "2rem",
        }}
      >
        Let’s start coding!
      </h1>
      {/* Input area */}
      <div style={textareaContainerStyle}>
        <textarea
          placeholder="Enter your prompt here..."
          style={textareaStyle}
        />
        <button
          type="button"
          style={{
            position: "absolute",
            bottom: "12px",
            right: "12px",
            width: "28px",
            height: "28px",
            padding: 0,
            border: "none",
            background: "none",
            cursor: "pointer",
          }}
          aria-label="Textarea icon button"
        >
          <img
            src="https://cdn.pixabay.com/photo/2020/02/19/07/16/paper-plane-4861531_1280.png"
            alt="Textarea icon"
            style={{
              width: "28px",
              height: "28px",
              display: "block",
            }}
          />
        </button>
      </div>
      {/* Button Row */}
      <div style={buttonRowStyle}>
        <button
          style={{
            flex: 1,
            padding: "0.75rem 1.5rem",
            fontSize: "1rem",
            borderRadius: "12px",
            border: "none",
            backgroundColor: "#a3d4ec",
            color: "#001F3F",
            fontWeight: "bold",
            cursor: "pointer",
            minWidth: "0",
          }}
        >
          <img
            src="https://cdn-icons-png.flaticon.com/512/5728/5728506.png"
            alt="Light Bulb"
            style={{ width: "24px", height: "24px", marginRight: "0.5rem" }}
          />
          Give me suggestions
        </button>
        <button
          style={{
            flex: 1,
            padding: "0.75rem 1.5rem",
            fontSize: "1rem",
            borderRadius: "12px",
            border: "none",
            backgroundColor: "#a3d4ec",
            color: "#001F3F",
            fontWeight: "bold",
            cursor: "pointer",
            minWidth: "0",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            justifyContent: "center",
          }}
        >
          <img
            src="https://www.pngarts.com/files/2/Upload-PNG-Background-Image.png"
            alt="Upload"
            style={{ width: "24px", height: "24px", objectFit: "contain" }}
          />
          Upload your own code file
        </button>
      </div>
    </div>
  );
};
export default PromptPage;