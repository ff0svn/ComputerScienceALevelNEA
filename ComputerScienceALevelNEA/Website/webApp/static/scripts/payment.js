console.log("Hello World!")

// Get Stripe public key 
fetch("/config")
.then((result) => { return result.json(); })

.then((data) => {
    // Initialize Stripe.js
    const stripe = Stripe(data.publicKey);

    // On button click
    document.querySelector("#submitButton").addEventListener("click", () => {
        // Get Checkout Session ID
        fetch("/checkoutSession?videoID=" + videoID)
        .then((result) => { return result.json(); })

        .then((data) => {
            console.log(data);
            // Redirect to Stripe Checkout
            return stripe.redirectToCheckout({sessionId: data.sessionId})
        })

        .then((res) => {
            console.log(res);
        });
    });
});