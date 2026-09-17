const fileInput = document.getElementById("fileInput");
const uploadButton = document.getElementById("uploadButton");
const sendButton = document.getElementById("sendButton");
const selectedFile = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const message = document.getElementById("message");
const dropZone = document.getElementById("dropZone");

let currentFile = null;

function selectFile(file) {
    if (!file) return;
    currentFile = file;
    fileName.textContent = file.name;
    selectedFile.hidden = false;
    message.textContent = "Ready to upload.";
}

uploadButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("dragging");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("dragging");
    });
});

dropZone.addEventListener("drop", (event) => {
    selectFile(event.dataTransfer.files[0]);
});

sendButton.addEventListener("click", async () => {
    if (!currentFile) return;

    const formData = new FormData();
    formData.append("file", currentFile);

    sendButton.disabled = true;
    uploadButton.disabled = true;
    message.textContent = "Uploading...";

    try {
        const response = await fetch("/api/v1/upload", {
            method: "POST",
            body: formData,
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "Upload failed.");

        message.textContent = result.message;
    } catch (error) {
        message.textContent = error.message || "Something went wrong.";
    } finally {
        sendButton.disabled = false;
        uploadButton.disabled = false;
    }
});
