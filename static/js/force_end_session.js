
    setInterval(async () => {
        try {
            const response = await fetch("/evote/booth-status");
            const data = await response.json();

            // If PO has ended the session
            if (data.active === false) {
                window.location.href = "/evote/waiting";
            }
        } catch (err) {
            console.error("Session check failed", err);
        }
    }, 2000); // check every 2 seconds

