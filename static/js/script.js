const form = document.getElementById("documentForm");

const documentType = document.getElementById("documentType");

const userDetails = document.getElementById("userDetails");

const generateButton =
    document.getElementById("generateButton");

const buttonText =
    document.getElementById("buttonText");

const loadingSpinner =
    document.getElementById("loadingSpinner");

const errorMessage =
    document.getElementById("errorMessage");

const resultSection =
    document.getElementById("resultSection");

const resultTitle =
    document.getElementById("resultTitle");

const generatedDocument =
    document.getElementById("generatedDocument");

const copyButton =
    document.getElementById("copyButton");

const downloadButton =
    document.getElementById("downloadButton");

const regenerateButton =
    document.getElementById("regenerateButton");


let currentDocumentType = "";


/* ---------------------------------------------------------
   Show error
--------------------------------------------------------- */

function showError(message) {

    errorMessage.textContent = message;

    errorMessage.classList.remove("hidden");
}


/* ---------------------------------------------------------
   Hide error
--------------------------------------------------------- */

function hideError() {

    errorMessage.textContent = "";

    errorMessage.classList.add("hidden");
}


/* ---------------------------------------------------------
   Loading state
--------------------------------------------------------- */

function setLoading(isLoading) {

    generateButton.disabled = isLoading;

    if (isLoading) {

        buttonText.textContent = "Generating...";

        loadingSpinner.classList.remove("hidden");

    } else {

        buttonText.textContent = "Generate Document";

        loadingSpinner.classList.add("hidden");
    }
}


/* ---------------------------------------------------------
   Generate document
--------------------------------------------------------- */

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    hideError();

    const selectedType =
        documentType.value.trim();

    const details =
        userDetails.value.trim();


    if (!selectedType) {

        showError(
            "Please select a document type."
        );

        return;
    }


    if (!details) {

        showError(
            "Please enter the document details."
        );

        return;
    }


    setLoading(true);


    try {

        const response = await fetch(
            "/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    document_type: selectedType,
                    user_details: details
                })
            }
        );


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to generate the document."
            );
        }


        currentDocumentType =
            data.document_type;


        resultTitle.textContent =
            data.document_type;


        generatedDocument.value =
            data.document;


        resultSection.classList.remove(
            "hidden"
        );


        resultSection.scrollIntoView({
            behavior: "smooth"
        });


    } catch (error) {

        console.error(error);

        showError(
            error.message ||
            "Something went wrong."
        );

    } finally {

        setLoading(false);
    }

});


/* ---------------------------------------------------------
   Copy document
--------------------------------------------------------- */

copyButton.addEventListener(
    "click",
    async function () {

        const text =
            generatedDocument.value.trim();


        if (!text) {

            showError(
                "There is no document to copy."
            );

            return;
        }


        try {

            await navigator.clipboard.writeText(
                text
            );

            const originalText =
                copyButton.textContent;

            copyButton.textContent =
                "Copied!";


            setTimeout(function () {

                copyButton.textContent =
                    originalText;

            }, 1500);


        } catch (error) {

            showError(
                "Unable to copy the document."
            );
        }

    }
);


/* ---------------------------------------------------------
   Download PDF
--------------------------------------------------------- */

downloadButton.addEventListener(
    "click",
    async function () {

        hideError();


        const documentText =
            generatedDocument.value.trim();


        if (!documentText) {

            showError(
                "There is no document to download."
            );

            return;
        }


        downloadButton.disabled = true;

        const originalText =
            downloadButton.textContent;

        downloadButton.textContent =
            "Preparing PDF...";


        try {

            const response = await fetch(
                "/download-pdf",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        document: documentText,
                        document_type:
                            currentDocumentType
                    })
                }
            );


            if (!response.ok) {

                let errorMessageText =
                    "Unable to create PDF.";

                try {

                    const data =
                        await response.json();

                    if (data.error) {
                        errorMessageText =
                            data.error;
                    }

                } catch (ignored) {
                    // Keep default error
                }

                throw new Error(
                    errorMessageText
                );
            }


            const blob =
                await response.blob();


            const url =
                window.URL.createObjectURL(blob);


            const link =
                document.createElement("a");


            link.href = url;

            link.download =
                "LegalEase_Document.pdf";


            document.body.appendChild(link);

            link.click();

            link.remove();

            window.URL.revokeObjectURL(url);


        } catch (error) {

            console.error(error);

            showError(
                error.message ||
                "Unable to download PDF."
            );

        } finally {

            downloadButton.disabled = false;

            downloadButton.textContent =
                originalText;
        }

    }
);


/* ---------------------------------------------------------
   Generate again
--------------------------------------------------------- */

regenerateButton.addEventListener(
    "click",
    function () {

        resultSection.classList.add(
            "hidden"
        );

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }
);